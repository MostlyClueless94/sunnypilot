from types import SimpleNamespace

from cereal import car
from openpilot.common.constants import CV
from openpilot.sunnypilot.selfdrive.car.intelligent_cruise_button_management.controller import (
  IntelligentCruiseButtonManagement,
  SendButtonState,
)


ButtonType = car.CarState.ButtonEvent.Type


def _build_controller():
  cp = SimpleNamespace(brand="subaru", openpilotLongitudinalControl=False, pcmCruise=True)
  cp_sp = SimpleNamespace(intelligentCruiseButtonManagementAvailable=True, pcmCruiseSpeed=False)
  return IntelligentCruiseButtonManagement(cp, cp_sp)


def _build_cs(cluster_speed_mph, cruise_enabled=True, button_events=None, v_ego_mph=None):
  if v_ego_mph is None:
    v_ego_mph = cluster_speed_mph

  return SimpleNamespace(
    cruiseState=SimpleNamespace(
      available=True,
      enabled=cruise_enabled,
      speedCluster=cluster_speed_mph * CV.MPH_TO_MS,
    ),
    vEgo=v_ego_mph * CV.MPH_TO_MS,
    buttonEvents=button_events or [],
  )


def _build_cc(enabled=True):
  return SimpleNamespace(
    enabled=enabled,
    cruiseControl=SimpleNamespace(override=False, cancel=False, resume=False),
  )


def _build_lp(speed_limit_mph, assist_enabled=True):
  return SimpleNamespace(
    vTarget=speed_limit_mph * CV.MPH_TO_MS,
    speedLimit=SimpleNamespace(
      assist=SimpleNamespace(enabled=assist_enabled, active=assist_enabled, vTarget=speed_limit_mph * CV.MPH_TO_MS),
      resolver=SimpleNamespace(speedLimitFinalLast=speed_limit_mph * CV.MPH_TO_MS),
    ),
  )


def test_subaru_icbm_arms_only_on_speed_limit_change_while_ready():
  controller = _build_controller()

  controller.run(_build_cs(35, cruise_enabled=False), _build_cc(False), _build_lp(35, assist_enabled=False), False)
  assert controller.cruise_button == SendButtonState.none
  assert controller.pending_speed_limit_target == 0

  controller.run(_build_cs(35, cruise_enabled=True), _build_cc(True), _build_lp(35, assist_enabled=True), False)
  assert controller.cruise_button == SendButtonState.none
  assert controller.pending_speed_limit_target == 0

  controller.run(_build_cs(35, cruise_enabled=True), _build_cc(True), _build_lp(45, assist_enabled=True), False)
  assert controller.pending_speed_limit_target == 45
  assert controller.cruise_button == SendButtonState.none

  controller.pre_active_timer = 0
  controller.run(_build_cs(35, cruise_enabled=True), _build_cc(True), _build_lp(45, assist_enabled=True), False)
  assert controller.cruise_button == SendButtonState.increase


def test_subaru_icbm_stops_after_target_is_reached_and_does_not_reassert_without_new_event():
  controller = _build_controller()
  cc = _build_cc(True)

  controller.run(_build_cs(35), cc, _build_lp(45), False)
  controller.pre_active_timer = 0
  controller.run(_build_cs(35), cc, _build_lp(45), False)
  assert controller.cruise_button == SendButtonState.increase

  controller.run(_build_cs(45), cc, _build_lp(45), False)
  assert controller.cruise_button == SendButtonState.none
  assert controller.pending_speed_limit_target == 0

  controller.run(_build_cs(40), cc, _build_lp(45), False)
  assert controller.cruise_button == SendButtonState.none
  assert controller.pending_speed_limit_target == 0


def test_subaru_icbm_manual_button_cancels_pending_target_until_next_speed_limit_event():
  controller = _build_controller()
  cc = _build_cc(True)

  controller.run(_build_cs(35), cc, _build_lp(45), False)
  controller.pre_active_timer = 0
  controller.run(_build_cs(35), cc, _build_lp(45), False)
  assert controller.cruise_button == SendButtonState.increase

  controller.run(
    _build_cs(35, button_events=[SimpleNamespace(type=ButtonType.accelCruise, pressed=True)]),
    cc,
    _build_lp(45),
    False,
  )
  assert controller.cruise_button == SendButtonState.none
  assert controller.pending_speed_limit_target == 0

  controller.run(_build_cs(35), cc, _build_lp(45), False)
  assert controller.cruise_button == SendButtonState.none
  assert controller.pending_speed_limit_target == 0


def test_subaru_icbm_valid_speed_limit_increase_is_not_blocked_by_initial_speed_guard():
  controller = _build_controller()
  cc = _build_cc(True)

  controller.run(_build_cs(30, v_ego_mph=30), cc, _build_lp(30), False)
  controller.run(_build_cs(30, v_ego_mph=30), cc, _build_lp(55), False)
  controller.pre_active_timer = 0
  controller.run(_build_cs(30, v_ego_mph=30), cc, _build_lp(55), False)

  assert controller.pending_speed_limit_target == 55
  assert controller.cruise_button == SendButtonState.increase
