from __future__ import annotations

from typing import Any

from openpilot.selfdrive.ui.ui_state import ui_state


def is_vehicle_braking(sm: Any, _cp: Any | None) -> bool:
  car_state_sp = sm['carStateSP']

  if getattr(car_state_sp, "brakeLightsAvailable", False):
    return bool(getattr(car_state_sp, "brakeLightsOn", False))

  return False


def should_highlight_braking_speed(show_brake_status: bool) -> bool:
  if not show_brake_status:
    return False

  return is_vehicle_braking(ui_state.sm, None)
