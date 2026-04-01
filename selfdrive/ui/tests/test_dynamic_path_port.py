from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_RENDERER = REPO_ROOT / "selfdrive/ui/onroad/model_renderer.py"
MICI_RENDERER = REPO_ROOT / "selfdrive/ui/mici/onroad/model_renderer.py"
MC_CUSTOM = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/mc_custom.py"
UI_STATE = REPO_ROOT / "selfdrive/ui/sunnypilot/ui_state.py"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_ui_state_reads_dynamic_path_params():
  source = _read(UI_STATE)
  assert 'self.dynamic_path_color = self.params.get_bool("DynamicPathColor")' in source
  assert 'self.dynamic_path_color_palette = self._get_int_param("DynamicPathColorPalette")' in source


def test_ui_state_has_dynamic_path_status_helper_for_mads_preenabled():
  source = _read(UI_STATE)
  assert "def get_dynamic_path_status(ss, ss_sp, onroad_evt) -> str:" in source
  assert "state == OpenpilotState.preEnabled" in source
  assert 'return "lat_only"' in source
  assert "not any(e.overrideLongitudinal for e in onroad_evt)" in source


def test_base_renderers_reference_dynamic_path_helpers():
  for renderer_path in (TICI_RENDERER, MICI_RENDERER):
    source = _read(renderer_path)
    assert "get_dynamic_path_colors" in source
    assert "get_dynamic_edge_color" in source
    assert "ui_state.get_dynamic_path_status(" in source
    assert "dynamic_colors = get_dynamic_path_colors(dynamic_status, ui_state.dynamic_path_color_palette)" in source
    assert "self._active_path_edge_color = get_dynamic_edge_color(dynamic_status, ui_state.dynamic_path_color_palette)" in source


def test_mici_renderer_draws_dynamic_path_edges_only_when_enabled():
  source = _read(MICI_RENDERER)
  assert "if ui_state.dynamic_path_color:" in source
  assert "self._draw_path_edges()" in source


def test_mc_custom_contains_dynamic_path_controls():
  source = _read(MC_CUSTOM)
  assert 'param="DynamicPathColor"' in source
  assert 'param="DynamicPathColorPalette"' in source
  assert 'self._dynamic_path_color_palette.action_item.set_enabled(self._params.get_bool("DynamicPathColor"))' in source
