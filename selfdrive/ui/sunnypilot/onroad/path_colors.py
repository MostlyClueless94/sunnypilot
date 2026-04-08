from __future__ import annotations

import pyray as rl

from openpilot.selfdrive.ui.ui_state import UIStatus

PATH_GRADIENT_STOPS = [0.0, 0.5, 1.0]

CUSTOM_MODEL_PATH_COLOR_LABELS = [
  "Stock",
  "Blue",
  "Green",
  "Purple",
  "Orange",
  "Red",
  "Cyan",
  "Yellow",
]

BLUEPILOT_GRAY_BASE_COLOR = rl.Color(248, 248, 248, 255)
BLUEPILOT_BLUE_BASE_COLOR = rl.Color(0, 153, 255, 255)
BLUEPILOT_GREEN_BASE_COLOR = rl.Color(0, 235, 125, 255)
BLUEPILOT_PURPLE_BASE_COLOR = rl.Color(176, 92, 255, 255)
BLUEPILOT_ORANGE_BASE_COLOR = rl.Color(255, 156, 32, 255)
BLUEPILOT_RED_BASE_COLOR = rl.Color(255, 68, 68, 255)
BLUEPILOT_CYAN_BASE_COLOR = rl.Color(0, 230, 255, 255)
BLUEPILOT_YELLOW_BASE_COLOR = rl.Color(245, 232, 48, 255)

STOCK_DISENGAGED_COLOR = BLUEPILOT_GRAY_BASE_COLOR
STOCK_OVERRIDE_COLOR = BLUEPILOT_GRAY_BASE_COLOR
STOCK_ENGAGED_COLOR = rl.Color(0x16, 0x7F, 0x40, 0xFF)
STOCK_LAT_ONLY_COLOR = rl.Color(0x00, 0xC8, 0xC8, 0xFF)
STOCK_LONG_ONLY_COLOR = rl.Color(0x96, 0x1C, 0xA8, 0xFF)
DEFAULT_GREEN_PATH_COLORS = [
  rl.Color(0, 255, 80, 140),
  rl.Color(0, 255, 100, 110),
  rl.Color(0, 255, 100, 0),
]


def make_path_gradient_colors(base_color: rl.Color) -> list[rl.Color]:
  return [
    rl.Color(base_color.r, base_color.g, base_color.b, 102),
    rl.Color(base_color.r, base_color.g, base_color.b, 89),
    rl.Color(base_color.r, base_color.g, base_color.b, 0),
  ]


def solid_color_from_gradient(colors: list[rl.Color], fallback: rl.Color | None = None) -> rl.Color:
  if colors:
    base_color = colors[0]
    return rl.Color(base_color.r, base_color.g, base_color.b, 255)

  return fallback if fallback is not None else rl.Color(255, 255, 255, 255)


def vibrant_edge_color_from_gradient(colors: list[rl.Color], fallback: rl.Color | None = None) -> rl.Color:
  base_color = solid_color_from_gradient(colors, fallback)

  # Keep the outline aligned to the fill family, but brighten it to match BP's more vivid edging.
  return rl.Color(
    min(base_color.r + 51, 255),
    min(base_color.g + 51, 255),
    min(base_color.b + 51, 255),
    255,
  )


BLUEPILOT_GRAY_PATH_COLORS = make_path_gradient_colors(BLUEPILOT_GRAY_BASE_COLOR)
BLUEPILOT_BLUE_PATH_COLORS = make_path_gradient_colors(BLUEPILOT_BLUE_BASE_COLOR)
BLUEPILOT_GREEN_PATH_COLORS = make_path_gradient_colors(BLUEPILOT_GREEN_BASE_COLOR)
BLUEPILOT_PURPLE_PATH_COLORS = make_path_gradient_colors(BLUEPILOT_PURPLE_BASE_COLOR)
BLUEPILOT_ORANGE_PATH_COLORS = make_path_gradient_colors(BLUEPILOT_ORANGE_BASE_COLOR)
BLUEPILOT_RED_PATH_COLORS = make_path_gradient_colors(BLUEPILOT_RED_BASE_COLOR)
BLUEPILOT_CYAN_PATH_COLORS = make_path_gradient_colors(BLUEPILOT_CYAN_BASE_COLOR)
BLUEPILOT_YELLOW_PATH_COLORS = make_path_gradient_colors(BLUEPILOT_YELLOW_BASE_COLOR)

