from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import (
  BLUEPILOT_GRAY_BASE_COLOR,
  BLUEPILOT_GRAY_PATH_COLORS,
  CUSTOM_MODEL_PATH_COLOR_PRESETS,
  CUSTOM_MODEL_PATH_EDGE_COLORS,
  DEFAULT_GREEN_BORDER_COLOR,
  DEFAULT_GREEN_PATH_COLORS,
  PATH_GRADIENT_STOPS,
  STOCK_LAT_ONLY_COLOR,
  STOCK_DYNAMIC_BORDER_COLORS,
  STOCK_DYNAMIC_EDGE_COLORS,
  get_default_path_edge_color,
  get_dynamic_edge_color,
  get_dynamic_path_colors,
  vibrant_edge_color_from_gradient,
)
from openpilot.selfdrive.ui.ui_state import UIStatus
from pathlib import Path


def _color_tuple(color):
  return color.r, color.g, color.b, color.a


REPO_ROOT = Path(__file__).resolve().parents[3]
PATH_COLORS = REPO_ROOT / "selfdrive/ui/sunnypilot/onroad/path_colors.py"
TICI_MODEL_RENDERER = REPO_ROOT / "selfdrive/ui/onroad/model_renderer.py"
MICI_MODEL_RENDERER = REPO_ROOT / "selfdrive/ui/mici/onroad/model_renderer.py"


def test_vibrant_edge_color_from_gradient():
  blue_edge = vibrant_edge_color_from_gradient(CUSTOM_MODEL_PATH_COLOR_PRESETS[1])
  assert _color_tuple(CUSTOM_MODEL_PATH_COLOR_PRESETS[1][0]) == (0, 153, 255, 102)
  assert _color_tuple(blue_edge) == (51, 204, 255, 255)
  assert _color_tuple(CUSTOM_MODEL_PATH_EDGE_COLORS[1]) == (51, 204, 255, 255)


def test_custom_palette_uses_more_vibrant_blue_and_green_bases():
  assert _color_tuple(CUSTOM_MODEL_PATH_COLOR_PRESETS[1][0]) == (0, 153, 255, 102)
  assert _color_tuple(CUSTOM_MODEL_PATH_COLOR_PRESETS[2][0]) == (0, 235, 125, 102)


def test_default_green_path_colors_match_current_default_engaged_gradient():
  assert [_color_tuple(color) for color in DEFAULT_GREEN_PATH_COLORS] == [
    (0, 255, 80, 140),
    (0, 255, 100, 110),
    (0, 255, 100, 0),
  ]


def test_path_gradient_stops_stay_compatible():
  assert PATH_GRADIENT_STOPS == [0.0, 0.5, 1.0]


def test_dynamic_custom_edge_colors_follow_custom_status_palette():
  color = get_dynamic_edge_color(UIStatus.LAT_ONLY)
  assert _color_tuple(color) == _color_tuple(STOCK_DYNAMIC_EDGE_COLORS[UIStatus.LAT_ONLY])
  assert _color_tuple(color) == (51, 251, 251, 255)


def test_dynamic_path_helpers_use_stock_palette_without_palette_argument():
  path_colors_source = PATH_COLORS.read_text(encoding="utf-8")
  assert "def get_dynamic_path_colors(status: UIStatus):" in path_colors_source
  assert "def get_dynamic_edge_color(status: UIStatus):" in path_colors_source
  assert "def get_dynamic_solid_color(status: UIStatus):" in path_colors_source
  assert "DYNAMIC_PATH_COLORS_BY_PALETTE" not in path_colors_source
  assert "DYNAMIC_BORDER_COLORS_BY_PALETTE" not in path_colors_source
  assert "DYNAMIC_PATH_COLOR_PALETTE_CUSTOM" not in path_colors_source
  assert "DYNAMIC_PATH_COLOR_PALETTE_STOCK" not in path_colors_source


def test_dynamic_green_states_match_default_green_exactly():
  for status in (UIStatus.ENGAGED, UIStatus.LONG_ONLY):
    edge_color = get_dynamic_edge_color(status)
    fill_colors = get_dynamic_path_colors(status)
    assert _color_tuple(edge_color) == _color_tuple(DEFAULT_GREEN_BORDER_COLOR)
    assert [_color_tuple(color) for color in fill_colors] == [_color_tuple(color) for color in DEFAULT_GREEN_PATH_COLORS]


def test_default_path_edge_colors_use_bp_status_fallback():
  color = get_default_path_edge_color(UIStatus.OVERRIDE)
  assert _color_tuple(color) == (255, 255, 255, 255)


def test_default_path_green_edge_matches_canonical_green():
  color = get_default_path_edge_color(UIStatus.ENGAGED)
  assert _color_tuple(color) == _color_tuple(DEFAULT_GREEN_BORDER_COLOR)


def test_dynamic_gray_states_are_significantly_lighter():
  for status in (UIStatus.DISENGAGED, UIStatus.OVERRIDE):
    edge_color = get_dynamic_edge_color(status)
    fill_colors = get_dynamic_path_colors(status)
    assert _color_tuple(edge_color) == _color_tuple(BLUEPILOT_GRAY_BASE_COLOR)
    assert [_color_tuple(color) for color in fill_colors] == [_color_tuple(color) for color in BLUEPILOT_GRAY_PATH_COLORS]
    assert _color_tuple(STOCK_DYNAMIC_BORDER_COLORS[status]) == _color_tuple(BLUEPILOT_GRAY_BASE_COLOR)
    assert _color_tuple(STOCK_DYNAMIC_EDGE_COLORS[status]) == _color_tuple(BLUEPILOT_GRAY_BASE_COLOR)


def test_stock_lat_only_color_matches_expected_mads_teal():
  assert _color_tuple(STOCK_LAT_ONLY_COLOR) == (0, 200, 200, 255)


def test_model_renderers_use_stock_mads_teal_for_non_dynamic_lat_only_lane_lines():
  tici_source = TICI_MODEL_RENDERER.read_text(encoding="utf-8")
  mici_source = MICI_MODEL_RENDERER.read_text(encoding="utf-8")

  expected_logic = "base = get_dynamic_edge_color(ui_state.status) if ui_state.dynamic_path_color else STOCK_LAT_ONLY_COLOR"
  assert "STOCK_LAT_ONLY_COLOR" in tici_source
  assert expected_logic in tici_source
  assert "STOCK_LAT_ONLY_COLOR" in mici_source
  assert expected_logic in mici_source


def test_custom_model_green_preset_remains_separate_from_default_green_path():
  assert _color_tuple(CUSTOM_MODEL_PATH_COLOR_PRESETS[2][0]) == (0, 235, 125, 102)
  assert _color_tuple(DEFAULT_GREEN_PATH_COLORS[0]) == (0, 255, 80, 140)
