from cereal import log
from openpilot.selfdrive.ui.sunnypilot.onroad.driver_state import DriverStateRendererSP
from openpilot.selfdrive.ui.ui_state import ui_state

AlertSize = log.SelfdriveState.AlertSize
VISIBILITY_HOLD_FRAMES = 20


class DriverStateRendererBP(DriverStateRendererSP):
  """BluePilot driver monitor renderer with stable visibility in experimental mode."""

  def __init__(self):
    super().__init__()
    self._last_visible_frame = -1
    self.set_visible(self._should_draw)

  def _current_ui_frame(self) -> int:
    try:
      return int(ui_state.sm.frame)
    except (AttributeError, TypeError, ValueError):
      return -1

  def _should_draw(self) -> bool:
    sm = ui_state.sm
    frame_id = self._current_ui_frame()

    try:
      driver_recent = sm.recv_frame.get("driverStateV2", 0) > ui_state.started_frame
      exp_mode = bool(sm["selfdriveState"].experimentalMode)
      alert_none = sm["selfdriveState"].alertSize == AlertSize.none
      visible_now = driver_recent and (alert_none or exp_mode)
    except (KeyError, AttributeError, TypeError):
      visible_now = False

    if visible_now:
      self._last_visible_frame = frame_id
      return True

    if frame_id >= 0 and self._last_visible_frame >= 0 and (frame_id - self._last_visible_frame) <= VISIBILITY_HOLD_FRAMES:
      return True

    return False
