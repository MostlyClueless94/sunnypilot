from typing import Optional
import pyray as rl
from cereal import log

from openpilot.selfdrive.ui.onroad.alert_renderer import AlertRenderer
from openpilot.selfdrive.ui.onroad.hud_renderer import UI_CONFIG
from openpilot.system.ui.lib.text_measure import measure_text_cached

AlertSize = log.SelfdriveState.AlertSize
AlertStatus = log.SelfdriveState.AlertStatus

# BluePilot: Y center for pill positioning (matching upstream speed display position)
SPEED_CENTER_Y = 180

# Pill notification constants (for informational notifications)
PILL_HEIGHT_SINGLE = 110
PILL_HEIGHT_DOUBLE = 164
PILL_PADDING_H = 30
PILL_PADDING_V = 15
PILL_FONT_SIZE = 48
PILL_LINE_SPACING = 8
PILL_MAX_CHARS_PER_LINE = 28

# Alert pill constants (3x larger than informational pills)
ALERT_PILL_HEIGHT_SINGLE = 210
ALERT_PILL_HEIGHT_DOUBLE = 348
ALERT_PILL_PADDING_H = 90
ALERT_PILL_PADDING_V = 45
ALERT_PILL_FONT_SIZE = 144
ALERT_PILL_LINE_SPACING = 24
ALERT_PILL_MAX_CHARS_PER_LINE = 28

# Pill notification colors
PILL_BACKGROUND_COLOR = rl.Color(45, 45, 45, 255)
PILL_ALERT_COLOR = rl.Color(0xDA, 0x6F, 0x25, 0xFF)


def _wrap_text(text: str, max_chars: int):
  """Split text into two lines at word boundary."""
  words = text.split()
  line1_words = []
  line2_words = []
  for word in words:
    test_line = ' '.join(line1_words + [word])
    if len(test_line) <= max_chars:
      line1_words.append(word)
    else:
      line2_words.append(word)
  line1 = ' '.join(line1_words) if line1_words else text[:max_chars]
  line2 = ' '.join(line2_words) if line2_words else text[max_chars:]
  return line1, line2


