"""
Shared offroad model info widget for sunnypilot home screens.
"""
import re

import pyray as rl

from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget

CARD_BG = rl.Color(38, 38, 38, 255)
CARD_BORDER = rl.Color(255, 255, 255, 26)
NAME_CONTAINER_BG = rl.Color(255, 255, 255, 13)
NAME_CONTAINER_BORDER = rl.Color(255, 255, 255, 26)
MODEL_NAME_COLOR = rl.Color(24, 180, 255, 255)

DATE_PATTERN = re.compile(r"\s+(\([A-Za-z]+\s+\d{1,2},\s+\d{4}\))")
DEFAULT_MODEL_NAME = "Default Model"


class ModelInfoWidget(Widget):
  def __init__(self):
    super().__init__()
    self._model_name = DEFAULT_MODEL_NAME

  def _update_state(self):
    self._model_name = self._get_active_model_name()

  def _get_active_model_name(self) -> str:
    try:
      model_manager = ui_state.sm["modelManagerSP"]
      if model_manager.activeBundle.ref:
        return model_manager.activeBundle.displayName
    except Exception:
      pass
    return DEFAULT_MODEL_NAME

  def _render(self, rect: rl.Rectangle):
    padding_x = max(18, int(rect.width * 0.03))
    padding_top = max(16, int(rect.height * 0.07))

    rl.draw_rectangle_rounded(rect, 0.05, 10, CARD_BG)
    rl.draw_rectangle_rounded_lines(rect, 0.05, 10, CARD_BORDER)

    title_font = gui_app.font(FontWeight.BOLD)
    title_size = max(28, min(36, int(rect.height * 0.18)))
    title_pos = rl.Vector2(rect.x + padding_x, rect.y + padding_top)
    rl.draw_text_ex(title_font, "Driving Model", title_pos, title_size, 0, rl.WHITE)

    container_top = rect.y + padding_top + title_size + 10
    container_margin = 10
    container_height = rect.y + rect.height - container_top - container_margin
    container_rect = rl.Rectangle(
      rect.x + container_margin,
      container_top,
      rect.width - 2 * container_margin,
      container_height,
    )
    rl.draw_rectangle_rounded(container_rect, 0.08, 10, NAME_CONTAINER_BG)
    rl.draw_rectangle_rounded_lines(container_rect, 0.08, 10, NAME_CONTAINER_BORDER)

    display_name = DATE_PATTERN.sub(r"\n\1", self._model_name)
    name_font = gui_app.font(FontWeight.SEMI_BOLD)
    font_size = max(24, min(40, int(container_rect.height * 0.23)))
    available_width = container_rect.width - 40

    text_size = measure_text_cached(name_font, display_name, font_size)
    while text_size.x > available_width and font_size > 24:
      font_size -= 2
      text_size = measure_text_cached(name_font, display_name, font_size)

    text_x = container_rect.x + (container_rect.width - text_size.x) / 2
    text_y = container_rect.y + (container_rect.height - text_size.y) / 2
    rl.draw_text_ex(name_font, display_name, rl.Vector2(text_x, text_y), font_size, 0, MODEL_NAME_COLOR)
