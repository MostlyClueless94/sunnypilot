"""
BluePilot Torque Bar Renderer

A standalone torque bar for the BP onroad UI, derived from sunnypilot's TorqueBar
but fully separate for easier maintenance and upstream syncing.

Key differences from upstream:
- Smoother filters (higher time constants) to reduce visual jitter/glitchiness
- Supports gauge_height_offset to position the arc above battery/power flow gauges
- Uses lateralUncertainty from controllerStateBP for angleState vehicles (Tesla etc.)
- Softer color transitions and more refined visual feel
"""
import math
from functools import wraps
from collections import OrderedDict

import numpy as np
import pyray as rl
from opendbc.car import ACCELERATION_DUE_TO_GRAVITY
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.selfdrive.ui.mici.onroad import blend_colors
from openpilot.selfdrive.ui.ui_state import ui_state, UIStatus
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.shader_polygon import draw_polygon, Gradient

# Arc geometry
TORQUE_ANGLE_SPAN = 12.7


def _quantized_lru_cache(maxsize=128):
  def decorator(func):
    cache = OrderedDict()
    @wraps(func)
    def wrapper(cx, cy, r_mid, thickness, a0_deg, a1_deg, **kwargs):
      key = (round(cx), round(cy), round(r_mid),
             round(thickness),
             round(a0_deg * 10) / 10,
             round(a1_deg * 10) / 10,
             tuple(sorted(kwargs.items())))
      if key in cache:
        cache.move_to_end(key)
      else:
        if len(cache) >= maxsize:
          cache.popitem(last=False)
        result = func(cx, cy, r_mid, thickness, a0_deg, a1_deg, **kwargs)
        cache[key] = result
      return cache[key]
    return wrapper
  return decorator


@_quantized_lru_cache(maxsize=256)
def _arc_bar_pts(cx: float, cy: float,
                 r_mid: float, thickness: float,
                 a0_deg: float, a1_deg: float,
                 *, max_points: int = 100, cap_segs: int = 10,
                 cap_radius: float = 7, px_per_seg: float = 2.0) -> np.ndarray:
  """Return Nx2 np.float32 points for a closed polygon (rounded thick arc).

  Duplicated from upstream torque_bar.arc_bar_pts to keep BP fully independent.
  """
  def get_cap(left: bool, a_deg: float):
    nx, ny = math.cos(math.radians(a_deg)), math.sin(math.radians(a_deg))
    tx, ty = -ny, nx
    mx, my = cx + nx * r_mid, cy + ny * r_mid

    ex = mx + nx * (half - cap_radius)
    ey = my + ny * (half - cap_radius)

    if not left:
      alpha = np.deg2rad(np.linspace(90, 0, cap_segs + 2))[1:-1]
    else:
      alpha = np.deg2rad(np.linspace(180, 90, cap_segs + 2))[1:-1]
    cap_end = np.c_[ex + np.cos(alpha) * cap_radius * tx + np.sin(alpha) * cap_radius * nx,
                    ey + np.cos(alpha) * cap_radius * ty + np.sin(alpha) * cap_radius * ny]

    ex2 = mx + nx * (-half + cap_radius)
    ey2 = my + ny * (-half + cap_radius)

    if not left:
      alpha2 = np.deg2rad(np.linspace(0, -90, cap_segs + 1))[:-1]
    else:
      alpha2 = np.deg2rad(np.linspace(90 - 90 - 90, 0 - 90 - 90, cap_segs + 1))[:-1]
    cap_end_bot = np.c_[ex2 + np.cos(alpha2) * cap_radius * tx + np.sin(alpha2) * cap_radius * nx,
                        ey2 + np.cos(alpha2) * cap_radius * ty + np.sin(alpha2) * cap_radius * ny]

    if not left:
      cap_end = np.vstack((cap_end, cap_end_bot))
    else:
      cap_end = np.vstack((cap_end_bot, cap_end))
    return cap_end

  if a1_deg < a0_deg:
    a0_deg, a1_deg = a1_deg, a0_deg
  half = thickness * 0.5
  cap_radius = min(cap_radius, half)
  span = max(1e-3, a1_deg - a0_deg)

  arc_len = r_mid * math.radians(span)
  arc_segs = max(6, int(arc_len / px_per_seg))
  max_arc = (max_points - (4 * cap_segs + 3)) // 2
  arc_segs = max(6, min(arc_segs, max_arc))

  ang_o = np.deg2rad(np.linspace(a0_deg, a1_deg, arc_segs + 1))
  outer = np.c_[cx + np.cos(ang_o) * (r_mid + half),
                cy + np.sin(ang_o) * (r_mid + half)]

  cap_end = get_cap(False, a1_deg)

  ang_i = np.deg2rad(np.linspace(a1_deg, a0_deg, arc_segs + 1))
  inner = np.c_[cx + np.cos(ang_i) * (r_mid - half),
                cy + np.sin(ang_i) * (r_mid - half)]

  cap_start = get_cap(True, a0_deg)

  pts = np.vstack((outer, cap_end, inner, cap_start, outer[:1])).astype(np.float32)
  pts = np.roll(pts, cap_segs, axis=0)
  return pts


