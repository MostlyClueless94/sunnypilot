from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_SETTINGS = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/settings.py"
TICI_SUBARU = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/subaru.py"
TICI_VISUALS = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/visuals.py"
MICI_SETTINGS = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/layouts/settings.py"
MICI_SUBARU = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/layouts/subaru.py"
MICI_TOGGLES = REPO_ROOT / "selfdrive/ui/mici/layouts/settings/toggles.py"
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"

TUNING_PARAMS = [
  "MCSubaruAdvancedTuning",
  "MCSubaruManualYieldTorqueThresholdEnabled",
  "MCSubaruManualYieldTorqueThreshold",
  "MCSubaruManualYieldResumeSoftnessEnabled",
  "MCSubaruManualYieldResumeSoftness",
  "MCSubaruManualYieldReleaseGuardEnabled",
  "MCSubaruManualYieldReleaseGuardLevel",
  "MCSubaruSoftCaptureEnabled",
  "MCSubaruSoftCaptureLevel",
]
METADATA_PARAMS = ["MCSubaruMatchVehicleSpeedometer", *TUNING_PARAMS]
RETIRED_TUNING_PARAMS = [
  "MCSubaruSmoothingTune",
  "MCSubaruSmoothingStrength",
  "MCSubaruCenterDampingTune",
  "MCSubaruCenterDampingStrength",
]


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_tici_and_mici_settings_roots_still_expose_dedicated_subaru_panels():
  tici_source = _read(TICI_SETTINGS)
  mici_source = _read(MICI_SETTINGS)

  assert 'from openpilot.selfdrive.ui.sunnypilot.layouts.settings.subaru import SubaruLayout' in tici_source
  assert 'PanelInfo(tr_noop("Subaru"), SubaruLayout()' in tici_source
  assert 'from openpilot.selfdrive.ui.sunnypilot.mici.layouts.subaru import SubaruLayoutMici' in mici_source
  assert 'subaru_panel = SubaruLayoutMici(back_callback=gui_app.pop_widget)' in mici_source
  assert 'subaru_btn = BigButton("subaru"' in mici_source


def test_tici_subaru_page_uses_bluepilot_tuning_order_and_per_toggle_enablement():
  source = _read(TICI_SUBARU)
  positions = [source.index(f'param="{param}"') for param in TUNING_PARAMS]
  tuning_items = source[source.index('SubaruSectionHeader(lambda: tr("Angle Subaru Tuning"))'):source.index('SubaruSectionHeader(lambda: tr("Visuals"))')]
  visuals_items = source[source.index('SubaruSectionHeader(lambda: tr("Visuals"))'):source.index("  def _update_state")]

  assert 'tr("Angle Subaru Tuning")' in source
  assert 'tr("Visuals")' in source
  assert positions == sorted(positions)
  assert "self._subaru_match_vehicle_speed" not in tuning_items
  assert visuals_items.index("self._subaru_match_vehicle_speed") < visuals_items.index("self._show_brake_status")
  for param in RETIRED_TUNING_PARAMS:
    assert f'param="{param}"' not in source
  assert 'Angle-based Subaru only. Does not affect older torque-based Subaru models.' in source
  assert 'Experiment - subi-staging only.' in source
  assert 'self._manual_yield_torque_threshold_enabled.set_visible(enabled)' in source
  assert 'self._manual_yield_resume_softness_enabled.set_visible(enabled)' in source
  assert 'self._manual_yield_release_guard_enabled.set_visible(enabled)' in source
  assert 'self._subaru_soft_capture.set_visible(enabled)' in source
  assert 'self._manual_yield_torque_threshold.action_item.set_enabled(torque_threshold_enabled)' in source
  assert 'self._manual_yield_resume_softness.action_item.set_enabled(resume_softness_enabled)' in source
  assert 'self._manual_yield_release_guard_level.action_item.set_enabled(release_guard_enabled)' in source
  assert 'self._subaru_soft_capture_strength.action_item.set_enabled(soft_capture_enabled)' in source
  assert 'no SubiPilot reclaim ramp is applied' in source
  assert '80 - Stock' in source
  assert '1 - Light' in source
  assert "1 \u2014 Light" not in source


def test_tici_visuals_page_still_does_not_duplicate_subaru_visual_controls():
  source = _read(TICI_VISUALS)
  assert '"DynamicPathColor"' not in source
  assert '"ShowBrakeStatus"' not in source
  assert '"HideVEgoUI"' not in source
  assert '"CustomModelPathColor"' not in source


