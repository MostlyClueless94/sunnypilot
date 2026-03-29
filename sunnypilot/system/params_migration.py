"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import json

from openpilot.common.swaglog import cloudlog

ONROAD_BRIGHTNESS_MIGRATION_VERSION: str = "1.0"
LANEFULL_MODE_RESET_MIGRATION_VERSION: str = "1.0"
SUBARU_ADVANCED_LATERAL_TUNING_RESET_MIGRATION_VERSION: str = "1.0"


def _get_platform_brand(_params) -> str:
  bundle = _params.get("CarPlatformBundle")
  if bundle is None:
    return ""

  if isinstance(bundle, bytes):
    try:
      bundle = bundle.decode("utf-8")
    except Exception:
      return ""

  if isinstance(bundle, str):
    try:
      bundle = json.loads(bundle)
    except Exception:
      return ""

  if hasattr(bundle, "get"):
    return str(bundle.get("brand", "")).lower()

  return ""


def run_migration(_params):
  # migrate OnroadScreenOffBrightness
  if _params.get("OnroadScreenOffBrightnessMigrated") != ONROAD_BRIGHTNESS_MIGRATION_VERSION:
    try:
      val = _params.get("OnroadScreenOffBrightness")
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

  if _params.get("LanefullModeResetMigrated") != LANEFULL_MODE_RESET_MIGRATION_VERSION:
    try:
      _params.put_bool("enable_lane_full_mode", False)
      _params.put("LanefullModeResetMigrated", LANEFULL_MODE_RESET_MIGRATION_VERSION)
      cloudlog.info("Successfully reset enable_lane_full_mode to False. "
                    f"Setting LanefullModeResetMigrated to {LANEFULL_MODE_RESET_MIGRATION_VERSION}")
    except Exception as e:
      cloudlog.exception(f"Error resetting enable_lane_full_mode: {e}")

  if (_params.get("SubaruAdvancedLateralTuningResetMigrated") != SUBARU_ADVANCED_LATERAL_TUNING_RESET_MIGRATION_VERSION and
      _get_platform_brand(_params) == "subaru"):
    try:
      _params.put_bool("enable_human_turn_detection", True)
      _params.put("lane_change_factor_high", 0.85)
      _params.put_bool("enable_lane_positioning", False)
      _params.put("custom_path_offset", 0.0)
      _params.put_bool("enable_lane_full_mode", False)
      _params.put("custom_profile", 0)
      _params.put("pc_blend_ratio_high_C_UI", 0.4)
      _params.put("pc_blend_ratio_low_C_UI", 0.4)
      _params.put("LC_PID_gain_UI", 3.0)
      _params.put("SubaruAdvancedLateralTuningResetMigrated", SUBARU_ADVANCED_LATERAL_TUNING_RESET_MIGRATION_VERSION)
      cloudlog.info("Successfully reset hidden Subaru advanced lateral tuning params to safe defaults. "
                    f"Setting SubaruAdvancedLateralTuningResetMigrated to {SUBARU_ADVANCED_LATERAL_TUNING_RESET_MIGRATION_VERSION}")
    except Exception as e:
      cloudlog.exception(f"Error resetting hidden Subaru advanced lateral tuning params: {e}")
