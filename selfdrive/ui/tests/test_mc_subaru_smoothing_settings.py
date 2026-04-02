from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MC_CUSTOM = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/mc_custom.py"
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_mc_custom_contains_subaru_smoothing_controls():
  source = _read(MC_CUSTOM)
  assert 'param="MCSubaruSmoothingTune"' in source
  assert 'param="MCSubaruSmoothingStrength"' in source
  assert 'param="MCSubaruCenterDampingStrength"' in source
  assert 'self._subaru_smoothing_strength.action_item.set_enabled(subaru_smoothing_tune_enabled)' in source
  assert 'self._subaru_center_damping_strength.action_item.set_enabled(subaru_smoothing_tune_enabled)' in source
  assert 'return tr("Stock") if value == 0 else f"{value:+d}"' in source


def test_params_keys_register_subaru_smoothing_params():
  source = _read(PARAMS_KEYS)
  assert '{"MCSubaruSmoothingTune", {PERSISTENT | BACKUP, BOOL, "0"}}' in source
  assert '{"MCSubaruSmoothingStrength", {PERSISTENT | BACKUP, INT, "0"}}' in source
  assert '{"MCSubaruCenterDampingStrength", {PERSISTENT | BACKUP, INT, "0"}}' in source


def test_params_metadata_describes_subaru_smoothing_params():
  source = _read(PARAMS_METADATA)
  assert '"MCSubaruSmoothingTune"' in source
  assert '"MCSubaruSmoothingStrength"' in source
  assert '"MCSubaruCenterDampingStrength"' in source
  assert '"label": "Stock"' in source
