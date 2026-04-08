from openpilot.common.params import Params
from openpilot.sunnypilot.system.params_migration import (
  SUBARU_SOFT_CAPTURE_ONLY_MIGRATION_VERSION,
  run_migration,
)


class TestSunnypilotParamsMigration:
  def setup_method(self):
    self.params = Params()
    for key in (
      "MCSubaruSoftCaptureEnabled",
      "MCSubaruSoftCaptureLevel",
      "MCSubaruSmoothingTune",
      "MCSubaruSmoothingStrength",
      "MCSubaruCenterDampingTune",
      "MCSubaruCenterDampingStrength",
      "SubaruSoftCaptureOnlyMigrated",
    ):
      self.params.remove(key)

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
