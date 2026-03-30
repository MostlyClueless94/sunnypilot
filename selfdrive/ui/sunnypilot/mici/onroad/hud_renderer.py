"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import pyray as rl

from openpilot.common.params import Params
from openpilot.selfdrive.ui.mici.onroad.hud_renderer import HudRenderer
from openpilot.selfdrive.ui.mici.onroad.hud_renderer import COLORS, FONT_SIZES
from openpilot.selfdrive.ui.sunnypilot.onroad.blind_spot_indicators import BlindSpotIndicators
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.lib.text_measure import measure_text_cached


class HudRendererSP(HudRenderer):
  def __init__(self):
    super().__init__()
    self._params = Params()
    self._brakes_on = False
    self.blind_spot_indicators = BlindSpotIndicators()

  def _update_state(self) -> None:
    super()._update_state()
    car_state = ui_state.sm['carState']
    self._brakes_on = self._params.get_bool("ShowBrakeStatus") and (car_state.brakePressed or car_state.regenBraking)
    self.blind_spot_indicators.update()

  def _render(self, rect: rl.Rectangle) -> None:
    self._torque_bar.render(rect)

    if self.is_cruise_set:
      self._draw_set_speed(rect)

    self._draw_current_speed(rect)
    self._draw_steering_wheel(rect)
    self.blind_spot_indicators.render(rect)

  def _draw_current_speed(self, rect: rl.Rectangle) -> None:
    if ui_state.hide_v_ego_ui:
      return

    speed_text = str(round(self.speed))
    speed_text_size = measure_text_cached(self._font_bold, speed_text, FONT_SIZES.current_speed)
    speed_pos = rl.Vector2(rect.x + rect.width / 2 - speed_text_size.x / 2, 180 - speed_text_size.y / 2)
    speed_color = rl.Color(255, 60, 60, 255) if self._brakes_on else COLORS.WHITE
    rl.draw_text_ex(self._font_bold, speed_text, speed_pos, FONT_SIZES.current_speed, 0, speed_color)

    unit_text = tr("km/h") if ui_state.is_metric else tr("mph")
    unit_text_size = measure_text_cached(self._font_medium, unit_text, FONT_SIZES.speed_unit)
    unit_pos = rl.Vector2(rect.x + rect.width / 2 - unit_text_size.x / 2, 290 - unit_text_size.y / 2)
    rl.draw_text_ex(self._font_medium, unit_text, unit_pos, FONT_SIZES.speed_unit, 0, COLORS.WHITE_TRANSLUCENT)

  def _has_blind_spot_detected(self) -> bool:

    return self.blind_spot_indicators.detected
