from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_MODELS = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/models.py"
MICI_MODELS = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/layouts/models.py"
TREE_DIALOG = REPO_ROOT / "system/ui/sunnypilot/widgets/tree_dialog.py"
MODEL_HELPERS = REPO_ROOT / "sunnypilot/models/helpers.py"
MODEL_MANAGER = REPO_ROOT / "sunnypilot/models/manager.py"
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


def test_angle_subaru_nnmv2_policy_wires_into_model_selection_without_ui_changes():
  tici_source = _read(TICI_MODELS)
  mici_source = _read(MICI_MODELS)
  helpers_source = _read(MODEL_HELPERS)
  manager_source = _read(MODEL_MANAGER)

  assert 'update_angle_subaru_nnmv2_selection_policy(ui_state.params, default_selected=True)' in tici_source
  assert 'update_angle_subaru_nnmv2_selection_policy(ui_state.params, selected_bundle=selected_bundle)' in tici_source
  assert 'update_angle_subaru_nnmv2_selection_policy(ui_state.params, default_selected=True)' in mici_source
  assert 'update_angle_subaru_nnmv2_selection_policy(ui_state.params, selected_bundle=bundle)' in mici_source

  assert 'ANGLE_SUBARU_NNMV2_INTERNAL_NAME = "NNMV2"' in helpers_source
  assert 'def select_angle_subaru_auto_default_bundle' in helpers_source
  assert 'def update_angle_subaru_nnmv2_selection_policy' in helpers_source
  assert 'default_selected: bool = False' in helpers_source

  assert 'get_angle_subaru_auto_default_bundle(' in manager_source
  assert 'Auto-queueing {ANGLE_SUBARU_NNMV2_INTERNAL_NAME} for angle Subaru default model' in manager_source
  assert 'self.params.put_bool(ANGLE_SUBARU_NNMV2_AUTOFAILED_PARAM, True)' in manager_source
  assert 'self.params.put_bool(ANGLE_SUBARU_NNMV2_AUTOFAILED_PARAM, False)' in manager_source


def test_builtin_stock_param_is_removed_from_params_files():
  params_source = _read(PARAMS_KEYS)
  metadata_source = _read(PARAMS_METADATA)

  assert 'ModelManager_UseBuiltinStock' not in params_source
  assert '"ModelManager_UseBuiltinStock"' not in metadata_source


def test_angle_subaru_nnmv2_internal_params_are_declared_without_user_facing_metadata():
  params_source = _read(PARAMS_KEYS)
  metadata_source = _read(PARAMS_METADATA)

  assert '"ModelManager_AngleSubaruNNMV2OptOut"' in params_source
  assert '"ModelManager_AngleSubaruNNMV2AutoFailed"' in params_source
  assert '"ModelManager_AngleSubaruNNMV2OptOut"' not in metadata_source
  assert '"ModelManager_AngleSubaruNNMV2AutoFailed"' not in metadata_source
