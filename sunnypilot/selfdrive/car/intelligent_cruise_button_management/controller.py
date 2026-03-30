"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from cereal import car, custom
from opendbc.car import structs, apply_hysteresis
from openpilot.common.constants import CV
from openpilot.common.realtime import DT_CTRL
from openpilot.sunnypilot.selfdrive.car.intelligent_cruise_button_management.helpers import get_minimum_set_speed
from openpilot.sunnypilot.selfdrive.car.cruise_ext import CRUISE_BUTTON_TIMER, update_manual_button_timers

LongitudinalPlanSource = custom.LongitudinalPlanSP.LongitudinalPlanSource
State = custom.IntelligentCruiseButtonManagement.IntelligentCruiseButtonManagementState
SendButtonState = custom.IntelligentCruiseButtonManagement.SendButtonState

ALLOWED_SPEED_THRESHOLD = 1.8  # m/s, ~4 MPH
HYST_GAP = 0.0  # currently disabled; TODO-SP: might need to be brand-specific
INACTIVE_TIMER = 0.4


SEND_BUTTONS = {
  State.increasing: SendButtonState.increase,
  State.decreasing: SendButtonState.decrease,
}


class IntelligentCruiseButtonManagement:
  def __init__(self, CP: structs.CarParams, CP_SP: structs.CarParamsSP):
    self.CP = CP
    self.CP_SP = CP_SP
    self._subaru_speed_limit_trigger_mode = (
      CP.brand == "subaru"
      and CP_SP.intelligentCruiseButtonManagementAvailable
      and not CP.openpilotLongitudinalControl
    )

    self.v_target = 0
    self.v_cruise_cluster = 0
    self.v_cruise_min = 0
    self.cruise_button = SendButtonState.none
    self.state = State.inactive
    self.pre_active_timer = 0

    self.is_ready = False
    self.is_ready_prev = False
    self.v_target_ms_last = 0.0
    self.is_metric = False

    self.cruise_button_timers = CRUISE_BUTTON_TIMER
    
    # BluePilot: Track initial cruise speed when first enabled
    self.initial_cruise_speed_kph = 0
    self.cruise_enabled_prev = False
    self.pending_speed_limit_target = 0
    self.last_speed_limit_target = 0

  @property
  def v_cruise_equal(self) -> bool:
    return self.v_target == self.v_cruise_cluster

  def _capture_cruise_enable_state(self, CS: car.CarState) -> bool:
    cruise_enabled = CS.cruiseState.available and CS.cruiseState.enabled
    if cruise_enabled and not self.cruise_enabled_prev:
      current_speed_kph = CS.vEgo * CV.MS_TO_KPH
      self.initial_cruise_speed_kph = round(current_speed_kph)
    self.cruise_enabled_prev = cruise_enabled
    return cruise_enabled

  def _reset_pending_speed_limit_target(self) -> None:
    self.pending_speed_limit_target = 0

  def _get_subaru_resolved_speed_limit(self, LP_SP: custom.LongitudinalPlanSP) -> int:
    speed_limit = getattr(LP_SP.speedLimit.resolver, "speedLimitFinalLast", 0.0)
    if speed_limit <= 0.0:
      return 0

    speed_conv = CV.MS_TO_KPH if self.is_metric else CV.MS_TO_MPH
    return round(speed_limit * speed_conv)

  def _arm_subaru_speed_limit_target(self, CS: car.CarState, LP_SP: custom.LongitudinalPlanSP, cruise_enabled: bool) -> None:
    resolved_speed_limit = self._get_subaru_resolved_speed_limit(LP_SP)
    speed_limit_changed = resolved_speed_limit != self.last_speed_limit_target
    assist_enabled = LP_SP.speedLimit.assist.enabled

    if speed_limit_changed and resolved_speed_limit > 0:
      if assist_enabled and self.is_ready and cruise_enabled:
        if resolved_speed_limit == self.v_cruise_cluster:
          self._reset_pending_speed_limit_target()
          self.state = State.holding
        else:
          self.pending_speed_limit_target = resolved_speed_limit
          self.pre_active_timer = int(INACTIVE_TIMER / DT_CTRL)
          self.state = State.preActive

    if speed_limit_changed:
      self.last_speed_limit_target = resolved_speed_limit

  def update_calculations(self, CS: car.CarState, LP_SP: custom.LongitudinalPlanSP) -> None:
    speed_conv = CV.MS_TO_KPH if self.is_metric else CV.MS_TO_MPH
    ms_conv = CV.KPH_TO_MS if self.is_metric else CV.MPH_TO_MS

    cruise_enabled = self._capture_cruise_enable_state(CS)
    self.v_cruise_min = get_minimum_set_speed(self.is_metric)
    self.v_cruise_cluster = round(CS.cruiseState.speedCluster * speed_conv)

    if self._subaru_speed_limit_trigger_mode:
      self._arm_subaru_speed_limit_target(CS, LP_SP, cruise_enabled)
      self.v_target = self.pending_speed_limit_target if self.pending_speed_limit_target > 0 else self.v_cruise_cluster
      return

    self.v_target_ms_last = apply_hysteresis(LP_SP.vTarget, self.v_target_ms_last, HYST_GAP * ms_conv)
    self.v_target = round(self.v_target_ms_last * speed_conv)
    
    # BluePilot: If planner target is invalid/unreasonable and we have an initial cruise speed,
    # use the initial speed as the target (or cluster speed if it's been set)
    MAX_REASONABLE_TARGET = 145 if self.is_metric else 90
    if self.v_target >= MAX_REASONABLE_TARGET or self.v_target == 0:
      # Planner target is invalid - use initial cruise speed or cluster speed
      if self.initial_cruise_speed_kph > 0:
        self.v_target = self.initial_cruise_speed_kph
      elif self.v_cruise_cluster > 0:
        self.v_target = self.v_cruise_cluster

  def update_state_machine(self) -> custom.IntelligentCruiseButtonManagement.SendButtonState:
    self.pre_active_timer = max(0, self.pre_active_timer - 1)

    if self._subaru_speed_limit_trigger_mode:
      if not self.is_ready:
        self._reset_pending_speed_limit_target()
        self.state = State.inactive
      elif self.pending_speed_limit_target <= 0:
        self.state = State.holding
      else:
        self.v_target = self.pending_speed_limit_target
        if self.v_cruise_equal:
          self._reset_pending_speed_limit_target()
          self.state = State.holding
        elif self.state == State.preActive:
          if self.pre_active_timer <= 0:
            self.state = State.increasing if self.v_target > self.v_cruise_cluster else State.decreasing
        elif self.state in (State.inactive, State.holding):
          self.state = State.preActive
          self.pre_active_timer = int(INACTIVE_TIMER / DT_CTRL)
        elif self.state == State.increasing:
          if self.v_target < self.v_cruise_cluster:
            self.state = State.decreasing
        elif self.state == State.decreasing:
          if self.v_target > self.v_cruise_cluster:
            self.state = State.increasing
          elif self.v_cruise_cluster <= self.v_cruise_min:
            self._reset_pending_speed_limit_target()
            self.state = State.holding

      return SEND_BUTTONS.get(self.state, SendButtonState.none)

    # HOLDING, ACCELERATING, DECELERATING, PRE_ACTIVE
    if self.state != State.inactive:
      if not self.is_ready:
        self.state = State.inactive

      else:
        # PRE_ACTIVE
        if self.state == State.preActive:
          if self.pre_active_timer <= 0:
            if self.v_cruise_equal:
              self.state = State.holding

            elif self.v_target > self.v_cruise_cluster:
              # BluePilot: Prevent ICBM from increasing speed when cruise is first enabled
              # If cluster speed is 0 or very low, don't increase - wait for user to set initial speed
              # Also cap target to reasonable maximum (145 kph / 90 mph)
              # Don't increase if target exceeds initial cruise speed by more than 5 mph/kph
              MAX_REASONABLE_TARGET = 145 if self.is_metric else 90
              MAX_INITIAL_INCREASE = 5  # Allow small increases from initial speed
              
              if self.v_cruise_cluster == 0 or self.v_target >= MAX_REASONABLE_TARGET:
                # Don't increase - stay in preActive or go to holding
                self.state = State.holding
              elif self.initial_cruise_speed_kph > 0 and self.v_target > (self.initial_cruise_speed_kph + MAX_INITIAL_INCREASE):
                # Don't increase beyond initial cruise speed + small margin
                # This prevents ICBM from ramping up when cruise is first enabled
                self.state = State.holding
              else:
                self.state = State.increasing

            elif self.v_target < self.v_cruise_cluster and self.v_cruise_cluster > self.v_cruise_min:
              self.state = State.decreasing

        # HOLDING
        elif self.state == State.holding:
          if not self.v_cruise_equal:
            self.state = State.preActive

        # ACCELERATING
        elif self.state == State.increasing:
          if self.v_target <= self.v_cruise_cluster:
            self.state = State.holding

        # DECELERATING
        elif self.state == State.decreasing:
          if self.v_target >= self.v_cruise_cluster or self.v_cruise_cluster <= self.v_cruise_min:
            self.state = State.holding

    # INACTIVE
    elif self.state == State.inactive:
      if self.is_ready and not self.is_ready_prev:
        self.pre_active_timer = int(INACTIVE_TIMER / DT_CTRL)
        self.state = State.preActive

    send_button = SEND_BUTTONS.get(self.state, SendButtonState.none)

    return send_button

  def update_readiness(self, CS: car.CarState, CC: car.CarControl) -> None:
    update_manual_button_timers(CS, self.cruise_button_timers)

    ready = CC.enabled and not CC.cruiseControl.override and not CC.cruiseControl.cancel and not CC.cruiseControl.resume
    button_pressed = any(self.cruise_button_timers[k] > 0 for k in self.cruise_button_timers)

    # BluePilot: Clear button timers when cruise is disabled to prevent stale presses
    # This ensures that when cruise is re-enabled, ICBM doesn't see stale button presses
    if not ready:
      for k in self.cruise_button_timers:
        self.cruise_button_timers[k] = 0
      # BluePilot: Reset initial cruise speed when cruise is disabled
      # This ensures we capture a fresh initial speed when cruise is re-enabled
      self.initial_cruise_speed_kph = 0
      if self._subaru_speed_limit_trigger_mode:
        self._reset_pending_speed_limit_target()

    self.is_ready = ready and not button_pressed
    if self._subaru_speed_limit_trigger_mode and not self.is_ready:
      self._reset_pending_speed_limit_target()

  def run(self, CS: car.CarState, CC: car.CarControl, LP_SP: custom.LongitudinalPlanSP, is_metric: bool) -> None:
    if self.CP_SP.pcmCruiseSpeed:
      return

    self.is_metric = is_metric

    self.update_calculations(CS, LP_SP)
    self.update_readiness(CS, CC)

    self.cruise_button = self.update_state_machine()

    self.is_ready_prev = self.is_ready