def test_mici_subaru_page_matches_same_bluepilot_tuning_model():
  source = _read(MICI_SUBARU)
  main_items = source[source.index("self.main_items = ["):source.index("self._scroller.add_widgets")]
  ordered_items = [
    "self._subaru_advanced_tuning_toggle",
    "self._manual_yield_torque_threshold_toggle",
    "self._manual_yield_torque_threshold_btn",
    "self._manual_yield_resume_softness_toggle",
    "self._manual_yield_resume_softness_btn",
    "self._manual_yield_release_guard_toggle",
    "self._manual_yield_release_guard_btn",
    "self._subaru_soft_capture_toggle",
    "self._subaru_soft_capture_strength_btn",
  ]
  positions = [main_items.index(item) for item in ordered_items]

  assert 'GreyBigButton("angle subaru\\ntuning")' in source
  assert 'GreyBigButton("visuals")' in source
  assert positions == sorted(positions)
  assert main_items.index("self._visuals_header") < main_items.index("self._match_vehicle_speed")
  assert main_items.index("self._match_vehicle_speed") < main_items.index("self._show_brake_status")
  for param in RETIRED_TUNING_PARAMS:
    assert f'"{param}"' not in source
  assert 'older torque models unaffected' in source
  assert '"custom yield\\ntorque"' in source
  assert 'BigButton("manual yield\\ntorque")' in source
  assert '"custom resume\\nsoftness"' in source
  assert 'off means no SubiPilot reclaim ramp' in source
  assert 'BigButton("manual yield\\nresume softness")' in source
  assert '"manual yield\\nrelease guard"' in source
  assert 'BigButton("release guard\\nstrength")' in source
  assert '"soft-capture\\nengage blend"' in source
  assert 'BigButton("soft-capture\\nstrength")' in source
  assert 'self._manual_yield_torque_threshold_btn.set_enabled(torque_threshold_enabled)' in source
  assert 'self._manual_yield_resume_softness_btn.set_enabled(resume_softness_enabled)' in source
  assert 'self._manual_yield_release_guard_btn.set_enabled(release_guard_enabled)' in source
  assert 'self._subaru_soft_capture_strength_btn.set_enabled(soft_capture_enabled)' in source
  assert '1 - Light' in source
  assert "1 \u2014 Light" not in source


def test_mici_general_toggles_do_not_duplicate_brake_status():
  source = _read(MICI_TOGGLES)
  assert "ShowBrakeStatus" not in source


def test_staging_params_defaults_and_metadata_match_bluepilot_tuning_contract():
  params_source = _read(PARAMS_KEYS)
  metadata_source = _read(PARAMS_METADATA)

  assert '{"MCSubaruAdvancedTuning", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruMatchVehicleSpeedometer", {PERSISTENT | BACKUP, BOOL, "1"}}' in params_source
  assert '{"MCSubaruManualYieldTorqueThresholdEnabled", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruManualYieldTorqueThreshold", {PERSISTENT | BACKUP, INT, "80"}}' in params_source
  assert '{"MCSubaruManualYieldResumeSoftnessEnabled", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruManualYieldResumeSoftness", {PERSISTENT | BACKUP, INT, "4"}}' in params_source
  assert '{"MCSubaruManualYieldReleaseGuardEnabled", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruManualYieldReleaseGuardLevel", {PERSISTENT | BACKUP, INT, "2"}}' in params_source
  assert '{"MCSubaruSoftCaptureEnabled", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruSoftCaptureLevel", {PERSISTENT | BACKUP, INT, "3"}}' in params_source
  assert '{"Subaru11BluePilotTuningMigrated", {PERSISTENT | BACKUP, STRING, "0.0"}}' in params_source

  for param in METADATA_PARAMS:
    assert f'"{param}"' in metadata_source
  for param in RETIRED_TUNING_PARAMS:
    assert f'"{param}"' not in metadata_source
  assert '"MatchVehicleSpeedometer"' not in metadata_source
  assert 'Manual Yield Torque Threshold' in metadata_source
  assert 'Manual Yield Resume Softness' in metadata_source
  assert 'no SubiPilot reclaim ramp is applied' in metadata_source
  assert 'Release Guard Strength' in metadata_source
  assert 'Angle-based Subaru only. Does not affect older torque-based Subaru models.' in metadata_source
  assert 'Experiment - subi-staging only.' in metadata_source
  assert '{ "value": 80, "label": "80 - Stock" }' in metadata_source
  assert '{ "value": 1, "label": "1 - Light" }' in metadata_source
  assert '{ "value": 5, "label": "5 - Max" }' in metadata_source
  assert "1 \u2014 Light" not in metadata_source
