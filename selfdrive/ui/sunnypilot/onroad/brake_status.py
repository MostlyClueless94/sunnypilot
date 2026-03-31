from __future__ import annotations

from typing import Any

from openpilot.selfdrive.ui.ui_state import ui_state

STOCK_LONG_BRAKING_AEGO_THRESHOLD = -1.25


def is_vehicle_braking(sm: Any, cp: Any | None) -> bool:
  car_state = sm['carState']
  if car_state.brakePressed or car_state.regenBraking:
    return True

  if not sm['selfdriveState'].enabled:
    return False

  openpilot_longitudinal = bool(getattr(cp, "openpilotLongitudinalControl", False))
  if openpilot_longitudinal:
    return bool(sm['controlsState'].forceDecel or sm['carControl'].actuators.accel < 0.0)

  return car_state.aEgo < STOCK_LONG_BRAKING_AEGO_THRESHOLD


def should_highlight_braking_speed(show_brake_status: bool) -> bool:
  if not show_brake_status:
    return False

  cp = ui_state.CP if ui_state.CP is not None else ui_state.sm['carParams']
  return is_vehicle_braking(ui_state.sm, cp)
