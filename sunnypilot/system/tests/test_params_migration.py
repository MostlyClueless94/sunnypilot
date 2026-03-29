import unittest

from openpilot.common.params import Params
from openpilot.sunnypilot.system.params_migration import (
  LANEFULL_MODE_RESET_MIGRATION_VERSION,
  SUBARU_ADVANCED_LATERAL_TUNING_RESET_MIGRATION_VERSION,
  run_migration,
)


class TestParamsMigration(unittest.TestCase):
  def setUp(self):
    self.params = Params()
    for key in (
      "CarPlatformBundle",
      "enable_human_turn_detection",
      "lane_change_factor_high",
      "enable_lane_positioning",
      "custom_path_offset",
      "enable_lane_full_mode",
      "custom_profile",
      "pc_blend_ratio_high_C_UI",
      "pc_blend_ratio_low_C_UI",
      "LC_PID_gain_UI",
      "BlinkerPauseLaneChange",
      "BlinkerMinLateralControlSpeed",
      "disable_BP_lat_UI",
      "LanefullModeResetMigrated",
      "SubaruAdvancedLateralTuningResetMigrated",
    ):
      self.params.remove(key)

  def tearDown(self):
    for key in (
      "CarPlatformBundle",
      "enable_human_turn_detection",
      "lane_change_factor_high",
      "enable_lane_positioning",
      "custom_path_offset",
      "enable_lane_full_mode",
      "custom_profile",
      "pc_blend_ratio_high_C_UI",
      "pc_blend_ratio_low_C_UI",
      "LC_PID_gain_UI",
      "BlinkerPauseLaneChange",
      "BlinkerMinLateralControlSpeed",
      "disable_BP_lat_UI",
      "LanefullModeResetMigrated",
      "SubaruAdvancedLateralTuningResetMigrated",
    ):
      self.params.remove(key)

  def test_lanefull_mode_is_reset_once(self):
    self.params.put_bool("enable_lane_full_mode", True)
    self.params.put_bool("custom_profile", True)

    run_migration(self.params)

    self.assertFalse(self.params.get_bool("enable_lane_full_mode"))
    self.assertEqual(self.params.get("LanefullModeResetMigrated"), LANEFULL_MODE_RESET_MIGRATION_VERSION)
    self.assertTrue(self.params.get_bool("custom_profile"))

    self.params.put_bool("enable_lane_full_mode", True)
    run_migration(self.params)

    self.assertTrue(self.params.get_bool("enable_lane_full_mode"))

  def test_subaru_advanced_lateral_tuning_is_reset_once(self):
    self.params.put("CarPlatformBundle", {"brand": "subaru", "platform": "SUBARU_OUTBACK_2023"})
    self.params.put_bool("enable_human_turn_detection", False)
    self.params.put("lane_change_factor_high", 0.65)
    self.params.put_bool("enable_lane_positioning", True)
    self.params.put("custom_path_offset", 0.25)
    self.params.put_bool("enable_lane_full_mode", True)
    self.params.put("custom_profile", 1)
    self.params.put("pc_blend_ratio_high_C_UI", 0.9)
    self.params.put("pc_blend_ratio_low_C_UI", 0.8)
    self.params.put("LC_PID_gain_UI", 4.5)
    self.params.put_bool("BlinkerPauseLaneChange", True)
    self.params.put("BlinkerMinLateralControlSpeed", 35)
    self.params.put_bool("disable_BP_lat_UI", True)

    run_migration(self.params)

    self.assertTrue(self.params.get_bool("enable_human_turn_detection"))
    self.assertEqual(self.params.get("lane_change_factor_high"), 0.85)
    self.assertFalse(self.params.get_bool("enable_lane_positioning"))
    self.assertEqual(self.params.get("custom_path_offset"), 0.0)
    self.assertFalse(self.params.get_bool("enable_lane_full_mode"))
    self.assertEqual(self.params.get("custom_profile"), 0)
    self.assertEqual(self.params.get("pc_blend_ratio_high_C_UI"), 0.4)
    self.assertEqual(self.params.get("pc_blend_ratio_low_C_UI"), 0.4)
    self.assertEqual(self.params.get("LC_PID_gain_UI"), 3.0)
    self.assertEqual(self.params.get("SubaruAdvancedLateralTuningResetMigrated"), SUBARU_ADVANCED_LATERAL_TUNING_RESET_MIGRATION_VERSION)

    self.assertTrue(self.params.get_bool("BlinkerPauseLaneChange"))
    self.assertEqual(self.params.get("BlinkerMinLateralControlSpeed"), 35)
    self.assertTrue(self.params.get_bool("disable_BP_lat_UI"))

    self.params.put("custom_profile", 1)
    run_migration(self.params)

    self.assertEqual(self.params.get("custom_profile"), 1)

  def test_non_subaru_advanced_lateral_tuning_is_not_reset(self):
    self.params.put("CarPlatformBundle", {"brand": "ford", "platform": "FORD_F150"})
    self.params.put_bool("enable_lane_positioning", True)

    run_migration(self.params)

    self.assertTrue(self.params.get_bool("enable_lane_positioning"))
    self.assertIsNone(self.params.get("SubaruAdvancedLateralTuningResetMigrated"))
