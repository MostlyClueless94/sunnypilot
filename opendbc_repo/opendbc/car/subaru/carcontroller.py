import copy
import numpy as np
from openpilot.common.params import Params
from opendbc.can import CANPacker
from opendbc.car import Bus, DT_CTRL, make_tester_present_msg, structs
from opendbc.car.carlog import carlog
from opendbc.car.lateral import apply_driver_steer_torque_limits, apply_std_steer_angle_limits, common_fault_avoidance
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.subaru import subarucan
from opendbc.car.subaru.values import DBC, GLOBAL_ES_ADDR, OUTBACK_ALPHA_LONG_PHASE, CanBus, CarControllerParams, SubaruFlags

from opendbc.sunnypilot.car.subaru.stop_and_go import SnGCarController

# FIXME: These limits aren't exact. The real limit is more than likely over a larger time period and
# involves the total steering angle change rather than rate, but these limits work well for now
MAX_STEER_RATE = 25  # deg/s
MAX_STEER_RATE_FRAMES = 7  # tx control frames needed before torque can be cut
MADS_ONLY_MIN_SPEED = 2.24  # m/s (5 mph)
MADS_ONLY_MAX_STEER_ANGLE = 120.0  # deg
LOW_SPEED_SMOOTH_MAX_SPEED = 4.4704  # m/s (10 mph)
LOW_SPEED_SMOOTH_DEADBAND_MAX = 0.8  # deg at 0 mph
LOW_SPEED_SMOOTH_ALPHA_MIN = 0.35  # blend factor at 0 mph
LOW_SPEED_STRAIGHT_STABILITY_TARGET_MAX = 3.5  # deg, keep narrowly scoped to straight-ahead chatter
LOW_SPEED_STRAIGHT_STABILITY_STEER_MAX = 6.0  # deg, bypass real turning maneuvers
LOW_SPEED_STRAIGHT_CENTER_HOLD_TARGET_MAX = 1.0  # deg, hold near-center targets steady
LOW_SPEED_STRAIGHT_CENTER_HOLD_STEER_MAX = 2.5  # deg, measured wheel angle window for center hold
LOW_SPEED_STRAIGHT_SIGN_RELEASE_TARGET = 2.0  # deg, allow small opposite-sign moves only after persistence
LOW_SPEED_STRAIGHT_SIGN_RELEASE_FRAMES = 5  # 50 ms at 100 Hz
LOW_SPEED_STRAIGHT_SIGN_EPSILON = 0.05  # deg, ignore numerical noise around zero
HUMAN_TURN_STEER_ANGLE_THRESHOLD = 45.0
LONG_MESSAGE_STALE_MAX_FRAMES = 50  # 0.5s at 100Hz

LONGITUDINAL_SOURCE_KEYS = {
  "es_status": ("CHECKSUM", "Signal1", "Cruise_Fault", "Cruise_RPM", "Cruise_Activated", "Brake_Lights", "Cruise_Hold", "Signal3", "COUNTER"),
  "es_brake": ("CHECKSUM", "Signal1", "Brake_Pressure", "AEB_Status", "Cruise_Brake_Lights", "Cruise_Brake_Fault",
               "Cruise_Brake_Active", "Cruise_Activated", "Signal3", "COUNTER"),
  "es_distance": ("CHECKSUM", "Signal1", "Cruise_Fault", "Cruise_Throttle", "Signal2", "Car_Follow", "Low_Speed_Follow",
                  "Cruise_Soft_Disable", "Signal7", "Cruise_Brake_Active", "Distance_Swap", "Cruise_EPB", "Signal4",
                  "Close_Distance", "Signal5", "Cruise_Cancel", "Cruise_Set", "Cruise_Resume", "Signal6", "COUNTER"),
}

# ICBM button press rate limit: one press per 50 ms
ICBM_BUTTON_MIN_INTERVAL_FRAMES = max(1, int(round(0.05 / DT_CTRL)))


