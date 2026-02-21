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
from openpilot.selfdrive.ui.bp.onroad.power_flow_gauge import PowerFlowGauge
from openpilot.selfdrive.ui.bp.onroad.torque_bar_renderer_bp import TorqueBarRendererBP
from openpilot.selfdrive.ui.bp.mici.onroad.confidence_ball_bp import ConfidenceBallTiciBP
from openpilot.selfdrive.ui.onroad.driver_state import BTN_SIZE
from openpilot.selfdrive.ui.sunnypilot.onroad.developer_ui import DeveloperUiRenderer
from openpilot.selfdrive.ui.ui_state import ui_state

# BluePilot: Margin to keep confidence ball inside the colored border
BALL_BORDER_MARGIN = UI_BORDER_SIZE // 2  # 15px

# Shared container styling (matches battery/power flow gauge backgrounds)
SHARED_BG_COLOR = rl.Color(20, 20, 20, 100)
SHARED_BG_ROUNDNESS = 0.3
SHARED_BG_GLOW_EXPANSION = 4
SHARED_INNER_GAP = 10  # Pixels between battery and power flow gauges inside shared container
SHARED_PADDING = 8     # Padding around inner content in shared container
SHARED_BORDER_THICKNESS = 2.0  # Power flow mode-colored border thickness

# Full screen reference for sidebar detection
FULL_CONTENT_WIDTH = 2100.0