class AlertRendererBP(AlertRenderer):
  """BluePilot AlertRenderer with pill-shaped notifications."""

  def __init__(self):
    super().__init__()
    self.speed_right = 0

  def set_speed_right(self, speed_right: int):
    self.speed_right = speed_right

  def _render(self, rect: rl.Rectangle):
    from openpilot.selfdrive.ui.ui_state import ui_state
    alert = self.get_alert(ui_state.sm)
    if not alert:
      return

    is_informational = (alert.status == AlertStatus.normal and alert.size != AlertSize.full)
    is_alert_pill = (alert.status == AlertStatus.userPrompt and alert.size != AlertSize.full)

    if is_informational:
      alert_rect = self._get_pill_rect(rect, alert)
      if alert_rect:
        self._draw_pill_background(alert_rect)
        text_rect = rl.Rectangle(
          alert_rect.x + PILL_PADDING_H, alert_rect.y + PILL_PADDING_V,
          alert_rect.width - 2 * PILL_PADDING_H, alert_rect.height - 2 * PILL_PADDING_V
        )
        self._draw_pill_text(text_rect, alert)
    elif is_alert_pill:
      alert_rect = self._get_alert_pill_rect(rect, alert)
      if alert_rect:
        self._draw_alert_pill_background(alert_rect)
        text_rect = rl.Rectangle(
          alert_rect.x + ALERT_PILL_PADDING_H, alert_rect.y + ALERT_PILL_PADDING_V,
          alert_rect.width - 2 * ALERT_PILL_PADDING_H, alert_rect.height - 2 * ALERT_PILL_PADDING_V
        )
        self._draw_alert_pill_text(text_rect, alert)
    else:
      # Delegate to stock AlertRenderer for full-screen/critical alerts
      super()._render(rect)

  def _get_pill_rect(self, rect: rl.Rectangle, alert) -> Optional[rl.Rectangle]:
    """Calculate pill-shaped notification rectangle between speed and steering wheel."""
    wheel_x = rect.x + rect.width - UI_CONFIG.border_size - UI_CONFIG.button_size
    # Guard against speed_right not yet set (0) - use center of rect as fallback
    center_x = self.speed_right if self.speed_right > rect.x else rect.x + rect.width * 0.55
    available_width = wheel_x - center_x
    if available_width < 100:
      return None

    text = alert.text1 if alert.text1 else alert.text2
    if not text:
      return None

    needs_wrapping = len(text) > PILL_MAX_CHARS_PER_LINE
    if needs_wrapping:
      line1, line2 = _wrap_text(text, PILL_MAX_CHARS_PER_LINE)
      line1_size = measure_text_cached(self.font_bold, line1, PILL_FONT_SIZE)
      line2_size = measure_text_cached(self.font_bold, line2, PILL_FONT_SIZE)
      text_width = max(line1_size.x, line2_size.x)
      pill_height = PILL_HEIGHT_DOUBLE
    else:
      text_size = measure_text_cached(self.font_bold, text, PILL_FONT_SIZE)
      text_width = text_size.x
      pill_height = PILL_HEIGHT_SINGLE

    pill_width = min(text_width + 2 * PILL_PADDING_H, available_width)
    pill_x = center_x + (wheel_x - center_x) / 2 - pill_width / 2 + 10
    pill_y = SPEED_CENTER_Y - pill_height / 2

    return rl.Rectangle(pill_x, pill_y, pill_width, pill_height)

  def _draw_pill_background(self, rect: rl.Rectangle) -> None:
    rl.draw_rectangle_rounded(rect, 0.75, 10, PILL_BACKGROUND_COLOR)

  def _draw_pill_text(self, rect: rl.Rectangle, alert) -> None:
    """Draw text in pill-shaped notification (centered, single or two lines)."""
    text = alert.text1 if alert.text1 else alert.text2
    if not text:
      return

    needs_wrapping = len(text) > PILL_MAX_CHARS_PER_LINE
    if needs_wrapping:
      line1, line2 = _wrap_text(text, PILL_MAX_CHARS_PER_LINE)
      line1_size = measure_text_cached(self.font_bold, line1, PILL_FONT_SIZE)
      line2_size = measure_text_cached(self.font_bold, line2, PILL_FONT_SIZE)
      total_text_height = line1_size.y + PILL_LINE_SPACING + line2_size.y
      extra_top_padding = rect.height * 0.25
      extra_bottom_padding = rect.height * 0.22
      available_height = rect.height - extra_top_padding - extra_bottom_padding
      start_y = rect.y + extra_top_padding + (available_height - total_text_height) / 2

      line1_x = rect.x + (rect.width - line1_size.x) / 2
      rl.draw_text_ex(self.font_bold, line1, rl.Vector2(line1_x, start_y), PILL_FONT_SIZE, 0, rl.WHITE)
      line2_x = rect.x + (rect.width - line2_size.x) / 2
      line2_y = start_y + line1_size.y + PILL_LINE_SPACING
      rl.draw_text_ex(self.font_bold, line2, rl.Vector2(line2_x, line2_y), PILL_FONT_SIZE, 0, rl.WHITE)
    else:
      text_size = measure_text_cached(self.font_bold, text, PILL_FONT_SIZE)
      extra_padding = rect.height * 0.25
      available_height = rect.height - (extra_padding * 2)
      x = rect.x + (rect.width - text_size.x) / 2
      y = rect.y + extra_padding + (available_height - text_size.y) / 2
      rl.draw_text_ex(self.font_bold, text, rl.Vector2(x, y), PILL_FONT_SIZE, 0, rl.WHITE)

  def _get_alert_pill_rect(self, rect: rl.Rectangle, alert) -> Optional[rl.Rectangle]:
    """Calculate orange pill alert rectangle in middle of screen, 1/3 up from bottom."""
    text = alert.text1 if alert.text1 else alert.text2
    if not text:
      return None

    needs_wrapping = len(text) > ALERT_PILL_MAX_CHARS_PER_LINE
    if needs_wrapping:
      line1, line2 = _wrap_text(text, ALERT_PILL_MAX_CHARS_PER_LINE)
      line1_size = measure_text_cached(self.font_bold, line1, ALERT_PILL_FONT_SIZE)
      line2_size = measure_text_cached(self.font_bold, line2, ALERT_PILL_FONT_SIZE)
      text_width = max(line1_size.x, line2_size.x)
      pill_height = ALERT_PILL_HEIGHT_DOUBLE
    else:
      text_size = measure_text_cached(self.font_bold, text, ALERT_PILL_FONT_SIZE)
      text_width = text_size.x
      pill_height = ALERT_PILL_HEIGHT_SINGLE

    pill_width = text_width + 2 * ALERT_PILL_PADDING_H
    pill_x = rect.x + (rect.width - pill_width) / 2
    pill_y = rect.y + (rect.height * 2 / 3) - (pill_height / 2)
    return rl.Rectangle(pill_x, pill_y, pill_width, pill_height)

  def _draw_alert_pill_background(self, rect: rl.Rectangle) -> None:
    rl.draw_rectangle_rounded(rect, 0.75, 10, PILL_ALERT_COLOR)

  def _draw_alert_pill_text(self, rect: rl.Rectangle, alert) -> None:
    """Draw text in alert pill (centered, single or two lines, 3x larger)."""
    text = alert.text1 if alert.text1 else alert.text2
    if not text:
      return

    needs_wrapping = len(text) > ALERT_PILL_MAX_CHARS_PER_LINE
    if needs_wrapping:
      line1, line2 = _wrap_text(text, ALERT_PILL_MAX_CHARS_PER_LINE)
      line1_size = measure_text_cached(self.font_bold, line1, ALERT_PILL_FONT_SIZE)
      line2_size = measure_text_cached(self.font_bold, line2, ALERT_PILL_FONT_SIZE)
      total_text_height = line1_size.y + ALERT_PILL_LINE_SPACING + line2_size.y
      extra_top_padding = rect.height * 0.05
      extra_bottom_padding = rect.height * 0.08
      available_height = rect.height - extra_top_padding - extra_bottom_padding
      start_y = rect.y + extra_top_padding + (available_height - total_text_height) / 2

      line1_x = rect.x + (rect.width - line1_size.x) / 2
      rl.draw_text_ex(self.font_bold, line1, rl.Vector2(line1_x, start_y), ALERT_PILL_FONT_SIZE, 0, rl.WHITE)
      line2_x = rect.x + (rect.width - line2_size.x) / 2
      line2_y = start_y + line1_size.y + ALERT_PILL_LINE_SPACING
      rl.draw_text_ex(self.font_bold, line2, rl.Vector2(line2_x, line2_y), ALERT_PILL_FONT_SIZE, 0, rl.WHITE)
    else:
      text_size = measure_text_cached(self.font_bold, text, ALERT_PILL_FONT_SIZE)
      x = rect.x + (rect.width - text_size.x) / 2
      y = rect.y + (rect.height - text_size.y) / 2
      rl.draw_text_ex(self.font_bold, text, rl.Vector2(x, y), ALERT_PILL_FONT_SIZE, 0, rl.WHITE)
