from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_SUBARU = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/vehicle/brands/subaru.py"
TICI_FORD = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/vehicle/brands/ford.py"
MICI_VEHICLE = REPO_ROOT / "selfdrive/ui/bp/mici/layouts/settings/vehicle_mici.py"
MICI_SUBARU = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/layouts/subaru.py"
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_tici_subaru_brand_page_hosts_stop_and_go_only():
  source = _read(TICI_SUBARU)
  assert 'param="SubaruStopAndGo"' in source
  assert 'param="SubaruStopAndGoManualParkingBrake"' in source
  assert 'param="MCSubaruAdvancedTuning"' not in source
  assert 'param="MCSubaruSoftCaptureEnabled"' not in source
  assert "Manual Yield Resume" not in source


def test_tici_subaru_brand_page_preserves_stop_and_go_platform_logic():
  source = _read(TICI_SUBARU)
  assert "self.has_stop_and_go = not (config.flags & (SubaruFlags.GLOBAL_GEN2 | SubaruFlags.HYBRID))" in source
  assert "toggle.action_item.set_enabled(self.has_stop_and_go and ui_state.is_offroad())" in source
  assert 'Enable "Always Offroad" in Device panel, or turn vehicle off to toggle.' in source
  assert 'action_item.set_state(' not in source


def test_ford_brand_page_does_not_gain_subaru_controls():
  source = _read(TICI_FORD)
  assert "MCSubaru" not in source
  assert "SubaruStopAndGo" not in source


def test_mici_vehicle_menu_still_adds_subaru_entry_only_for_subaru_brand():
  source = _read(MICI_VEHICLE)
  assert 'self._btn_subaru = BigButtonBP(tr("subaru settings")' in source
  assert 'is_subaru = get_vehicle_brand() == "subaru"' in source
  assert "self._btn_subaru.set_visible(is_subaru)" in source


def test_mici_subaru_layout_remains_the_driving_only_subaru_page():
  source = _read(MICI_SUBARU)
  assert 'GreyBigButton("stop and\\ngo")' in source
  assert 'GreyBigButton("lateral\\ntuning")' in source
  assert '"SubaruStopAndGo"' in source
  assert '"MCSubaruAdvancedTuning"' in source
  assert '"MCSubaruSmoothingTune"' in source
  assert '"MCSubaruCenterDampingStrength"' in source
  assert '"MCSubaruManualYieldResumeSpeed"' in source
  assert '"MCSubaruManualYieldResumeSoftness"' in source
  assert '"MCSubaruSoftCaptureEnabled"' not in source
  assert '"MCSubaruCenterDampingTune"' not in source
  assert 'ShowBrakeStatus' not in source
  assert 'DynamicPathColor' not in source


def test_subaru_params_defaults_and_metadata_match_soft_capture_only_tici_contract():
  params_source = _read(PARAMS_KEYS)
  metadata_source = _read(PARAMS_METADATA)
  assert '{"MCSubaruAdvancedTuning", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruSoftCaptureEnabled", {PERSISTENT | BACKUP, BOOL, "1"}}' in params_source
  assert '{"MCSubaruSoftCaptureLevel", {PERSISTENT | BACKUP, INT, "1"}}' in params_source
  assert '{"MCSubaruSmoothingTune", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruSmoothingStrength", {PERSISTENT | BACKUP, INT, "0"}}' in params_source
  assert '{"MCSubaruCenterDampingTune", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruCenterDampingStrength", {PERSISTENT | BACKUP, INT, "0"}}' in params_source
  assert '{"MCSubaruManualYieldResumeSpeed", {PERSISTENT | BACKUP, INT, "4"}}' in params_source
  assert '{"MCSubaruManualYieldResumeSoftness", {PERSISTENT | BACKUP, INT, "4"}}' in params_source
  assert '"MCSubaruSoftCaptureEnabled"' in metadata_source
  assert '"MCSubaruSoftCaptureLevel"' in metadata_source
  assert '"MCSubaruCenterDampingTune"' in metadata_source
  assert '"MCSubaruCenterDampingStrength"' in metadata_source
  assert '"MCSubaruManualYieldResumeSpeed"' not in metadata_source
  assert '"MCSubaruManualYieldResumeSoftness"' not in metadata_source
