from openpilot.common.params import Params
from openpilot.sunnypilot.system.params_migration import (
  MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION,
  SUBARU_SOFT_CAPTURE_ONLY_MIGRATION_VERSION,
  run_migration,
)


class TestSunnypilotParamsMigration:
  def setup_method(self):
    self.params = Params()
    for key in (
      "TrueVEgoUI",
      "MatchVehicleSpeedometer",
      "MatchVehicleSpeedometerMigrated",
      "MCSubaruSoftCaptureEnabled",
      "MCSubaruSoftCaptureLevel",
      "MCSubaruSmoothingTune",
      "MCSubaruSmoothingStrength",
      "MCSubaruCenterDampingTune",
      "MCSubaruCenterDampingStrength",
      "SubaruSoftCaptureOnlyMigrated",
    ):
      self.params.remove(key)

  def test_true_v_ego_false_migrates_to_match_vehicle_speedometer_true(self):
    self.params.put_bool("TrueVEgoUI", False)

    run_migration(self.params)

    assert self.params.get_bool("MatchVehicleSpeedometer")
    assert self.params.get("TrueVEgoUI") is None
    assert self.params.get("MatchVehicleSpeedometerMigrated") == MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION

  def test_true_v_ego_true_migrates_to_match_vehicle_speedometer_false(self):
    self.params.put_bool("TrueVEgoUI", True)

    run_migration(self.params)

    assert not self.params.get_bool("MatchVehicleSpeedometer")
    assert self.params.get("TrueVEgoUI") is None
    assert self.params.get("MatchVehicleSpeedometerMigrated") == MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION

  def test_existing_match_vehicle_speedometer_value_wins_over_legacy_true_v_ego(self):
    self.params.put_bool("MatchVehicleSpeedometer", False)
    self.params.put_bool("TrueVEgoUI", False)

    run_migration(self.params)

    assert not self.params.get_bool("MatchVehicleSpeedometer")
    assert self.params.get("TrueVEgoUI") is None
    assert self.params.get("MatchVehicleSpeedometerMigrated") == MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION

  def test_match_vehicle_speedometer_migration_is_idempotent(self):
    self.params.put_bool("TrueVEgoUI", True)

    run_migration(self.params)
    migrated_value = self.params.get_bool("MatchVehicleSpeedometer")
    run_migration(self.params)

    assert self.params.get_bool("MatchVehicleSpeedometer") == migrated_value
    assert self.params.get("TrueVEgoUI") is None
    assert self.params.get("MatchVehicleSpeedometerMigrated") == MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION

  def test_subaru_soft_capture_only_migration_force_resets_existing_values(self):
    self.params.put_bool("MCSubaruSoftCaptureEnabled", False)
    self.params.put("MCSubaruSoftCaptureLevel", "5")
    self.params.put_bool("MCSubaruSmoothingTune", True)
    self.params.put("MCSubaruSmoothingStrength", "4")
    self.params.put_bool("MCSubaruCenterDampingTune", True)
    self.params.put("MCSubaruCenterDampingStrength", "4")

    run_migration(self.params)

    assert self.params.get_bool("MCSubaruSoftCaptureEnabled")
    assert self.params.get("MCSubaruSoftCaptureLevel") == "1"
    assert not self.params.get_bool("MCSubaruSmoothingTune")
    assert self.params.get("MCSubaruSmoothingStrength") == "0"
    assert not self.params.get_bool("MCSubaruCenterDampingTune")
    assert self.params.get("MCSubaruCenterDampingStrength") == "0"
    assert self.params.get("SubaruSoftCaptureOnlyMigrated") == SUBARU_SOFT_CAPTURE_ONLY_MIGRATION_VERSION

  def test_subaru_soft_capture_only_migration_is_idempotent_after_sentinel_is_set(self):
    run_migration(self.params)

    self.params.put_bool("MCSubaruSoftCaptureEnabled", False)
    self.params.put("MCSubaruSoftCaptureLevel", "5")
    self.params.put_bool("MCSubaruSmoothingTune", True)
    self.params.put("MCSubaruSmoothingStrength", "4")
    self.params.put_bool("MCSubaruCenterDampingTune", True)
    self.params.put("MCSubaruCenterDampingStrength", "4")

    run_migration(self.params)

    assert not self.params.get_bool("MCSubaruSoftCaptureEnabled")
    assert self.params.get("MCSubaruSoftCaptureLevel") == "5"
    assert self.params.get_bool("MCSubaruSmoothingTune")
    assert self.params.get("MCSubaruSmoothingStrength") == "4"
    assert self.params.get_bool("MCSubaruCenterDampingTune")
    assert self.params.get("MCSubaruCenterDampingStrength") == "4"
    assert self.params.get("SubaruSoftCaptureOnlyMigrated") == SUBARU_SOFT_CAPTURE_ONLY_MIGRATION_VERSION
