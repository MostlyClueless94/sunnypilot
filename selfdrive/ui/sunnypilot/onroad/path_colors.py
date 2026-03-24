import pyray as rl

from openpilot.selfdrive.ui.ui_state import UIStatus

PATH_GRADIENT_STOPS = [0.0, 0.5, 1.0]

DYNAMIC_PATH_COLOR_PALETTE_CUSTOM = 0
DYNAMIC_PATH_COLOR_PALETTE_STOCK = 1

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

DYNAMIC_PATH_COLOR_PALETTE_LABELS = [
  "Custom",
  "Stock",
]

BLUEPILOT_GRAY_PATH_COLORS = [
  rl.Color(242, 242, 242, 102),
  rl.Color(242, 242, 242, 89),
  rl.Color(242, 242, 242, 0),
]

BLUEPILOT_BLUE_PATH_COLORS = [
  rl.Color(0, 102, 204, 102),
  rl.Color(51, 153, 255, 89),
  rl.Color(51, 153, 255, 0),
]

BLUEPILOT_GREEN_PATH_COLORS = [
  rl.Color(0, 204, 102, 102),
  rl.Color(51, 255, 153, 89),
  rl.Color(51, 255, 153, 0),
]

BLUEPILOT_PURPLE_PATH_COLORS = [
  rl.Color(153, 51, 204, 102),
  rl.Color(178, 102, 255, 89),
  rl.Color(178, 102, 255, 0),
]

BLUEPILOT_ORANGE_PATH_COLORS = [
  rl.Color(255, 128, 0, 102),
  rl.Color(255, 153, 51, 89),
  rl.Color(255, 153, 51, 0),
]

BLUEPILOT_RED_PATH_COLORS = [
  rl.Color(204, 0, 0, 102),
  rl.Color(255, 51, 51, 89),
  rl.Color(255, 51, 51, 0),
]

BLUEPILOT_CYAN_PATH_COLORS = [
  rl.Color(0, 204, 204, 102),
  rl.Color(51, 255, 255, 89),
  rl.Color(51, 255, 255, 0),
]

BLUEPILOT_YELLOW_PATH_COLORS = [
  rl.Color(204, 204, 0, 102),
  rl.Color(255, 255, 51, 89),
  rl.Color(255, 255, 51, 0),
]

BLUEPILOT_GRAY_BORDER_COLOR = rl.Color(242, 242, 242, 255)
BLUEPILOT_BLUE_BORDER_COLOR = rl.Color(0, 102, 204, 255)
BLUEPILOT_GREEN_BORDER_COLOR = rl.Color(0, 204, 102, 255)

STOCK_DISENGAGED_COLOR = rl.Color(0x12, 0x28, 0x39, 0xFF)
STOCK_OVERRIDE_COLOR = rl.Color(0x89, 0x92, 0x8D, 0xFF)
STOCK_ENGAGED_COLOR = rl.Color(0x16, 0x7F, 0x40, 0xFF)
STOCK_LAT_ONLY_COLOR = rl.Color(0x00, 0xC8, 0xC8, 0xFF)
STOCK_LONG_ONLY_COLOR = rl.Color(0x96, 0x1C, 0xA8, 0xFF)


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


CUSTOM_MODEL_PATH_COLOR_PRESETS = {
  1: BLUEPILOT_BLUE_PATH_COLORS,
  2: BLUEPILOT_GREEN_PATH_COLORS,
  3: BLUEPILOT_PURPLE_PATH_COLORS,
  4: BLUEPILOT_ORANGE_PATH_COLORS,
  5: BLUEPILOT_RED_PATH_COLORS,
  6: BLUEPILOT_CYAN_PATH_COLORS,
  7: BLUEPILOT_YELLOW_PATH_COLORS,
}

CUSTOM_MODEL_PATH_SOLID_COLORS = {
  key: solid_color_from_gradient(colors) for key, colors in CUSTOM_MODEL_PATH_COLOR_PRESETS.items()
}

CUSTOM_DYNAMIC_PATH_COLORS = {
  UIStatus.DISENGAGED: BLUEPILOT_GRAY_PATH_COLORS,
  UIStatus.OVERRIDE: BLUEPILOT_GRAY_PATH_COLORS,
  UIStatus.LAT_ONLY: BLUEPILOT_BLUE_PATH_COLORS,
  UIStatus.LONG_ONLY: BLUEPILOT_GREEN_PATH_COLORS,
  UIStatus.ENGAGED: BLUEPILOT_GREEN_PATH_COLORS,
}

CUSTOM_DYNAMIC_BORDER_COLORS = {
  UIStatus.DISENGAGED: BLUEPILOT_GRAY_BORDER_COLOR,
  UIStatus.OVERRIDE: BLUEPILOT_GRAY_BORDER_COLOR,
  UIStatus.LAT_ONLY: BLUEPILOT_BLUE_BORDER_COLOR,
  UIStatus.LONG_ONLY: BLUEPILOT_GREEN_BORDER_COLOR,
  UIStatus.ENGAGED: BLUEPILOT_GREEN_BORDER_COLOR,
}

STOCK_DYNAMIC_BORDER_COLORS = {
  UIStatus.DISENGAGED: STOCK_DISENGAGED_COLOR,
  UIStatus.OVERRIDE: STOCK_OVERRIDE_COLOR,
  UIStatus.LAT_ONLY: STOCK_LAT_ONLY_COLOR,
  UIStatus.LONG_ONLY: STOCK_LONG_ONLY_COLOR,
  UIStatus.ENGAGED: STOCK_ENGAGED_COLOR,
}

STOCK_DYNAMIC_PATH_COLORS = {
  key: make_path_gradient_colors(color) for key, color in STOCK_DYNAMIC_BORDER_COLORS.items()
}

DYNAMIC_PATH_COLORS_BY_PALETTE = {
  DYNAMIC_PATH_COLOR_PALETTE_CUSTOM: CUSTOM_DYNAMIC_PATH_COLORS,
  DYNAMIC_PATH_COLOR_PALETTE_STOCK: STOCK_DYNAMIC_PATH_COLORS,
}

DYNAMIC_BORDER_COLORS_BY_PALETTE = {
  DYNAMIC_PATH_COLOR_PALETTE_CUSTOM: CUSTOM_DYNAMIC_BORDER_COLORS,
  DYNAMIC_PATH_COLOR_PALETTE_STOCK: STOCK_DYNAMIC_BORDER_COLORS,
}

# Backward-compatible aliases for the original custom dynamic palette.
DYNAMIC_PATH_COLORS = CUSTOM_DYNAMIC_PATH_COLORS
DYNAMIC_BORDER_COLORS = CUSTOM_DYNAMIC_BORDER_COLORS


def get_dynamic_path_colors(status: UIStatus, palette: int):
  colors_by_status = DYNAMIC_PATH_COLORS_BY_PALETTE.get(palette, CUSTOM_DYNAMIC_PATH_COLORS)
  return colors_by_status.get(status, CUSTOM_DYNAMIC_PATH_COLORS[UIStatus.DISENGAGED])


def get_dynamic_solid_color(status: UIStatus, palette: int):
  colors_by_status = DYNAMIC_BORDER_COLORS_BY_PALETTE.get(palette, CUSTOM_DYNAMIC_BORDER_COLORS)
  return colors_by_status.get(status, CUSTOM_DYNAMIC_BORDER_COLORS[UIStatus.DISENGAGED])