BLUEPILOT_GRAY_BORDER_COLOR = vibrant_edge_color_from_gradient(BLUEPILOT_GRAY_PATH_COLORS, BLUEPILOT_GRAY_BASE_COLOR)
BLUEPILOT_BLUE_BORDER_COLOR = vibrant_edge_color_from_gradient(BLUEPILOT_BLUE_PATH_COLORS, BLUEPILOT_BLUE_BASE_COLOR)
BLUEPILOT_GREEN_BORDER_COLOR = vibrant_edge_color_from_gradient(BLUEPILOT_GREEN_PATH_COLORS, BLUEPILOT_GREEN_BASE_COLOR)
DEFAULT_GREEN_BORDER_COLOR = vibrant_edge_color_from_gradient(DEFAULT_GREEN_PATH_COLORS)


CUSTOM_MODEL_PATH_COLOR_PRESETS = {
  1: BLUEPILOT_BLUE_PATH_COLORS,
  2: BLUEPILOT_GREEN_PATH_COLORS,
  3: BLUEPILOT_PURPLE_PATH_COLORS,
  4: BLUEPILOT_ORANGE_PATH_COLORS,
  5: BLUEPILOT_RED_PATH_COLORS,
  6: BLUEPILOT_CYAN_PATH_COLORS,
  7: BLUEPILOT_YELLOW_PATH_COLORS,
}

CUSTOM_MODEL_PATH_EDGE_COLORS = {
  key: vibrant_edge_color_from_gradient(colors) for key, colors in CUSTOM_MODEL_PATH_COLOR_PRESETS.items()
}

STOCK_DYNAMIC_BORDER_COLORS = {
  UIStatus.DISENGAGED: STOCK_DISENGAGED_COLOR,
  UIStatus.OVERRIDE: STOCK_OVERRIDE_COLOR,
  UIStatus.LAT_ONLY: STOCK_LAT_ONLY_COLOR,
  UIStatus.LONG_ONLY: solid_color_from_gradient(DEFAULT_GREEN_PATH_COLORS),
  UIStatus.ENGAGED: solid_color_from_gradient(DEFAULT_GREEN_PATH_COLORS),
}

STOCK_DYNAMIC_PATH_COLORS = {
  UIStatus.DISENGAGED: make_path_gradient_colors(STOCK_DYNAMIC_BORDER_COLORS[UIStatus.DISENGAGED]),
  UIStatus.OVERRIDE: make_path_gradient_colors(STOCK_DYNAMIC_BORDER_COLORS[UIStatus.OVERRIDE]),
  UIStatus.LAT_ONLY: make_path_gradient_colors(STOCK_DYNAMIC_BORDER_COLORS[UIStatus.LAT_ONLY]),
  UIStatus.LONG_ONLY: DEFAULT_GREEN_PATH_COLORS,
  UIStatus.ENGAGED: DEFAULT_GREEN_PATH_COLORS,
}

STOCK_DYNAMIC_EDGE_COLORS = {
  UIStatus.DISENGAGED: STOCK_DYNAMIC_BORDER_COLORS[UIStatus.DISENGAGED],
  UIStatus.OVERRIDE: STOCK_DYNAMIC_BORDER_COLORS[UIStatus.OVERRIDE],
  UIStatus.LAT_ONLY: vibrant_edge_color_from_gradient(
    STOCK_DYNAMIC_PATH_COLORS[UIStatus.LAT_ONLY], STOCK_DYNAMIC_BORDER_COLORS[UIStatus.LAT_ONLY],
  ),
  UIStatus.LONG_ONLY: DEFAULT_GREEN_BORDER_COLOR,
  UIStatus.ENGAGED: DEFAULT_GREEN_BORDER_COLOR,
}

DEFAULT_PATH_EDGE_COLORS = {
  UIStatus.DISENGAGED: BLUEPILOT_GRAY_BORDER_COLOR,
  UIStatus.OVERRIDE: BLUEPILOT_GRAY_BORDER_COLOR,
  UIStatus.LAT_ONLY: BLUEPILOT_BLUE_BORDER_COLOR,
  UIStatus.LONG_ONLY: DEFAULT_GREEN_BORDER_COLOR,
  UIStatus.ENGAGED: DEFAULT_GREEN_BORDER_COLOR,
}


def get_dynamic_path_colors(status: UIStatus):
  return STOCK_DYNAMIC_PATH_COLORS.get(status, STOCK_DYNAMIC_PATH_COLORS[UIStatus.DISENGAGED])


def get_dynamic_edge_color(status: UIStatus):
  return STOCK_DYNAMIC_EDGE_COLORS.get(status, STOCK_DYNAMIC_EDGE_COLORS[UIStatus.DISENGAGED])


def get_dynamic_solid_color(status: UIStatus):
  return get_dynamic_edge_color(status)


def get_default_path_edge_color(status: UIStatus):
  return DEFAULT_PATH_EDGE_COLORS.get(status, DEFAULT_PATH_EDGE_COLORS[UIStatus.DISENGAGED])
