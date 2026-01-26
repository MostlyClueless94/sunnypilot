"""
Hybrid Battery Gauge Widget for TICI UI

Displays a horizontal battery gauge with:
- Battery shape (double A battery style)
- State of charge percentage (to the right)
- Voltage and Amps (below battery)
- Color coding: Green for charging (positive amps), Red for discharging (negative amps)
"""
import traceback
import pyray as rl
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog


# Constants
BATTERY_WIDTH = 90  # Width of battery body (reduced from 120 to make room for larger SOC font)
BATTERY_HEIGHT = 50  # Height of battery body
BATTERY_TERMINAL_WIDTH = 20  # Width of battery terminal (positive end)
BATTERY_TERMINAL_HEIGHT = 20  # Height of battery terminal
BATTERY_ROUNDNESS = 0.3  # Roundness for battery body
BATTERY_BORDER_THICKNESS = 3  # Border thickness
BATTERY_X_SPACING = 40  # Space between driver monitor and battery gauge
BATTERY_Y_MARGIN = 30  # Margin from bottom of screen

SOC_FONT_SIZE = 48  # Font size for SOC percentage (increased from 36)
SOC_X_SPACING = 15  # Space between battery and SOC text

VOLTAGE_AMPS_Y_OFFSET = 8  # Space below battery for voltage/amps
VOLTAGE_AMPS_FONT_SIZE = 40  # Font size for voltage and amps (32 * 1.25 = 40)
VOLTAGE_AMPS_LINE_SPACING = 8  # Space between voltage and amps lines
BACKGROUND_PADDING = 15  # Padding around widget for background box
BACKGROUND_ROUNDNESS = 0.3  # Roundness for background box

# Colors
BACKGROUND_BOX_COLOR = rl.Color(20, 20, 20, 200)  # Translucent dark grey background
BATTERY_BG_COLOR = rl.Color(40, 40, 40, 220)  # Dark grey background
BATTERY_BORDER_COLOR = rl.Color(200, 200, 200, 255)  # Light grey border
BATTERY_FILL_COLOR = rl.Color(100, 200, 100, 255)  # Green fill (will be adjusted based on SOC)
BATTERY_LOW_COLOR = rl.Color(200, 100, 100, 255)  # Red for low SOC
BATTERY_MID_COLOR = rl.Color(200, 200, 100, 255)  # Yellow for mid SOC
BATTERY_HIGH_COLOR = rl.Color(100, 200, 100, 255)  # Green for high SOC
TEXT_COLOR = rl.Color(255, 255, 255, 255)  # White text
CHARGING_COLOR = rl.Color(100, 255, 100, 255)  # Bright green for charging
DISCHARGING_COLOR = rl.Color(255, 100, 100, 255)  # Red for discharging


