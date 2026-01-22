"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import numpy as np

import pyray as rl
from openpilot.common.constants import CV
from openpilot.common.params import Params
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached


class ChevronOptions:
  OFF = 0
  DISTANCE_ONLY = 1
  SPEED_ONLY = 2
  TTC_ONLY = 3
  ALL = 4


class ChevronMetrics:
  def __init__(self):
    self._lead_status_alpha: float = 0.0
    self._font = gui_app.font(FontWeight.SEMI_BOLD)
    self._params = Params()

  def update_alpha(self, has_lead: bool):
    """Update the alpha value for fade in/out animation"""
    if not has_lead:
      self._lead_status_alpha = max(0.0, self._lead_status_alpha - 0.05)
    else:
      self._lead_status_alpha = min(1.0, self._lead_status_alpha + 0.1)

  def should_render(self, ford_overlay_enabled: bool = False) -> bool:
    """Check if dev UI should be rendered"""
    # Render if chevron metrics is enabled OR if Ford overlay is enabled
    return (ui_state.chevron_metrics != ChevronOptions.OFF or ford_overlay_enabled) and self._lead_status_alpha > 0.0

  def _draw_lead(self, lead_data, lead_vehicle, v_ego: float, rect: rl.Rectangle, ford_overlay_enabled: bool = False):
    """Draw lead vehicle status information (distance, speed, TTC)"""
    if not self.should_render(ford_overlay_enabled):
      return

    d_rel = lead_data.dRel
    v_rel = lead_data.vRel

    if not lead_vehicle.chevron or len(lead_vehicle.chevron) < 3:
      return

    # Extract chevron points: [bottom_right, top, bottom_left]
    chevron_bottom_right = lead_vehicle.chevron[0]
    chevron_top = lead_vehicle.chevron[1]
    chevron_bottom_left = lead_vehicle.chevron[2]

    chevron_x = chevron_top[0]  # Center horizontally
    chevron_top_y = chevron_top[1]  # Top point y
    chevron_bottom_y = chevron_bottom_right[1]  # Bottom y (same for both bottom points)

    # Calculate chevron size for positioning
    sz = np.clip((25 * 30) / (d_rel / 3 + 30), 15.0, 30.0) * 2.35

    text_lines = self._build_text_lines(d_rel, v_rel, v_ego, ford_overlay_enabled)
    if not text_lines:
      return

    # Position text below chevron
    chevron_bottom_center_y = chevron_bottom_y + 20  # Position below chevron

    self._render_text_lines(text_lines, chevron_x, chevron_bottom_center_y, sz, rect, ford_overlay_enabled)

  def _build_text_lines(self, d_rel: float, v_rel: float, v_ego: float, ford_overlay_enabled: bool = False) -> list[str]:
    """Build text lines based on chevron info setting"""
    text_lines = []

    if ford_overlay_enabled:
      # When Ford overlay is enabled, show all 3 values: Distance, Speed, Time to Collision
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
      
      # Time to collision
      val = (d_rel / v_ego) if (d_rel > 0 and v_ego > 0) else 0.0
      ttc_text = f"{val:.1f} s" if (0 < val < 200) else "---"
      text_lines.append(ttc_text)
    else:
      # When Ford overlay is disabled, respect the chevron_metrics setting
      show_distance = ui_state.chevron_metrics == ChevronOptions.DISTANCE_ONLY or ui_state.chevron_metrics == ChevronOptions.ALL
      show_speed = ui_state.chevron_metrics == ChevronOptions.SPEED_ONLY or ui_state.chevron_metrics == ChevronOptions.ALL
      show_ttc = ui_state.chevron_metrics == ChevronOptions.TTC_ONLY or ui_state.chevron_metrics == ChevronOptions.ALL

      # Distance
      if show_distance:
        val = max(0.0, d_rel)
        unit = "m" if ui_state.is_metric else "ft"
        if not ui_state.is_metric:
          val *= 3.28084
        text_lines.append(f"{val:.0f} {unit}")

      # Speed
      if show_speed:
        multiplier = CV.MS_TO_KPH if ui_state.is_metric else CV.MS_TO_MPH
        val = max(0.0, (v_rel + v_ego) * multiplier)
        unit = "km/h" if ui_state.is_metric else "mph"
        text_lines.append(f"{val:.0f} {unit}")

      # Time to collision
      if show_ttc:
        val = (d_rel / v_ego) if (d_rel > 0 and v_ego > 0) else 0.0
        ttc_text = f"{val:.1f} s" if (0 < val < 200) else "---"
        text_lines.append(ttc_text)

    return text_lines

  def _render_text_lines(self, text_lines: list[str], chevron_x: float, chevron_y: float,
                         sz: float, rect: rl.Rectangle, ford_overlay_enabled: bool = False):
    """Render text lines with proper centering and positioning"""
    font_size = 60 if ford_overlay_enabled else 40
    margin = 20
    padding = 12  # Padding inside boxes
    box_spacing = 15  # Space between boxes

    alpha = int(255 * self._lead_status_alpha)
    text_color = rl.Color(255, 255, 255, alpha)
    shadow_color = rl.Color(0, 0, 0, int(200 * self._lead_status_alpha))
    box_color = rl.Color(40, 40, 40, int(220 * self._lead_status_alpha))  # Dark grey box

    if ford_overlay_enabled and len(text_lines) == 3:
      # Render all 3 values horizontally with dark grey boxes
      # Distance (left), Speed (middle), Time to Collision (right)
      
      # Measure all text sizes first
      text_sizes = []
      total_width = 0
      for line in text_lines:
        text_size = measure_text_cached(self._font, line, font_size, 0)
        text_sizes.append(text_size)
        total_width += text_size.x + (padding * 2)  # Add padding for box
      
      # Add spacing between boxes
      total_width += box_spacing * (len(text_lines) - 1)
      
      # Calculate starting x position (center all boxes on chevron)
      start_x = chevron_x - total_width / 2
      current_x = start_x
      
      # Get text height (all should be same)
      text_height = text_sizes[0].y if text_sizes else font_size
      box_height = text_height + (padding * 2)
      
      # Calculate y position (centered vertically at chevron_y)
      y = int(chevron_y - box_height / 2)
      
      # Ensure boxes stay within screen bounds
      if start_x < margin:
        start_x = margin
        current_x = margin
      elif start_x + total_width > rect.width - margin:
        start_x = rect.width - margin - total_width
        current_x = start_x
      
      # Render each value with its box
      for i, (line, text_size) in enumerate(zip(text_lines, text_sizes)):
        box_width = text_size.x + (padding * 2)
        
        # Draw dark grey box
        box_rect = rl.Rectangle(int(current_x), int(y), box_width, box_height)
        rl.draw_rectangle_rounded(box_rect, 0.2, 10, box_color)
        
        # Draw text centered in box
        text_x = int(current_x + padding)
        text_y = int(y + padding)
        
        # Draw shadow
        rl.draw_text_ex(self._font, line, rl.Vector2(text_x + 2, text_y + 2), font_size, 0, shadow_color)
        # Draw text
        rl.draw_text_ex(self._font, line, rl.Vector2(text_x, text_y), font_size, 0, text_color)
        
        # Move to next box position
        current_x += box_width + box_spacing
    else:
      # Original behavior: place text below chevron (vertical stack)
      line_height = 50
      text_y = chevron_y + sz + 15
      total_height = len(text_lines) * line_height

      # Adjust Y position if text would go off screen
      if text_y + total_height > rect.height - margin:
        y_max = min(chevron_y, rect.height - margin)
        text_y = y_max - 15 - total_height
        text_y = max(margin, text_y)

      for i, line in enumerate(text_lines):
        y = int(text_y + (i * line_height))
        if y + line_height > rect.height - margin:
          break

        # Measure actual text width for proper centering
        text_size = measure_text_cached(self._font, line, font_size, 0)
        text_width = text_size.x

        # Center the text horizontally on the chevron
        x = int(chevron_x - text_width / 2)
        x = int(np.clip(x, margin, rect.width - text_width - margin))

        # Draw shadow
        rl.draw_text_ex(self._font, line, rl.Vector2(x + 2, y + 2), font_size, 0, shadow_color)
        # Draw text
        rl.draw_text_ex(self._font, line, rl.Vector2(x, y), font_size, 0, text_color)

  def draw_lead_status(self, sm, radar_state, rect, lead_vehicles, ford_overlay_enabled: bool = False):
    lead_one = radar_state.leadOne
    lead_two = radar_state.leadTwo

    has_lead_one = lead_one.status if lead_one else False
    has_lead_two = lead_two.status if lead_two else False

    self.update_alpha(has_lead_one or has_lead_two)

    if not self.should_render(ford_overlay_enabled):
      return

    v_ego = sm['carState'].vEgo

    if has_lead_one and lead_vehicles[0].chevron:
      self._draw_lead(lead_one, lead_vehicles[0], v_ego, rect, ford_overlay_enabled)

    if has_lead_two and lead_vehicles[1].chevron:
      d_rel_diff = abs(lead_one.dRel - lead_two.dRel) if has_lead_one else float('inf')
      if d_rel_diff > 3.0:
        self._draw_lead(lead_two, lead_vehicles[1], v_ego, rect, ford_overlay_enabled)
