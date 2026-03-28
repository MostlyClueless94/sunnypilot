from __future__ import annotations

import pyray as rl

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


def vibrant_edge_color_from_gradient(colors: list[rl.Color], fallback: rl.Color | None = None) -> rl.Color:
  base_color = solid_color_from_gradient(colors, fallback)

  # Keep the outline visually related to the selected fill color, but brighter like stock green path edging.
  return rl.Color(
    min(base_color.r + 51, 255),
    min(base_color.g + 51, 255),
    min(base_color.b + 51, 255),
    255,
  )


CUSTOM_MODEL_PATH_EDGE_COLORS = {
  key: vibrant_edge_color_from_gradient(colors) for key, colors in CUSTOM_MODEL_PATH_COLOR_PRESETS.items()
}
