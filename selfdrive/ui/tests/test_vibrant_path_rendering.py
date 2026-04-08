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


def test_renderers_use_single_palette_dynamic_helpers():
  for renderer_path in (TICI_RENDERER, MICI_RENDERER):
    source = _read(renderer_path)
    assert "get_dynamic_path_colors(ui_state.status)" in source
    assert "get_dynamic_edge_color(ui_state.status)" in source
    assert "dynamic_path_color_palette" not in source
    assert "get_dynamic_path_status" not in source


def test_renderers_use_vibrant_custom_edges_without_tinting_markings():
  for renderer_path in (TICI_RENDERER, MICI_RENDERER):
    source = _read(renderer_path)
    assert "CUSTOM_MODEL_PATH_EDGE_COLORS" in source
    assert "DEFAULT_GREEN_PATH_COLORS" in source
    assert "CUSTOM_MODEL_PATH_SOLID_COLORS" not in source
    assert "_custom_marking_color" not in source


def test_renderers_keep_lane_lines_white_and_road_edges_red():
  tici_source = _read(TICI_RENDERER)
  mici_source = _read(MICI_RENDERER)

  assert "rl.Color(255, 255, 255, int(alpha * 255))" in tici_source
  assert "rl.Color(255, 0, 0, int(alpha * 255))" in tici_source
  assert "color = rl.Color(255, 255, 255, int(alpha * 255))" in mici_source
  assert "ROAD_EDGE_COLOR_BP" not in tici_source
  assert "ROAD_EDGE_COLOR_BP" not in mici_source


def test_renderers_blend_default_path_against_default_green_gradient():
  for renderer_path in (TICI_RENDERER, MICI_RENDERER):
    source = _read(renderer_path)
    assert "self._blend_colors(NO_THROTTLE_COLORS, DEFAULT_GREEN_PATH_COLORS, blend_factor)" in source
    assert "\nTHROTTLE_COLORS = [" not in source
