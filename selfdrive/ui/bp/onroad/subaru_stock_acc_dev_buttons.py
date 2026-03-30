import pyray as rl

from openpilot.common.params import Params
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import FontWeight, MouseEvent, gui_app
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget

SUBARU_STOCK_ACC_DEV_COMMAND_NONE = 0
SUBARU_STOCK_ACC_DEV_COMMAND_TAP_INCREASE = 1
SUBARU_STOCK_ACC_DEV_COMMAND_TAP_DECREASE = 2
SUBARU_STOCK_ACC_DEV_COMMAND_HOLD_INCREASE = 3
SUBARU_STOCK_ACC_DEV_COMMAND_HOLD_DECREASE = 4

# Match Subaru stock-ACC long-press timing used by the ICBM path.
SUBARU_STOCK_ACC_DEV_HOLD_THRESHOLD = 0.5


class _SubaruStockAccDevButton(Widget):
  def __init__(self, label: str, tap_command: int, hold_command: int):
    super().__init__()
    self._params = Params()
    self._font = gui_app.font(FontWeight.BOLD)
    self._label = label
    self._tap_command = tap_command
    self._hold_command = hold_command
    self._press_started_at: float | None = None
    self._hold_command_sent = False

  @property
  def has_active_input(self) -> bool:
    return self._press_started_at is not None or self._hold_command_sent

  def reset(self, clear_command: bool = False) -> None:
    if clear_command:
      self._params.put("SubaruStockAccDevButtonCommand", SUBARU_STOCK_ACC_DEV_COMMAND_NONE)
    self._press_started_at = None
    self._hold_command_sent = False

  def _write_command(self, command: int) -> None:
    self._params.put("SubaruStockAccDevButtonCommand", command)

  def _handle_mouse_press(self, _mouse_pos) -> None:
    self._press_started_at = rl.get_time()
    self._hold_command_sent = False

  def _handle_mouse_event(self, mouse_event: MouseEvent) -> None:
    if self._press_started_at is None:
      return

    if mouse_event.left_down and not self._hold_command_sent:
      if (mouse_event.t - self._press_started_at) >= SUBARU_STOCK_ACC_DEV_HOLD_THRESHOLD:
        self._write_command(self._hold_command)
        self._hold_command_sent = True
      return

    if mouse_event.left_released:
      if self._hold_command_sent:
        self._write_command(SUBARU_STOCK_ACC_DEV_COMMAND_NONE)
      else:
        self._write_command(self._tap_command)
      self._press_started_at = None
      self._hold_command_sent = False

  def _render(self, rect: rl.Rectangle) -> None:
    if self.enabled:
      fill_color = rl.Color(0, 0, 0, 210 if self.is_pressed else 166)
      border_color = rl.Color(255, 255, 255, 210 if self.is_pressed else 110)
      text_color = rl.Color(255, 255, 255, 255)
    else:
      fill_color = rl.Color(0, 0, 0, 95)
      border_color = rl.Color(255, 255, 255, 70)
      text_color = rl.Color(255, 255, 255, 115)

    center_x = int(rect.x + rect.width / 2)
    center_y = int(rect.y + rect.height / 2)
    radius = int(min(rect.width, rect.height) / 2)

    rl.draw_circle(center_x, center_y, radius, fill_color)
    rl.draw_circle_lines(center_x, center_y, radius, border_color)

    text_size = measure_text_cached(self._font, self._label, 92)
    text_pos = rl.Vector2(rect.x + (rect.width - text_size.x) / 2, rect.y + (rect.height - text_size.y) / 2 - 6)
    rl.draw_text_ex(self._font, self._label, text_pos, 92, 0, text_color)


class SubaruStockAccDevButtons(Widget):
  BUTTON_SIZE = 132
  BUTTON_GAP = 18
  HEIGHT = BUTTON_SIZE * 2 + BUTTON_GAP

  def __init__(self):
    super().__init__()
    self._params = Params()
    self._plus_button = _SubaruStockAccDevButton(
      "+",
      SUBARU_STOCK_ACC_DEV_COMMAND_TAP_INCREASE,
      SUBARU_STOCK_ACC_DEV_COMMAND_HOLD_INCREASE,
    )
    self._minus_button = _SubaruStockAccDevButton(
      "-",
      SUBARU_STOCK_ACC_DEV_COMMAND_TAP_DECREASE,
      SUBARU_STOCK_ACC_DEV_COMMAND_HOLD_DECREASE,
    )
    self.set_visible(self._should_show)

  def _is_supported_subaru(self) -> bool:
    brand = str(getattr(ui_state.CP, "brand", "")).lower() if ui_state.CP is not None else ""
    return brand == "subaru" and bool(
      ui_state.CP_SP is not None and getattr(ui_state.CP_SP, "intelligentCruiseButtonManagementAvailable", False)
    )

  def _should_show(self) -> bool:
    return self._is_supported_subaru() and self._params.get_bool("IntelligentCruiseButtonManagement") and \
      self._params.get_bool("SubaruStockAccDevButtonsEnabled")

  def _buttons_enabled(self) -> bool:
    if not self._should_show():
      return False
    if ui_state.sm.recv_frame["carState"] < ui_state.started_frame:
      return False
    return bool(ui_state.sm["carState"].cruiseState.enabled)

  def _update_layout_rects(self) -> None:
    self._plus_button.set_rect(rl.Rectangle(self.rect.x, self.rect.y, self.BUTTON_SIZE, self.BUTTON_SIZE))
    self._minus_button.set_rect(rl.Rectangle(
      self.rect.x,
      self.rect.y + self.BUTTON_SIZE + self.BUTTON_GAP,
      self.BUTTON_SIZE,
      self.BUTTON_SIZE,
    ))

  def _clear_if_needed(self) -> None:
    command = int(self._params.get("SubaruStockAccDevButtonCommand", return_default=True) or 0)
    if command != SUBARU_STOCK_ACC_DEV_COMMAND_NONE or self._plus_button.has_active_input or self._minus_button.has_active_input:
      self.clear_command()

  def clear_command(self) -> None:
    self._params.put("SubaruStockAccDevButtonCommand", SUBARU_STOCK_ACC_DEV_COMMAND_NONE)
    self._plus_button.reset()
    self._minus_button.reset()

  def user_interacting(self) -> bool:
    return self._plus_button.is_pressed or self._minus_button.is_pressed or \
      self._plus_button.has_active_input or self._minus_button.has_active_input

  def _update_state(self) -> None:
    interactive = self._buttons_enabled()
    self._plus_button.set_enabled(interactive)
    self._minus_button.set_enabled(interactive)

    if not self._should_show() or not interactive:
      self._clear_if_needed()

  def _render(self, _rect: rl.Rectangle) -> None:
    self._plus_button.render(self._plus_button.rect)
    self._minus_button.render(self._minus_button.rect)
