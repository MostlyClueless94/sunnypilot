import time
import pyray as rl
from cereal import messaging, car, log
from openpilot.selfdrive.ui.mici.onroad.augmented_road_view import AugmentedRoadView
from openpilot.selfdrive.ui.bp.onroad.blindspot_renderer import BlindspotRendererMixin
from openpilot.selfdrive.ui.ui_state import ui_state, UIStatus


class MiciAugmentedRoadViewBP(AugmentedRoadView, BlindspotRendererMixin):
  """BluePilot MICI AugmentedRoadView with blindspot indicators."""

  BLIND_SPOT_WIDTH = 125  # Narrower for MICI's smaller screen

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._init_blindspot()

  def _render(self, _):
    """Override render to add blindspot indicators after scissor mode."""
    # Call parent _render which handles the full MICI render flow
    super()._render(_)

    # Draw blindspot after scissor mode ends (so it appears on screen edges)
    self._draw_blindspot_screen_edges(self.rect, self.BLIND_SPOT_WIDTH)
