from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import (
  CUSTOM_DYNAMIC_BORDER_COLORS,
  CUSTOM_MODEL_PATH_EDGE_COLORS,
  CUSTOM_MODEL_PATH_COLOR_LABELS,
  CUSTOM_MODEL_PATH_COLOR_PRESETS,
  CUSTOM_MODEL_PATH_SOLID_COLORS,
  DYNAMIC_PATH_COLOR_PALETTE_CUSTOM,
  DYNAMIC_PATH_COLOR_PALETTE_LABELS,
  DYNAMIC_PATH_COLOR_PALETTE_STOCK,
  PATH_GRADIENT_STOPS,
  STOCK_DYNAMIC_BORDER_COLORS,
  STOCK_DYNAMIC_EDGE_COLORS,
  get_default_path_edge_color,
  get_dynamic_edge_color,
  solid_color_from_gradient,
  vibrant_edge_color_from_gradient,
)
from openpilot.selfdrive.ui.ui_state import UIStatus


def _color_tuple(color):
  return color.r, color.g, color.b, color.a


def test_custom_model_path_color_labels():
  assert CUSTOM_MODEL_PATH_COLOR_LABELS == [
    "Stock",
    "Blue",
    "Green",
    "Purple",
    "Orange",
    "Red",
    "Cyan",
    "Yellow",
  ]
  assert DYNAMIC_PATH_COLOR_PALETTE_LABELS == ["Custom", "Stock"]
  assert PATH_GRADIENT_STOPS == [0.0, 0.5, 1.0]


def test_custom_model_path_color_preset_lookup():
  blue_gradient = CUSTOM_MODEL_PATH_COLOR_PRESETS[1]
  assert [_color_tuple(color) for color in blue_gradient] == [
    (0, 102, 204, 102),
    (51, 153, 255, 89),
    (51, 153, 255, 0),
  ]


def test_solid_color_from_gradient():
  green_solid = solid_color_from_gradient(CUSTOM_MODEL_PATH_COLOR_PRESETS[2])
  assert _color_tuple(green_solid) == (0, 204, 102, 255)
  assert _color_tuple(CUSTOM_MODEL_PATH_SOLID_COLORS[2]) == (0, 204, 102, 255)


def test_vibrant_edge_color_from_gradient():
  blue_edge = vibrant_edge_color_from_gradient(CUSTOM_MODEL_PATH_COLOR_PRESETS[1])
  assert _color_tuple(blue_edge) == (51, 153, 255, 255)
  assert _color_tuple(CUSTOM_MODEL_PATH_EDGE_COLORS[1]) == (51, 153, 255, 255)
  assert _color_tuple(CUSTOM_MODEL_PATH_EDGE_COLORS[1]) != _color_tuple(CUSTOM_MODEL_PATH_SOLID_COLORS[1])


def test_dynamic_custom_edge_colors_follow_custom_status_palette():
  color = get_dynamic_edge_color(UIStatus.LAT_ONLY, DYNAMIC_PATH_COLOR_PALETTE_CUSTOM)
  assert _color_tuple(color) == _color_tuple(CUSTOM_DYNAMIC_BORDER_COLORS[UIStatus.LAT_ONLY])


def test_dynamic_stock_edge_colors_use_brightened_stock_outline():
  color = get_dynamic_edge_color(UIStatus.ENGAGED, DYNAMIC_PATH_COLOR_PALETTE_STOCK)
  expected = STOCK_DYNAMIC_EDGE_COLORS[UIStatus.ENGAGED]
  base = STOCK_DYNAMIC_BORDER_COLORS[UIStatus.ENGAGED]

  assert _color_tuple(color) == _color_tuple(expected)
  assert color.r >= base.r
  assert color.g >= base.g
  assert color.b >= base.b
  assert _color_tuple(color) != _color_tuple(base)


def test_default_path_edge_colors_use_bp_status_fallback():
  color = get_default_path_edge_color(UIStatus.OVERRIDE)
  assert _color_tuple(color) == _color_tuple(CUSTOM_DYNAMIC_BORDER_COLORS[UIStatus.OVERRIDE])
