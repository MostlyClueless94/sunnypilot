"""
Hybrid Battery Gauge Widget for TICI UI

Displays a horizontal battery gauge with:
- Battery shape (double A battery style)
- State of charge percentage (to the right)
- Voltage and Amps (below battery)
- Color coding: Green for charging (positive amps), Red for discharging (negative amps)
"""
import pyray as rl
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget
from openpilot.common.params import Params


# Constants
BATTERY_WIDTH = 120  # Width of battery body
BATTERY_HEIGHT = 50  # Height of battery body
BATTERY_TERMINAL_WIDTH = 20  # Width of battery terminal (positive end)
BATTERY_TERMINAL_HEIGHT = 20  # Height of battery terminal
BATTERY_ROUNDNESS = 0.3  # Roundness for battery body
BATTERY_BORDER_THICKNESS = 3  # Border thickness
BATTERY_X_OFFSET = 60  # X position from left edge (same as MAX box)
BATTERY_Y_OFFSET = 120  # Y position from top (between MAX box area and current speed at center)

SOC_FONT_SIZE = 36  # Font size for SOC percentage
SOC_X_SPACING = 15  # Space between battery and SOC text

VOLTAGE_AMPS_Y_OFFSET = 8  # Space below battery for voltage/amps
VOLTAGE_AMPS_FONT_SIZE = 24  # Font size for voltage and amps
VOLTAGE_AMPS_SPACING = 20  # Space between voltage and amps

# Colors
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
    
  def _should_render(self) -> bool:
    """Check if battery gauge should be rendered"""
    # Only render if hybrid drive overlay is enabled and battery data is available
    if not self._params.get_bool("FordPrefHybridDriveOverlay", default=False):
      return False
    
    sm = ui_state.sm
    try:
      # Check if message exists and is recent enough
      if "carStateBP" not in sm.recv_frame or sm.recv_frame["carStateBP"] < ui_state.started_frame:
        return False
      
      car_state_bp = sm['carStateBP']
      return car_state_bp.hybridBattery.dataAvailable
    except (KeyError, AttributeError):
      return False
  
  def _get_battery_data(self):
    """Get battery data from carStateBP message"""
    sm = ui_state.sm
    try:
      car_state_bp = sm['carStateBP']
      battery = car_state_bp.hybridBattery
      return {
        'soc': battery.socActual,  # 0-100
        'voltage': battery.voltActual,  # volts
        'amps': battery.ampsActual,  # amps (positive = charging, negative = discharging)
        'soc_min': battery.socMinPerc,
        'soc_max': battery.socMaxPerc,
      }
    except (KeyError, AttributeError):
      return None
  
  def _get_battery_fill_color(self, soc: float) -> rl.Color:
    """Get battery fill color based on SOC"""
    if soc < 20:
      return BATTERY_LOW_COLOR
    elif soc < 50:
      return BATTERY_MID_COLOR
    else:
      return BATTERY_HIGH_COLOR
  
  def _render(self, rect: rl.Rectangle, left_offset: int = 0) -> None:
    """Render the battery gauge
    
    Args:
        rect: Rectangle defining the rendering area
        left_offset: Left offset to account for confidence ball or other UI elements
    """
    try:
      if not self._should_render():
        return
      
      battery_data = self._get_battery_data()
      if battery_data is None:
        return
      
      soc = battery_data['soc']
      voltage = battery_data['voltage']
      amps = battery_data['amps']
      
      # Calculate battery position (accounting for left offset)
      x = rect.x + BATTERY_X_OFFSET + left_offset
      y = rect.y + BATTERY_Y_OFFSET
      
      # Draw battery body (rounded rectangle)
      battery_body = rl.Rectangle(x, y, BATTERY_WIDTH, BATTERY_HEIGHT)
      
      # Draw battery background
      rl.draw_rectangle_rounded(battery_body, BATTERY_ROUNDNESS, 10, BATTERY_BG_COLOR)
      
      # Draw battery fill based on SOC
      fill_width = int(BATTERY_WIDTH * (soc / 100.0))
      if fill_width > 0:
        fill_rect = rl.Rectangle(x, y, fill_width, BATTERY_HEIGHT)
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
      soc_text = f"{int(soc)}%"
      soc_text_size = measure_text_cached(self._font_bold, soc_text, SOC_FONT_SIZE)
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
      
      # Draw voltage and amps below battery
      voltage_text = f"{voltage:.1f}V"
      amps_text = f"{amps:+.1f}A"  # + sign for positive, - for negative
      
      voltage_text_size = measure_text_cached(self._font_medium, voltage_text, VOLTAGE_AMPS_FONT_SIZE)
      amps_text_size = measure_text_cached(self._font_medium, amps_text, VOLTAGE_AMPS_FONT_SIZE)
      
      # Position voltage on left, amps on right
      voltage_x = x
      amps_x = x + BATTERY_WIDTH - amps_text_size.x
      
      info_y = y + BATTERY_HEIGHT + VOLTAGE_AMPS_Y_OFFSET
      
      # Draw voltage (left side)
      rl.draw_text_ex(
        self._font_medium,
        voltage_text,
        rl.Vector2(voltage_x, info_y),
        VOLTAGE_AMPS_FONT_SIZE,
        0,
        TEXT_COLOR
      )
      
      # Draw amps (right side) with color coding
      amps_color = CHARGING_COLOR if amps > 0 else DISCHARGING_COLOR if amps < 0 else TEXT_COLOR
      rl.draw_text_ex(
        self._font_medium,
        amps_text,
        rl.Vector2(amps_x, info_y),
        VOLTAGE_AMPS_FONT_SIZE,
        0,
        amps_color
      )
    except Exception:
      # Silently fail if there's any error during rendering to prevent UI crash
      # This can happen in replay mode if message structure differs or data is missing
      return
