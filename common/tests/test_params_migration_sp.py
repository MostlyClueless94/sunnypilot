from openpilot.common.params import Params
from openpilot.sunnypilot.system.params_migration import (
  MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION,
  run_migration,
)


class TestSunnypilotParamsMigration:
  def setup_method(self):
    self.params = Params()

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

  def test_migration_is_idempotent(self):
    self.params.put_bool("TrueVEgoUI", True)

    run_migration(self.params)
    migrated_value = self.params.get_bool("MatchVehicleSpeedometer")
    run_migration(self.params)

    assert self.params.get_bool("MatchVehicleSpeedometer") == migrated_value
    assert self.params.get("TrueVEgoUI") is None
    assert self.params.get("MatchVehicleSpeedometerMigrated") == MATCH_VEHICLE_SPEEDOMETER_MIGRATION_VERSION

