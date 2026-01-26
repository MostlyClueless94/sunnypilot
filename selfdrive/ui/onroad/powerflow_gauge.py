"""
Powerflow Gauge Widget for Hybrid Vehicles

Displays an arch-shaped gauge above the torque bar showing power flow direction.
The gauge is concentric with the torque bar but has slightly more curvature and length.
"""
import numpy as np
import pyray as rl
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.widgets import Widget
from openpilot.selfdrive.ui.mici.onroad.torque_bar import arc_bar_pts, TORQUE_ANGLE_SPAN
from openpilot.selfdrive.ui.mici.onroad import blend_colors
from openpilot.system.ui.lib.shader_polygon import draw_polygon, Gradient

# Constants
POWERFLOW_ANGLE_SPAN = 15.0  # Slightly longer than torque bar (12.7 degrees)
POWERFLOW_RADIUS = 3400  # Slightly larger radius than torque bar (3300) for more curvature
POWERFLOW_LINE_HEIGHT = 60  # Height/thickness of the powerflow arch (doubled for text space)
POWERFLOW_Y_OFFSET = 50  # Vertical offset above torque bar
POWERFLOW_BG_COLOR = rl.Color(20, 20, 20, 200)  # Translucent dark grey
POWERFLOW_TICK_COLOR = rl.Color(200, 200, 200, 255)  # Light grey for tick marks
POWERFLOW_BORDER_COLOR = rl.Color(200, 200, 200, 255)  # Light grey for border (same as tick marks)
POWERFLOW_TICK_LENGTH_RATIO = 0.10  # Tick marks extend 10% into the bar
POWERFLOW_BORDER_THICKNESS = 2.0  # Border line thickness
POWERFLOW_BAR_HEIGHT = 40  # Height/thickness of the animated power flow bar
POWERFLOW_CENTER_COLOR = rl.Color(255, 255, 255, 255)  # White at center (no power flow)
POWERFLOW_REGEN_COLOR = rl.Color(100, 255, 100, 255)  # Green for regenerative braking (left)
POWERFLOW_DEMAND_COLOR = rl.Color(100, 150, 255, 255)  # Brighter blue for throttle demand (right) - better daytime visibility


