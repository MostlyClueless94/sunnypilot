"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import pyray as rl

from openpilot.selfdrive.ui.mici.onroad.hud_renderer import HudRenderer
from openpilot.selfdrive.ui.sunnypilot.onroad.blind_spot_indicators import BlindSpotIndicators
from openpilot.selfdrive.ui.sunnypilot.mici.onroad.speed_renderer import SpeedRenderer


class HudRendererSP(HudRenderer):
  def __init__(self):
    super().__init__()
    self.speed_renderer = SpeedRenderer()
    self.blind_spot_indicators = BlindSpotIndicators()

  def _update_state(self) -> None:
    super()._update_state()
    self.speed_renderer.update()
    self.blind_spot_indicators.update()

  def _render(self, rect: rl.Rectangle) -> None:
    self._torque_bar.render(rect)

    if self.is_cruise_set:
      self._draw_set_speed(rect)

    self._draw_current_speed(rect)
    self._draw_steering_wheel(rect)
    self.blind_spot_indicators.render(rect)

  def _draw_current_speed(self, rect: rl.Rectangle) -> None:
    self.speed_renderer.render(rect)

  def _has_blind_spot_detected(self) -> bool:

    return self.blind_spot_indicators.detected
