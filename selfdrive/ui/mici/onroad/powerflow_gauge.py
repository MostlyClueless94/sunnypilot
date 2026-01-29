import numpy as np
import pyray as rl
import math
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.widgets import Widget
from openpilot.selfdrive.ui.mici.onroad import blend_colors
from openpilot.system.ui.lib.shader_polygon import draw_polygon, Gradient
from opendbc.car.ford.helpers import get_hev_power_flow_text, get_hev_engine_on_reason_text
from openpilot.common.filter_simple import FirstOrderFilter

SEGMENTS = 50
SMOOTHING = 0.12
DEMO = False

# Angles (radians)
BOTTOM = math.radians(90)
TOP = math.radians(-90)
POWERFLOW_REGEN_COLOR = rl.Color(100, 255, 100, 255)
POWERFLOW_DEMAND_COLOR = rl.Color(100, 150, 255, 255)

class MiciPowerflowGauge(Widget):
  """Widget to display powerflow gauge as an arch above the torque bar"""
  RADIUS = 20

  def __init__(self):
    super().__init__()
    self._value = 0
    self._inc = 0.01
    self._powerflow_filter = FirstOrderFilter(0.0, 0.0, 1.0 / gui_app.target_fps * 10)
    self._power_flow_mode_value = 0
    self._engine_on_reason_value = 0
    self._top_angle = -90
    if DEMO:
       self._demo_value = 0.0
       self._demo_inc = 0.01

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

      # Store current power flow mode and engine on reason for text display
      self._power_flow_mode_value = car_state_bp.hybridDrive.powerFlowModeValue
    except (KeyError, AttributeError, TypeError):
      self._power_flow_mode_value = 0

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
    if not self._should_render() and not DEMO:
      return

    if DEMO:
      self._demo_value += self._demo_inc
      if self._demo_value > 1.0 or self._demo_value < -1.0:
        self._demo_inc *= -1

    self._center = rl.Vector2(rect.x + rect.width // 2, rect.y + rect.height // 2)
    self._outer_radius = rect.width // 2
    self._inner_radius = self._outer_radius - self.RADIUS * 1.1

    self._value += self._inc
    if self._value > 1.0 or self._value < -1.0:
        self._inc *= -1

    if DEMO:
      self.draw_circular_gauge(self._demo_value)
    else:
      self.draw_circular_gauge(self._powerflow_filter.x)

  def draw_arc_segment(self, angle, color):
    x1 = self._center.x + math.cos(angle) * self._inner_radius
    y1 = self._center.y + math.sin(angle) * self._inner_radius
    x2 = self._center.x + math.cos(angle) * self._outer_radius
    y2 = self._center.y + math.sin(angle) * self._outer_radius

    rl.draw_line_ex(
        rl.Vector2(x1, y1),
        rl.Vector2(x2, y2),
        6,
        color
    )

  def draw_circular_gauge(self, value):
    # --- Regen (left side) ---
    if value < 0:
        active = abs(value)
        for i in range(SEGMENTS):
            t = i / (SEGMENTS - 1)
            if t >= active:
                break

            angle = -TOP + t * (BOTTOM - TOP)
            self.draw_arc_segment(angle, POWERFLOW_REGEN_COLOR)

    # --- Throttle (right side) ---
    if value > 0:
        active = value
        for i in range(SEGMENTS):
            t = i / (SEGMENTS - 1)
            if t >= active:
                break

            angle = BOTTOM + t * (TOP - BOTTOM)
            self.draw_arc_segment(angle, POWERFLOW_DEMAND_COLOR)