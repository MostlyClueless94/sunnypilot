"""
Unified Gauge Widget for BluePilot.

Combines the power flow meter and steering arc (torque bar) into one
container with shared layout math.
"""

from dataclasses import dataclass

import numpy as np
import pyray as rl

from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.common.params import Params
from openpilot.selfdrive.ui.bp.mici.onroad.torque_bar_bp import TorqueBarBP
from openpilot.selfdrive.ui.mici.onroad import blend_colors
from openpilot.selfdrive.ui.mici.onroad.torque_bar import TORQUE_ANGLE_SPAN, arc_bar_pts
from openpilot.selfdrive.ui.sunnypilot.onroad.developer_ui import DeveloperUiRenderer
from openpilot.selfdrive.ui.ui_state import UIStatus, ui_state
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.shader_polygon import Gradient, draw_polygon
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget
from opendbc.car.ford.helpers import get_hev_engine_on_reason_text, get_hev_power_flow_text

# --- Modes ---
MODE_NONE = 0
MODE_POWERFLOW_ONLY = 1
MODE_STEERING_ONLY = 2
MODE_UNIFIED = 3

# --- Steering arc constants (matching TorqueBar scale=3.0) ---
STEERING_SCALE = 3.0
STEERING_BASE_RADIUS = 1200.0 * STEERING_SCALE
STEERING_CAP_RADIUS = 7.0 * STEERING_SCALE
STEERING_MIN_HEIGHT = 14 * STEERING_SCALE
STEERING_MAX_HEIGHT = 18 * STEERING_SCALE

# --- Power flow layout constants ---
POWERFLOW_ANGLE_SPAN_UNIFIED = 16.0
POWERFLOW_ANGLE_SPAN_SOLO = 13.5
POWERFLOW_TEXT_FONT_SIZE = 44
POWERFLOW_TEXT_COLOR = rl.Color(255, 255, 255, 240)
POWERFLOW_TEXT_GAP = 30
POWERFLOW_VALUE_EPS = 0.005
POWERFLOW_UNIFIED_GAP = 26.0
POWERFLOW_SOLO_BASE_OFFSET = 95.0
POWERFLOW_THICKNESS_RATIO_UNIFIED = 0.90
POWERFLOW_IDLE_THICKNESS_RATIO = 0.78
POWERFLOW_ACTIVE_THICKNESS_RATIO = 1.10
POWERFLOW_ACTIVITY_DEADBAND = 0.03
TEXT_LETTER_SPACING = 1.0

# --- Tick marks ---
TICK_COLOR = rl.Color(200, 200, 200, 200)
TICK_LENGTH_RATIO = 0.10
TICK_ALPHA_IDLE = 115
TICK_ALPHA_ACTIVE = 190

# --- Background ---
BG_PADDING = 18
BG_STYLE_SOLID = 0
BG_STYLE_GRADIENT = 1
BG_COLOR = rl.Color(20, 20, 20, 142)

# --- Color constants ---
REGEN_COLOR = rl.Color(80, 230, 80, 255)
DEMAND_COLOR = rl.Color(80, 140, 255, 255)
CENTER_COLOR = rl.Color(255, 255, 255, 240)

# --- Anti-alias glow ---
GLOW_EXPANSION = 4
GLOW_ALPHA = 60

# --- Divider ---
DIVIDER_THICKNESS = 3
DIVIDER_COLOR = rl.Color(220, 220, 220, 110)
DIVIDER_ALPHA_IDLE = 80
DIVIDER_ALPHA_ACTIVE = 130

# --- Dynamic scaling reference ---
FULL_CONTENT_WIDTH = 2100.0
PARAM_REFRESH_FRAMES = 60


