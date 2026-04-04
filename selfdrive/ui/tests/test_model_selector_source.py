from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_MODELS = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/models.py"
MICI_MODELS = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/layouts/models.py"
TREE_DIALOG = REPO_ROOT / "system/ui/sunnypilot/widgets/tree_dialog.py"
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_model_selector_exposes_staging_default_and_builtin_stock_options():
  tici_source = _read(TICI_MODELS)
  mici_source = _read(MICI_MODELS)

  assert 'DEFAULT_MODEL_OPTION_LABEL' in tici_source
  assert 'BUILTIN_STOCK_OPTION_REF' in tici_source
  assert 'ModelManager_UseBuiltinStock' in tici_source
  assert 'North Nevada Model V2 is the default on subi-staging.' in tici_source

  assert 'BigButton("north nevada\\nmodel v2", "default")' in mici_source
  assert 'BigButton("built-in\\nstock"' in mici_source
  assert 'GreyBigButton("north nevada v2\\ndefault"' in mici_source
  assert 'ModelManager_UseBuiltinStock' in mici_source


def test_tree_dialog_can_disable_favorites_for_special_model_entries():
  source = _read(TREE_DIALOG)
  assert 'favoriteable = node.data.get("favoriteable", node.ref != "Default")' in source


def test_builtin_stock_param_is_declared_in_params_files():
  params_source = _read(PARAMS_KEYS)
  metadata_source = _read(PARAMS_METADATA)

  assert 'ModelManager_UseBuiltinStock' in params_source
  assert '"ModelManager_UseBuiltinStock"' in metadata_source
