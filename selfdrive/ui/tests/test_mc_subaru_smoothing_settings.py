from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MC_CUSTOM = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/mc_custom.py"
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_mc_custom_contains_subaru_smoothing_controls():
  source = _read(MC_CUSTOM)
  assert 'param="MCSubaruUnwindRateTest"' not in source
  assert 'param="MCSubaruUnwindRateMode"' not in source
  assert 'param="MCSubaruChatterFix"' not in source
  assert 'MCSubaruActuatorDelayTest' in source
  assert 'Subaru Faster Unwind (Test)' not in source
  assert 'Subaru Unwind Mode' not in source
  assert 'Subaru Chatter Fix (Test)' not in source
  assert 'SUBARU_UNWIND_MODE_LABELS' not in source
  assert 'subaru_unwind_rate_test_enabled' not in source
  assert 'Subaru Delay Tweak (Test)' in source
  assert 'ConfirmDialog(tr("System reboot required for changes to take effect. Reboot now?")' in source
  assert 'ui_state.params.put_bool("DoReboot", True)' in source
  assert 'self._subaru_actuator_delay_test.action_item.set_enabled(ui_state.is_offroad())' in source
  assert 'param="MCSubaruSmoothingTune"' in source
  assert 'param="MCSubaruSmoothingStrength"' in source
  assert 'param="MCSubaruCenterDampingStrength"' in source
  assert 'self._subaru_smoothing_strength.action_item.set_enabled(subaru_smoothing_tune_enabled)' in source
  assert 'self._subaru_center_damping_strength.action_item.set_enabled(subaru_smoothing_tune_enabled)' in source
  assert 'return tr("Stock") if value == 0 else f"{value:+d}"' in source


def test_params_keys_register_subaru_smoothing_params():
  source = _read(PARAMS_KEYS)
  assert '{"MCSubaruChatterFix", {PERSISTENT | BACKUP, BOOL, "0"}}' in source
  assert '{"MCSubaruUnwindRateTest", {PERSISTENT | BACKUP, BOOL, "0"}}' in source
  assert '{"MCSubaruUnwindRateMode", {PERSISTENT | BACKUP, INT, "0"}}' in source
  assert '{"MCSubaruActuatorDelayTest", {PERSISTENT | BACKUP, BOOL, "0"}}' in source
  assert '{"MCSubaruSmoothingTune", {PERSISTENT | BACKUP, BOOL, "0"}}' in source
  assert '{"MCSubaruSmoothingStrength", {PERSISTENT | BACKUP, INT, "0"}}' in source
  assert '{"MCSubaruCenterDampingStrength", {PERSISTENT | BACKUP, INT, "0"}}' in source


def test_params_metadata_describes_subaru_smoothing_params():
  source = _read(PARAMS_METADATA)
  assert '"MCSubaruChatterFix"' in source
  assert '"MCSubaruUnwindRateTest"' in source
  assert '"MCSubaruUnwindRateMode"' in source
  assert '"label": "Both"' in source
  assert '"label": "Low Only"' in source
  assert '"label": "High Only"' in source
  assert '"MCSubaruActuatorDelayTest"' in source
  assert '"MCSubaruSmoothingTune"' in source
  assert '"MCSubaruSmoothingStrength"' in source
  assert '"MCSubaruCenterDampingStrength"' in source
  assert '"label": "Stock"' in source
