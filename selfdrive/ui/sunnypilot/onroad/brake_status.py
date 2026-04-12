from __future__ import annotations

from typing import Any

from openpilot.selfdrive.ui.ui_state import ui_state

STOCK_LONG_BRAKING_AEGO_THRESHOLD = -1.25


def _cruise_enabled(car_state: Any) -> bool:
  return bool(getattr(getattr(car_state, "cruiseState", None), "enabled", False))


def _mads_enabled(sm: Any) -> bool:
  return bool(getattr(getattr(sm['selfdriveStateSP'], "mads", None), "enabled", False))


def is_vehicle_braking(sm: Any, cp: Any | None) -> bool:
  car_state = sm['carState']
  car_state_sp = sm['carStateSP']

  if getattr(car_state_sp, "brakeLightsAvailable", False):
    return bool(getattr(car_state_sp, "brakeLightsOn", False))

  if car_state.brakePressed or car_state.regenBraking:
    return True

  assisted_driving_active = bool(sm['selfdriveState'].enabled or _mads_enabled(sm) or _cruise_enabled(car_state))
  if not assisted_driving_active:
    return False

  openpilot_longitudinal = bool(getattr(cp, "openpilotLongitudinalControl", False))
  if openpilot_longitudinal:
    return bool(sm['controlsState'].forceDecel or sm['carControl'].actuators.accel < 0.0)

  return bool(_cruise_enabled(car_state) and car_state.aEgo < STOCK_LONG_BRAKING_AEGO_THRESHOLD)


def should_highlight_braking_speed(show_brake_status: bool) -> bool:
  if not show_brake_status:
    return False

  cp = ui_state.CP if ui_state.CP is not None else ui_state.sm['carParams']
  return is_vehicle_braking(ui_state.sm, cp)