class HybridBatteryGauge(Widget):
  """Widget to display hybrid battery status gauge"""
  
  def __init__(self):
    super().__init__()
    self._params = Params()
    self._font_medium = gui_app.font(FontWeight.MEDIUM)
    self._font_bold = gui_app.font(FontWeight.BOLD)
    self._left_offset = 0  # Initialize left_offset
    
    # Smooth animation for SOC changes
    from openpilot.common.filter_simple import FirstOrderFilter
    # Use frame-based time constant for smooth 60fps animation (~0.17s at 60fps)
    self._soc_filter = FirstOrderFilter(50.0, 50.0, 1.0 / gui_app.target_fps * 10)
  
  def _update_state(self):
    """Update battery state and animate SOC changes"""
    battery_data = self._get_battery_data()
    if battery_data is not None:
      # Update filter with current SOC for smooth animation
      self._soc_filter.update(battery_data['soc'])
  
  def _should_render(self) -> bool:
    """Check if battery gauge should be rendered"""
    # Only render if hybrid battery status is enabled and battery data is available
    battery_status_enabled = self._params.get_bool("FordPrefHybridBatteryStatus")
    if not battery_status_enabled:
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
      return car_state_bp.hybridBattery.dataAvailable
    except (KeyError, AttributeError, TypeError):
      return False
  
  def _get_battery_data(self):
    """Get battery data from carStateBP message"""
    sm = ui_state.sm
    try:
      car_state_bp = sm['carStateBP']
      battery = car_state_bp.hybridBattery
      data = {
        'soc': battery.socActual,  # 0-100
        'voltage': battery.voltActual,  # volts
        'amps': battery.ampsActual,  # amps (positive = charging, negative = discharging)
        'soc_min': battery.socMinPerc,
        'soc_max': battery.socMaxPerc,
      }
      cloudlog.debug(f"HybridBatteryGauge: Got battery data: {data}")
      return data
    except (KeyError, AttributeError, TypeError) as e:
      cloudlog.debug(f"HybridBatteryGauge: Error getting battery data: {e}, using default values")
      # Return default/placeholder data for debugging
      return {
        'soc': 50.0,  # Default 50% for debugging
        'voltage': 0.0,
        'amps': 0.0,
        'soc_min': 0.0,
        'soc_max': 100.0,
      }
  
  def _get_battery_fill_color(self, soc: float) -> rl.Color:
    """Get battery fill color based on SOC"""
    if soc < 20:
      return BATTERY_LOW_COLOR
    elif soc < 50:
      return BATTERY_MID_COLOR
    else:
      return BATTERY_HIGH_COLOR
  
  def render(self, rect: rl.Rectangle = None, left_offset: int = 0) -> None:
    """Override render to accept left_offset parameter"""
    if rect is not None:
      self.set_rect(rect)
    # Store left_offset for use in _render
    self._left_offset = left_offset
    # Call parent render which will call _render
    return super().render(rect)
  
  def _render(self, rect: rl.Rectangle) -> None:
    """Render the battery gauge
    
    Args:
        rect: Rectangle defining the rendering area
    """
    try:
      # Get left_offset from instance variable (set in render() method)
      left_offset = getattr(self, '_left_offset', 0)
      
      if not self._should_render():
        return
      
      battery_data = self._get_battery_data()
      if battery_data is None:
        return
      
      soc = battery_data['soc']
      voltage = battery_data['voltage']
      amps = battery_data['amps']
      
      # Use filtered SOC for smooth animation (filter is updated in _update_state)
      animated_soc = self._soc_filter.x
      
      # Calculate battery position: bottom of screen, to the right of driver monitor
      # Driver monitor button is BTN_SIZE (192px) positioned at offset from left
      # offset = UI_BORDER_SIZE + BTN_SIZE/2, so right edge ≈ offset + BTN_SIZE/2
      # For LHD: position_x = left_rect.x + offset, so right edge ≈ left_rect.x + offset + BTN_SIZE/2
      # Simplified: right edge ≈ left_rect.x + UI_BORDER_SIZE + BTN_SIZE
      # Use ~250px from left_offset to position between driver monitor and torque bar (which is centered)
      driver_monitor_right_edge = 250  # Approximate right edge of driver monitor area
      battery_x_base = left_offset + driver_monitor_right_edge + BATTERY_X_SPACING
      # Move 25% of battery width to the left
      x = battery_x_base - (BATTERY_WIDTH * 0.25)
      # Position at bottom: account for battery height + voltage line + amps line + spacing + margin
      # Voltage and amps are now on separate lines, so we need 2x font size + line spacing
      total_height = BATTERY_HEIGHT + VOLTAGE_AMPS_Y_OFFSET + (VOLTAGE_AMPS_FONT_SIZE * 2) + VOLTAGE_AMPS_LINE_SPACING
      y = rect.y + rect.height - total_height - BATTERY_Y_MARGIN
      
      # Calculate text sizes for background box dimensions
      soc_text = f"{int(soc)}%"
      soc_text_size = measure_text_cached(self._font_bold, soc_text, SOC_FONT_SIZE)
      
      # Calculate background box dimensions
      # Width: from battery left edge to end of SOC text + padding
      soc_text_end_x = x + BATTERY_WIDTH + BATTERY_TERMINAL_WIDTH + SOC_X_SPACING + soc_text_size.x
      background_width = soc_text_end_x - x + BACKGROUND_PADDING * 2
      # Height: from battery top to bottom of amps text (second line) + padding
      # total_height already accounts for both voltage and amps lines
      background_height = total_height + BACKGROUND_PADDING * 2
      background_x = x - BACKGROUND_PADDING
      background_y = y - BACKGROUND_PADDING
      
      # Draw background box behind entire widget
      background_rect = rl.Rectangle(background_x, background_y, background_width, background_height)
      rl.draw_rectangle_rounded(background_rect, BACKGROUND_ROUNDNESS, 10, BACKGROUND_BOX_COLOR)
      
      # Draw battery body (rounded rectangle)
      battery_body = rl.Rectangle(x, y, BATTERY_WIDTH, BATTERY_HEIGHT)
      
      # Draw battery background
      rl.draw_rectangle_rounded(battery_body, BATTERY_ROUNDNESS, 10, BATTERY_BG_COLOR)
      
      # Draw battery fill based on animated SOC
      fill_width = int(BATTERY_WIDTH * (animated_soc / 100.0))
      if fill_width > 0:
        fill_rect = rl.Rectangle(x, y, fill_width, BATTERY_HEIGHT)
        # Use actual SOC for color (not animated) so color changes are immediate
        fill_color = self._get_battery_fill_color(soc)
        rl.draw_rectangle_rounded(fill_rect, BATTERY_ROUNDNESS, 10, fill_color)
      
      # Draw battery border
      rl.draw_rectangle_rounded_lines_ex(
        battery_body, BATTERY_ROUNDNESS, 10, BATTERY_BORDER_THICKNESS, BATTERY_BORDER_COLOR
      )
      
      # Draw battery terminal (positive end, on the right)
      terminal_x = x + BATTERY_WIDTH
      terminal_y = y + (BATTERY_HEIGHT - BATTERY_TERMINAL_HEIGHT) / 2
      terminal_rect = rl.Rectangle(terminal_x, terminal_y, BATTERY_TERMINAL_WIDTH, BATTERY_TERMINAL_HEIGHT)
      rl.draw_rectangle_rounded(terminal_rect, 0.5, 10, BATTERY_BG_COLOR)
      rl.draw_rectangle_rounded_lines_ex(
        terminal_rect, 0.5, 10, BATTERY_BORDER_THICKNESS, BATTERY_BORDER_COLOR
      )
      
      # Draw SOC percentage to the right of battery
      # Note: soc_text and soc_text_size already calculated above for background box
      soc_x = x + BATTERY_WIDTH + BATTERY_TERMINAL_WIDTH + SOC_X_SPACING
      soc_y = y + (BATTERY_HEIGHT - soc_text_size.y) / 2
      rl.draw_text_ex(
        self._font_bold,
        soc_text,
        rl.Vector2(soc_x, soc_y),
        SOC_FONT_SIZE,
        0,
        TEXT_COLOR
      )
      
      # Draw voltage and amps below battery on separate lines
      voltage_text = f"{voltage:.1f}V"
      amps_text = f"{amps:+.1f}A"  # + sign for positive, - for negative
      
      voltage_text_size = measure_text_cached(self._font_medium, voltage_text, VOLTAGE_AMPS_FONT_SIZE)
      amps_text_size = measure_text_cached(self._font_medium, amps_text, VOLTAGE_AMPS_FONT_SIZE)
      
      # Position voltage and amps on left (below battery), on separate lines
      voltage_x = x
      amps_x = x
      
      # Calculate Y positions for separate lines
      voltage_y = y + BATTERY_HEIGHT + VOLTAGE_AMPS_Y_OFFSET
      amps_y = voltage_y + VOLTAGE_AMPS_FONT_SIZE + VOLTAGE_AMPS_LINE_SPACING
      
      # Draw voltage (first line, below battery)
      rl.draw_text_ex(
        self._font_medium,
        voltage_text,
        rl.Vector2(voltage_x, voltage_y),
        VOLTAGE_AMPS_FONT_SIZE,
        0,
        TEXT_COLOR
      )
      
      # Draw amps (second line, below voltage) with color coding
      amps_color = CHARGING_COLOR if amps > 0 else DISCHARGING_COLOR if amps < 0 else TEXT_COLOR
      rl.draw_text_ex(
        self._font_medium,
        amps_text,
        rl.Vector2(amps_x, amps_y),
        VOLTAGE_AMPS_FONT_SIZE,
        0,
        amps_color
      )
    except Exception as e:
      # Log the error to help debug, but don't crash the UI
      cloudlog.error(f"HybridBatteryGauge render error: {e}")
      cloudlog.error(traceback.format_exc())
      return
