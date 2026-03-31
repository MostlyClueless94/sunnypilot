from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_RENDERER = REPO_ROOT / "selfdrive/ui/onroad/model_renderer.py"
MICI_RENDERER = REPO_ROOT / "selfdrive/ui/mici/onroad/model_renderer.py"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_renderers_draw_path_edges_after_path_fill():
  for renderer_path in (TICI_RENDERER, MICI_RENDERER):
    source = _read(renderer_path)
    gradient_idx = source.index("draw_polygon(self._rect, self._path.projected_points, gradient=self._active_path_gradient)")
    edge_idx = source.index("self._draw_path_edges()")
    assert gradient_idx < edge_idx


def test_renderers_use_custom_and_dynamic_edge_color_sources():
  for renderer_path in (TICI_RENDERER, MICI_RENDERER):
    source = _read(renderer_path)
    assert "CUSTOM_MODEL_PATH_EDGE_COLORS" in source
    assert "get_dynamic_edge_color" in source
    assert "self._active_path_edge_color = CUSTOM_MODEL_PATH_EDGE_COLORS[ui_state.custom_model_path_color]" in source
    assert "self._active_path_edge_color = vibrant_edge_color_from_gradient(" in source
    assert "blended_colors," in source


def test_renderers_keep_lane_and_road_colors_decoupled_from_active_path_fill():
  for renderer_path in (TICI_RENDERER, MICI_RENDERER):
    source = _read(renderer_path)
    assert "ROAD_EDGE_COLOR_BP" in source
    assert "_draw_lane_glow_effects" in source
    assert "_draw_road_edge_glow_effects" in source
    assert "_expand_polygon" in source
    assert "_active_marking_color" not in source


def test_renderers_use_bp_glow_and_outline_widths():
  for renderer_path in (TICI_RENDERER, MICI_RENDERER):
    source = _read(renderer_path)
    assert "glow_widths = [20.0, 12.0, 6.0]" in source
    assert "glow_widths = [28.0, 18.0, 10.0]" in source
    assert "        4.0," in source