class AugmentedRoadViewBP(AugmentedRoadView, BlindspotRendererMixin):
  """BluePilot AugmentedRoadView with blindspot indicators, gauges, and BP renderers."""

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
    self._power_flow_gauge = PowerFlowGauge()

    # BluePilot: Standalone torque bar renderer (smoother, positioned above gauges)
    self._torque_bar = TorqueBarRendererBP(scale=3.0)

    # BluePilot: Add confidence ball on left side (MADS beam + enhanced coloring)
    self._confidence_ball = ConfidenceBallTiciBP()
    self._show_confidence_ball = self._bp_params.get_bool("BPShowConfidenceBall")
    self._param_counter = 0

  def _render(self, rect):
    """Override render to add blindspot, gauges, confidence ball on left, and speed_right passing."""
    start_draw = time.monotonic()
    if not ui_state.started:
      return

    # Refresh param periodically (~1s at 60fps)
    self._param_counter += 1
    if self._param_counter >= 60:
      self._param_counter = 0
      self._show_confidence_ball = self._bp_params.get_bool("BPShowConfidenceBall")

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
    if self._show_confidence_ball:
      ball_strip_width = ConfidenceBallTiciBP.BALL_WIDTH + BALL_BORDER_MARGIN
      ball_rect = rl.Rectangle(
        self._content_rect.x + BALL_BORDER_MARGIN,
        self._content_rect.y,
        ball_strip_width,
        self._content_rect.height,
      )
      self._confidence_ball.render(ball_rect)

    # BluePilot: Render HUD, driver state before gauges and alerts
    self._hud_renderer.set_gradient_rect(self._content_rect)
    self._hud_renderer.render(ui_rect)

    # Defensive: re-establish scissor before drawing driver state and battery. Some HUD widgets
    # (e.g. speed limit, brake status, unified gauge) can leave raylib state in a bad way on device,
    # causing the bottom-left widgets to be clipped or not drawn. Resetting scissor to content_rect
    # ensures DM and battery always render in the correct clip region.
    rl.end_scissor_mode()
    rl.begin_scissor_mode(
      int(self._content_rect.x),
      int(self._content_rect.y),
      int(self._content_rect.width),
      int(self._content_rect.height)
    )
    self.driver_state_renderer.render(ui_rect)

    # BluePilot: Render battery + power flow gauges with shared container when both visible
    gauge_height_offset = self._render_gauges(self._content_rect, ball_offset)

    # BluePilot: Update and render torque bar ABOVE gauges and ON TOP in draw order
    self._torque_bar.update()
    torque_rect = ui_rect
    if ui_state.developer_ui in (DeveloperUiRenderer.DEV_UI_BOTTOM, DeveloperUiRenderer.DEV_UI_BOTH):
      torque_rect = rl.Rectangle(ui_rect.x, ui_rect.y, ui_rect.width, ui_rect.height - DeveloperUiRenderer.BOTTOM_BAR_HEIGHT)
    self._torque_bar.render(torque_rect, gauge_height_offset=gauge_height_offset)

    # Alerts last so they are never covered by gauges or other overlays
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

  def _get_dm_center_y(self, content_rect: rl.Rectangle) -> float:
    """Get the driver monitor face icon's vertical center Y coordinate.

    This matches the positioning in DriverStateRendererSP._pre_calculate_drawing_elements():
      position_y = rect.y + height - (UI_BORDER_SIZE + BTN_SIZE // 2) - dev_ui_offset
    """
    dev_ui_offset = DeveloperUiRenderer.get_bottom_dev_ui_offset()
    return content_rect.y + content_rect.height - (UI_BORDER_SIZE + BTN_SIZE // 2) - dev_ui_offset

  def _render_gauges(self, content_rect: rl.Rectangle, ball_offset: float) -> float:
    """Render power flow and battery gauges, vertically centered with the driver monitor.

    When both are visible:
    - Horizontally centered as a unit in the content area
    - Battery on the left, power flow immediately to the right (small gap)
    - Battery content vertically centered within the shared container
    - Shared background container wraps both tightly
    - Power flow mode-colored border wraps the entire shared container
    - Entire container vertically centered with the driver monitor face icon

    Returns:
        gauge_height_offset: Pixels from bottom of content_rect to top of gauge area.
            Used to push the torque bar arc above the gauges. Returns 0 if no gauges visible.
    """
    left_offset = content_rect.x + ball_offset
    sidebar_visible = content_rect.width < (FULL_CONTENT_WIDTH * 0.9)
    content_bottom = content_rect.y + content_rect.height

    # Driver monitor center Y — gauges will be vertically centered to this
    dm_center_y = self._get_dm_center_y(content_rect)

    # Check visibility of each gauge
    battery_rect = self._battery_gauge_bp.get_bounding_rect(content_rect, left_offset)
    pf_visible = self._power_flow_gauge.should_render()

    # Track the top of the gauge area for torque bar positioning
    gauge_top = content_bottom  # default: no gauges, no offset

    if battery_rect is not None and pf_visible:
      # Both visible: horizontally center the combined container
      pf_rect = self._power_flow_gauge.get_gauge_rect(
        content_rect, sidebar_visible, self._show_confidence_ball,
      )

      # Compute total width: battery + gap + power flow
      total_inner_width = battery_rect.width + SHARED_INNER_GAP + pf_rect.width

      # Center the combined unit horizontally within the content area
      combined_left = content_rect.x + (content_rect.width - total_inner_width) / 2
      battery_x = combined_left
      pf_x = battery_x + battery_rect.width + SHARED_INNER_GAP

      # Use the taller gauge's height as the shared container inner height
      container_inner_height = max(battery_rect.height, pf_rect.height)

      # Vertically center with the driver monitor
      container_top = dm_center_y - container_inner_height / 2

      # Position power flow at the top of the container (it defines the height)
      pf_y = container_top

      # Vertically center battery content within the container height
      battery_y = container_top + (container_inner_height - battery_rect.height) / 2

      # Build the shared container rect with padding
      shared_rect = rl.Rectangle(
        combined_left - SHARED_PADDING,
        container_top - SHARED_PADDING,
        total_inner_width + SHARED_PADDING * 2,
        container_inner_height + SHARED_PADDING * 2,
      )

      # Draw shared background + power flow mode-colored border around both gauges
      self._draw_shared_background(shared_rect)
      border_color = self._power_flow_gauge.get_border_color()
      rl.draw_rectangle_rounded_lines_ex(
        shared_rect, SHARED_BG_ROUNDNESS, 10, SHARED_BORDER_THICKNESS, border_color,
      )

      # Render battery at the centered position
      # Compute offsets relative to the battery's natural position
      battery_x_offset = combined_left - battery_rect.x
      battery_y_offset = battery_y - battery_rect.y
      self._battery_gauge_bp.render_at(content_rect, left_offset, draw_background=False,
                                       x_offset=battery_x_offset, y_offset=battery_y_offset)

      # Render power flow gauge at adjusted position, without its own background or border
      adjusted_pf_rect = rl.Rectangle(pf_x, pf_y, pf_rect.width, pf_rect.height)
      self._power_flow_gauge.render_at(adjusted_pf_rect, draw_background=False, draw_border=False)

      # Gauge area top = top of shared container
      gauge_top = shared_rect.y

    elif pf_visible:
      # Only power flow visible: center with driver monitor
      pf_rect = self._power_flow_gauge.get_gauge_rect(
        content_rect, sidebar_visible, self._show_confidence_ball,
      )
      # Shift to center with DM
      pf_center_y = pf_rect.y + pf_rect.height / 2
      y_shift = dm_center_y - pf_center_y
      centered_pf_rect = rl.Rectangle(pf_rect.x, pf_rect.y + y_shift, pf_rect.width, pf_rect.height)
      self._power_flow_gauge.render_at(centered_pf_rect, draw_background=True)
      gauge_top = centered_pf_rect.y

    elif battery_rect is not None:
      # Only battery visible: center with driver monitor
      battery_center_y = battery_rect.y + battery_rect.height / 2
      y_shift = dm_center_y - battery_center_y
      self._battery_gauge_bp.render(content_rect, left_offset, y_offset=y_shift)
      # Battery-only: don't push torque bar up — let it sit at its natural low position

    # Return the offset from the bottom: how many pixels the gauge area occupies
    return max(0.0, content_bottom - gauge_top)

  def _draw_shared_background(self, rect: rl.Rectangle):
    """Draw shared background container (glow + fill). Border drawn separately."""
    glow_exp = SHARED_BG_GLOW_EXPANSION
    glow_rect = rl.Rectangle(
      rect.x - glow_exp, rect.y - glow_exp,
      rect.width + glow_exp * 2, rect.height + glow_exp * 2,
    )
    rl.draw_rectangle_rounded(
      glow_rect, SHARED_BG_ROUNDNESS, 10,
      rl.Color(20, 20, 20, int(SHARED_BG_COLOR.a * 0.3)),
    )
    rl.draw_rectangle_rounded(rect, SHARED_BG_ROUNDNESS, 10, SHARED_BG_COLOR)