class PowerflowGauge(Widget):
  """Widget to display powerflow gauge as an arch above the torque bar"""
  
  def __init__(self):
    super().__init__()
    self.set_visible(lambda: ui_state.sm.recv_frame.get("carStateBP", 0) > ui_state.started_frame)
    # Smooth animation filter for power flow value
    from openpilot.common.filter_simple import FirstOrderFilter
    self._powerflow_filter = FirstOrderFilter(0.0, 0.0, 1.0 / gui_app.target_fps * 10)
  
  def _update_state(self):
    """Update power flow state and animate changes"""
    if not self._should_render():
      return
    
    sm = ui_state.sm
    try:
      car_state_bp = sm['carStateBP']
      throttle_demand = car_state_bp.hybridDrive.throttleDemandPercent
      # Clamp to expected range [-102.2, 102.4] and normalize to [-1, 1] for easier calculation
      # Positive = throttle demand (power out, should be blue)
      # Negative = regenerative braking (power in, should be green)
      normalized_value = np.clip(throttle_demand / 102.0, -1.0, 1.0)
      self._powerflow_filter.update(normalized_value)
    except (KeyError, AttributeError, TypeError):
      pass
  
  def _should_render(self) -> bool:
    """Check if powerflow gauge should be rendered"""
    # Only render if hybrid power flow is enabled
    from openpilot.common.params import Params
    params = Params()
    power_flow_enabled = params.get_bool("FordPrefHybridPowerFlow")
    if not power_flow_enabled:
      return False
    
    sm = ui_state.sm
    try:
      # Check if message exists and is recent enough
      if "carStateBP" not in sm.recv_frame:
        return False
      
      recv_frame = sm.recv_frame["carStateBP"]
      if recv_frame < ui_state.started_frame:
        return False
      
      car_state_bp = sm['carStateBP']
      return car_state_bp.hybridDrive.dataAvailable
    except (KeyError, AttributeError, TypeError):
      return False
  
  def _render(self, rect: rl.Rectangle) -> None:
    """Render the powerflow gauge arch"""
    if not self._should_render():
      return
    
    try:
      # Get torque bar parameters to position concentrically
      # Torque bar center: cx = rect.x + rect.width / 2 + 8
      # Torque bar radius: 3300
      # Torque bar cy: rect.y + rect.height + torque_line_radius - torque_line_offset
      # For concentric positioning, use same center point
      
      # Calculate center point (same as torque bar for concentric positioning)
      cx = rect.x + rect.width / 2 + 8
      
      # Position concentrically with torque bar
      # Torque bar uses: cy = rect.y + rect.height + torque_line_radius - torque_line_offset
      # Use same calculation but account for being "above" - the larger radius will naturally position it higher
      torque_bar_radius = 3300
      # Estimate torque_line_offset (typically 22-26px, use middle value)
      torque_line_offset_estimate = 24
      cy = rect.y + rect.height + torque_bar_radius - torque_line_offset_estimate
      
      # Calculate arch angles (centered at top, slightly longer span than torque bar)
      top_angle = -90  # Same as torque bar
      powerflow_start_angle = top_angle - POWERFLOW_ANGLE_SPAN / 2
      powerflow_end_angle = top_angle + POWERFLOW_ANGLE_SPAN / 2
      
      # Calculate centerline radius
      mid_r = POWERFLOW_RADIUS + POWERFLOW_LINE_HEIGHT / 2
      
      # Draw powerflow arch background
      bg_pts = arc_bar_pts(
        cx, cy, mid_r, POWERFLOW_LINE_HEIGHT,
        powerflow_start_angle, powerflow_end_angle
      )
      draw_polygon(rect, bg_pts, color=POWERFLOW_BG_COLOR)
      
      # Draw border around the arch (outer and inner edges)
      outer_radius = mid_r + POWERFLOW_LINE_HEIGHT / 2
      inner_radius = mid_r - POWERFLOW_LINE_HEIGHT / 2
      
      # Calculate number of segments for smooth border
      num_segments = int(POWERFLOW_ANGLE_SPAN * 2)  # 2 segments per degree
      angle_step = POWERFLOW_ANGLE_SPAN / num_segments
      
      # Draw outer border (top edge)
      for i in range(num_segments + 1):
        angle_deg = powerflow_start_angle + angle_step * i
        angle_rad = np.deg2rad(angle_deg)
        x = cx + np.cos(angle_rad) * outer_radius
        y = cy + np.sin(angle_rad) * outer_radius
        
        if i > 0:
          prev_angle_deg = powerflow_start_angle + angle_step * (i - 1)
          prev_angle_rad = np.deg2rad(prev_angle_deg)
          prev_x = cx + np.cos(prev_angle_rad) * outer_radius
          prev_y = cy + np.sin(prev_angle_rad) * outer_radius
          rl.draw_line_ex(
            rl.Vector2(prev_x, prev_y),
            rl.Vector2(x, y),
            POWERFLOW_BORDER_THICKNESS,
            POWERFLOW_BORDER_COLOR
          )
      
      # Draw inner border (bottom edge)
      for i in range(num_segments + 1):
        angle_deg = powerflow_start_angle + angle_step * i
        angle_rad = np.deg2rad(angle_deg)
        x = cx + np.cos(angle_rad) * inner_radius
        y = cy + np.sin(angle_rad) * inner_radius
        
        if i > 0:
          prev_angle_deg = powerflow_start_angle + angle_step * (i - 1)
          prev_angle_rad = np.deg2rad(prev_angle_deg)
          prev_x = cx + np.cos(prev_angle_rad) * inner_radius
          prev_y = cy + np.sin(prev_angle_rad) * inner_radius
          rl.draw_line_ex(
            rl.Vector2(prev_x, prev_y),
            rl.Vector2(x, y),
            POWERFLOW_BORDER_THICKNESS,
            POWERFLOW_BORDER_COLOR
          )
      
      # Draw tick marks at every 10% (0%, 10%, 20%, ..., 100%)
      tick_length = POWERFLOW_LINE_HEIGHT * POWERFLOW_TICK_LENGTH_RATIO
      outer_radius = mid_r + POWERFLOW_LINE_HEIGHT / 2
      inner_radius = mid_r - POWERFLOW_LINE_HEIGHT / 2
      
      # Calculate tick positions (0% to 100% in 10% increments)
      for percent in range(0, 101, 10):
        # Calculate angle for this percentage
        # 0% = start_angle, 100% = end_angle
        angle_deg = powerflow_start_angle + (powerflow_end_angle - powerflow_start_angle) * (percent / 100.0)
        angle_rad = np.deg2rad(angle_deg)
        
        # Calculate outer and inner points for top tick (outer edge)
        outer_x_top = cx + np.cos(angle_rad) * outer_radius
        outer_y_top = cy + np.sin(angle_rad) * outer_radius
        inner_x_top = cx + np.cos(angle_rad) * (outer_radius - tick_length)
        inner_y_top = cy + np.sin(angle_rad) * (outer_radius - tick_length)
        
        # Calculate outer and inner points for bottom tick (inner edge)
        outer_x_bottom = cx + np.cos(angle_rad) * inner_radius
        outer_y_bottom = cy + np.sin(angle_rad) * inner_radius
        inner_x_bottom = cx + np.cos(angle_rad) * (inner_radius + tick_length)
        inner_y_bottom = cy + np.sin(angle_rad) * (inner_radius + tick_length)
        
        # Draw top tick mark
        rl.draw_line_ex(
          rl.Vector2(outer_x_top, outer_y_top),
          rl.Vector2(inner_x_top, inner_y_top),
          2.0,  # Line thickness
          POWERFLOW_TICK_COLOR
        )
        
        # Draw bottom tick mark
        rl.draw_line_ex(
          rl.Vector2(outer_x_bottom, outer_y_bottom),
          rl.Vector2(inner_x_bottom, inner_y_bottom),
          2.0,  # Line thickness
          POWERFLOW_TICK_COLOR
        )
      
      # Draw animated power flow bar with dynamic colors
      self._draw_powerflow_bar(rect, cx, cy, mid_r, powerflow_start_angle, powerflow_end_angle)
      
    except Exception as e:
      # Log error but don't crash
      from openpilot.common.swaglog import cloudlog
      import traceback
      cloudlog.error(f"PowerflowGauge render error: {e}")
      cloudlog.error(traceback.format_exc())
      return
  
  def _draw_powerflow_bar(self, rect, cx, cy, mid_r, start_angle, end_angle):
    """Draw the animated power flow bar with dynamic colors"""
    # Get filtered power flow value (normalized to [-1, 1])
    powerflow_value = self._powerflow_filter.x
    
    # Calculate bar position along the arch
    # Negative values (regen) go left, positive values (demand) go right
    # Center (0) is at the top (-90 degrees)
    center_angle = -90  # Top of arch
    
    if abs(powerflow_value) < 0.01:  # Very close to zero, show nothing
      return
    
    # Calculate the angle span for the bar
    # Map [-1, 1] to [start_angle, end_angle] with center at -90
    if powerflow_value < 0:
      # Regenerative braking (left side, green)
      bar_start_angle = center_angle
      bar_end_angle = center_angle + (start_angle - center_angle) * abs(powerflow_value)
      # Ensure we don't go beyond start_angle
      bar_end_angle = max(bar_end_angle, start_angle)
    else:
      # Throttle demand (right side, blue)
      bar_start_angle = center_angle
      bar_end_angle = center_angle + (end_angle - center_angle) * powerflow_value
      # Ensure we don't go beyond end_angle
      bar_end_angle = min(bar_end_angle, end_angle)
    
    # Calculate solid color based on power flow value
    # Full green for regen (negative), full blue for demand (positive)
    # Always use 100% opacity for better daytime visibility
    if powerflow_value < 0:
      # Regenerative braking (negative) - full green
      bar_color = POWERFLOW_REGEN_COLOR
    else:
      # Throttle demand (positive) - full blue
      bar_color = POWERFLOW_DEMAND_COLOR
    
    # Draw the power flow bar as an arc with solid color
    bar_pts = arc_bar_pts(
      cx, cy, mid_r, POWERFLOW_BAR_HEIGHT,
      bar_start_angle, bar_end_angle
    )
    
    # Draw with solid color instead of gradient
    draw_polygon(rect, bar_pts, color=bar_color)
