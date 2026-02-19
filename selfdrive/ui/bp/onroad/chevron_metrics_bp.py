import numpy as np
import pyray as rl
from openpilot.common.constants import CV
from openpilot.common.params import Params
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.sunnypilot.onroad.chevron_metrics import ChevronMetrics, ChevronOptions
from openpilot.system.ui.lib.text_measure import measure_text_cached

# BluePilot: Deadband thresholds for close-proximity mode (in meters)
CLOSE_MODE_THRESHOLD_M = 50.0 * 0.3048   # 50 feet = 15.24 meters
NORMAL_MODE_THRESHOLD_M = 60.0 * 0.3048  # 60 feet = 18.29 meters

# Deadband thresholds when powerflow gauge is active (wider to avoid overlap)
POWERFLOW_UPPER_THRESHOLD_M = 150.0 * 0.3048  # 150 feet = 45.72 meters
POWERFLOW_LOWER_THRESHOLD_M = 100.0 * 0.3048  # 100 feet = 30.48 meters

# BluePilot: Border colors for radar vs vision leads
RADAR_BORDER_COLOR_BASE = rl.Color(0, 100, 200, 255)   # Blue for radar
VISION_BORDER_COLOR_BASE = rl.Color(201, 34, 49, 255)   # Red for vision


class ChevronMetricsBP(ChevronMetrics):
  """BluePilot ChevronMetrics with horizontal boxed layout and radar/vision colored borders."""

  def __init__(self):
    super().__init__()
    self._bp_params = Params()
    self._close_mode: bool = False

    # Set by ModelRendererBP before calling draw_lead_status
    self.ford_overlay_enabled: bool = False
    self.lead_is_radar: list[bool] = [False, False]

  def should_render(self) -> bool:
    # Render if chevron metrics is enabled OR if Ford overlay is enabled
    return (ui_state.chevron_metrics != ChevronOptions.OFF or self.ford_overlay_enabled) and self._lead_status_alpha > 0.0

  def _draw_lead(self, lead_data, lead_vehicle, v_ego: float, rect: rl.Rectangle, lead_index: int = 0):
    """Draw lead vehicle status with close-proximity mode and boxed layout."""
    if not self.should_render():
      return

    d_rel = lead_data.dRel
    v_rel = lead_data.vRel

    if not lead_vehicle.chevron or len(lead_vehicle.chevron) < 3:
      return

    # BluePilot: Deadband logic for close-proximity positioning
    powerflow_enabled = self._bp_params.get_bool("FordPrefHybridPowerFlow")

    if powerflow_enabled:
      if d_rel < POWERFLOW_UPPER_THRESHOLD_M:
        self._close_mode = True
      elif d_rel > POWERFLOW_LOWER_THRESHOLD_M:
        self._close_mode = False
    else:
      if d_rel < CLOSE_MODE_THRESHOLD_M:
        self._close_mode = True
      elif d_rel > NORMAL_MODE_THRESHOLD_M:
        self._close_mode = False

    # Extract chevron geometry
    chevron_point_0 = lead_vehicle.chevron[0]
    chevron_point_1 = lead_vehicle.chevron[1]
    chevron_point_2 = lead_vehicle.chevron[2]

    chevron_x = chevron_point_1[0]

    all_y_coords = [chevron_point_0[1], chevron_point_1[1], chevron_point_2[1]]
    chevron_top_y = min(all_y_coords)
    chevron_bottom_y = max(all_y_coords)

    sz = np.clip((25 * 30) / (d_rel / 3 + 30), 15.0, 30.0) * 2.35

    text_lines = self._build_text_lines_bp(d_rel, v_rel, v_ego)
    if not text_lines:
      return

    # Position text: below chevron normally, above chevron when in close mode
    spacing_offset = max(70, sz * 0.6)

    if self._close_mode:
      if powerflow_enabled:
        chevron_text_y = chevron_top_y - (spacing_offset * 0.85)
      else:
        upward_offset = sz * 3.0
        chevron_text_y = chevron_top_y - spacing_offset - upward_offset
    else:
      chevron_text_y = chevron_bottom_y + spacing_offset

    is_radar = self.lead_is_radar[lead_index] if lead_index < len(self.lead_is_radar) else False
    self._render_text_lines_bp(text_lines, chevron_x, chevron_text_y, sz, rect, is_radar)

  def _build_text_lines_bp(self, d_rel: float, v_rel: float, v_ego: float) -> list[str]:
    """Build text lines - Ford overlay forces all 3, otherwise respects setting."""
    if self.ford_overlay_enabled:
      # When Ford overlay is enabled, always show all 3 values
      text_lines = []

      # Distance
      val = max(0.0, d_rel)
      unit = "m" if ui_state.is_metric else "ft"
      if not ui_state.is_metric:
        val *= 3.28084
      text_lines.append(f"{val:.0f} {unit}")

      # Speed
      multiplier = CV.MS_TO_KPH if ui_state.is_metric else CV.MS_TO_MPH
      val = max(0.0, (v_rel + v_ego) * multiplier)
      unit = "km/h" if ui_state.is_metric else "mph"
      text_lines.append(f"{val:.0f} {unit}")

      # Lead time
      val = (d_rel / v_ego) if (d_rel > 0 and v_ego > 0) else 0.0
      ttc_text = f"{val:.1f} s" if (0 < val < 200) else "---"
      text_lines.append(ttc_text)

      return text_lines
    else:
      return ChevronMetrics._build_text_lines(d_rel, v_rel, v_ego)

  def _render_text_lines_bp(self, text_lines: list[str], chevron_x: float, chevron_y: float,
                            sz: float, rect: rl.Rectangle, is_radar: bool = False):
    """Render text lines with horizontal boxed layout when Ford overlay is active."""
    margin = 20
    alpha = int(255 * self._lead_status_alpha)
    text_color = rl.Color(255, 255, 255, alpha)
    shadow_color = rl.Color(0, 0, 0, int(200 * self._lead_status_alpha))

    if self.ford_overlay_enabled and len(text_lines) == 3:
      # BluePilot: Horizontal boxed layout with colored borders
      font_size = 60
      padding = 12
      box_spacing = 15
      box_color = rl.Color(40, 40, 40, int(220 * self._lead_status_alpha))

      # Measure all text sizes
      text_sizes = []
      total_width = 0
      for line in text_lines:
        text_size = measure_text_cached(self._font, line, font_size, 0)
        text_sizes.append(text_size)
        total_width += text_size.x + (padding * 2)
      total_width += box_spacing * (len(text_lines) - 1)

      # Center boxes horizontally on chevron
      start_x = chevron_x - total_width / 2
      current_x = start_x

      text_height = text_sizes[0].y if text_sizes else font_size
      box_height = text_height + (padding * 2)

      # Position based on close mode
      if self._close_mode:
        y = int(chevron_y - box_height)
      else:
        y = int(chevron_y)

      # Clamp to screen bounds
      if start_x < margin:
        start_x = margin
        current_x = margin
      elif start_x + total_width > rect.width - margin:
        start_x = rect.width - margin - total_width
        current_x = start_x

      # Border color: blue for radar, red for vision
      if is_radar:
        border_color = rl.Color(RADAR_BORDER_COLOR_BASE.r, RADAR_BORDER_COLOR_BASE.g,
                                RADAR_BORDER_COLOR_BASE.b, alpha)
      else:
        border_color = rl.Color(VISION_BORDER_COLOR_BASE.r, VISION_BORDER_COLOR_BASE.g,
                                VISION_BORDER_COLOR_BASE.b, alpha)

      border_thickness = 6

      for line, text_size in zip(text_lines, text_sizes):
        box_width = text_size.x + (padding * 2)

        # Dark grey box
        box_rect = rl.Rectangle(int(current_x), int(y), box_width, box_height)
        rl.draw_rectangle_rounded(box_rect, 0.2, 10, box_color)

        # Colored border (drawn on same rect so there's no gap)
        rl.draw_rectangle_rounded_lines_ex(box_rect, 0.2, 10, border_thickness, border_color)

        # Text centered in box
        text_x = int(current_x + padding)
        text_y_pos = int(y + padding)

        rl.draw_text_ex(self._font, line, rl.Vector2(text_x + 2, text_y_pos + 2), font_size, 0, shadow_color)
        rl.draw_text_ex(self._font, line, rl.Vector2(text_x, text_y_pos), font_size, 0, text_color)

        current_x += box_width + box_spacing
    else:
      # Fall back to base vertical stack rendering
      self._render_text_lines(text_lines, chevron_x, chevron_y, sz, rect)

  def draw_lead_status(self, sm, radar_state, rect, lead_vehicles):
    lead_one = radar_state.leadOne
    lead_two = radar_state.leadTwo

    has_lead_one = lead_one.status if lead_one else False
    has_lead_two = lead_two.status if lead_two else False

    self.update_alpha(has_lead_one or has_lead_two)

    if not self.should_render():
      return

    v_ego = sm['carState'].vEgo

    if has_lead_one and lead_vehicles[0].chevron:
      self._draw_lead(lead_one, lead_vehicles[0], v_ego, rect, lead_index=0)

    if has_lead_two and lead_vehicles[1].chevron:
      d_rel_diff = abs(lead_one.dRel - lead_two.dRel) if has_lead_one else float('inf')
      if d_rel_diff > 3.0:
        self._draw_lead(lead_two, lead_vehicles[1], v_ego, rect, lead_index=1)
