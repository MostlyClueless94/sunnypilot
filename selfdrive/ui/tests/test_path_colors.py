from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import (
  CUSTOM_MODEL_PATH_EDGE_COLORS,
  CUSTOM_MODEL_PATH_COLOR_LABELS,
  CUSTOM_MODEL_PATH_COLOR_PRESETS,
  CUSTOM_MODEL_PATH_SOLID_COLORS,
  PATH_GRADIENT_STOPS,
  solid_color_from_gradient,
  vibrant_edge_color_from_gradient,
)


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
