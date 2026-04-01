"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import pyray as rl

from openpilot.common.constants import CV
from openpilot.common.params import Params
from openpilot.selfdrive.ui.mici.onroad.hud_renderer import COLORS
from openpilot.selfdrive.ui.sunnypilot.onroad.brake_status import should_highlight_braking_speed
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.lib.text_measure import measure_text_cached


CURRENT_SPEED_FONT_SIZE = 112
SPEED_UNIT_FONT_SIZE = 36
CURRENT_SPEED_CENTER_Y = 92
SPEED_UNIT_CENTER_Y = 146


class SpeedRenderer:
  def __init__(self):
    self.speed: float = 0.0
    self.v_ego_cluster_seen: bool = False
    self._brakes_on: bool = False
    self._params = Params()

    self._font_bold: rl.Font = gui_app.font(FontWeight.BOLD)
    self._font_medium: rl.Font = gui_app.font(FontWeight.MEDIUM)

  def update(self) -> None:
    car_state = ui_state.sm['carState']
    v_ego_cluster = car_state.vEgoCluster
    self.v_ego_cluster_seen = self.v_ego_cluster_seen or v_ego_cluster != 0.0
    v_ego = v_ego_cluster if self.v_ego_cluster_seen and not ui_state.true_v_ego_ui else car_state.vEgo
    speed_conversion = CV.MS_TO_KPH if ui_state.is_metric else CV.MS_TO_MPH
    self.speed = max(0.0, v_ego * speed_conversion)
    self._brakes_on = should_highlight_braking_speed(self._params.get_bool("ShowBrakeStatus"))

  def render(self, rect: rl.Rectangle) -> None:
    if ui_state.hide_v_ego_ui:
      return

    speed_text = str(round(self.speed))
    speed_text_size = measure_text_cached(self._font_bold, speed_text, CURRENT_SPEED_FONT_SIZE)
    speed_pos = rl.Vector2(
      rect.x + rect.width / 2 - speed_text_size.x / 2,
      rect.y + CURRENT_SPEED_CENTER_Y - speed_text_size.y / 2,
    )
    speed_color = rl.Color(255, 60, 60, 255) if self._brakes_on else COLORS.WHITE
    rl.draw_text_ex(self._font_bold, speed_text, speed_pos, CURRENT_SPEED_FONT_SIZE, 0, speed_color)

    unit_text = tr("km/h") if ui_state.is_metric else tr("mph")
    unit_text_size = measure_text_cached(self._font_medium, unit_text, SPEED_UNIT_FONT_SIZE)
    unit_pos = rl.Vector2(
      rect.x + rect.width / 2 - unit_text_size.x / 2,
      rect.y + SPEED_UNIT_CENTER_Y - unit_text_size.y / 2,
    )
    rl.draw_text_ex(self._font_medium, unit_text, unit_pos, SPEED_UNIT_FONT_SIZE, 0, COLORS.WHITE_TRANSLUCENT)
