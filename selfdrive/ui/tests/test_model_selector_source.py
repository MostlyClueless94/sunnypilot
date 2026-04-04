from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_MODELS = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/models.py"
MICI_MODELS = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/layouts/models.py"
TREE_DIALOG = REPO_ROOT / "system/ui/sunnypilot/widgets/tree_dialog.py"
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_model_selector_uses_single_default_model_behavior():
  tici_source = _read(TICI_MODELS)
  mici_source = _read(MICI_MODELS)

  assert 'TreeNode("Default", {\'display_name\': tr("Default Model"), \'short_name\': "Default"})' in tici_source
  assert 'DEFAULT_MODEL_OPTION_LABEL' not in tici_source
  assert 'BUILTIN_STOCK_OPTION_REF' not in tici_source
  assert 'ModelManager_UseBuiltinStock' not in tici_source
  assert 'North Nevada Model V2 is the default on subi-staging.' not in tici_source

  assert 'BigButton(tr("default model"))' in mici_source
  assert 'BigButton("north nevada\\nmodel v2", "default")' not in mici_source
  assert 'BigButton("built-in\\nstock"' not in mici_source
  assert 'ModelManager_UseBuiltinStock' not in mici_source


def test_builtin_stock_param_is_removed_from_params_files():
  params_source = _read(PARAMS_KEYS)
  metadata_source = _read(PARAMS_METADATA)

  assert 'ModelManager_UseBuiltinStock' not in params_source
  assert '"ModelManager_UseBuiltinStock"' not in metadata_source
