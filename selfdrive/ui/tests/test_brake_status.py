from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from openpilot.selfdrive.ui.sunnypilot.onroad import brake_status
from openpilot.selfdrive.ui.sunnypilot.onroad.brake_status import (
  STOCK_LONG_BRAKING_AEGO_THRESHOLD,
  is_vehicle_braking,
  should_highlight_braking_speed,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_SPEED_RENDERER = REPO_ROOT / "selfdrive/ui/sunnypilot/onroad/speed_renderer.py"
MICI_SPEED_RENDERER = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/onroad/speed_renderer.py"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def _build_sm(*, brake_pressed=False, regen_braking=False, enabled=False, mads_enabled=False, cruise_enabled=False,
              force_decel=False, accel=0.0, a_ego=0.0, brake_lights_available=False, brake_lights_on=False):
  return {
    'carState': SimpleNamespace(
      brakePressed=brake_pressed,
      regenBraking=regen_braking,
      aEgo=a_ego,
      cruiseState=SimpleNamespace(enabled=cruise_enabled),
    ),
    'carStateSP': SimpleNamespace(
      brakeLightsAvailable=brake_lights_available,
      brakeLightsOn=brake_lights_on,
    ),
    'selfdriveState': SimpleNamespace(enabled=enabled),
    'selfdriveStateSP': SimpleNamespace(mads=SimpleNamespace(enabled=mads_enabled)),
    'controlsState': SimpleNamespace(forceDecel=force_decel),
    'carControl': SimpleNamespace(actuators=SimpleNamespace(accel=accel)),
  }


def _build_cp(*, openpilot_longitudinal=False):
  return SimpleNamespace(openpilotLongitudinalControl=openpilot_longitudinal)


def test_brake_status_triggers_on_brake_pedal():
  assert is_vehicle_braking(_build_sm(brake_pressed=True), _build_cp()) is True


def test_brake_status_triggers_on_regen():
  assert is_vehicle_braking(_build_sm(regen_braking=True), _build_cp()) is True


def test_brake_status_prefers_brake_lights_when_available():
  sm = _build_sm(brake_lights_available=True, brake_lights_on=True, enabled=False, cruise_enabled=False, a_ego=0.0)
  assert is_vehicle_braking(sm, _build_cp()) is True


def test_brake_status_does_not_fall_through_when_brake_lights_available_but_off():
  sm = _build_sm(brake_lights_available=True, brake_lights_on=False, enabled=True, force_decel=True, accel=-0.1)
  assert is_vehicle_braking(sm, _build_cp(openpilot_longitudinal=True)) is False


def test_brake_status_triggers_on_openpilot_longitudinal_braking():
  sm = _build_sm(enabled=True, accel=-0.1)
  assert is_vehicle_braking(sm, _build_cp(openpilot_longitudinal=True)) is True


def test_brake_status_triggers_on_force_decel():
  sm = _build_sm(enabled=True, force_decel=True)
  assert is_vehicle_braking(sm, _build_cp(openpilot_longitudinal=True)) is True


def test_brake_status_triggers_on_stock_acc_braking_without_selfdrive_enabled():
  sm = _build_sm(cruise_enabled=True, a_ego=STOCK_LONG_BRAKING_AEGO_THRESHOLD - 0.01)
  assert is_vehicle_braking(sm, _build_cp(openpilot_longitudinal=False)) is True


def test_brake_status_does_not_trigger_on_coast():
  sm = _build_sm(enabled=True, cruise_enabled=True, accel=0.0, a_ego=-0.2)
  assert is_vehicle_braking(sm, _build_cp(openpilot_longitudinal=False)) is False


def test_should_highlight_braking_speed_respects_show_toggle():
  ui_state = SimpleNamespace(sm=_build_sm(brake_lights_available=True, brake_lights_on=True), CP=_build_cp())
  with patch.object(brake_status, "ui_state", ui_state):
    assert should_highlight_braking_speed(False) is False


def test_speed_renderers_still_call_brake_status_helper():
  tici_source = _read(TICI_SPEED_RENDERER)
  mici_source = _read(MICI_SPEED_RENDERER)

  assert "from openpilot.selfdrive.ui.sunnypilot.onroad.brake_status import should_highlight_braking_speed" in tici_source
  assert "should_highlight_braking_speed" in tici_source
  assert "from openpilot.selfdrive.ui.sunnypilot.onroad.brake_status import should_highlight_braking_speed" in mici_source
  assert "should_highlight_braking_speed" in mici_source


def test_speed_renderers_still_switch_between_cluster_and_true_speed():
  tici_source = _read(TICI_SPEED_RENDERER)
  mici_source = _read(MICI_SPEED_RENDERER)
  expected_logic = "v_ego = v_ego_cluster if self.v_ego_cluster_seen and ui_state.match_vehicle_speedometer else car_state.vEgo"

  assert expected_logic in tici_source
  assert expected_logic in mici_source
