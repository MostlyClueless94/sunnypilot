import numpy as np
import pyray as rl

from openpilot.selfdrive.ui.mici.onroad.model_renderer import ModelRenderer
from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import STOCK_LAT_ONLY_COLOR, get_dynamic_edge_color
from openpilot.selfdrive.ui.ui_state import ui_state, UIStatus
from openpilot.system.ui.lib.shader_polygon import draw_polygon


LANE_LINE_COLORS_BP = {
  UIStatus.DISENGAGED: rl.Color(0, 0, 0, 255),
  UIStatus.LAT_ONLY: STOCK_LAT_ONLY_COLOR,
  UIStatus.LONG_ONLY: rl.Color(0, 255, 80, 255),
  UIStatus.ENGAGED: rl.Color(0, 255, 80, 255),
  UIStatus.OVERRIDE: rl.Color(145, 155, 149, 255),
}
OUTER_LANE_LINE_COLOR_BP = rl.Color(255, 255, 255, 255)
ROAD_EDGE_COLOR_BP = rl.Color(255, 0, 0, 255)


class ModelRendererBP(ModelRenderer):
  def __init__(self):
    super().__init__()
    self._rainbow_v = 20

  def _get_lane_line_color(self, prob: float, is_current_lane: bool) -> rl.Color:
    if ui_state.status == UIStatus.DISENGAGED:
      return LANE_LINE_COLORS_BP[UIStatus.DISENGAGED]

    if not is_current_lane:
      return OUTER_LANE_LINE_COLOR_BP

    if ui_state.status == UIStatus.LAT_ONLY and ui_state.dynamic_path_color:
      base = get_dynamic_edge_color(UIStatus.LAT_ONLY, ui_state.dynamic_path_color_palette)
    else:
      base = LANE_LINE_COLORS_BP.get(ui_state.status, LANE_LINE_COLORS_BP[UIStatus.DISENGAGED])

    brightness = np.interp(prob, [0.0, 0.5, 1.0], [0.4, 0.7, 1.0])
    return rl.Color(int(base.r * brightness), int(base.g * brightness), int(base.b * brightness), 255)

  def _draw_lane_lines(self):
    self._draw_enhanced_lane_lines()

  def _draw_enhanced_lane_lines(self):
    for i, lane_line in enumerate(self._lane_lines):
      if lane_line.projected_points.size == 0 or self._lane_line_probs[i] < 0.4:
        continue

      base_alpha = np.clip(self._lane_line_probs[i] * 0.8, 0.3, 0.8)
      is_current_lane = i in (1, 2)
      if not is_current_lane:
        base_alpha *= 0.4

      base_color = self._get_lane_line_color(float(self._lane_line_probs[i]), is_current_lane)
      color = rl.Color(base_color.r, base_color.g, base_color.b, int(base_alpha * 255))
      draw_polygon(self._rect, lane_line.projected_points, color)

    self._draw_lane_glow_effects()

    for i, road_edge in enumerate(self._road_edges):
      if road_edge.projected_points.size == 0:
        continue

      edge_alpha = np.clip(1.0 - self._road_edge_stds[i], 0.0, 1.0) * 0.6
      color = rl.Color(ROAD_EDGE_COLOR_BP.r, ROAD_EDGE_COLOR_BP.g, ROAD_EDGE_COLOR_BP.b, int(edge_alpha * 255))
      draw_polygon(self._rect, road_edge.projected_points, color)

    self._draw_road_edge_glow_effects()

  def _draw_lane_glow_effects(self):
    glow_widths = [20.0, 12.0, 6.0]
    glow_alphas = [0.05, 0.10, 0.20]

    for i, lane_line in enumerate(self._lane_lines):
      if lane_line.projected_points.size == 0 or self._lane_line_probs[i] < 0.4:
        continue

      base_alpha = np.clip(self._lane_line_probs[i] * 0.8, 0.3, 0.8)
      is_current_lane = i in (1, 2)
      if not is_current_lane:
        base_alpha *= 0.4

      base_color = self._get_lane_line_color(float(self._lane_line_probs[i]), is_current_lane)
      for glow_width, glow_alpha in zip(glow_widths, glow_alphas, strict=True):
        expanded_points = self._expand_polygon(lane_line.projected_points, glow_width)
        if expanded_points.size == 0:
          continue

        color = rl.Color(base_color.r, base_color.g, base_color.b, int(base_alpha * glow_alpha * 255))
        draw_polygon(self._rect, expanded_points, color)

  def _draw_road_edge_glow_effects(self):
    glow_widths = [28.0, 18.0, 10.0]
    glow_alphas = [0.03, 0.07, 0.15]

    for i, road_edge in enumerate(self._road_edges):
      if road_edge.projected_points.size == 0:
        continue

      edge_alpha = np.clip(1.0 - self._road_edge_stds[i], 0.0, 1.0)
      if edge_alpha < 0.3:
        continue

      for glow_width, glow_alpha in zip(glow_widths, glow_alphas, strict=True):
        expanded_points = self._expand_polygon(road_edge.projected_points, glow_width)
        if expanded_points.size == 0:
          continue

        color = rl.Color(ROAD_EDGE_COLOR_BP.r, ROAD_EDGE_COLOR_BP.g, ROAD_EDGE_COLOR_BP.b, int(edge_alpha * glow_alpha * 255))
        draw_polygon(self._rect, expanded_points, color)

  def _expand_polygon(self, points: np.ndarray, width: float) -> np.ndarray:
    if points.size == 0 or len(points) < 4:
      return np.empty((0, 2), dtype=np.float32)

    n = len(points)
    half = n // 2
    local_widths = np.empty(half, dtype=np.float32)

    for i in range(half):
      local_widths[i] = np.linalg.norm(points[n - 1 - i] - points[i])

    max_width = np.max(local_widths)
    if max_width < 1e-6:
      return np.empty((0, 2), dtype=np.float32)

    scales = np.empty(n, dtype=np.float32)
    for i in range(half):
      scale = local_widths[i] / max_width
      scales[i] = scale
      scales[n - 1 - i] = scale

    expanded = []
    for i in range(n):
      prev_idx = (i - 1) % n
      next_idx = (i + 1) % n
      p_prev = points[prev_idx]
      p_curr = points[i]
      p_next = points[next_idx]
      edge1 = p_curr - p_prev
      edge2 = p_next - p_curr
      len1 = np.linalg.norm(edge1)
      len2 = np.linalg.norm(edge2)
      if len1 > 1e-6:
        edge1 = edge1 / len1
      if len2 > 1e-6:
        edge2 = edge2 / len2
      normal1 = np.array([-edge1[1], edge1[0]])
      normal2 = np.array([-edge2[1], edge2[0]])
      normal = (normal1 + normal2) / 2.0
      normal_len = np.linalg.norm(normal)
      if normal_len > 1e-6:
        normal = normal / normal_len
      expanded.append(p_curr + normal * width * scales[i])

    return np.array(expanded, dtype=np.float32)

  def _draw_path(self):
    if not self._path.projected_points.size:
      return

    if (ui_state.rainbow_path and not ui_state.dynamic_path_color and
        not ui_state.custom_model_path_color and not self._experimental_mode):
      self._rainbow_v = np.clip(ui_state.sm["carState"].vEgo, 2.5, 35) / 30
      draw_polygon(self._rect, self._path.projected_points, rainbow=True, rainbow_v=self._rainbow_v)
    elif self._active_path_gradient is not None:
      draw_polygon(self._rect, self._path.projected_points, gradient=self._active_path_gradient)
    else:
      draw_polygon(self._rect, self._path.projected_points, self._active_path_color)

    self._draw_path_edges()

  def _draw_path_edges(self):
    if not self._path.projected_points.size:
      return

    points = self._path.projected_points
    mid_point = len(points) // 2
    if mid_point < 2:
      return

    left_edge = points[:mid_point]
    right_edge = points[mid_point:][::-1]

    for i in range(len(left_edge) - 1):
      rl.draw_line_ex(
        rl.Vector2(left_edge[i][0], left_edge[i][1]),
        rl.Vector2(left_edge[i + 1][0], left_edge[i + 1][1]),
        4.0,
        self._active_path_edge_color,
      )

    for i in range(len(right_edge) - 1):
      rl.draw_line_ex(
        rl.Vector2(right_edge[i][0], right_edge[i][1]),
        rl.Vector2(right_edge[i + 1][0], right_edge[i + 1][1]),
        4.0,
        self._active_path_edge_color,
      )

    if len(left_edge) > 0 and len(right_edge) > 0:
      rl.draw_line_ex(
        rl.Vector2(left_edge[-1][0], left_edge[-1][1]),
        rl.Vector2(right_edge[-1][0], right_edge[-1][1]),
        4.0,
        self._active_path_edge_color,
      )
