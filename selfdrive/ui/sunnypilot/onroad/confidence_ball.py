import math

import pyray as rl

from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import STOCK_ENGAGED_COLOR, get_dynamic_solid_color
from openpilot.selfdrive.ui.ui_state import ui_state, UIStatus
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.widgets import Widget


def draw_circle_gradient(center_x: float, center_y: float, radius: int,
                         top: rl.Color, bottom: rl.Color) -> None:
  rl.draw_rectangle_gradient_v(int(center_x - radius), int(center_y - radius),
                               radius * 2, radius * 2,
                               top, bottom)

  outer_radius = math.ceil(radius * math.sqrt(2)) + 1
  rl.draw_ring(rl.Vector2(int(center_x), int(center_y)), radius, outer_radius,
               0.0, 360.0, 20, rl.BLACK)


LAT_ONLY_COLOR = rl.Color(0x00, 0xC8, 0xC8, 0xFF)
LONG_ONLY_COLOR = rl.Color(0x96, 0x1C, 0xA8, 0xFF)


class ConfidenceBallBase(Widget):
  def __init__(self, demo: bool = False, radius: float = 24, width: float = 60,
               align_right: bool = True):
    Widget.__init__(self)
    self._demo = demo
    self._align_right = align_right
    self._width = width
    self._status_dot_radius = radius
    self._confidence_filter = FirstOrderFilter(-0.5, 0.5, 1 / gui_app.target_fps)

  @staticmethod
  def get_animate_status_probs():
    if ui_state.status == UIStatus.LAT_ONLY:
      return ui_state.sm['modelV2'].meta.disengagePredictions.steerOverrideProbs
    return ui_state.sm['modelV2'].meta.disengagePredictions.brakeDisengageProbs

  @staticmethod
  def get_lat_long_dot_color():
    return LAT_ONLY_COLOR if ui_state.status == UIStatus.LAT_ONLY else LONG_ONLY_COLOR

  @staticmethod
  def get_beam_color():
    if ui_state.status == UIStatus.LAT_ONLY:
      return LAT_ONLY_COLOR
    if ui_state.status == UIStatus.LONG_ONLY:
      return LONG_ONLY_COLOR
    if ui_state.status == UIStatus.ENGAGED:
      if ui_state.dynamic_path_color:
        return get_dynamic_solid_color(UIStatus.ENGAGED, ui_state.dynamic_path_color_palette)
      return STOCK_ENGAGED_COLOR
    return None

  def update_filter(self, value: float):
    self._confidence_filter.update(value)

  def _update_state(self):
    if self._demo:
      return

    if ui_state.status == UIStatus.DISENGAGED:
      self._confidence_filter.update(-0.5)
    elif ui_state.status in (UIStatus.LAT_ONLY, UIStatus.LONG_ONLY):
      self._confidence_filter.update(1 - max(self.get_animate_status_probs() or [1]))
    else:
      self._confidence_filter.update(
        (1 - max(ui_state.sm['modelV2'].meta.disengagePredictions.brakeDisengageProbs or [1])) *
        (1 - max(ui_state.sm['modelV2'].meta.disengagePredictions.steerOverrideProbs or [1]))
      )

  @staticmethod
  def draw_mads_beam(x: int, y: int, width: int, height: int, color: rl.Color):
    transparent = rl.Color(color.r, color.g, color.b, 0)
    segments = 3
    seg_width = width // segments

    rl.draw_rectangle(x + seg_width, y, seg_width, height, color)
    rl.draw_rectangle_gradient_h(x, y, seg_width, height, transparent, color)
    rl.draw_rectangle_gradient_h(x + seg_width * (segments - 1), y, width - seg_width, height, color, transparent)

  def _draw_circle(self, cx: float, cy: float, radius: float, top: rl.Color, bottom: rl.Color):
    draw_circle_gradient(cx, cy, int(radius), top, bottom)

  def _render(self, _):
    x = self.rect.x if not self._align_right else self.rect.x + self.rect.width - self._width
    content_rect = rl.Rectangle(x, self.rect.y, self._width, self.rect.height)

    bottom_position = content_rect.height
    filter_min = -0.5
    filter_max = 1.0
    normalized = (self._confidence_filter.x - filter_min) / (filter_max - filter_min)
    normalized = max(0.0, min(1.0, normalized))
    dot_height = content_rect.y + bottom_position - (normalized * content_rect.height) + self._status_dot_radius

    if ui_state.status in (UIStatus.LAT_ONLY, UIStatus.LONG_ONLY, UIStatus.ENGAGED) or self._demo:
      if self._confidence_filter.x > 0.5:
        top_dot_color = rl.Color(0, 255, 204, 255)
        bottom_dot_color = rl.Color(0, 255, 38, 255)
      elif self._confidence_filter.x > 0.2:
        top_dot_color = rl.Color(255, 200, 0, 255)
        bottom_dot_color = rl.Color(255, 115, 0, 255)
      else:
        top_dot_color = rl.Color(255, 0, 21, 255)
        bottom_dot_color = rl.Color(255, 0, 89, 255)
    elif ui_state.status == UIStatus.OVERRIDE:
      top_dot_color = rl.Color(255, 255, 255, 255)
      bottom_dot_color = rl.Color(82, 82, 82, 255)
    else:
      top_dot_color = rl.Color(50, 50, 50, 255)
      bottom_dot_color = rl.Color(13, 13, 13, 255)

    if content_rect.width < 2 * self._status_dot_radius:
      ball_center_x = content_rect.x + self._status_dot_radius
    else:
      ball_center_x = content_rect.x + content_rect.width - self._status_dot_radius

    if ui_state.status in (UIStatus.LAT_ONLY, UIStatus.LONG_ONLY, UIStatus.ENGAGED):
      color = self.get_beam_color()
      if color is None:
        return
      color = rl.Color(color.r, color.g, color.b, 150)
      self.draw_mads_beam(int(content_rect.x), int(content_rect.y), int(content_rect.width), int(content_rect.height), color)

    self._draw_circle(ball_center_x, dot_height, self._status_dot_radius, top_dot_color, bottom_dot_color)


class ConfidenceBallMiciSP(ConfidenceBallBase):
  BALL_WIDTH = 60

  def __init__(self, demo: bool = False):
    super().__init__(demo=demo, radius=24, width=self.BALL_WIDTH, align_right=False)


TICI_CONFIDENCE_BALL_R = 50
TICI_CONFIDENCE_BALL_MARGIN = 5
TICI_CONFIDENCE_BALL_W = TICI_CONFIDENCE_BALL_R * 2 + TICI_CONFIDENCE_BALL_MARGIN


class ConfidenceBallTiciSP(ConfidenceBallBase):
  BALL_WIDTH = TICI_CONFIDENCE_BALL_W

  def __init__(self, demo: bool = False):
    super().__init__(demo=demo, radius=TICI_CONFIDENCE_BALL_R, width=self.BALL_WIDTH, align_right=False)
