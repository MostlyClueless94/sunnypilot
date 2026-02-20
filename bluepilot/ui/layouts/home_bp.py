"""
BluePilot Home Layout
Extends the stock HomeLayout to replace PrimeWidget in the left column
with DriveStats and ModelInfo widgets, matching the old Qt OffroadHomeSP layout.
"""

import pyray as rl
from collections.abc import Callable

from openpilot.selfdrive.ui.layouts.home import HomeLayout, SPACING
from bluepilot.ui.widgets.drive_stats import DriveStatsWidget
from bluepilot.ui.widgets.model_info import ModelInfoWidget


class HomeLayoutBP(HomeLayout):
  def __init__(self):
    super().__init__()
    # BP widgets for the left column (PrimeWidget is still created by super but won't be rendered)
    self._drive_stats = DriveStatsWidget()
    self._model_info = ModelInfoWidget()

  def set_model_settings_callback(self, callback: Callable[[], None]):
    """Wire model info click to open Models settings panel."""
    self._model_info.set_click_callback(callback)

  def _render_left_column(self):
    """Override: render DriveStats + ModelInfo instead of PrimeWidget."""
    rect = self.left_column_rect

    # DriveStats takes ~60% of height, ModelInfo takes ~40%
    stats_height = rect.height * 0.6 - SPACING / 2
    model_height = rect.height * 0.4 - SPACING / 2

    stats_rect = rl.Rectangle(rect.x, rect.y, rect.width, stats_height)
    self._drive_stats.render(stats_rect)

    model_rect = rl.Rectangle(rect.x, rect.y + stats_height + SPACING, rect.width, model_height)
    self._model_info.render(model_rect)
