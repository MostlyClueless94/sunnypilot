import time
import pyray as rl
from cereal import messaging
from openpilot.common.params import Params
from openpilot.selfdrive.ui import UI_BORDER_SIZE
from openpilot.selfdrive.ui.onroad.augmented_road_view import AugmentedRoadView
from openpilot.selfdrive.ui.onroad.cameraview import CameraView
from openpilot.selfdrive.ui.bp.onroad.blindspot_renderer import BlindspotRendererMixin
from openpilot.selfdrive.ui.bp.onroad.hud_renderer_bp import HudRendererBP
from openpilot.selfdrive.ui.bp.onroad.alert_renderer_bp import AlertRendererBP
from openpilot.selfdrive.ui.bp.onroad.model_renderer_bp import ModelRendererBP
from openpilot.selfdrive.ui.bp.onroad.hybrid_battery_gauge import HybridBatteryGauge
from openpilot.selfdrive.ui.bp.mici.onroad.confidence_ball_bp import ConfidenceBallTiciBP
from openpilot.selfdrive.ui.ui_state import ui_state

# BluePilot: Margin to keep confidence ball inside the colored border
BALL_BORDER_MARGIN = UI_BORDER_SIZE // 2  # 15px


class AugmentedRoadViewBP(AugmentedRoadView, BlindspotRendererMixin):
  """BluePilot AugmentedRoadView with blindspot indicators, battery gauge, and BP renderers."""

  BLIND_SPOT_WIDTH = 250  # Wider for TICI's larger screen

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._init_blindspot()
    self._bp_params = Params()

    # BluePilot: Replace renderers with BP versions
    self.model_renderer = ModelRendererBP()
    self._hud_renderer = HudRendererBP()
    self.alert_renderer = AlertRendererBP()
    self._battery_gauge_bp = HybridBatteryGauge()

    # BluePilot: Add confidence ball on left side (MADS beam + enhanced coloring)
    self._confidence_ball = ConfidenceBallTiciBP()
    self._show_confidence_ball = self._bp_params.get_bool("BPShowConfidenceBall")
    self._param_counter = 0

  def _render(self, rect):
    """Override render to add blindspot, battery gauge, confidence ball on left, and speed_right passing."""
    start_draw = time.monotonic()
    if not ui_state.started:
      return

    # Refresh param periodically (~1s at 60fps)
    self._param_counter += 1
    if self._param_counter >= 60:
      self._param_counter = 0
      self._show_confidence_ball = self._bp_params.get_bool("BPShowConfidenceBall")

    # TEMPORARY TEST: Disable confidence ball completely to see if DM/battery still disappear when engaged.
    # If they still disappear, the cause is not the confidence ball. Remove this block after testing.
    _confidence_ball_disabled_for_test = True
    if _confidence_ball_disabled_for_test:
      self._show_confidence_ball = False

    self._switch_stream_if_needed(ui_state.sm)
    self._update_calibration()

    # Create inner content area with border padding
    self._content_rect = rl.Rectangle(
      rect.x + UI_BORDER_SIZE,
      rect.y + UI_BORDER_SIZE,
      rect.width - 2 * UI_BORDER_SIZE,
      rect.height - 2 * UI_BORDER_SIZE,
    )

    # BluePilot: Offset rect pushes HUD/driver state/alerts right of the confidence ball
    ball_offset = (ConfidenceBallTiciBP.BALL_WIDTH + BALL_BORDER_MARGIN) if self._show_confidence_ball else 0
    ui_rect = rl.Rectangle(
      self._content_rect.x + ball_offset,
      self._content_rect.y,
      self._content_rect.width - ball_offset,
      self._content_rect.height,
    )

    rl.begin_scissor_mode(
      int(self._content_rect.x),
      int(self._content_rect.y),
      int(self._content_rect.width),
      int(self._content_rect.height)
    )

    # Render the base camera view
    CameraView._render(self, rect)

    # BluePilot: Draw blindspot screen edge indicators (behind other UI elements)
    self._draw_blindspot_screen_edges(self._content_rect, self.BLIND_SPOT_WIDTH)

    # Render model (uses full content rect for camera-space overlays)
    self.model_renderer.render(self._content_rect)

    # SP fade overlay
    self.update_fade_out_bottom_overlay(self._content_rect)

    # BluePilot: Render confidence ball on left side (narrow rect = ball strip only, not full width)
    # Using a strip-sized rect avoids the ball widget having a full-width rect that could affect
    # layout/visibility of driver state and battery when the teal beam is not drawn (ENGAGED).
    if self._show_confidence_ball:
      ball_strip_width = ConfidenceBallTiciBP.BALL_WIDTH + BALL_BORDER_MARGIN
      ball_rect = rl.Rectangle(
        self._content_rect.x + BALL_BORDER_MARGIN,
        self._content_rect.y,
        ball_strip_width,
        self._content_rect.height,
      )
      self._confidence_ball.render(ball_rect)

    # BluePilot: Render HUD, driver state, and battery before alerts so alerts draw on top
    # Header gradient uses full content width, HUD elements use offset rect
    self._hud_renderer.set_gradient_rect(self._content_rect)
    self._hud_renderer.render(ui_rect)
    self.driver_state_renderer.render(ui_rect)
    self._battery_gauge_bp.render(self._content_rect, self._content_rect.x + ball_offset)

    # Alerts last so they are never covered by battery or other overlays
    self.alert_renderer.set_speed_right(self._hud_renderer.get_speed_right())
    self.alert_renderer.render(ui_rect)

    rl.end_scissor_mode()

    # BluePilot: Conditionally draw border
    if not self._bp_params.get_bool("BPHideOnroadBorder"):
      self._draw_border(rect)

    # Publish uiDebug
    msg = messaging.new_message('uiDebug')
    msg.uiDebug.drawTimeMillis = (time.monotonic() - start_draw) * 1000
    self._pm.send('uiDebug', msg)
