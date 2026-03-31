def _get_brake_light_status(sm) -> tuple[bool, bool]:
  try:
    if not sm.valid["carStateBP"]:
      return False, False

    brake_light_status = sm["carStateBP"].brakeLightStatus
    return bool(brake_light_status.dataAvailable), bool(brake_light_status.brakeLightsOn)
  except (KeyError, AttributeError, TypeError):
    return False, False


def _get_openpilot_longitudinal_control(sm, fallback_cp=None) -> bool:
  try:
    if sm.valid["carParams"]:
      return bool(sm["carParams"].openpilotLongitudinalControl)
  except (KeyError, AttributeError, TypeError):
    pass

  return bool(getattr(fallback_cp, "openpilotLongitudinalControl", False))


def bp_brake_status_active(sm) -> bool:
  available, lights_on = _get_brake_light_status(sm)
  return available and lights_on


def mc_vehicle_braking_active(sm, fallback_cp=None) -> bool:
  available, lights_on = _get_brake_light_status(sm)
  if available:
    return lights_on

  try:
    car_state = sm["carState"]
  except (KeyError, AttributeError, TypeError):
    return False

  if bool(getattr(car_state, "brakePressed", False)) or bool(getattr(car_state, "regenBraking", False)):
    return True

  try:
    if not sm["selfdriveState"].enabled:
      return False
  except (KeyError, AttributeError, TypeError):
    return False

  if _get_openpilot_longitudinal_control(sm, fallback_cp):
    try:
      if bool(sm["controlsState"].forceDecel):
        return True
    except (KeyError, AttributeError, TypeError):
      pass

    try:
      return float(sm["carControl"].actuators.accel) < 0.0
    except (KeyError, AttributeError, TypeError, ValueError):
      return False

  try:
    return float(getattr(car_state, "aEgo", 0.0)) < -1.25
  except (TypeError, ValueError):
    return False


def should_highlight_braking_speed(show_bp_brake_status: bool, show_mc_vehicle_brake_status: bool, sm, fallback_cp=None) -> bool:
  return (
    show_bp_brake_status and bp_brake_status_active(sm)
  ) or (
    show_mc_vehicle_brake_status and mc_vehicle_braking_active(sm, fallback_cp)
  )
