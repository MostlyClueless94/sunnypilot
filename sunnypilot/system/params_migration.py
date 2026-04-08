"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.common.swaglog import cloudlog

ONROAD_BRIGHTNESS_MIGRATION_VERSION: str = "1.0"
ONROAD_BRIGHTNESS_TIMER_MIGRATION_VERSION: str = "1.0"
MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION: str = "1.0"
SUBARU_SOFT_CAPTURE_ONLY_MIGRATION_VERSION: str = "subi-staging-1.0"

# index → seconds mapping for OnroadScreenOffTimer (SSoT)
ONROAD_BRIGHTNESS_TIMER_VALUES = {0: 3, 1: 5, 2: 7, 3: 10, 4: 15, 5: 30, **{i: (i - 5) * 60 for i in range(6, 16)}}
VALID_TIMER_VALUES = set(ONROAD_BRIGHTNESS_TIMER_VALUES.values())


def run_migration(_params):
  # migrate OnroadScreenOffBrightness
  if _params.get("OnroadScreenOffBrightnessMigrated") != ONROAD_BRIGHTNESS_MIGRATION_VERSION:
    try:
      val = _params.get("OnroadScreenOffBrightness", return_default=True)
      if val >= 2:  # old: 5%, new: Screen Off
        new_val = val + 1
        _params.put("OnroadScreenOffBrightness", new_val)
        log_str = f"Successfully migrated OnroadScreenOffBrightness from {val} to {new_val}."
      else:
        log_str = "Migration not required for OnroadScreenOffBrightness."

      _params.put("OnroadScreenOffBrightnessMigrated", ONROAD_BRIGHTNESS_MIGRATION_VERSION)
      cloudlog.info(log_str + f" Setting OnroadScreenOffBrightnessMigrated to {ONROAD_BRIGHTNESS_MIGRATION_VERSION}")
    except Exception as e:
      cloudlog.exception(f"Error migrating OnroadScreenOffBrightness: {e}")

  # migrate OnroadScreenOffTimer
  if _params.get("OnroadScreenOffTimerMigrated") != ONROAD_BRIGHTNESS_TIMER_MIGRATION_VERSION:
    try:
      val = _params.get("OnroadScreenOffTimer", return_default=True)
      if val not in VALID_TIMER_VALUES:
        _params.put("OnroadScreenOffTimer", 15)
        log_str = f"Successfully migrated OnroadScreenOffTimer from {val} to 15 (default)."
      else:
        log_str = "Migration not required for OnroadScreenOffTimer."

      _params.put("OnroadScreenOffTimerMigrated", ONROAD_BRIGHTNESS_TIMER_MIGRATION_VERSION)
      cloudlog.info(log_str + f" Setting OnroadScreenOffTimerMigrated to {ONROAD_BRIGHTNESS_TIMER_MIGRATION_VERSION}")
    except Exception as e:
      cloudlog.exception(f"Error migrating OnroadScreenOffTimer: {e}")

  # migrate TrueVEgoUI -> MatchVehicleSpeedometer
  if _params.get("MatchVehicleSpeedometerMigrated") != MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION:
    try:
      if _params.get("MatchVehicleSpeedometer") is None:
        legacy_true_v_ego = _params.get("TrueVEgoUI")
        if legacy_true_v_ego is not None:
          match_vehicle_speedometer = not _params.get_bool("TrueVEgoUI")
          _params.put_bool("MatchVehicleSpeedometer", match_vehicle_speedometer)
          log_str = f"Successfully migrated TrueVEgoUI to MatchVehicleSpeedometer with value {match_vehicle_speedometer}."
        else:
          log_str = "Migration not required for MatchVehicleSpeedometer."
      else:
        log_str = "Migration not required for MatchVehicleSpeedometer."

      _params.remove("TrueVEgoUI")
      _params.put("MatchVehicleSpeedometerMigrated", MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION)
      cloudlog.info(log_str + f" Setting MatchVehicleSpeedometerMigrated to {MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION}")
    except Exception as e:
      cloudlog.exception(f"Error migrating MatchVehicleSpeedometer: {e}")

  # reset Subaru tuning to the soft-capture-only staging defaults
  if _params.get("SubaruSoftCaptureOnlyMigrated") != SUBARU_SOFT_CAPTURE_ONLY_MIGRATION_VERSION:
    try:
      _params.put_bool("MCSubaruSoftCaptureEnabled", True)
      _params.put("MCSubaruSoftCaptureLevel", "1")
      _params.put_bool("MCSubaruSmoothingTune", False)
      _params.put("MCSubaruSmoothingStrength", "0")
      _params.put_bool("MCSubaruCenterDampingTune", False)
      _params.put("MCSubaruCenterDampingStrength", "0")
      _params.put("SubaruSoftCaptureOnlyMigrated", SUBARU_SOFT_CAPTURE_ONLY_MIGRATION_VERSION)
      cloudlog.info(
        "Successfully reset Subaru tuning to the subi-staging soft-capture-only defaults. "
        + f"Setting SubaruSoftCaptureOnlyMigrated to {SUBARU_SOFT_CAPTURE_ONLY_MIGRATION_VERSION}"
      )
    except Exception as e:
      cloudlog.exception(f"Error migrating Subaru soft-capture-only defaults: {e}")