@dataclass(frozen=True)
class GaugeLayout:
  rect: rl.Rectangle
  cx: float
  cy: float
  steering_height: float
  angle_span: float
  text_size: int
  pf_thickness: float = STEERING_MIN_HEIGHT
  pf_mid: float = STEERING_BASE_RADIUS + POWERFLOW_SOLO_BASE_OFFSET + STEERING_MIN_HEIGHT / 2
  pf_outer: float = STEERING_BASE_RADIUS + POWERFLOW_SOLO_BASE_OFFSET + STEERING_MIN_HEIGHT
  pf_inner: float = STEERING_BASE_RADIUS + POWERFLOW_SOLO_BASE_OFFSET
  divider_radius: float = STEERING_BASE_RADIUS + POWERFLOW_SOLO_BASE_OFFSET + STEERING_MIN_HEIGHT + POWERFLOW_TEXT_GAP / 2
  text_radius: float = STEERING_BASE_RADIUS + POWERFLOW_SOLO_BASE_OFFSET + STEERING_MIN_HEIGHT + POWERFLOW_TEXT_GAP
  bg_top: float = STEERING_BASE_RADIUS + POWERFLOW_SOLO_BASE_OFFSET + STEERING_MIN_HEIGHT + POWERFLOW_TEXT_GAP + POWERFLOW_TEXT_FONT_SIZE
  bg_bottom: float = STEERING_BASE_RADIUS + POWERFLOW_SOLO_BASE_OFFSET - BG_PADDING