class TorqueBarRendererBP:
  """BluePilot torque bar renderer — smoother, repositionable, independent of upstream.

  This is NOT a Widget subclass. It's rendered explicitly by the augmented road view
  so we have full control over when and where it draws relative to gauges and alerts.
  """

  def __init__(self, scale: float = 3.0):
    self._scale = scale
    # Smoother filters: higher rc = slower response = less jittery
    # Upstream uses rc=0.1 for both; we use 0.2/0.15 for a calmer feel
    self._torque_filter = FirstOrderFilter(0.0, 0.2, 1.0 / gui_app.target_fps)
    self._alpha_filter = FirstOrderFilter(0.0, 0.15, 1.0 / gui_app.target_fps)

  def update(self):
    """Update torque state from car messages. Call once per frame."""
    # BluePilot: Use lateral uncertainty from controllerStateBP on angleState vehicles
    try:
      if ui_state.sm['controlsState'].lateralControlState.which() == 'angleState':
        if ui_state.sm.valid.get("controllerStateBP", False):
          try:
            lateral_uncertainty = ui_state.sm['controllerStateBP'].lateralUncertainty
            self._torque_filter.update(min(max(lateral_uncertainty, -1.0), 1.0))
            self._update_alpha()
            return
          except (KeyError, AttributeError):
            pass

        # angleState fallback: acceleration-based
        controls_state = ui_state.sm['controlsState']
        car_state = ui_state.sm['carState']
        live_parameters = ui_state.sm['liveParameters']
        lateral_acceleration = controls_state.curvature * car_state.vEgo ** 2 - live_parameters.roll * ACCELERATION_DUE_TO_GRAVITY
        max_lateral_acceleration = 3
        actual_lateral_accel = controls_state.curvature * car_state.vEgo ** 2
        desired_lateral_accel = controls_state.desiredCurvature * car_state.vEgo ** 2
        accel_diff = desired_lateral_accel - actual_lateral_accel
        self._torque_filter.update(min(max(lateral_acceleration / max_lateral_acceleration + accel_diff, -1.0), 1.0))
      else:
        # Non-angleState: use actuator torque output
        self._torque_filter.update(-ui_state.sm['carOutput'].actuatorsOutput.torque)
    except (KeyError, AttributeError):
      pass

    self._update_alpha()

  def _update_alpha(self):
    """Update visibility alpha based on engagement status."""
    self._alpha_filter.update(ui_state.status not in (UIStatus.DISENGAGED, UIStatus.LONG_ONLY))

  def render(self, rect: rl.Rectangle, gauge_height_offset: float = 0.0):
    """Render the torque bar arc.

    Args:
        rect: The UI rect to position the arc within.
        gauge_height_offset: Pixels to subtract from rect height to push the arc above gauges.
    """
    if not ui_state.torque_bar:
      return

    # Shrink effective rect to push arc above the gauge area
    effective_rect = rect
    if gauge_height_offset > 0:
      effective_rect = rl.Rectangle(rect.x, rect.y, rect.width, rect.height - gauge_height_offset)

    torque = self._torque_filter.x
    alpha = self._alpha_filter.x

    if alpha < 0.01:
      return

    abs_torque = abs(torque)

    # Arc geometry — offset/height scale with torque magnitude
    # BluePilot: Reduced max height vs upstream (56→28) for a subtler, less exaggerated look
    # at high torque. The bar grows slightly thicker but doesn't balloon.
    torque_line_offset = np.interp(abs_torque, [0.5, 1.0], [22 * self._scale, 26 * self._scale])
    torque_line_height = np.interp(abs_torque, [0.5, 1.0], [14 * self._scale, 28 * self._scale])

    # Background alpha varies with torque magnitude
    bg_alpha = np.interp(abs_torque, [0.5, 1.0], [0.25, 0.5])

    # Colors depend on engagement status
    is_active = ui_state.status in (UIStatus.ENGAGED, UIStatus.LAT_ONLY)

    if is_active:
      bg_color = rl.Color(255, 255, 255, int(255 * bg_alpha * alpha))
    else:
      bg_color = rl.Color(255, 255, 255, int(255 * 0.15 * alpha))

    # Arc center and radius
    torque_line_radius = 1200 * self._scale
    top_angle = -90
    bg_angle_span = alpha * TORQUE_ANGLE_SPAN
    start_angle = top_angle - bg_angle_span / 2
    end_angle = top_angle + bg_angle_span / 2
    mid_r = torque_line_radius + torque_line_height / 2

    cx = effective_rect.x + effective_rect.width / 2 + 8
    cy = effective_rect.y + effective_rect.height + torque_line_radius - torque_line_offset

    # Background arc
    bg_pts = _arc_bar_pts(cx, cy, mid_r, torque_line_height, start_angle, end_angle,
                          cap_radius=7 * self._scale)
    draw_polygon(effective_rect, bg_pts, color=bg_color)

    # Active torque fill arc
    a0 = top_angle
    a1 = a0 + bg_angle_span / 2 * torque
    fill_pts = _arc_bar_pts(cx, cy, mid_r, torque_line_height, a0, a1,
                            cap_radius=7 * self._scale)

    # Gradient from center to ~65% of the arc width
    start_grad_pt = cx / effective_rect.width
    if torque < 0:
      end_grad_pt = (cx * (1 - 0.65) + (min(bg_pts[:, 0]) * 0.65)) / effective_rect.width
    else:
      end_grad_pt = (cx * (1 - 0.65) + (max(bg_pts[:, 0]) * 0.65)) / effective_rect.width

    if is_active:
      # Smooth color transition: white → yellow/orange at high torque
      high_blend = max(0.0, abs_torque - 0.75) * 4
      start_color = blend_colors(
        rl.Color(255, 255, 255, int(255 * 0.9 * alpha)),
        rl.Color(255, 200, 0, int(255 * alpha)),
        high_blend,
      )
      end_color = blend_colors(
        rl.Color(255, 255, 255, int(255 * 0.9 * alpha)),
        rl.Color(255, 115, 0, int(255 * alpha)),
        high_blend,
      )
    else:
      start_color = end_color = rl.Color(255, 255, 255, int(255 * 0.35 * alpha))

    gradient = Gradient(
      start=(start_grad_pt, 0),
      end=(end_grad_pt, 0),
      colors=[start_color, end_color],
      stops=[0.0, 1.0],
    )
    draw_polygon(effective_rect, fill_pts, gradient=gradient)

    # Center dot (only at low torque)
    if abs_torque < 0.5:
      dot_y = effective_rect.y + effective_rect.height - torque_line_offset - torque_line_height / 2
      rl.draw_circle(int(cx), int(dot_y), 10 // 2 * self._scale,
                     rl.Color(182, 182, 182, int(255 * 0.9 * alpha)))
