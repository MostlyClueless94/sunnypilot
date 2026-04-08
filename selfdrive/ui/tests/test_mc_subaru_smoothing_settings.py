from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MC_CUSTOM = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/mc_custom.py"
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_mc_custom_hosts_soft_capture_only_subaru_test_rows_at_the_end_of_the_page():
  source = _read(MC_CUSTOM)
  positions = [
    source.index('param="MCSubaruAdvancedTuning"'),
    source.index('param="MCSubaruSoftCaptureEnabled"'),
    source.index('param="MCSubaruSoftCaptureLevel"'),
    source.index('param="MCSubaruSmoothingTune"'),
    source.index('param="MCSubaruSmoothingStrength"'),
    source.index('param="MCSubaruCenterDampingTune"'),
    source.index('param="MCSubaruCenterDampingStrength"'),
  ]

  assert 'SectionHeader(tr("Subaru"))' in source
  assert source.index("self._show_vehicle_brake_status,") < source.index("self._subaru_header,")
  assert positions == sorted(positions)
  assert 'param="MCSubaruManualYieldResumeSpeed"' not in source
  assert 'param="MCSubaruManualYieldResumeSoftness"' not in source
  assert 'title=lambda: tr("Subaru Center Damping")' in source
  assert 'title=lambda: tr("Center Damping Strength")' in source
  assert 'SOFT_CAPTURE_STRENGTH_LABELS = ["1 - Light", "2 - Mild", "3 - Medium", "4 - Strong", "5 - Max"]' in source


def test_mc_custom_keeps_all_subaru_rows_under_advanced_tuning_and_uses_per_toggle_enablement():
  source = _read(MC_CUSTOM)
  assert 'self._subaru_soft_capture.set_visible(advanced_tuning_enabled)' in source
  assert 'self._subaru_soft_capture_strength.set_visible(advanced_tuning_enabled)' in source
  assert 'self._subaru_smoothing_tune.set_visible(advanced_tuning_enabled)' in source
  assert 'self._subaru_smoothing_strength.set_visible(advanced_tuning_enabled)' in source
  assert 'self._subaru_center_damping_tune.set_visible(advanced_tuning_enabled)' in source
  assert 'self._subaru_center_damping_strength.set_visible(advanced_tuning_enabled)' in source
  assert 'self._subaru_soft_capture_strength.action_item.set_enabled(soft_capture_enabled)' in source
  assert 'self._subaru_smoothing_strength.action_item.set_enabled(smoothing_enabled)' in source
  assert 'self._subaru_center_damping_strength.action_item.set_enabled(center_damping_enabled)' in source
  assert 'self._subaru_soft_capture.action_item.current_value' not in source
  assert 'self._subaru_center_damping_tune.action_item.set_state(center_damping_enabled)' in source


def test_params_keys_register_soft_capture_only_defaults_and_keep_manual_yield_as_legacy_storage():
  source = _read(PARAMS_KEYS)
  assert '{"MCSubaruAdvancedTuning", {PERSISTENT | BACKUP, BOOL, "0"}}' in source
  assert '{"MCSubaruSoftCaptureEnabled", {PERSISTENT | BACKUP, BOOL, "1"}}' in source
  assert '{"MCSubaruSoftCaptureLevel", {PERSISTENT | BACKUP, INT, "1"}}' in source
  assert '{"MCSubaruSmoothingTune", {PERSISTENT | BACKUP, BOOL, "0"}}' in source
  assert '{"MCSubaruSmoothingStrength", {PERSISTENT | BACKUP, INT, "0"}}' in source
  assert '{"MCSubaruCenterDampingTune", {PERSISTENT | BACKUP, BOOL, "0"}}' in source
  assert '{"MCSubaruCenterDampingStrength", {PERSISTENT | BACKUP, INT, "0"}}' in source
  assert '{"SubaruSoftCaptureOnlyMigrated", {PERSISTENT | BACKUP, STRING, "0.0"}}' in source
  assert '{"MCSubaruManualYieldResumeSpeed", {PERSISTENT | BACKUP, INT, "4"}}' in source
  assert '{"MCSubaruManualYieldResumeSoftness", {PERSISTENT | BACKUP, INT, "4"}}' in source


def test_params_metadata_exposes_only_active_soft_capture_smoothing_and_center_damping_controls():
  source = _read(PARAMS_METADATA)
  assert '"MCSubaruAdvancedTuning"' in source
  assert '"MCSubaruSoftCaptureEnabled"' in source
  assert '"MCSubaruSoftCaptureLevel"' in source
  assert '"MCSubaruSmoothingTune"' in source
  assert '"MCSubaruSmoothingStrength"' in source
  assert '"MCSubaruCenterDampingTune"' in source
  assert '"MCSubaruCenterDampingStrength"' in source
  assert '"MCSubaruManualYieldResumeSpeed"' not in source
  assert '"MCSubaruManualYieldResumeSoftness"' not in source
  assert 'Experiment - MostlyClueless only.' in source
  assert '"title": "Subaru Center Damping"' in source
  assert '"title": "Center Damping Strength"' in source
  assert 'Enable the optional Subaru low-speed smoothing experiment below.' in source
  assert 'Enable the optional Subaru near-center damping experiment below.' in source
  assert '"label": "1 - Light"' in source
  assert '"label": "5 - Max"' in source
  assert 'Experiment — MostlyClueless only.' not in source