class UnifiedGauge(Widget):
  """Unified power flow + steering arc gauge for BluePilot."""

  def __init__(self):
    super().__init__()
    self._params = Params()

    self._powerflow_filter = FirstOrderFilter(0.0, 0.5, 1.0 / gui_app.target_fps)
    self._torque_bar = TorqueBarBP(scale=STEERING_SCALE, always=True)
    self._torque_bar._torque_filter = FirstOrderFilter(0, 0.5, 1.0 / gui_app.target_fps)

    self._font_bold = gui_app.font(FontWeight.BOLD)

    self._power_flow_mode_value = 0
    self._engine_on_reason_value = 0
    self._powerflow_enabled = self._params.get_bool("FordPrefHybridPowerFlow")
    self._bg_style = BG_STYLE_SOLID
    self._param_frame_counter = PARAM_REFRESH_FRAMES

  def _update_state(self):
    self._refresh_params_if_needed()

    steering_active = self._should_render_steering()
    if steering_active:
      self._torque_bar._update_state()
      self._torque_bar._torque_line_alpha_filter.update(
        ui_state.status not in (UIStatus.DISENGAGED, UIStatus.LONG_ONLY)
      )

    if self._should_render_powerflow():
      self._update_powerflow_state()

  def _refresh_params_if_needed(self) -> None:
    self._param_frame_counter += 1
    if self._param_frame_counter >= PARAM_REFRESH_FRAMES:
      self._param_frame_counter = 0
      self._powerflow_enabled = self._params.get_bool("FordPrefHybridPowerFlow")

  def _update_powerflow_state(self) -> None:
    try:
      car_state_bp = ui_state.sm["carStateBP"]
      throttle_demand = car_state_bp.hybridDrive.throttleDemandPercent
      normalized = np.clip(throttle_demand / 102.0, -1.0, 1.0)
      self._powerflow_filter.update(normalized)
      self._power_flow_mode_value = car_state_bp.hybridDrive.powerFlowModeValue
      self._engine_on_reason_value = car_state_bp.hybridDrive.engineOnReasonValue
    except (KeyError, AttributeError, TypeError):
      self._power_flow_mode_value = 0
      self._engine_on_reason_value = 0

  def _should_render_powerflow(self) -> bool:
    if not self._powerflow_enabled:
      return False
    try:
      if "carStateBP" not in ui_state.sm.recv_frame:
        return False
      if ui_state.sm.recv_frame["carStateBP"] < ui_state.started_frame:
        return False
      return ui_state.sm["carStateBP"].hybridDrive.dataAvailable
    except (KeyError, AttributeError, TypeError):
      return False

  def _should_render_steering(self) -> bool:
    return ui_state.torque_bar

  def _get_mode(self) -> int:
    powerflow_active = self._should_render_powerflow()
    steering_active = self._should_render_steering()
    if powerflow_active and steering_active:
      return MODE_UNIFIED
    if powerflow_active:
      return MODE_POWERFLOW_ONLY
    if steering_active:
      return MODE_STEERING_ONLY
    return MODE_NONE

  def _render(self, rect: rl.Rectangle) -> None:
    mode = self._get_mode()
    if mode == MODE_NONE:
      return

    layout = self._compute_layout(rect, mode)

    if mode == MODE_STEERING_ONLY:
      self._render_steering_background(layout.rect, layout.cx, layout.cy, layout.steering_height)
      self._render_steering_arc(layout.rect, layout.cx, layout.cy, TORQUE_ANGLE_SPAN, layout.steering_height)
      return

    pf_activity = self._activity_from_value(self._powerflow_filter.x)
    self._render_background(layout.rect, layout.cx, layout.cy, layout.angle_span, layout.bg_top, layout.bg_bottom)
    self._render_powerflow_bar(layout.rect, layout.cx, layout.cy, layout.angle_span,
                               layout.pf_mid, layout.pf_thickness, pf_activity)
    self._render_tick_marks(layout.cx, layout.cy, layout.angle_span, layout.pf_mid, layout.pf_thickness, pf_activity)
    self._render_divider(layout.rect, layout.cx, layout.cy, layout.angle_span, layout.divider_radius, pf_activity)
    self._render_text_labels(layout.cx, layout.cy, layout.angle_span, layout.text_size, layout.text_radius, pf_activity)

    if mode == MODE_UNIFIED:
      self._render_steering_arc(layout.rect, layout.cx, layout.cy, layout.angle_span, layout.steering_height)

  def _compute_layout(self, rect: rl.Rectangle, mode: int) -> GaugeLayout:
    effective_rect = self._get_effective_rect(rect)

    cx = effective_rect.x + effective_rect.width / 2 + 8
    torque = self._torque_bar._torque_filter.x
    torque_line_offset = self._get_torque_line_offset(torque, mode)
    cy = effective_rect.y + effective_rect.height + STEERING_BASE_RADIUS - torque_line_offset
    steering_height = np.interp(abs(torque), [0.7, 1.0], [STEERING_MIN_HEIGHT, STEERING_MAX_HEIGHT])

    width_ratio = min(1.0, rect.width / FULL_CONTENT_WIDTH)
    base_angle_span = POWERFLOW_ANGLE_SPAN_UNIFIED if mode == MODE_UNIFIED else POWERFLOW_ANGLE_SPAN_SOLO
    angle_span = base_angle_span * width_ratio
    text_size = max(28, int(POWERFLOW_TEXT_FONT_SIZE * width_ratio))

    pf_thickness = steering_height * POWERFLOW_THICKNESS_RATIO_UNIFIED if mode == MODE_UNIFIED else STEERING_MIN_HEIGHT
    # Steering arc is rendered with:
    # mid_r = STEERING_BASE_RADIUS + steering_height / 2, thickness = steering_height
    # So its core lane is [STEERING_BASE_RADIUS, STEERING_BASE_RADIUS + steering_height].
    steering_core_inner = STEERING_BASE_RADIUS
    steering_core_outer = STEERING_BASE_RADIUS + steering_height
    steering_glow_outer = steering_core_outer + GLOW_EXPANSION

    if mode == MODE_UNIFIED:
      # Unified lane stack from inner -> outer: steering, divider, powerflow, text.
      pf_inner = steering_glow_outer + POWERFLOW_UNIFIED_GAP
      divider_radius = steering_glow_outer + max(6.0, POWERFLOW_UNIFIED_GAP * 0.45)
    else:
      pf_inner = STEERING_BASE_RADIUS + POWERFLOW_SOLO_BASE_OFFSET
      divider_radius = pf_inner - POWERFLOW_TEXT_GAP / 2

    pf_outer = pf_inner + pf_thickness
    pf_mid = (pf_inner + pf_outer) / 2
    text_radius = pf_outer + POWERFLOW_TEXT_GAP
    text_top = text_radius + text_size * 0.6
    bg_top = max(text_top, pf_outer) + BG_PADDING
    bg_bottom = steering_core_inner - BG_PADDING if mode == MODE_UNIFIED else pf_inner - BG_PADDING

    return GaugeLayout(
      rect=effective_rect,
      cx=cx,
      cy=cy,
      steering_height=steering_height,
      angle_span=angle_span,
      text_size=text_size,
      pf_thickness=pf_thickness,
      pf_mid=pf_mid,
      pf_outer=pf_outer,
      pf_inner=pf_inner,
      divider_radius=divider_radius,
      text_radius=text_radius,
      bg_top=bg_top,
      bg_bottom=bg_bottom,
    )

  def _get_effective_rect(self, rect: rl.Rectangle) -> rl.Rectangle:
    if ui_state.developer_ui in (DeveloperUiRenderer.DEV_UI_BOTTOM, DeveloperUiRenderer.DEV_UI_BOTH):
      return rl.Rectangle(rect.x, rect.y, rect.width, rect.height - DeveloperUiRenderer.BOTTOM_BAR_HEIGHT)
    return rect

  def _get_torque_line_offset(self, torque: float, mode: int) -> float:
    if mode == MODE_POWERFLOW_ONLY:
      return 22 * STEERING_SCALE
    return np.interp(abs(torque), [0.7, 1.0], [22 * STEERING_SCALE, 26 * STEERING_SCALE])

  def _render_background(self, rect, cx, cy, angle_span, bg_top, bg_bottom):
    bg_r_mid = (bg_top + bg_bottom) / 2
    bg_thickness = bg_top - bg_bottom
    start_angle, end_angle = self._angles(angle_span)

    glow_pts = arc_bar_pts(
      cx, cy, bg_r_mid, bg_thickness + GLOW_EXPANSION * 2,
      start_angle, end_angle, cap_radius=min(14, bg_thickness / 2 + GLOW_EXPANSION),
    )
    draw_polygon(rect, glow_pts, color=rl.Color(20, 20, 20, int(BG_COLOR.a * 0.30)))

    bg_pts = arc_bar_pts(
      cx, cy, bg_r_mid, bg_thickness, start_angle, end_angle,
      cap_radius=min(12, bg_thickness / 2),
    )
    if self._bg_style == BG_STYLE_SOLID:
      draw_polygon(rect, bg_pts, color=BG_COLOR)
    else:
      gradient = Gradient(
        start=(cx / rect.width, 0),
        end=((cx - 250) / rect.width, 0),
        colors=[rl.Color(15, 15, 15, 200), rl.Color(15, 15, 15, 60)],
        stops=[0.0, 1.0],
      )
      draw_polygon(rect, bg_pts, gradient=gradient)

  def _render_steering_background(self, rect, cx, cy, steering_height):
    alpha_val = self._torque_bar._torque_line_alpha_filter.x
    if alpha_val < 0.01:
      return

    mid_r = STEERING_BASE_RADIUS + steering_height / 2
    bg_top = mid_r + steering_height / 2 + BG_PADDING
    bg_bottom = STEERING_BASE_RADIUS - BG_PADDING
    bg_r_mid = (bg_top + bg_bottom) / 2
    bg_thickness = bg_top - bg_bottom

    bg_angle_span = alpha_val * TORQUE_ANGLE_SPAN
    start_angle, end_angle = self._angles(bg_angle_span)
    bg_alpha = int(100 * alpha_val)

    glow_pts = arc_bar_pts(
      cx, cy, bg_r_mid, bg_thickness + GLOW_EXPANSION * 2,
      start_angle, end_angle, cap_radius=min(14, bg_thickness / 2 + GLOW_EXPANSION),
    )
    draw_polygon(rect, glow_pts, color=rl.Color(20, 20, 20, int(bg_alpha * 0.3)))

    bg_pts = arc_bar_pts(
      cx, cy, bg_r_mid, bg_thickness, start_angle, end_angle,
      cap_radius=min(12, bg_thickness / 2),
    )
    draw_polygon(rect, bg_pts, color=rl.Color(20, 20, 20, bg_alpha))

  def _render_powerflow_bar(self, rect, cx, cy, angle_span, pf_mid, pf_thickness, pf_activity):
    center_angle = -90.0
    half_span = angle_span / 2
    start_angle, end_angle = self._angles(angle_span)
    draw_thickness = pf_thickness * np.interp(
      pf_activity, [0.0, 1.0], [POWERFLOW_IDLE_THICKNESS_RATIO, POWERFLOW_ACTIVE_THICKNESS_RATIO]
    )

    track_glow_thickness = draw_thickness + GLOW_EXPANSION * 2
    track_glow_pts = arc_bar_pts(
      cx, cy, pf_mid, track_glow_thickness,
      start_angle, end_angle, cap_radius=min(10, track_glow_thickness / 2),
    )
    track_glow_alpha = int(np.interp(pf_activity, [0.0, 1.0], [10, 20]))
    draw_polygon(rect, track_glow_pts, color=rl.Color(255, 255, 255, track_glow_alpha))

    track_pts = arc_bar_pts(
      cx, cy, pf_mid, draw_thickness,
      start_angle, end_angle, cap_radius=min(8, draw_thickness / 2),
    )
    track_alpha = int(np.interp(pf_activity, [0.0, 1.0], [22, 40]))
    draw_polygon(rect, track_pts, color=rl.Color(255, 255, 255, track_alpha))

    value = self._powerflow_filter.x
    if abs(value) < POWERFLOW_VALUE_EPS:
      return

    if value < 0:
      bar_end = max(center_angle - half_span * abs(value), start_angle)
      tip_color = REGEN_COLOR
    else:
      bar_end = min(center_angle + half_span * value, end_angle)
      tip_color = DEMAND_COLOR

    glow_thickness = draw_thickness + GLOW_EXPANSION * 2
    glow_pts = arc_bar_pts(
      cx, cy, pf_mid, glow_thickness,
      center_angle, bar_end, cap_radius=min(10, glow_thickness / 2),
    )
    glow_tip_x = min(glow_pts[:, 0]) if value < 0 else max(glow_pts[:, 0])
    glow_gradient = Gradient(
      start=(cx / rect.width, 0),
      end=(glow_tip_x / rect.width, 0),
      colors=[
        rl.Color(255, 255, 255, int(np.interp(pf_activity, [0.0, 1.0], [45, GLOW_ALPHA]))),
        rl.Color(tip_color.r, tip_color.g, tip_color.b, int(np.interp(pf_activity, [0.0, 1.0], [45, GLOW_ALPHA]))),
      ],
      stops=[0.0, 1.0],
    )
    draw_polygon(rect, glow_pts, gradient=glow_gradient)

    bar_pts = arc_bar_pts(
      cx, cy, pf_mid, draw_thickness,
      center_angle, bar_end, cap_radius=min(8, draw_thickness / 2),
    )
    tip_x = min(bar_pts[:, 0]) if value < 0 else max(bar_pts[:, 0])
    center_color = rl.Color(CENTER_COLOR.r, CENTER_COLOR.g, CENTER_COLOR.b, int(np.interp(pf_activity, [0.0, 1.0], [170, 240])))
    tip_draw_color = rl.Color(tip_color.r, tip_color.g, tip_color.b, int(np.interp(pf_activity, [0.0, 1.0], [200, 255])))
    gradient = Gradient(
      start=(cx / rect.width, 0),
      end=(tip_x / rect.width, 0),
      colors=[center_color, tip_draw_color],
      stops=[0.0, 1.0],
    )
    draw_polygon(rect, bar_pts, gradient=gradient)

  def _render_tick_marks(self, cx, cy, angle_span, pf_mid, pf_thickness, pf_activity):
    draw_thickness = pf_thickness * np.interp(
      pf_activity, [0.0, 1.0], [POWERFLOW_IDLE_THICKNESS_RATIO, POWERFLOW_ACTIVE_THICKNESS_RATIO]
    )
    outer_radius = pf_mid + draw_thickness / 2
    inner_radius = pf_mid - draw_thickness / 2
    tick_length = draw_thickness * TICK_LENGTH_RATIO
    start_angle, end_angle = self._angles(angle_span)
    tick_alpha = int(np.interp(pf_activity, [0.0, 1.0], [TICK_ALPHA_IDLE, TICK_ALPHA_ACTIVE]))
    tick_color = rl.Color(TICK_COLOR.r, TICK_COLOR.g, TICK_COLOR.b, tick_alpha)
    tick_thickness = np.interp(pf_activity, [0.0, 1.0], [1.4, 2.2])

    for percent in range(0, 101, 10):
      angle_deg = start_angle + (end_angle - start_angle) * (percent / 100.0)
      angle_rad = np.deg2rad(angle_deg)
      cos_a = float(np.cos(angle_rad))
      sin_a = float(np.sin(angle_rad))

      rl.draw_line_ex(
        rl.Vector2(cx + cos_a * outer_radius, cy + sin_a * outer_radius),
        rl.Vector2(cx + cos_a * (outer_radius - tick_length), cy + sin_a * (outer_radius - tick_length)),
        tick_thickness, tick_color,
      )
      rl.draw_line_ex(
        rl.Vector2(cx + cos_a * inner_radius, cy + sin_a * inner_radius),
        rl.Vector2(cx + cos_a * (inner_radius + tick_length), cy + sin_a * (inner_radius + tick_length)),
        tick_thickness, tick_color,
      )

  def _render_divider(self, rect, cx, cy, angle_span, divider_radius, pf_activity):
    start_angle, end_angle = self._angles(angle_span)
    divider_alpha = int(np.interp(pf_activity, [0.0, 1.0], [DIVIDER_ALPHA_IDLE, DIVIDER_ALPHA_ACTIVE]))
    divider_color = rl.Color(DIVIDER_COLOR.r, DIVIDER_COLOR.g, DIVIDER_COLOR.b, divider_alpha)
    divider_pts = arc_bar_pts(cx, cy, divider_radius, DIVIDER_THICKNESS, start_angle, end_angle, cap_radius=1)
    draw_polygon(rect, divider_pts, color=divider_color)

  def _render_text_labels(self, cx, cy, angle_span, font_size, text_radius, pf_activity):
    power_flow_text = get_hev_power_flow_text(self._power_flow_mode_value)
    engine_reason_text = get_hev_engine_on_reason_text(self._engine_on_reason_value)
    quarter_angle = angle_span / 4
    max_width = text_radius * np.deg2rad(angle_span / 2) * 0.86
    text_alpha = int(np.interp(pf_activity, [0.0, 1.0], [175, POWERFLOW_TEXT_COLOR.a]))
    text_color = rl.Color(POWERFLOW_TEXT_COLOR.r, POWERFLOW_TEXT_COLOR.g, POWERFLOW_TEXT_COLOR.b, text_alpha)

    if power_flow_text:
      left_size = self._fit_font_size(power_flow_text, self._font_bold, font_size, max_width)
      self._render_arc_text(
        cx, cy, text_radius, -90.0 - quarter_angle,
        power_flow_text, self._font_bold, left_size, text_color,
      )

    if engine_reason_text:
      right_size = self._fit_font_size(engine_reason_text, self._font_bold, font_size, max_width)
      self._render_arc_text(
        cx, cy, text_radius, -90.0 + quarter_angle,
        engine_reason_text, self._font_bold, right_size, text_color,
      )

  def _render_steering_arc(self, rect, cx, cy, _angle_span, steering_height):
    torque = self._torque_bar._torque_filter.x
    alpha_val = self._torque_bar._torque_line_alpha_filter.x
    mid_r = STEERING_BASE_RADIUS + steering_height / 2

    bg_angle_span = alpha_val * TORQUE_ANGLE_SPAN
    start_angle, end_angle = self._angles(bg_angle_span)

    bg_alpha = np.interp(abs(torque), [0.5, 1.0], [0.25, 0.5])
    bg_color = rl.Color(255, 255, 255, int(255 * bg_alpha * alpha_val))
    if ui_state.status not in (UIStatus.ENGAGED, UIStatus.LAT_ONLY):
      bg_color = rl.Color(255, 255, 255, int(255 * 0.15 * alpha_val))

    glow_height = steering_height + GLOW_EXPANSION * 2
    glow_cap = min(STEERING_CAP_RADIUS + GLOW_EXPANSION, glow_height / 2)
    bg_glow_pts = arc_bar_pts(cx, cy, mid_r, glow_height, start_angle, end_angle, cap_radius=glow_cap)
    draw_polygon(rect, bg_glow_pts, color=rl.Color(bg_color.r, bg_color.g, bg_color.b, int(bg_color.a * 0.25)))

    bg_pts = arc_bar_pts(cx, cy, mid_r, steering_height, start_angle, end_angle, cap_radius=STEERING_CAP_RADIUS)
    draw_polygon(rect, bg_pts, color=bg_color)

    a0 = -90.0
    a1 = a0 + bg_angle_span / 2 * torque
    fg_pts = arc_bar_pts(cx, cy, mid_r, steering_height, a0, a1, cap_radius=STEERING_CAP_RADIUS)

    transition = np.clip((abs(torque) - 0.35) / 0.65, 0.0, 1.0)
    transition_t = transition * transition * (3.0 - 2.0 * transition)
    brightness_boost = 1.0 + 0.3 * min(abs(torque), 1.0)

    if ui_state.status in (UIStatus.ENGAGED, UIStatus.LAT_ONLY):
      base_alpha = int(min(255, 255 * 0.82 * alpha_val * brightness_boost))
      start_color = blend_colors(
        rl.Color(255, 255, 255, base_alpha),
        rl.Color(255, 220, 0, int(min(255, 255 * alpha_val * brightness_boost))),
        transition_t,
      )
      end_color = blend_colors(
        rl.Color(255, 255, 255, base_alpha),
        rl.Color(255, 130, 0, int(min(255, 255 * alpha_val * brightness_boost))),
        transition_t,
      )
    else:
      dimmed = rl.Color(255, 255, 255, int(255 * 0.30 * alpha_val))
      start_color = dimmed
      end_color = dimmed

    start_grad_pt = cx / rect.width
    if torque < 0:
      end_grad_pt = (cx * 0.35 + min(bg_pts[:, 0]) * 0.65) / rect.width
    else:
      end_grad_pt = (cx * 0.35 + max(bg_pts[:, 0]) * 0.65) / rect.width

    fg_glow_pts = arc_bar_pts(cx, cy, mid_r, glow_height, a0, a1, cap_radius=glow_cap)
    glow_gradient = Gradient(
      start=(start_grad_pt, 0),
      end=(end_grad_pt, 0),
      colors=[
        rl.Color(start_color.r, start_color.g, start_color.b, int(start_color.a * 0.25)),
        rl.Color(end_color.r, end_color.g, end_color.b, int(end_color.a * 0.25)),
      ],
      stops=[0.0, 1.0],
    )
    draw_polygon(rect, fg_glow_pts, gradient=glow_gradient)

    gradient = Gradient(
      start=(start_grad_pt, 0),
      end=(end_grad_pt, 0),
      colors=[start_color, end_color],
      stops=[0.0, 1.0],
    )
    draw_polygon(rect, fg_pts, gradient=gradient)

    if abs(torque) < 0.5:
      dot_offset = np.interp(abs(torque), [0.7, 1.0], [22 * STEERING_SCALE, 26 * STEERING_SCALE])
      dot_y = rect.y + rect.height - dot_offset - steering_height / 2
      rl.draw_circle(int(cx), int(dot_y), 15, rl.Color(182, 182, 182, int(255 * 0.9 * alpha_val)))

  def _angles(self, angle_span: float) -> tuple[float, float]:
    return -90.0 - angle_span / 2, -90.0 + angle_span / 2

  def _activity_from_value(self, value: float) -> float:
    t = np.clip((abs(value) - POWERFLOW_ACTIVITY_DEADBAND) / (1.0 - POWERFLOW_ACTIVITY_DEADBAND), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

  def _fit_font_size(self, text, font, base_size, max_width):
    text_size = measure_text_cached(font, text, base_size)
    if text_size.x <= max_width or max_width <= 0:
      return base_size
    return max(16, int(base_size * max_width / text_size.x))

  def _render_arc_text(self, cx, cy, radius, center_angle_deg, text, font, font_size, color):
    angle_rad = np.deg2rad(center_angle_deg)
    pos_x = cx + np.cos(angle_rad) * radius
    pos_y = cy + np.sin(angle_rad) * radius

    text_size = measure_text_cached(font, text, font_size)
    origin = rl.Vector2(text_size.x / 2, text_size.y / 2)
    rotation = center_angle_deg + 90

    rl.draw_text_pro(font, text, rl.Vector2(pos_x, pos_y), origin, rotation, font_size, TEXT_LETTER_SPACING, color)
