import math
import pyray as rl
from openpilot.selfdrive.ui.mici.onroad import SIDE_PANEL_WIDTH
from openpilot.selfdrive.ui.ui_state import ui_state, UIStatus
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.lib.application import gui_app
from openpilot.common.filter_simple import FirstOrderFilter

from openpilot.selfdrive.ui.sunnypilot.mici.onroad.confidence_ball import ConfidenceBallSP


def draw_circle_gradient(center_x: float, center_y: float, radius: int,
                         top: rl.Color, bottom: rl.Color, ring: rl.Color) -> None:
  # Draw a square with vertical gradient (top to bottom)
  rl.draw_rectangle_gradient_v(int(center_x - radius), int(center_y - radius),
                               radius * 2, radius * 2,
                               top, bottom)

  # Paint over square with a ring (border thickness is 1/4 of original visible thickness)
  # Original: outer_radius = math.ceil(radius * math.sqrt(2)) + 1, thickness ≈ radius * (sqrt(2) - 1) + 1
  # For radius=50: outer_radius ≈ 71, thickness ≈ 21
  # Square diagonal extends to radius * sqrt(2), so outer_radius must be at least that to cover square corners
  # Then add 1/4 of the original visible border thickness for the actual border
  square_diagonal_radius = radius * math.sqrt(2)
  original_outer_radius = math.ceil(radius * math.sqrt(2)) + 1
  original_visible_thickness = original_outer_radius - radius
  new_visible_thickness = max(1.0, original_visible_thickness / 4.0)  # 1/4 of original visible thickness, min 1px
  # Ensure ring covers square corners, then add thin border
  outer_radius = max(square_diagonal_radius, radius + new_visible_thickness)
  rl.draw_ring(rl.Vector2(int(center_x), int(center_y)), radius, outer_radius,
               0.0, 360.0,
               20, ring)


class ConfidenceBall(Widget, ConfidenceBallSP):
  def __init__(self, demo: bool = False, radius: float=24):
    Widget.__init__(self)
    ConfidenceBallSP.__init__(self)
    self._demo = demo
    self._confidence_filter = FirstOrderFilter(-0.5, 0.5, 1 / gui_app.target_fps)
    self._status_dot_radius = radius

  def update_filter(self, value: float):
    self._confidence_filter.update(value)

  def _update_state(self):
    if self._demo:
      return

    # animate status dot in from bottom
    if ui_state.status == UIStatus.DISENGAGED:
      self._confidence_filter.update(-0.5)
    elif ui_state.status in (UIStatus.LAT_ONLY, UIStatus.LONG_ONLY):
      self._confidence_filter.update(1 - max(self.get_animate_status_probs() or [1]))
    else:
      self._confidence_filter.update((1 - max(ui_state.sm['modelV2'].meta.disengagePredictions.brakeDisengageProbs or [1])) *
                                                        (1 - max(ui_state.sm['modelV2'].meta.disengagePredictions.steerOverrideProbs or [1])))

  def _render(self, _):
    # Use rect width directly (works for both MICI and TICI)
    # For MICI: rect.width matches SIDE_PANEL_WIDTH
    # For TICI: rect.width is CONFIDENCE_BALL_R (thinner bar)
    bar_width = self.rect.width
    content_rect = rl.Rectangle(
      self.rect.x,
      self.rect.y,
      bar_width,
      self.rect.height,
    )

    dot_height = (1 - self._confidence_filter.x) * (content_rect.height - 2 * self._status_dot_radius) + self._status_dot_radius
    dot_height = content_rect.y + dot_height  # Use content_rect.y, not self._rect.y

    # confidence zones
    if ui_state.status == UIStatus.ENGAGED or self._demo:
      if self._confidence_filter.x > 0.5:
        top_dot_color = rl.Color(0, 255, 204, 255)
        bottom_dot_color = rl.Color(0, 255, 38, 255)
      elif self._confidence_filter.x > 0.2:
        top_dot_color = rl.Color(255, 200, 0, 255)
        bottom_dot_color = rl.Color(255, 115, 0, 255)
      else:
        top_dot_color = rl.Color(255, 0, 21, 255)
        bottom_dot_color = rl.Color(255, 0, 89, 255)

    elif ui_state.status in (UIStatus.LAT_ONLY, UIStatus.LONG_ONLY):
      top_dot_color = bottom_dot_color = self.get_lat_long_dot_color()

    elif ui_state.status == UIStatus.OVERRIDE:
      top_dot_color = rl.Color(255, 255, 255, 255)
      bottom_dot_color = rl.Color(82, 82, 82, 255)

    else:
      top_dot_color = rl.Color(50, 50, 50, 255)
      bottom_dot_color = rl.Color(13, 13, 13, 255)

    ring_color = rl.BLACK
    # Position ball so it fits within the bar without going off the left edge
    # If bar is narrower than 2*radius, position ball so left edge aligns with bar left edge
    # Otherwise, position ball centered or aligned to right edge
    if content_rect.width < 2 * self._status_dot_radius:
      # Bar is narrower than ball diameter - position so left edge of ball is at bar left edge
      ball_center_x = content_rect.x + self._status_dot_radius
    else:
      # Bar is wide enough - position ball aligned to right edge of bar (original behavior)
      ball_center_x = content_rect.x + content_rect.width - self._status_dot_radius
    draw_circle_gradient(ball_center_x,
                         dot_height, self._status_dot_radius,
                         top_dot_color, bottom_dot_color, ring_color)
