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


def test_tici_subaru_page_uses_soft_capture_only_tuning_order_and_per_toggle_enablement():
  source = _read(TICI_SUBARU)
  positions = [
    source.index('param="MCSubaruAdvancedTuning"'),
    source.index('param="MCSubaruSoftCaptureEnabled"'),
    source.index('param="MCSubaruSoftCaptureLevel"'),
    source.index('param="MCSubaruSmoothingTune"'),
    source.index('param="MCSubaruSmoothingStrength"'),
    source.index('param="MCSubaruCenterDampingTune"'),
    source.index('param="MCSubaruCenterDampingStrength"'),
    source.index('param="ShowBrakeStatus"'),
  ]

  assert 'tr("Angle Subaru Tuning")' in source
  assert 'tr("Visuals")' in source
  assert positions == sorted(positions)
  assert 'param="MCSubaruManualYieldResumeSpeed"' not in source
  assert 'param="MCSubaruManualYieldResumeSoftness"' not in source
  assert 'title=lambda: tr("Subaru Center Damping")' in source
  assert 'title=lambda: tr("Center Damping Strength")' in source
  assert 'Angle-based Subaru only. Does not affect older torque-based Subaru models.' in source
  assert 'self._subaru_soft_capture.set_visible(enabled)' in source
  assert 'self._subaru_soft_capture_strength.set_visible(enabled)' in source
  assert 'self._subaru_smoothing_tune.set_visible(enabled)' in source
  assert 'self._subaru_smoothing_strength.set_visible(enabled)' in source
  assert 'self._subaru_center_damping_tune.set_visible(enabled)' in source
  assert 'self._subaru_center_damping_strength.set_visible(enabled)' in source
  assert 'self._subaru_soft_capture_strength.action_item.set_enabled(soft_capture_enabled)' in source
  assert 'self._subaru_smoothing_strength.action_item.set_enabled(smoothing_enabled)' in source
  assert 'self._subaru_center_damping_strength.action_item.set_enabled(center_damping_enabled)' in source
  assert '1 - Light' in source
  assert '1 — Light' not in source


def test_tici_visuals_page_still_does_not_duplicate_subaru_visual_controls():
  source = _read(TICI_VISUALS)
  assert '"DynamicPathColor"' not in source
  assert '"ShowBrakeStatus"' not in source
  assert '"HideVEgoUI"' not in source
  assert '"CustomModelPathColor"' not in source


def test_mici_subaru_page_matches_same_soft_capture_only_tuning_model():
  source = _read(MICI_SUBARU)
  positions = [
    source.index('"MCSubaruAdvancedTuning"'),
    source.index('"MCSubaruSoftCaptureEnabled"'),
    source.index('"MCSubaruSoftCaptureLevel"'),
    source.index('"MCSubaruSmoothingTune"'),
    source.index('"MCSubaruSmoothingStrength"'),
    source.index('"MCSubaruCenterDampingTune"'),
    source.index('"MCSubaruCenterDampingStrength"'),
    source.index('"ShowBrakeStatus"'),
  ]

  assert 'GreyBigButton("angle subaru\\ntuning")' in source
  assert 'GreyBigButton("visuals")' in source
  assert positions == sorted(positions)
  assert '"MCSubaruManualYieldResumeSpeed"' not in source
  assert '"MCSubaruManualYieldResumeSoftness"' not in source
  assert 'BigParamControl(' in source
  assert 'older torque models unaffected' in source
  assert '"subaru center\\ndamping"' in source
  assert '"MCSubaruCenterDampingTune"' in source
  assert 'BigButton("center damping\\nstrength")' in source
  assert 'self._subaru_soft_capture_strength_btn.set_enabled(soft_capture_enabled)' in source
  assert 'self._subaru_smoothing_strength_btn.set_enabled(smoothing_enabled)' in source
  assert 'self._subaru_center_damping_strength_btn.set_enabled(center_damping_enabled)' in source
  assert '1 - Light' in source
  assert '1 — Light' not in source


def test_mici_general_toggles_do_not_duplicate_brake_status():
  source = _read(MICI_TOGGLES)
  assert "ShowBrakeStatus" not in source


def test_staging_params_defaults_and_metadata_match_soft_capture_only_contract():
  params_source = _read(PARAMS_KEYS)
  metadata_source = _read(PARAMS_METADATA)

  assert '{"MCSubaruAdvancedTuning", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruSoftCaptureEnabled", {PERSISTENT | BACKUP, BOOL, "1"}}' in params_source
  assert '{"MCSubaruSoftCaptureLevel", {PERSISTENT | BACKUP, INT, "1"}}' in params_source
  assert '{"MCSubaruSmoothingTune", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruSmoothingStrength", {PERSISTENT | BACKUP, INT, "0"}}' in params_source
  assert '{"MCSubaruCenterDampingTune", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruCenterDampingStrength", {PERSISTENT | BACKUP, INT, "0"}}' in params_source
  assert '{"SubaruSoftCaptureOnlyMigrated", {PERSISTENT | BACKUP, STRING, "0.0"}}' in params_source
  assert '{"MCSubaruManualYieldResumeSpeed", {PERSISTENT | BACKUP, INT, "4"}}' in params_source
  assert '{"MCSubaruManualYieldResumeSoftness", {PERSISTENT | BACKUP, INT, "4"}}' in params_source

  assert '"MCSubaruAdvancedTuning"' in metadata_source
  assert '"MCSubaruSoftCaptureEnabled"' in metadata_source
  assert '"MCSubaruSoftCaptureLevel"' in metadata_source
  assert '"MCSubaruSmoothingTune"' in metadata_source
  assert '"MCSubaruSmoothingStrength"' in metadata_source
  assert '"MCSubaruCenterDampingTune"' in metadata_source
  assert '"MCSubaruCenterDampingStrength"' in metadata_source
  assert '"MCSubaruManualYieldResumeSpeed"' not in metadata_source
  assert '"MCSubaruManualYieldResumeSoftness"' not in metadata_source
  assert '"title": "Subaru Center Damping"' in metadata_source
  assert '"title": "Center Damping Strength"' in metadata_source
  assert 'Angle-based Subaru only. Does not affect older torque-based Subaru models.' in metadata_source
  assert 'Show angle Subaru tuning controls. Hidden controls keep their saved values active.' in metadata_source
  assert '{ "value": 1, "label": "1 - Light" }' in metadata_source
  assert '{ "value": 5, "label": "5 - Max" }' in metadata_source
  assert '1 — Light' not in metadata_source
