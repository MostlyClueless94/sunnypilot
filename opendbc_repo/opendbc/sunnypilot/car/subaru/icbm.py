"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.

Subaru ICBM (Intelligent Cruise Button Management)
---------------------------------------------------
Emulates ACC set/resume button presses via the ES_Distance CAN message to
adjust the stock Subaru ACC set-speed in response to map-based speed limit
changes from sunnypilot's SpeedLimitAssist stack.

Button emulation works by overriding the Cruise_Set or Cruise_Resume fields
in a replayed ES_Distance frame on the correct bus (alt/bus-1 for Gen2 cars).

This path fires only when openpilot longitudinal control is OFF. When OP long
is active, the longitudinal controller adjusts speed directly and ICBM is
bypassed. The carcontroller gates entry here on:
  - CP_SP.intelligentCruiseButtonManagementAvailable == True
  - CP.openpilotLongitudinalControl == False
  - CS.out.cruiseState.available == True  (ACC main switch on)
"""

from opendbc.car import structs, DT_CTRL
from opendbc.car.can_definitions import CanData
from opendbc.car.carlog import carlog
from opendbc.car.subaru.values import CanBus, SubaruFlags
from opendbc.sunnypilot.car.intelligent_cruise_button_management_interface_base import (
  IntelligentCruiseButtonManagementInterfaceBase,
)

SendButtonState = structs.IntelligentCruiseButtonManagement.SendButtonState

# ES_Distance cadence is 20 Hz, so one button message every 50 ms matches the stock path.
ICBM_BUTTON_MIN_INTERVAL = 0.05  # seconds
ICBM_BUTTON_MIN_INTERVAL_FRAMES = max(1, int(round(ICBM_BUTTON_MIN_INTERVAL / DT_CTRL)))
ICBM_MANUAL_LONG_PRESS_FRAMES = 50  # match the repo's existing 0.5 s cruise long-press convention

# Subaru long-press behavior advances the set speed in larger OEM chunks.
ICBM_HOLD_INCREMENT_MPH = 5
MS_TO_MPH = 2.2369362920544

# Single taps should wait for cluster feedback before another synthetic press is sent.
ICBM_TAP_SETTLE_FRAMES = max(ICBM_BUTTON_MIN_INTERVAL_FRAMES, ICBM_MANUAL_LONG_PRESS_FRAMES // 2)

# Do not allow an unbounded synthetic hold if the cluster never reacts.
ICBM_HOLD_MAX_FRAMES = ICBM_MANUAL_LONG_PRESS_FRAMES * 6


class IntelligentCruiseButtonManagementInterface(IntelligentCruiseButtonManagementInterfaceBase):
  """
  Subaru-specific ICBM implementation.

  Injects Cruise_Set (speed down) or Cruise_Resume (speed up) into a copied
  ES_Distance frame. Large display-speed gaps use a continuous hold so the
  Subaru ACC ECU can apply OEM 5 mph jumps; smaller cleanup deltas
  use true single taps and wait for the cluster to react before retrying.

  Bus selection mirrors the long replay path:
    Gen2 cars (OUTBACK_2023, ASCENT_2023, CROSSTREK_2025) -> CanBus.alt (bus 1)
    Other global cars                                      -> CanBus.main (bus 0)
  """

  def __init__(self, CP: structs.CarParams, CP_SP: structs.CarParamsSP):
    super().__init__(CP, CP_SP)

    self.hold_active = False
    self.hold_direction = SendButtonState.none
    self.hold_start_frame = 0
    self.release_until_frame = 0

    self.tap_wait_direction = SendButtonState.none
    self.tap_wait_cluster_speed = 0
    self.tap_wait_until_frame = 0

    self.last_update_frame = -1

  def _reset_hold(self) -> None:
    self.hold_active = False
    self.hold_direction = SendButtonState.none
    self.hold_start_frame = 0

  def _reset_tap_wait(self) -> None:
    self.tap_wait_direction = SendButtonState.none
    self.tap_wait_cluster_speed = 0
    self.tap_wait_until_frame = 0

  def _reset_state(self) -> None:
    self._reset_hold()
    self._reset_tap_wait()
    self.release_until_frame = 0

  def _get_display_speed(self, speed_ms: float) -> int:
    return round(speed_ms * MS_TO_MPH)

  def _get_hold_increment(self) -> int:
    return ICBM_HOLD_INCREMENT_MPH

  @staticmethod
  def _requested_direction(target_speed: int, cluster_speed: int) -> structs.IntelligentCruiseButtonManagement.SendButtonState:
    if target_speed > cluster_speed:
      return SendButtonState.increase
    if target_speed < cluster_speed:
      return SendButtonState.decrease
    return SendButtonState.none

  @staticmethod
  def _has_manual_button_event(CS) -> bool:
    return bool(getattr(CS, "buttonEvents", ()))

  def _build_button_message(
    self,
    send_button: structs.IntelligentCruiseButtonManagement.SendButtonState,
    es_distance_msg,
    packer,
    frame: int,
    last_button_frame: int,
  ) -> list[CanData]:
    can_sends: list[CanData] = []

    elapsed = (frame - last_button_frame) * DT_CTRL
    if elapsed < ICBM_BUTTON_MIN_INTERVAL:
      return can_sends

    try:
      values = dict(es_distance_msg)
    except (TypeError, ValueError):
      carlog.warning(f"subaru[{self.CP.carFingerprint}] ICBM: es_distance_msg not iterable, skipping")
      return can_sends

    values["COUNTER"] = (int(values.get("COUNTER", 0)) + 1) % 0x10
    values["Cruise_Set"] = 0
    values["Cruise_Resume"] = 0
    values["Cruise_Cancel"] = 0

    mode = "hold" if self.hold_active else "tap"
    if send_button == SendButtonState.decrease:
      values["Cruise_Set"] = 1
      carlog.info(f"subaru[{self.CP.carFingerprint}] ICBM: sending Cruise_Set ({mode}) counter={values['COUNTER']}")
    elif send_button == SendButtonState.increase:
      values["Cruise_Resume"] = 1
      carlog.info(f"subaru[{self.CP.carFingerprint}] ICBM: sending Cruise_Resume ({mode}) counter={values['COUNTER']}")

    values["Cruise_Soft_Disable"] = 0
    values["Cruise_Fault"] = 0

    bus = CanBus.alt if (self.CP.flags & SubaruFlags.GLOBAL_GEN2) else CanBus.main
    can_sends.append(packer.make_can_msg("ES_Distance", bus, values))
    return can_sends

  def update(
    self,
    CC_SP,
    packer,
    frame: int,
    last_button_frame: int,
    CS,
  ) -> list[CanData]:
    """
    Called each carcontroller tick when ICBM is available and ACC is active.

    Returns a list of CAN messages (0 or 1 ES_Distance frame with a button pulse).
    Returns an empty list when no button is requested or the rate limit is active.
    """
    can_sends: list[CanData] = []

    icbm = CC_SP.intelligentCruiseButtonManagement
    send_button = icbm.sendButton

    if self.last_update_frame != -1 and (frame - self.last_update_frame) > 1:
      self._reset_state()
    self.last_update_frame = frame

    if send_button == SendButtonState.none:
      self._reset_state()
      return can_sends

    if self._has_manual_button_event(CS):
      self._reset_state()
      return can_sends

    es_distance_msg = getattr(CS, "es_distance_msg", None)
    if not es_distance_msg:
      self._reset_state()
      carlog.warning(f"subaru[{self.CP.carFingerprint}] ICBM: es_distance_msg not available, skipping button press")
      return can_sends

    cluster_speed = self._get_display_speed(CS.out.cruiseState.speedCluster)
    target_speed = int(round(getattr(icbm, "vTarget", cluster_speed)))
    requested_direction = self._requested_direction(target_speed, cluster_speed)
    remaining_gap = abs(target_speed - cluster_speed)
    hold_increment = self._get_hold_increment()

    if requested_direction == SendButtonState.none or requested_direction != send_button:
      self._reset_state()
      return can_sends

    if frame < self.release_until_frame:
      return can_sends

    if self.hold_active:
      if send_button != self.hold_direction:
        self._reset_state()
        return can_sends

      if remaining_gap < hold_increment:
        self._reset_hold()
        self.release_until_frame = frame + ICBM_BUTTON_MIN_INTERVAL_FRAMES
        carlog.info(f"subaru[{self.CP.carFingerprint}] ICBM: releasing hold for cleanup target={target_speed} cluster={cluster_speed}")
        return can_sends

      if (frame - self.hold_start_frame) >= ICBM_HOLD_MAX_FRAMES:
        self._reset_hold()
        self.release_until_frame = frame + ICBM_BUTTON_MIN_INTERVAL_FRAMES
        carlog.info(f"subaru[{self.CP.carFingerprint}] ICBM: hold timeout target={target_speed} cluster={cluster_speed}")
        return can_sends

      return self._build_button_message(send_button, es_distance_msg, packer, frame, last_button_frame)

    if self.tap_wait_direction != SendButtonState.none:
      cluster_updated = cluster_speed != self.tap_wait_cluster_speed
      direction_changed = send_button != self.tap_wait_direction
      tap_wait_expired = frame >= self.tap_wait_until_frame
      if cluster_updated or direction_changed or tap_wait_expired:
        self._reset_tap_wait()
      else:
        return can_sends

    if remaining_gap >= hold_increment:
      self._reset_tap_wait()
      self.hold_active = True
      self.hold_direction = send_button
      self.hold_start_frame = frame
      carlog.info(f"subaru[{self.CP.carFingerprint}] ICBM: entering hold target={target_speed} cluster={cluster_speed}")
      return self._build_button_message(send_button, es_distance_msg, packer, frame, last_button_frame)

    can_sends = self._build_button_message(send_button, es_distance_msg, packer, frame, last_button_frame)
    if can_sends:
      self.tap_wait_direction = send_button
      self.tap_wait_cluster_speed = cluster_speed
      self.tap_wait_until_frame = frame + ICBM_TAP_SETTLE_FRAMES
    return can_sends