class CarController(CarControllerBase, SnGCarController):
  def __init__(self, dbc_names, CP, CP_SP):
    CarControllerBase.__init__(self, dbc_names, CP, CP_SP)
    SnGCarController.__init__(self, CP, CP_SP)
    self.apply_torque_last = 0
    self.apply_angle_last = 0

    self.cruise_button_prev = 0
    self.steer_rate_counter = 0
    self._debug_state = {}
    self.longitudinal_msg_state = {
      name: {"counter": None, "last_update_frame": -LONG_MESSAGE_STALE_MAX_FRAMES - 1, "msg": None}
      for name in LONGITUDINAL_SOURCE_KEYS
    }

    # ICBM (stock ACC set-speed button emulation) state
    self.icbm_last_button_frame = 0
    self._icbm_available = getattr(CP_SP, "intelligentCruiseButtonManagementAvailable", False)
    if self._icbm_available:
      try:
        from opendbc.sunnypilot.car.subaru.icbm import IntelligentCruiseButtonManagementInterface
        self.icbm_interface = IntelligentCruiseButtonManagementInterface(CP, CP_SP)
      except ImportError:
        self.icbm_interface = None
        self._icbm_available = False
    else:
      self.icbm_interface = None

    self.p = CarControllerParams(CP)
    self.packer = CANPacker(DBC[CP.carFingerprint][Bus.pt])
    self.params = Params()
    self.enable_human_turn_detection = True
    self.disable_bp_lat_ui = False
    self.low_speed_straight_pending_direction = 0
    self.low_speed_straight_pending_frames = 0

  def _log_transition(self, key, value, message):
    if self._debug_state.get(key) != value:
      carlog.info(f"subaru[{self.CP.carFingerprint}] {message}")
      self._debug_state[key] = value

  def _get_low_speed_smoothed_angle_target(self, raw_target, v_ego):
    speed_factor = np.clip(v_ego / LOW_SPEED_SMOOTH_MAX_SPEED, 0.0, 1.0)
    deadband = (1.0 - speed_factor) * LOW_SPEED_SMOOTH_DEADBAND_MAX
    delta = raw_target - self.apply_angle_last

    if abs(delta) <= deadband:
      return self.apply_angle_last

    delta = delta - deadband if delta > 0 else delta + deadband
    alpha = np.interp(v_ego, [0.0, LOW_SPEED_SMOOTH_MAX_SPEED], [LOW_SPEED_SMOOTH_ALPHA_MIN, 1.0])
    return self.apply_angle_last + alpha * delta

  def _reset_low_speed_straight_stability(self):
    self.low_speed_straight_pending_direction = 0
    self.low_speed_straight_pending_frames = 0

  @staticmethod
  def _angle_direction(angle: float) -> int:
    if angle > LOW_SPEED_STRAIGHT_SIGN_EPSILON:
      return 1
    if angle < -LOW_SPEED_STRAIGHT_SIGN_EPSILON:
      return -1
    return 0

  def _get_low_speed_stable_angle_target(self, raw_target: float, CS) -> float:
    if CS.out.vEgoRaw >= LOW_SPEED_SMOOTH_MAX_SPEED or CS.out.standstill or CS.out.steeringPressed:
      self._reset_low_speed_straight_stability()
      return raw_target

    measured_angle = CS.out.steeringAngleDeg
    if abs(raw_target) > LOW_SPEED_STRAIGHT_STABILITY_TARGET_MAX or \
       abs(measured_angle) > LOW_SPEED_STRAIGHT_STABILITY_STEER_MAX or \
       abs(self.apply_angle_last) > LOW_SPEED_STRAIGHT_STABILITY_STEER_MAX:
      self._reset_low_speed_straight_stability()
      return raw_target

    if abs(raw_target) <= LOW_SPEED_STRAIGHT_CENTER_HOLD_TARGET_MAX and \
       abs(measured_angle) <= LOW_SPEED_STRAIGHT_CENTER_HOLD_STEER_MAX:
      self._reset_low_speed_straight_stability()
      return 0.0

    target_direction = self._angle_direction(raw_target)
    current_direction = self._angle_direction(self.apply_angle_last)
    if target_direction == 0:
      self._reset_low_speed_straight_stability()
      return 0.0

    needs_release = abs(raw_target) < LOW_SPEED_STRAIGHT_SIGN_RELEASE_TARGET and \
      (current_direction == 0 or current_direction != target_direction)
    if not needs_release:
      self._reset_low_speed_straight_stability()
      return raw_target

    if self.low_speed_straight_pending_direction != target_direction:
      self.low_speed_straight_pending_direction = target_direction
      self.low_speed_straight_pending_frames = 1
    else:
      self.low_speed_straight_pending_frames += 1

    if self.low_speed_straight_pending_frames < LOW_SPEED_STRAIGHT_SIGN_RELEASE_FRAMES:
      return 0.0 if current_direction == 0 else self.apply_angle_last

    self._reset_low_speed_straight_stability()
    return raw_target

  def _update_params(self):
    self.enable_human_turn_detection = self.params.get_bool("enable_human_turn_detection")
    self.disable_bp_lat_ui = self.params.get_bool("disable_BP_lat_UI")

  def _human_turn_active(self, CS) -> bool:
    if self.disable_bp_lat_ui or not self.enable_human_turn_detection:
      return False

    return bool(CS.out.steeringPressed and abs(CS.out.steeringAngleDeg) > HUMAN_TURN_STEER_ANGLE_THRESHOLD)

  def _update_longitudinal_message_state(self, name, msg):
    state = self.longitudinal_msg_state[name]
    required_keys = LONGITUDINAL_SOURCE_KEYS[name]
    if not all(k in msg for k in required_keys):
      return False

    counter = msg["COUNTER"]
    if state["counter"] != counter:
      state["counter"] = counter
      state["last_update_frame"] = self.frame
      state["msg"] = copy.copy(msg)

    return (self.frame - state["last_update_frame"]) <= LONG_MESSAGE_STALE_MAX_FRAMES

  def _get_longitudinal_source_messages(self, CS):
    current_msgs = {
      "es_status": getattr(CS, "es_status_msg", {}),
      "es_brake": getattr(CS, "es_brake_msg", {}),
      "es_distance": getattr(CS, "es_distance_msg", {}),
    }

    valid = True
    for name, msg in current_msgs.items():
      valid &= self._update_longitudinal_message_state(name, msg)

    cached_msgs = {name: self.longitudinal_msg_state[name]["msg"] for name in LONGITUDINAL_SOURCE_KEYS}
    return valid, cached_msgs

  def handle_angle_lateral(self, CC, CS):
    # Angle-LKAS can hard fault during low-speed MADS lateral-only maneuvers.
    # Keep MADS behavior above 5 mph, but block sharp parking-lot style steering in lateral-only mode.
    human_turn_active = self._human_turn_active(CS)
    mads_only = CC.latActive and not CC.enabled
    mads_manual_override = mads_only and CS.out.steeringPressed
    mads_only_ok = CS.out.vEgoRaw > MADS_ONLY_MIN_SPEED and abs(CS.out.steeringAngleDeg) < MADS_ONLY_MAX_STEER_ANGLE
    lkas_request = CC.latActive and (CC.enabled or not mads_only or mads_only_ok) and \
      CS.out.gearShifter == structs.CarState.GearShifter.drive and not CS.out.standstill and not mads_manual_override and not human_turn_active

    inhibit_reason = "none"
    if not CC.latActive:
      inhibit_reason = "lat_inactive"
    elif human_turn_active:
      inhibit_reason = "human_turn"
    elif mads_manual_override:
      inhibit_reason = "manual_override"
    elif CS.out.gearShifter != structs.CarState.GearShifter.drive:
      inhibit_reason = "gear_not_drive"
    elif CS.out.standstill:
      inhibit_reason = "standstill"
    elif mads_only and not mads_only_ok:
      inhibit_reason = "mads_below_min_speed" if CS.out.vEgoRaw <= MADS_ONLY_MIN_SPEED else "mads_angle_limit"

    self._log_transition(
      "angle_lkas_request",
      lkas_request,
      f"angle LKAS request={lkas_request} inhibit={inhibit_reason} latActive={CC.latActive} "
      f"enabled={CC.enabled} vEgo={CS.out.vEgoRaw:.2f} steeringAngle={CS.out.steeringAngleDeg:.2f} "
      f"steeringPressed={CS.out.steeringPressed}",
    )
    self._log_transition("angle_lkas_inhibit", inhibit_reason, f"angle LKAS inhibit={inhibit_reason}")

    steer_target = CC.actuators.steeringAngleDeg
    if lkas_request and CS.out.vEgoRaw < LOW_SPEED_SMOOTH_MAX_SPEED:
      # Low-speed damping to reduce left-right command chatter while retaining large steering authority.
      steer_target = self._get_low_speed_smoothed_angle_target(steer_target, CS.out.vEgoRaw)
      steer_target = self._get_low_speed_stable_angle_target(steer_target, CS)
    else:
      self._reset_low_speed_straight_stability()

    apply_steer = apply_std_steer_angle_limits(
      steer_target,
      self.apply_angle_last,
      CS.out.vEgoRaw,
      CS.out.steeringAngleDeg,
      lkas_request,
      self.p.ANGLE_LIMITS,
    )

    if not lkas_request:
      apply_steer = CS.out.steeringAngleDeg

    self.apply_angle_last = apply_steer

    # Pass the current steering frame counter so ES_LKAS_ANGLE increments correctly.
    # A pinned-at-zero counter causes Steer_Error_1 and the immediate LKAS fault.
    angle_frame_counter = (self.frame // self.p.STEER_STEP) % 0x10
    self._log_transition(
      "angle_lkas_counter_sample",
      angle_frame_counter,
      f"angle LKAS ES_LKAS_ANGLE COUNTER={angle_frame_counter} lkas_request={lkas_request}",
    )
    return subarucan.create_steering_control_angle(self.packer, angle_frame_counter, apply_steer, lkas_request)

  def handle_torque_lateral(self, CC, CS):
    lat_active = CC.latActive and not self._human_turn_active(CS)
    apply_torque = int(round(CC.actuators.torque * self.p.STEER_MAX))

    new_torque = int(round(apply_torque))
    apply_torque = apply_driver_steer_torque_limits(new_torque, self.apply_torque_last, CS.out.steeringTorque, self.p)

    if not lat_active:
      apply_torque = 0

    if self.CP.flags & SubaruFlags.PREGLOBAL:
      msg = subarucan.create_preglobal_steering_control(self.packer, self.frame // self.p.STEER_STEP, apply_torque, lat_active)
    else:
      apply_steer_req = lat_active

      if self.CP.flags & SubaruFlags.STEER_RATE_LIMITED:
        # Steering rate fault prevention
        self.steer_rate_counter, apply_steer_req = common_fault_avoidance(
          abs(CS.out.steeringRateDeg) > MAX_STEER_RATE,
          apply_steer_req,
          self.steer_rate_counter,
          MAX_STEER_RATE_FRAMES,
        )

      msg = subarucan.create_steering_control(self.packer, apply_torque, apply_steer_req)

    self.apply_torque_last = apply_torque
    return msg

  def update(self, CC, CC_SP, CS, now_nanos):
    actuators = CC.actuators
    hud_control = CC.hudControl
    pcm_cancel_cmd = CC.cruiseControl.cancel

    can_sends = []
    self._update_params()

    # *** steering ***
    if (self.frame % self.p.STEER_STEP) == 0:
      if self.CP.flags & SubaruFlags.LKAS_ANGLE:
        can_sends.append(self.handle_angle_lateral(CC, CS))
      else:
        can_sends.append(self.handle_torque_lateral(CC, CS))

    # *** longitudinal ***

    if CC.longActive:
      apply_throttle = int(round(np.interp(actuators.accel, CarControllerParams.THROTTLE_LOOKUP_BP, CarControllerParams.THROTTLE_LOOKUP_V)))
      apply_rpm = int(round(np.interp(actuators.accel, CarControllerParams.RPM_LOOKUP_BP, CarControllerParams.RPM_LOOKUP_V)))
      apply_brake = int(round(np.interp(actuators.accel, CarControllerParams.BRAKE_LOOKUP_BP, CarControllerParams.BRAKE_LOOKUP_V)))

      # limit min and max values
      cruise_throttle = np.clip(apply_throttle, CarControllerParams.THROTTLE_MIN, CarControllerParams.THROTTLE_MAX)
      cruise_rpm = np.clip(apply_rpm, CarControllerParams.RPM_MIN, CarControllerParams.RPM_MAX)
      cruise_brake = np.clip(apply_brake, CarControllerParams.BRAKE_MIN, CarControllerParams.BRAKE_MAX)
    else:
      cruise_throttle = CarControllerParams.THROTTLE_INACTIVE
      cruise_rpm = CarControllerParams.RPM_MIN
      cruise_brake = CarControllerParams.BRAKE_MIN

    long_sources_valid = True
    long_source_msgs = {}
    if self.CP.openpilotLongitudinalControl:
      long_sources_valid, long_source_msgs = self._get_longitudinal_source_messages(CS)
      self._log_transition(
        "long_sources_valid",
        long_sources_valid,
        f"long source validity changed: valid={long_sources_valid}",
      )

    long_bus = CanBus.alt if self.CP.flags & SubaruFlags.GLOBAL_GEN2 else CanBus.main
    in_drive = CS.out.gearShifter == structs.CarState.GearShifter.drive

    # Phase gate: Phase 3+ allows full actuation. Phase 1/2 force override off.
    # Phase 2 allows replay for counter/message maintenance but no gas/brake.
    # Phase 1 suppresses replay entirely (EyeSight disable only).
    phase_allows_replay = OUTBACK_ALPHA_LONG_PHASE >= 2
    phase_allows_actuation = OUTBACK_ALPHA_LONG_PHASE >= 3

    long_override_active = (
      self.CP.openpilotLongitudinalControl
      and CC.longActive
      and in_drive
      and phase_allows_actuation
    )

    # *** alerts and pcm cancel ***
    if self.CP.flags & SubaruFlags.PREGLOBAL:
      if self.frame % 5 == 0:
        # 1 = main, 2 = set shallow, 3 = set deep, 4 = resume shallow, 5 = resume deep
        # disengage ACC when OP is disengaged
        if pcm_cancel_cmd:
          cruise_button = 1
        # turn main on if off and past start-up state
        elif not CS.out.cruiseState.available and CS.ready:
          cruise_button = 1
        else:
          cruise_button = CS.cruise_button

        # unstick previous mocked button press
        if cruise_button == 1 and self.cruise_button_prev == 1:
          cruise_button = 0
        self.cruise_button_prev = cruise_button

        can_sends.append(subarucan.create_preglobal_es_distance(self.packer, cruise_button, CS.es_distance_msg))

    else:
      if self.frame % 10 == 0:
        can_sends.append(subarucan.create_es_dashstatus(self.packer, self.frame // 10, CS.es_dashstatus_msg, CC.enabled,
                                                        self.CP.openpilotLongitudinalControl, CC.longActive, hud_control.leadVisible))

        can_sends.append(subarucan.create_es_lkas_state(self.packer, self.frame // 10, CS.es_lkas_state_msg, CC.enabled, hud_control.visualAlert,
                                                        hud_control.leftLaneVisible, hud_control.rightLaneVisible,
                                                        hud_control.leftLaneDepart, hud_control.rightLaneDepart))

        if self.CP.flags & SubaruFlags.SEND_INFOTAINMENT:
          can_sends.append(subarucan.create_es_infotainment(self.packer, self.frame // 10, CS.es_infotainment_msg, hud_control.visualAlert))

      if self.CP.openpilotLongitudinalControl and phase_allows_replay:
        if self.frame % 5 == 0:
          has_cached_long_sources = all(msg is not None for msg in long_source_msgs.values())
          if long_sources_valid:
            self._log_transition("long_replay_branch", "live", "long replay: using live source messages")
            can_sends.append(subarucan.create_es_status(self.packer, self.frame // 5, long_source_msgs["es_status"],
                                                        long_bus, long_override_active, long_override_active, cruise_rpm))

            can_sends.append(subarucan.create_es_brake(self.packer, self.frame // 5, long_source_msgs["es_brake"],
                                                       long_bus, long_override_active, long_override_active, cruise_brake))

            can_sends.append(subarucan.create_es_distance(self.packer, self.frame // 5, long_source_msgs["es_distance"], long_bus, pcm_cancel_cmd,
                                                          long_override_active, cruise_brake > 0, cruise_throttle))
          elif has_cached_long_sources:
            # Source has gone stale: maintain message cadence but suppress all actuation to avoid
            # sending stale throttle/brake commands. Cancel is still forwarded for safety.
            self._log_transition("long_replay_branch", "stale_cache", "long replay: source stale, using cached messages with actuation suppressed")
            can_sends.append(subarucan.create_es_status(self.packer, self.frame // 5, long_source_msgs["es_status"],
                                                        long_bus, False, False, CarControllerParams.RPM_MIN))

            can_sends.append(subarucan.create_es_brake(self.packer, self.frame // 5, long_source_msgs["es_brake"],
                                                       long_bus, False, False, CarControllerParams.BRAKE_MIN))

            can_sends.append(subarucan.create_es_distance(self.packer, self.frame // 5, long_source_msgs["es_distance"], long_bus, pcm_cancel_cmd,
                                                          False, False, CarControllerParams.THROTTLE_INACTIVE))
          else:
            self._log_transition("long_replay_branch", "skipped", "long replay: no valid cache, skipping ES replay this tick")

      elif self.CP.openpilotLongitudinalControl and not phase_allows_replay:
        # Phase 1: EyeSight disable is active but ES replay is intentionally suppressed.
        # This isolates whether the LKAS fault comes from EyeSight disable alone.
        if self.frame % 5 == 0:
          self._log_transition("long_replay_branch", "phase1_suppressed", "long replay: suppressed by OUTBACK_ALPHA_LONG_PHASE=1")

      else:
        # openpilot long is off: handle cancel and ICBM button emulation
        if pcm_cancel_cmd:
          if not (self.CP.flags & SubaruFlags.HYBRID):
            bus = CanBus.alt if self.CP.flags & SubaruFlags.GLOBAL_GEN2 else CanBus.main
            can_sends.append(subarucan.create_es_distance(self.packer, CS.es_distance_msg["COUNTER"] + 1, CS.es_distance_msg, bus, pcm_cancel_cmd))

        # ICBM: map-based stock ACC set-speed automation via button emulation in ES_Distance.
        # Fires only when openpilot long is off, ACC is actively engaged, and ICBM requests a button.
        if (self._icbm_available
            and self.icbm_interface is not None
            and CS.out.cruiseState.enabled
            and not (self.CP.flags & SubaruFlags.HYBRID)):
          icbm_sends = self.icbm_interface.update(CC_SP, self.packer, self.frame, self.icbm_last_button_frame, CS)
          if icbm_sends:
            can_sends.extend(icbm_sends)
            self.icbm_last_button_frame = self.frame

      if self.CP.flags & SubaruFlags.DISABLE_EYESIGHT:
        # Tester present (keeps eyesight disabled)
        if self.frame % 100 == 0:
          self._log_transition(
            "eyesight_disable_active",
            True,
            f"EyeSight disable: tester present sent at frame={self.frame} bus={CanBus.camera} addr={GLOBAL_ES_ADDR:#x}",
          )
          can_sends.append(make_tester_present_msg(GLOBAL_ES_ADDR, CanBus.camera, suppress_response=True))

        # Create all of the other eyesight messages to keep the rest of the car happy when eyesight is disabled
        if self.frame % 5 == 0:
          can_sends.append(subarucan.create_es_highbeamassist(self.packer))

        if self.frame % 10 == 0:
          can_sends.append(subarucan.create_es_static_1(self.packer))

        if self.frame % 2 == 0:
          can_sends.append(subarucan.create_es_static_2(self.packer))

    can_sends.extend(SnGCarController.create_stop_and_go(self, self.packer, CC, CS, self.frame))

    new_actuators = actuators.as_builder()
    new_actuators.steeringAngleDeg = self.apply_angle_last
    new_actuators.torque = self.apply_torque_last / self.p.STEER_MAX
    new_actuators.torqueOutputCan = self.apply_torque_last

    self.frame += 1
    return new_actuators, can_sends
