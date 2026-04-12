from openpilot.common.params import Params
from openpilot.sunnypilot.system.params_migration import (
  MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION,
  SUBARU_11_BLUEPILOT_TUNING_MIGRATION_VERSION,
  run_migration,
)


class TestSunnypilotParamsMigration:
  def setup_method(self):
    self.params = Params()
    for key in (
      "TrueVEgoUI",
      "MatchVehicleSpeedometer",
      "MCSubaruMatchVehicleSpeedometer",
      "MatchVehicleSpeedometerMigrated",
      "MCSubaruManualYieldTorqueThresholdEnabled",
      "MCSubaruManualYieldTorqueThreshold",
      "MCSubaruManualYieldResumeSoftnessEnabled",
      "MCSubaruManualYieldResumeSoftness",
      "MCSubaruManualYieldReleaseGuardEnabled",
      "MCSubaruManualYieldReleaseGuardLevel",
      "MCSubaruSoftCaptureEnabled",
      "MCSubaruSoftCaptureLevel",
      "MCSubaruSmoothingTune",
      "MCSubaruSmoothingStrength",
      "MCSubaruCenterDampingTune",
      "MCSubaruCenterDampingStrength",
      "Subaru11BluePilotTuningMigrated",
    ):
      self.params.remove(key)

  def test_true_v_ego_false_migrates_to_subaru_match_vehicle_speedometer_true(self):
    self.params.put_bool("TrueVEgoUI", False)

    run_migration(self.params)

    assert self.params.get_bool("MCSubaruMatchVehicleSpeedometer")
    assert self.params.get("TrueVEgoUI") is None
    assert self.params.get("MatchVehicleSpeedometerMigrated") == MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION

  def test_true_v_ego_true_migrates_to_subaru_match_vehicle_speedometer_false(self):
    self.params.put_bool("TrueVEgoUI", True)

    run_migration(self.params)

    assert not self.params.get_bool("MCSubaruMatchVehicleSpeedometer")
    assert self.params.get("TrueVEgoUI") is None
    assert self.params.get("MatchVehicleSpeedometerMigrated") == MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION

  def test_existing_match_vehicle_speedometer_value_wins_over_legacy_true_v_ego(self):
    self.params.put_bool("MatchVehicleSpeedometer", False)
    self.params.put_bool("TrueVEgoUI", False)

    run_migration(self.params)

    assert not self.params.get_bool("MCSubaruMatchVehicleSpeedometer")
    assert self.params.get("TrueVEgoUI") is None
    assert self.params.get("MatchVehicleSpeedometerMigrated") == MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION

  def test_existing_subaru_match_vehicle_speedometer_value_wins_over_legacy_keys(self):
    self.params.put_bool("MCSubaruMatchVehicleSpeedometer", False)
    self.params.put_bool("MatchVehicleSpeedometer", True)
    self.params.put_bool("TrueVEgoUI", False)

    run_migration(self.params)

    assert not self.params.get_bool("MCSubaruMatchVehicleSpeedometer")
    assert self.params.get("TrueVEgoUI") is None
    assert self.params.get("MatchVehicleSpeedometerMigrated") == MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION

  def test_match_vehicle_speedometer_migration_is_idempotent(self):
    self.params.put_bool("TrueVEgoUI", True)

    run_migration(self.params)
    migrated_value = self.params.get_bool("MCSubaruMatchVehicleSpeedometer")
    run_migration(self.params)

    assert self.params.get_bool("MCSubaruMatchVehicleSpeedometer") == migrated_value
    assert self.params.get("TrueVEgoUI") is None
    assert self.params.get("MatchVehicleSpeedometerMigrated") == MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION

  def test_subaru_bluepilot_tuning_migration_force_resets_existing_values(self):
    self.params.put_bool("MCSubaruManualYieldTorqueThresholdEnabled", True)
    self.params.put("MCSubaruManualYieldTorqueThreshold", "10")
    self.params.put_bool("MCSubaruManualYieldResumeSoftnessEnabled", False)
    self.params.put("MCSubaruManualYieldResumeSoftness", "0")
    self.params.put_bool("MCSubaruManualYieldReleaseGuardEnabled", True)
    self.params.put("MCSubaruManualYieldReleaseGuardLevel", "3")
    self.params.put_bool("MCSubaruSoftCaptureEnabled", True)
    self.params.put("MCSubaruSoftCaptureLevel", "1")
    self.params.put_bool("MCSubaruSmoothingTune", True)
    self.params.put("MCSubaruSmoothingStrength", "4")
    self.params.put_bool("MCSubaruCenterDampingTune", True)
    self.params.put("MCSubaruCenterDampingStrength", "4")

    run_migration(self.params)

    assert not self.params.get_bool("MCSubaruManualYieldTorqueThresholdEnabled")
    assert self.params.get("MCSubaruManualYieldTorqueThreshold") == "80"
    assert self.params.get_bool("MCSubaruManualYieldResumeSoftnessEnabled")
    assert self.params.get("MCSubaruManualYieldResumeSoftness") == "4"
    assert not self.params.get_bool("MCSubaruManualYieldReleaseGuardEnabled")
    assert self.params.get("MCSubaruManualYieldReleaseGuardLevel") == "2"
    assert not self.params.get_bool("MCSubaruSoftCaptureEnabled")
    assert self.params.get("MCSubaruSoftCaptureLevel") == "3"
    assert not self.params.get_bool("MCSubaruSmoothingTune")
    assert self.params.get("MCSubaruSmoothingStrength") == "0"
    assert not self.params.get_bool("MCSubaruCenterDampingTune")
    assert self.params.get("MCSubaruCenterDampingStrength") == "0"
    assert self.params.get("Subaru11BluePilotTuningMigrated") == SUBARU_11_BLUEPILOT_TUNING_MIGRATION_VERSION

  def test_subaru_bluepilot_tuning_migration_is_idempotent_after_sentinel_is_set(self):
    run_migration(self.params)

    self.params.put_bool("MCSubaruManualYieldTorqueThresholdEnabled", True)
    self.params.put("MCSubaruManualYieldTorqueThreshold", "10")
    self.params.put_bool("MCSubaruManualYieldResumeSoftnessEnabled", False)
    self.params.put("MCSubaruManualYieldResumeSoftness", "0")
    self.params.put_bool("MCSubaruManualYieldReleaseGuardEnabled", True)
    self.params.put("MCSubaruManualYieldReleaseGuardLevel", "3")
    self.params.put_bool("MCSubaruSoftCaptureEnabled", True)
    self.params.put("MCSubaruSoftCaptureLevel", "1")

    run_migration(self.params)

    assert self.params.get_bool("MCSubaruManualYieldTorqueThresholdEnabled")
    assert self.params.get("MCSubaruManualYieldTorqueThreshold") == "10"
    assert not self.params.get_bool("MCSubaruManualYieldResumeSoftnessEnabled")
    assert self.params.get("MCSubaruManualYieldResumeSoftness") == "0"
    assert self.params.get_bool("MCSubaruManualYieldReleaseGuardEnabled")
    assert self.params.get("MCSubaruManualYieldReleaseGuardLevel") == "3"
    assert self.params.get_bool("MCSubaruSoftCaptureEnabled")
    assert self.params.get("MCSubaruSoftCaptureLevel") == "1"
    assert self.params.get("Subaru11BluePilotTuningMigrated") == SUBARU_11_BLUEPILOT_TUNING_MIGRATION_VERSION
