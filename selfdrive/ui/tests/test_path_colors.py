from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import (
  CUSTOM_DYNAMIC_BORDER_COLORS,
  CUSTOM_MODEL_PATH_COLOR_PRESETS,
  CUSTOM_MODEL_PATH_EDGE_COLORS,
  DYNAMIC_PATH_COLOR_PALETTE_CUSTOM,
  DYNAMIC_PATH_COLOR_PALETTE_STOCK,
  PATH_GRADIENT_STOPS,
  STOCK_DYNAMIC_BORDER_COLORS,
  get_default_path_edge_color,
  get_dynamic_edge_color,
  vibrant_edge_color_from_gradient,
)
from openpilot.selfdrive.ui.ui_state import UIStatus


def _color_tuple(color):
  return color.r, color.g, color.b, color.a


def test_vibrant_edge_color_from_gradient():
  blue_edge = vibrant_edge_color_from_gradient(CUSTOM_MODEL_PATH_COLOR_PRESETS[1])
  assert _color_tuple(blue_edge) == (51, 153, 255, 255)
  assert _color_tuple(CUSTOM_MODEL_PATH_EDGE_COLORS[1]) == (51, 153, 255, 255)


def test_path_gradient_stops_stay_compatible():
  assert PATH_GRADIENT_STOPS == [0.0, 0.5, 1.0]


def test_dynamic_custom_edge_colors_follow_custom_status_palette():
  color = get_dynamic_edge_color(UIStatus.LAT_ONLY, DYNAMIC_PATH_COLOR_PALETTE_CUSTOM)
  assert _color_tuple(color) == _color_tuple(CUSTOM_DYNAMIC_BORDER_COLORS[UIStatus.LAT_ONLY])


def test_dynamic_stock_edge_colors_follow_stock_status_palette():
  color = get_dynamic_edge_color(UIStatus.ENGAGED, DYNAMIC_PATH_COLOR_PALETTE_STOCK)
  assert _color_tuple(color) == _color_tuple(STOCK_DYNAMIC_BORDER_COLORS[UIStatus.ENGAGED])


def test_default_path_edge_colors_use_bp_status_fallback():
  color = get_default_path_edge_color(UIStatus.OVERRIDE)
  assert _color_tuple(color) == _color_tuple(CUSTOM_DYNAMIC_BORDER_COLORS[UIStatus.OVERRIDE])
