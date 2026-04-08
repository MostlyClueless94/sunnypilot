from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MC_CUSTOM = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/mc_custom.py"
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_mc_custom_hosts_subaru_controls_at_the_end_of_the_page():
  source = _read(MC_CUSTOM)
  assert 'param="DynamicPathColor"' in source
  assert 'param="DynamicPathColorPalette"' in source
  assert 'param="CustomModelPathColor"' in source
  assert 'param="MCShowVehicleBrakeStatus"' in source
  assert 'SectionHeader(tr("Subaru"))' in source
  assert source.index("self._show_vehicle_brake_status,") < source.index("self._subaru_header,")
  assert 'param="SubaruStopAndGo"' not in source
  assert 'param="SubaruStopAndGoManualParkingBrake"' not in source
  assert 'param="MCSubaruAdvancedTuning"' in source
  assert 'param="MCSubaruSmoothingTune"' in source
  assert 'param="MCSubaruSmoothingStrength"' in source
  assert 'param="MCSubaruCenterDampingStrength"' in source
  assert 'param="MCSubaruManualYieldResumeSpeed"' in source
  assert 'param="MCSubaruManualYieldResumeSoftness"' in source
  assert 'Subaru Delay Tweak (Test)' not in source
  assert 'self._dynamic_path_color_palette.action_item.set_enabled(self._params.get_bool("DynamicPathColor"))' in source


def test_mc_custom_always_shows_subaru_section_and_preserves_tuning_logic():
  source = _read(MC_CUSTOM)
  assert 'def _get_current_brand(self) -> str:' not in source
  assert 'CarPlatformBundle' not in source
  assert 'def _is_subaru_active(self) -> bool:' not in source
  assert 'def _get_subaru_stop_and_go_available(self) -> bool:' not in source
  assert 'def _set_subaru_section_visibility(self, advanced_tuning_enabled: bool) -> None:' in source
  assert 'self._subaru_header.set_visible(True)' in source
  assert 'self._subaru_advanced_tuning.set_visible(True)' in source
  assert 'self._subaru_smoothing_tune.set_visible(advanced_tuning_enabled)' in source
  assert 'self._manual_yield_resume_softness.set_visible(advanced_tuning_enabled)' in source
  assert 'self._subaru_smoothing_strength.action_item.set_enabled(smoothing_enabled)' in source
  assert 'self._subaru_center_damping.action_item.set_enabled(smoothing_enabled)' in source
  assert 'self._set_subaru_section_visibility(advanced_tuning_enabled)' in source
  assert 'callback=self._on_subaru_toggle_changed' not in source
  assert 'def _on_subaru_toggle_changed(self, _):' not in source
  assert 'self._subaru_advanced_tuning.action_item.set_state(advanced_tuning_enabled)' in source
  assert 'self._subaru_smoothing_tune.action_item.set_state(smoothing_enabled)' in source


def test_params_keys_register_subaru_tuning_defaults_for_mc_custom_menu():
  source = _read(PARAMS_KEYS)
  assert '{"MCSubaruAdvancedTuning", {PERSISTENT | BACKUP, BOOL, "0"}}' in source
  assert '{"MCSubaruSmoothingTune", {PERSISTENT | BACKUP, BOOL, "1"}}' in source
  assert '{"MCSubaruSmoothingStrength", {PERSISTENT | BACKUP, INT, "2"}}' in source
  assert '{"MCSubaruCenterDampingStrength", {PERSISTENT | BACKUP, INT, "2"}}' in source
  assert '{"MCSubaruManualYieldResumeSpeed", {PERSISTENT | BACKUP, INT, "4"}}' in source
  assert '{"MCSubaruManualYieldResumeSoftness", {PERSISTENT | BACKUP, INT, "4"}}' in source
  assert '{"SubaruStopAndGo", {PERSISTENT | BACKUP, BOOL, "0"}}' in source
  assert '{"SubaruStopAndGoManualParkingBrake", {PERSISTENT | BACKUP, BOOL, "0"}}' in source


def test_params_metadata_describes_subaru_brand_menu_ranges_and_labels():
  source = _read(PARAMS_METADATA)
  assert '"MCSubaruAdvancedTuning"' in source
  assert '"title": "Advanced Tuning"' in source
  assert 'Show Subaru lateral tuning controls. Hidden controls keep their saved values active.' in source
  assert '"MCSubaruSmoothingTune"' in source
  assert '"title": "Subaru Steering Smoothing"' in source
  assert '"MCSubaruSmoothingStrength"' in source
  assert '"min": -3' in source
  assert '"max": 4' in source
  assert '"label": "-3"' in source
  assert '"label": "+4"' in source
  assert '"label": "+5"' not in source
  assert '"label": "-4"' not in source
  assert '"MCSubaruCenterDampingStrength"' in source
  assert '"title": "Center Damping"' in source
  assert '"MCSubaruManualYieldResumeSpeed"' in source
  assert '"title": "Manual Yield Resume Speed"' in source
  assert '"label": "Fastest"' in source
  assert '"label": "Slow"' in source
  assert '"label": "Slowest"' in source
  assert '"MCSubaruManualYieldResumeSoftness"' in source
  assert '"title": "Manual Yield Resume Softness"' in source
  assert '"label": "Standard"' in source
  assert '"label": "Extra Soft"' in source
  assert '"label": "Max Soft"' in source
