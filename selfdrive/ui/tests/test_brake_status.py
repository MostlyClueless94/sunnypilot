from types import SimpleNamespace

from openpilot.selfdrive.ui.sunnypilot.onroad.brake_status import (
  STOCK_LONG_BRAKING_AEGO_THRESHOLD,
  is_vehicle_braking,
)


def _build_sm(*, brake_pressed=False, regen_braking=False, enabled=False, force_decel=False,
              accel=0.0, a_ego=0.0):
  return {
    'carState': SimpleNamespace(
      brakePressed=brake_pressed,
      regenBraking=regen_braking,
      aEgo=a_ego,
    ),
    'selfdriveState': SimpleNamespace(enabled=enabled),
    'controlsState': SimpleNamespace(forceDecel=force_decel),
    'carControl': SimpleNamespace(actuators=SimpleNamespace(accel=accel)),
  }


def _build_cp(*, openpilot_longitudinal=False):
  return SimpleNamespace(openpilotLongitudinalControl=openpilot_longitudinal)


def test_brake_status_triggers_on_brake_pedal():
  assert is_vehicle_braking(_build_sm(brake_pressed=True), _build_cp()) is True


def test_brake_status_triggers_on_regen():
  assert is_vehicle_braking(_build_sm(regen_braking=True), _build_cp()) is True


def test_brake_status_triggers_on_openpilot_longitudinal_braking():
  sm = _build_sm(enabled=True, accel=-0.1)
  assert is_vehicle_braking(sm, _build_cp(openpilot_longitudinal=True)) is True


def test_brake_status_triggers_on_force_decel():
  sm = _build_sm(enabled=True, force_decel=True)
  assert is_vehicle_braking(sm, _build_cp(openpilot_longitudinal=True)) is True


def test_brake_status_triggers_on_stock_acc_braking():
  sm = _build_sm(enabled=True, a_ego=STOCK_LONG_BRAKING_AEGO_THRESHOLD - 0.01)
  assert is_vehicle_braking(sm, _build_cp(openpilot_longitudinal=False)) is True


def test_brake_status_does_not_trigger_on_coast():
  sm = _build_sm(enabled=True, accel=0.0, a_ego=-0.2)
  assert is_vehicle_braking(sm, _build_cp(openpilot_longitudinal=False)) is False
