from types import SimpleNamespace

from openpilot.selfdrive.ui.sunnypilot.onroad.brake_status import (
  bp_brake_status_active,
  mc_vehicle_braking_active,
  should_highlight_braking_speed,
)


class FakeSubMaster(dict):
  def __init__(self, messages, valid=None):
    super().__init__(messages)
    self.valid = valid or {}


def _messages(*, brake_available=False, brake_lights_on=False, brake_pressed=False, regen=False,
              selfdrive_enabled=False, force_decel=False, accel=0.0, a_ego=0.0,
              openpilot_longitudinal=False):
  return FakeSubMaster(
    {
      "carStateBP": SimpleNamespace(
        brakeLightStatus=SimpleNamespace(
          dataAvailable=brake_available,
          brakeLightsOn=brake_lights_on,
        )
      ),
      "carState": SimpleNamespace(
        brakePressed=brake_pressed,
        regenBraking=regen,
        aEgo=a_ego,
      ),
      "selfdriveState": SimpleNamespace(enabled=selfdrive_enabled),
      "controlsState": SimpleNamespace(forceDecel=force_decel),
      "carControl": SimpleNamespace(actuators=SimpleNamespace(accel=accel)),
      "carParams": SimpleNamespace(openpilotLongitudinalControl=openpilot_longitudinal),
    },
    valid={
      "carStateBP": brake_available,
      "carParams": True,
    },
  )


def test_bp_brake_status_uses_brake_lights():
  sm = _messages(brake_available=True, brake_lights_on=True)
  assert bp_brake_status_active(sm) is True


def test_mc_brake_status_prefers_available_brake_lights_over_fallback():
  sm = _messages(brake_available=True, brake_lights_on=False, selfdrive_enabled=True, a_ego=-2.0)
  assert mc_vehicle_braking_active(sm) is False


def test_mc_brake_status_falls_back_to_openpilot_braking():
  sm = _messages(selfdrive_enabled=True, accel=-0.1, openpilot_longitudinal=True)
  assert mc_vehicle_braking_active(sm) is True


def test_mc_brake_status_falls_back_to_stock_acc_decel():
  sm = _messages(selfdrive_enabled=True, a_ego=-1.3, openpilot_longitudinal=False)
  assert mc_vehicle_braking_active(sm) is True


def test_combined_brake_status_accepts_either_toggle_path():
  sm = _messages(brake_available=True, brake_lights_on=True)
  assert should_highlight_braking_speed(False, True, sm) is True
  assert should_highlight_braking_speed(True, False, sm) is True
