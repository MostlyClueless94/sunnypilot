"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.common.swaglog import cloudlog

ONROAD_BRIGHTNESS_MIGRATION_VERSION: str = "1.0"
ONROAD_BRIGHTNESS_TIMER_MIGRATION_VERSION: str = "1.0"
MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION: str = "1.1"
SUBARU_11_BLUEPILOT_TUNING_MIGRATION_VERSION: str = "subi-staging-1.1-preserve-bluepilot-tuning"
SUBARU_MANUAL_YIELD_TORQUE_FLOOR_MIGRATION_VERSION: str = "subi-staging-1.1-torque-floor-40"

# index -> seconds mapping for OnroadScreenOffTimer (SSoT)
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

  # migrate TrueVEgoUI / MatchVehicleSpeedometer -> MCSubaruMatchVehicleSpeedometer
  if _params.get("MatchVehicleSpeedometerMigrated") != MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION:
    try:
      if _params.get("MCSubaruMatchVehicleSpeedometer") is None:
        legacy_true_v_ego = _params.get("TrueVEgoUI")
        legacy_match_vehicle_speedometer = _params.get("MatchVehicleSpeedometer")
        if legacy_match_vehicle_speedometer is not None:
          match_vehicle_speedometer = _params.get_bool("MatchVehicleSpeedometer")
          _params.put_bool("MCSubaruMatchVehicleSpeedometer", match_vehicle_speedometer)
          log_str = f"Successfully migrated MatchVehicleSpeedometer to MCSubaruMatchVehicleSpeedometer with value {match_vehicle_speedometer}."
        elif legacy_true_v_ego is not None:
          match_vehicle_speedometer = not _params.get_bool("TrueVEgoUI")
          _params.put_bool("MCSubaruMatchVehicleSpeedometer", match_vehicle_speedometer)
          log_str = f"Successfully migrated TrueVEgoUI to MCSubaruMatchVehicleSpeedometer with value {match_vehicle_speedometer}."
        else:
          log_str = "Migration not required for MCSubaruMatchVehicleSpeedometer."
      else:
        log_str = "Migration not required for MCSubaruMatchVehicleSpeedometer."

      _params.remove("TrueVEgoUI")
      _params.put("MatchVehicleSpeedometerMigrated", MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION)
      cloudlog.info(log_str + f" Setting MatchVehicleSpeedometerMigrated to {MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION}")
    except Exception as e:
      cloudlog.exception(f"Error migrating MCSubaruMatchVehicleSpeedometer: {e}")

  # seed Subaru angle tuning defaults for the 1.1 staging rebuild without overwriting saved test choices
  if _params.get("Subaru11BluePilotTuningMigrated") != SUBARU_11_BLUEPILOT_TUNING_MIGRATION_VERSION:
    try:
      seeded_keys = []
      bool_defaults = {
        "MCSubaruManualYieldTorqueThresholdEnabled": False,
        "MCSubaruManualYieldResumeSoftnessEnabled": False,
        "MCSubaruManualYieldReleaseGuardEnabled": False,
        "MCSubaruSoftCaptureEnabled": False,
        "MCSubaruSmoothingTune": False,
        "MCSubaruCenterDampingTune": False,
      }
      value_defaults = {
        "MCSubaruManualYieldTorqueThreshold": "80",
        "MCSubaruManualYieldResumeSoftness": "4",
        "MCSubaruManualYieldReleaseGuardLevel": "2",
        "MCSubaruSoftCaptureLevel": "3",
        "MCSubaruSmoothingStrength": "0",
        "MCSubaruCenterDampingStrength": "0",
      }

      for key, default in bool_defaults.items():
        if _params.get(key) is None:
          _params.put_bool(key, default)
          seeded_keys.append(key)

      for key, default in value_defaults.items():
        if _params.get(key) is None:
          _params.put(key, default)
          seeded_keys.append(key)

      _params.put("Subaru11BluePilotTuningMigrated", SUBARU_11_BLUEPILOT_TUNING_MIGRATION_VERSION)
      cloudlog.info(
        "Successfully preserved existing Subaru tuning and seeded missing BluePilot defaults "
        + f"for {seeded_keys}. "
        + f"Setting Subaru11BluePilotTuningMigrated to {SUBARU_11_BLUEPILOT_TUNING_MIGRATION_VERSION}"
      )
    except Exception as e:
      cloudlog.exception(f"Error migrating Subaru BluePilot tuning defaults: {e}")

  # clamp unsafe old custom manual-yield torque floors without resetting other Subaru tuning choices
  if _params.get("SubaruManualYieldTorqueFloorMigrated") != SUBARU_MANUAL_YIELD_TORQUE_FLOOR_MIGRATION_VERSION:
    try:
      val = _params.get("MCSubaruManualYieldTorqueThreshold", return_default=True)
      try:
        threshold = int(val)
      except (TypeError, ValueError):
        threshold = 80

      if threshold < 40:
        _params.put("MCSubaruManualYieldTorqueThreshold", "40")
        log_str = f"Successfully clamped MCSubaruManualYieldTorqueThreshold from {threshold} to 40."
      else:
        log_str = "Migration not required for MCSubaruManualYieldTorqueThreshold floor."

      _params.put("SubaruManualYieldTorqueFloorMigrated", SUBARU_MANUAL_YIELD_TORQUE_FLOOR_MIGRATION_VERSION)
      cloudlog.info(log_str + f" Setting SubaruManualYieldTorqueFloorMigrated to {SUBARU_MANUAL_YIELD_TORQUE_FLOOR_MIGRATION_VERSION}")
    except Exception as e:
      cloudlog.exception(f"Error migrating Subaru manual-yield torque floor: {e}")
