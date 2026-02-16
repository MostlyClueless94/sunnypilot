import time
import pyray as rl
from cereal import messaging
from openpilot.selfdrive.ui import UI_BORDER_SIZE
from openpilot.selfdrive.ui.onroad.augmented_road_view import AugmentedRoadView, CONFIDENCE_BALL_W, CONFIDENCE_BALL_R, CONFIDENCE_BALL_MARGIN
from openpilot.selfdrive.ui.bp.onroad.blindspot_renderer import BlindspotRendererMixin
from openpilot.selfdrive.ui.bp.onroad.hybrid_battery_gauge import HybridBatteryGauge
from openpilot.selfdrive.ui.ui_state import ui_state


class AugmentedRoadViewBP(AugmentedRoadView, BlindspotRendererMixin):
  """BluePilot AugmentedRoadView with blindspot indicators and battery gauge."""

  BLIND_SPOT_WIDTH = 250  # Wider for TICI's larger screen

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._init_blindspot()
    self._battery_gauge_bp = HybridBatteryGauge()

  def _render(self, rect):
    """Override render to add blindspot and battery gauge within scissor mode."""
    start_draw = time.monotonic()
    if not ui_state.started:
      return

    self._switch_stream_if_needed(ui_state.sm)
    self._update_calibration()

    self._content_rect = rect

    rl.begin_scissor_mode(
      int(self._content_rect.x),
      int(self._content_rect.y),
      int(self._content_rect.width),
      int(self._content_rect.height)
    )

    # Render the base camera view
    from openpilot.selfdrive.ui.onroad.cameraview import CameraView
    CameraView._render(self, rect)

    # BP: Draw blindspot screen edge indicators (behind other UI elements)
    self._draw_blindspot_screen_edges(rect, self.BLIND_SPOT_WIDTH)

    self.model_renderer.render(self._content_rect)

    # Confidence ball
    confidence_ball_rect = rl.Rectangle(
      self.rect.x + CONFIDENCE_BALL_MARGIN,
      self.rect.y,
      CONFIDENCE_BALL_W,
      self.rect.height,
    )
    dark_grey = rl.Color(40, 40, 40, 255)
    rl.draw_rectangle_rec(confidence_ball_rect, dark_grey)
    confidence_ball_rect.x -= CONFIDENCE_BALL_MARGIN
    self._confidence_ball.render(confidence_ball_rect)

    left_rect = rl.Rectangle(
      self.rect.x + CONFIDENCE_BALL_W,
      self.rect.y,
      self.rect.width - CONFIDENCE_BALL_W,
      self.rect.height,
    )
    self._hud_renderer.render(self._content_rect)
    self.alert_renderer.set_speed_right(self._hud_renderer.get_speed_right())
    self.alert_renderer.render(self._content_rect)
    self.driver_state_renderer.render(left_rect)

    # BP: Render hybrid battery gauge
    self._battery_gauge_bp.render(self._content_rect, left_rect.x)

    rl.end_scissor_mode()
