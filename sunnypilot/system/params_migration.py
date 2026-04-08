"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.common.swaglog import cloudlog

ONROAD_BRIGHTNESS_MIGRATION_VERSION: str = "1.0"
SUBARU_SOFT_CAPTURE_ONLY_MIGRATION_VERSION: str = "mostlyclueless-1.0"


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

  # reset Subaru tuning to the soft-capture-only test defaults
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
        "Successfully reset Subaru tuning to the MostlyClueless soft-capture-only test defaults. "
        + f"Setting SubaruSoftCaptureOnlyMigrated to {SUBARU_SOFT_CAPTURE_ONLY_MIGRATION_VERSION}"
      )
    except Exception as e:
      cloudlog.exception(f"Error migrating Subaru soft-capture-only defaults: {e}")
