import pyray as rl
from openpilot.common.params import Params
from openpilot.system.hardware import PC
from openpilot.selfdrive.ui.mici.onroad.torque_bar import TorqueBar
from openpilot.selfdrive.ui.bp.onroad.powerflow_gauge import PowerflowGauge
from openpilot.selfdrive.ui.bp.onroad.hybrid_battery_gauge import HybridBatteryGauge
from openpilot.selfdrive.ui.onroad.hud_renderer import UI_CONFIG, FONT_SIZES, COLORS, HudRenderer
from openpilot.selfdrive.ui.sunnypilot.onroad.hud_renderer import HudRendererSP
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.text_measure import measure_text_cached

ROAD_NAME_PILL_BG = rl.Color(45, 45, 45, 255)


class HudRendererBP(HudRendererSP):
  """BluePilot HudRenderer with torque bar, powerflow gauge, road name, and brake status."""

  def __init__(self, left_offset: int = 0):
    super().__init__(left_offset=left_offset)
    self._torque_bar = TorqueBar(scale=3.0, always=True)
    self._powerflow_gauge = PowerflowGauge()
    self._battery_gauge = HybridBatteryGauge()
    self._bp_params = Params()
    self._brakes_on = False
    self.speed_right = 0

  def get_speed_right(self) -> int:
    return self.speed_right

  def _update_state(self) -> None:
    super()._update_state()

    # Check brake status if enabled
    if self._bp_params.get_bool("ShowBrakeStatus"):
      sm = ui_state.sm
      if sm.valid['carStateBP']:
        try:
          car_state_bp = sm['carStateBP']
          brake_light_status = car_state_bp.brakeLightStatus
          self._brakes_on = brake_light_status.dataAvailable and brake_light_status.brakeLightsOn
        except (KeyError, AttributeError):
          self._brakes_on = False
      else:
        self._brakes_on = False
    else:
      self._brakes_on = False

    self._torque_bar._update_state()
    self._powerflow_gauge._update_state()

  def _render(self, rect: rl.Rectangle) -> None:
    # Render powerflow gauge above torque bar
    self._powerflow_gauge.render(rect)

    if ui_state.sm['controlsState'].lateralControlState.which() != 'angleState' or ui_state.sm.updated["controllerStateBP"]:
      self._torque_bar.render(rect)

    # Draw stock+SP HUD elements (set speed, exp button, developer UI)
    # We call grandparent (HudRenderer) _render for set speed and exp button,
    # then SP _render adds developer UI
    # But we need to insert road_name between set_speed and current_speed
    # So we replicate the render flow with our additions

    # Draw the header background
    rl.draw_rectangle_gradient_v(
      int(rect.x), int(rect.y), int(rect.width), UI_CONFIG.header_height,
      COLORS.HEADER_GRADIENT_START, COLORS.HEADER_GRADIENT_END,
    )

    if self.is_cruise_available:
      self._draw_set_speed(rect)

    self._draw_road_name(rect)
    self._draw_current_speed(rect)

    button_x = rect.x + rect.width - UI_CONFIG.border_size - UI_CONFIG.button_size
    button_y = rect.y + UI_CONFIG.header_align_center_y - UI_CONFIG.button_size / 2
    self._exp_button.render(rl.Rectangle(button_x, button_y, UI_CONFIG.button_size, UI_CONFIG.button_size))

    # Developer UI from SP
    self.developer_ui.render(rect)

  def _draw_current_speed(self, rect: rl.Rectangle) -> None:
    """Draw current speed with brake status red coloring."""
    speed_text = str(round(self.speed))
    speed_text_size = measure_text_cached(self._font_bold, speed_text, FONT_SIZES.current_speed)
    speed_pos = rl.Vector2(
      rect.x + rect.width / 2 - speed_text_size.x / 2,
      rect.y + UI_CONFIG.header_align_center_y - speed_text_size.y / 2
    )
    self.speed_right = speed_pos.x + speed_text_size.x

    # Show red when braking if brake status is enabled
    speed_color = rl.Color(255, 60, 60, 255) if self._brakes_on else COLORS.WHITE
    rl.draw_text_ex(self._font_bold, speed_text, speed_pos, FONT_SIZES.current_speed, 0, speed_color)

    unit_text = "km/h" if ui_state.is_metric else "mph"
    unit_text_size = measure_text_cached(self._font_medium, unit_text, FONT_SIZES.speed_unit)
    unit_pos = rl.Vector2(rect.x + rect.width / 2 - unit_text_size.x / 2, rect.y + 290 - unit_text_size.y / 2)
    rl.draw_text_ex(self._font_medium, unit_text, unit_pos, FONT_SIZES.speed_unit, 0, COLORS.WHITE_TRANSLUCENT)

  def _draw_road_name(self, rect: rl.Rectangle) -> None:
    """Draw road name in a dark grey pill between max speed setpoint and current speed."""
    if (self._bp_params.get("RoadNameToggle") or "1") != "1":
      return

    # Get road name from liveMapDataSP (preferred) or Params fallback
    road_name = ""
    if ui_state.sm.valid.get("liveMapDataSP", False):
      try:
        road_name = (ui_state.sm["liveMapDataSP"].roadName or "").strip()
      except (KeyError, AttributeError):
        pass
    if not road_name:
      road_name = (self._bp_params.get("RoadName") or "").strip()
    if not road_name and PC:
      road_name = "west grand parkway south"
    if not road_name:
      return

    MAX_CHARS_PER_LINE = 22
    line_spacing = 4

    def _wrap_at_spaces(text: str, max_len: int) -> list[str]:
      if len(text) <= max_len:
        return [text] if text else []
      lines = []
      remaining = text.strip()
      while remaining:
        if len(remaining) <= max_len:
          lines.append(remaining)
          break
        chunk = remaining[: max_len + 1]
        last_space = chunk.rfind(' ')
        if last_space > 0:
          lines.append(remaining[:last_space])
          remaining = remaining[last_space + 1:].lstrip()
        else:
          lines.append(remaining[:max_len])
          remaining = remaining[max_len:].lstrip()
      return lines

    road_name_lines = _wrap_at_spaces(road_name, MAX_CHARS_PER_LINE)
    if not road_name_lines:
      return

    set_speed_width = UI_CONFIG.set_speed_width_metric if ui_state.is_metric else UI_CONFIG.set_speed_width_imperial
    set_speed_x = rect.x + 60 + self._left_offset + (UI_CONFIG.set_speed_width_imperial - set_speed_width) // 2
    gap_left = set_speed_x + set_speed_width + 24
    gap_right = rect.x + rect.width / 2 - 80
    center_x = (gap_left + gap_right) / 2 - 25

    line_sizes = [measure_text_cached(self._font_bold, line, FONT_SIZES.road_name) for line in road_name_lines]
    max_line_width = max(s.x for s in line_sizes)
    single_line_height = line_sizes[0].y
    total_text_height = single_line_height * len(road_name_lines) + line_spacing * (len(road_name_lines) - 1)

    pill_padding_h = 48
    pill_padding_v = 12
    pill_height = int(total_text_height) + 2 * pill_padding_v
    pill_width = min(int(max_line_width) + 2 * pill_padding_h, int(gap_right - gap_left))
    if pill_width < 60:
      return

    pill_x = center_x - pill_width / 2
    pill_y = rect.y + UI_CONFIG.header_align_center_y - pill_height / 2

    pill_rect = rl.Rectangle(pill_x, pill_y, pill_width, pill_height)
    rl.draw_rectangle_rounded(pill_rect, 0.75, 10, ROAD_NAME_PILL_BG)

    text_y = pill_y + pill_padding_v
    for line, line_size in zip(road_name_lines, line_sizes):
      text_x = pill_x + (pill_width - line_size.x) / 2
      rl.draw_text_ex(self._font_bold, line, rl.Vector2(text_x, text_y), FONT_SIZES.road_name, 0, rl.WHITE)
      text_y += single_line_height + line_spacing
