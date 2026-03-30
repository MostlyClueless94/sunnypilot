"""
BluePilot-inspired chevron metrics renderer adapted for the stable sunnypilot UI.
"""
import numpy as np
import pyray as rl

from openpilot.selfdrive.ui.sunnypilot.onroad.chevron_metrics import ChevronMetrics, ChevronOptions
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.text_measure import measure_text_cached

INVERT_UNDER_M = 100.0 * 0.3048
NORMAL_OVER_M = 125.0 * 0.3048
LEAD_GLOW = rl.Color(218, 202, 37, 255)
LEAD_BORDER = rl.Color(201, 34, 49, 255)


class ChevronMetricsBP(ChevronMetrics):
  def __init__(self, scale: float = 1.0, inverted_top_offset_ratio: float = 0.32):
    super().__init__()
    self._scale = scale
    self._inverted_mode = False
    self._inverted_top_offset_ratio = inverted_top_offset_ratio

  def should_render(self) -> bool:
    return ui_state.chevron_metrics != ChevronOptions.OFF and self._lead_status_alpha > 0.0

  def _draw_lead(self, lead_data, lead_vehicle, v_ego: float, rect: rl.Rectangle):
    if not self.should_render():
      return

    d_rel = lead_data.dRel
    v_rel = lead_data.vRel

    if not lead_vehicle.chevron or len(lead_vehicle.chevron) < 3:
      return

    text_lines = self._build_text_lines(d_rel, v_rel, v_ego)
    if not text_lines:
      return

    self._render_text_lines_bp(text_lines, lead_vehicle, rect, self._inverted_mode)

  def _render_text_lines_bp(self, text_lines: list[str], lead_vehicle, rect: rl.Rectangle, inverted: bool):
    chevron_h = max(28, int(40 * self._scale))
    font_size = max(30, int(60 * self._scale))
    padding = max(10, int(12 * self._scale))
    box_spacing = max(10, int(15 * self._scale))
    border_thickness = max(2, int(6 * self._scale))
    margin = 20
    alpha = int(255 * self._lead_status_alpha)
    text_color = rl.Color(255, 255, 255, alpha)
    shadow_color = rl.Color(0, 0, 0, int(200 * self._lead_status_alpha))
    box_color = rl.Color(40, 40, 40, int(220 * self._lead_status_alpha))
    border_color = rl.Color(LEAD_BORDER.r, LEAD_BORDER.g, LEAD_BORDER.b, alpha)

    chevron_x = lead_vehicle.chevron[1][0]
    chevron_y = lead_vehicle.chevron[1][1]

    text_sizes = [measure_text_cached(self._font, line, font_size, 0) for line in text_lines]
    total_width = sum(text_size.x + (padding * 2) for text_size in text_sizes)
    total_width += box_spacing * max(0, len(text_lines) - 1)
    text_height = text_sizes[0].y if text_sizes else font_size
    box_height = text_height + (padding * 2)

    center_x = rect.x + rect.width / 2 if inverted else chevron_x
    start_x = np.clip(center_x - total_width / 2, rect.x + margin, rect.x + rect.width - margin - total_width)
    y = rect.y + rect.height * self._inverted_top_offset_ratio if inverted else chevron_y + chevron_h

    box_rects: list[rl.Rectangle] = []
    current_x = start_x
    for line, text_size in zip(text_lines, text_sizes):
      box_width = text_size.x + (padding * 2)
      box_rect = rl.Rectangle(int(current_x), int(y), box_width, box_height)
      box_rects.append(box_rect)
      rl.draw_rectangle_rounded(box_rect, 0.2, 10, box_color)
      rl.draw_rectangle_rounded_lines_ex(box_rect, 0.2, 10, border_thickness, border_color)

      text_x = int(current_x + padding)
      text_y = int(y + padding)
      rl.draw_text_ex(self._font, line, rl.Vector2(text_x + 2, text_y + 2), font_size, 0, shadow_color)
      rl.draw_text_ex(self._font, line, rl.Vector2(text_x, text_y), font_size, 0, text_color)
      current_x += box_width + box_spacing

    box = box_rects[0] if len(box_rects) == 1 else box_rects[len(box_rects) // 2]
    center_x = box.x + box.width / 2
    if inverted:
      base_y = y + box_height
      apex_y = base_y + chevron_h
      chevron = [
        rl.Vector2(center_x, apex_y),
        rl.Vector2(box.x, base_y),
        rl.Vector2(box.x + box.width, base_y),
      ]
    else:
      chevron = [
        rl.Vector2(center_x, y - chevron_h),
        rl.Vector2(box.x, y),
        rl.Vector2(box.x + box.width, y),
      ]

    rl.draw_triangle_fan(chevron, len(chevron), border_color)
    rl.draw_line_ex(chevron[0], chevron[1], border_thickness, LEAD_GLOW)
    rl.draw_line_ex(chevron[1], chevron[2], border_thickness, LEAD_GLOW)
    rl.draw_line_ex(chevron[2], chevron[0], border_thickness, LEAD_GLOW)
    radius = border_thickness / 2
    rl.draw_circle_v(chevron[0], radius, LEAD_GLOW)
    rl.draw_circle_v(chevron[1], radius, LEAD_GLOW)
    rl.draw_circle_v(chevron[2], radius, LEAD_GLOW)

  def draw_lead_status(self, sm, radar_state, rect, lead_vehicles):
    lead_one = radar_state.leadOne
    lead_two = radar_state.leadTwo

    has_lead_one = lead_one.status if lead_one else False
    has_lead_two = lead_two.status if lead_two else False
    self.update_alpha(has_lead_one or has_lead_two)

    if not self.should_render():
      return

    if has_lead_one or has_lead_two:
      d_rel_closest = min(
        lead_one.dRel if has_lead_one else float("inf"),
        lead_two.dRel if has_lead_two else float("inf"),
      )
      if d_rel_closest < INVERT_UNDER_M:
        self._inverted_mode = True
      elif d_rel_closest > NORMAL_OVER_M:
        self._inverted_mode = False

    v_ego = sm["carState"].vEgo
    if has_lead_one and lead_vehicles[0].chevron:
      self._draw_lead(lead_one, lead_vehicles[0], v_ego, rect)
    if has_lead_two and lead_vehicles[1].chevron:
      d_rel_diff = abs(lead_one.dRel - lead_two.dRel) if has_lead_one else float("inf")
      if d_rel_diff > 3.0:
        self._draw_lead(lead_two, lead_vehicles[1], v_ego, rect)
