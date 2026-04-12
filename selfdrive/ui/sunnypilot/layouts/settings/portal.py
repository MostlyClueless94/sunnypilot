"""
SubiPilot Portal settings page for TICI.
"""

import pyray as rl

from openpilot.selfdrive.ui.sunnypilot.layouts.settings.portal_common import (
  CachedPortalInfo,
  FEATURE_SUMMARY,
  NETWORK_SAFETY_NOTE,
  PORTAL_ENABLED_PARAM,
  get_port,
)
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.sunnypilot.widgets.list_view import button_item_sp, toggle_item_sp
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.label import UnifiedLabel, gui_label
from openpilot.system.ui.widgets.scroller_tici import LineSeparator, Scroller


def _draw_qr(matrix: list[list[bool]], rect: rl.Rectangle) -> None:
  if not matrix:
    return

  size = len(matrix)
  cell = max(1, int(min(rect.width, rect.height) // size))
  qr_size = cell * size
  x0 = int(rect.x + (rect.width - qr_size) / 2)
  y0 = int(rect.y + (rect.height - qr_size) / 2)
  rl.draw_rectangle(x0 - 8, y0 - 8, qr_size + 16, qr_size + 16, rl.WHITE)
  for y, row in enumerate(matrix):
    for x, filled in enumerate(row):
      if filled:
        rl.draw_rectangle(x0 + x * cell, y0 + y * cell, cell, cell, rl.BLACK)


class PortalStatusCard(Widget):
  def __init__(self):
    super().__init__()
    self.info = CachedPortalInfo(ui_state.params)
    self._rect.height = 560
    self._title_font = gui_app.font(FontWeight.BOLD)
    self._body_font = gui_app.font(FontWeight.NORMAL)
    self._summary = UnifiedLabel(
      text=tr(FEATURE_SUMMARY),
      font_size=40,
      font_weight=FontWeight.NORMAL,
      text_color=rl.Color(210, 210, 210, 255),
      alignment=rl.GuiTextAlignment.TEXT_ALIGN_LEFT,
      alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_TOP,
      wrap_text=True,
      elide=False,
    )

  @property
  def url(self) -> str:
    return self.info.url

  def refresh(self, force: bool = False) -> None:
    self.info.refresh(force)

  def set_parent_rect(self, parent_rect: rl.Rectangle) -> None:
    super().set_parent_rect(parent_rect)
    self._rect.width = parent_rect.width

  def _update_state(self):
    self.refresh()

  def _render(self, rect: rl.Rectangle):
    enabled = ui_state.params.get_bool(PORTAL_ENABLED_PARAM)
    self.refresh()

    rl.draw_rectangle_rounded(rect, 0.05, 16, rl.Color(24, 28, 26, 255))
    rl.draw_rectangle_rounded_lines_ex(rect, 0.05, 16, 2, rl.Color(70, 120, 95, 255))

    padding = 44
    title = tr("SubiPilot Portal")
    title_size = measure_text_cached(self._title_font, title, 62)
    rl.draw_text_ex(self._title_font, title, rl.Vector2(rect.x + padding, rect.y + 34), 62, 0, rl.WHITE)

    status_text = tr("Enabled") if enabled else tr("Disabled")
    status_color = rl.Color(80, 230, 145, 255) if enabled else rl.Color(235, 180, 80, 255)
    gui_label(
      rl.Rectangle(rect.x + padding + title_size.x + 34, rect.y + 35, 260, 70),
      status_text,
      font_size=42,
      color=status_color,
      font_weight=FontWeight.BOLD,
    )

    summary_rect = rl.Rectangle(rect.x + padding, rect.y + 122, rect.width - 340, 150)
    self._summary.render(summary_rect)

    url_text = self.info.url if enabled else tr("Enable portal to show the device URL.")
    rl.draw_text_ex(self._body_font, tr("Address"), rl.Vector2(rect.x + padding, rect.y + 300), 42, 0, rl.Color(160, 190, 170, 255))
    rl.draw_text_ex(self._title_font, url_text, rl.Vector2(rect.x + padding, rect.y + 354), 42, 0, rl.WHITE)

    rl.draw_text_ex(self._body_font, self.info.route_stats, rl.Vector2(rect.x + padding, rect.y + 430), 38, 0, rl.Color(190, 190, 190, 255))
    rl.draw_text_ex(self._body_font, tr(NETWORK_SAFETY_NOTE), rl.Vector2(rect.x + padding, rect.y + 488), 32, 0, rl.Color(235, 200, 130, 255))

    qr_rect = rl.Rectangle(rect.x + rect.width - 278, rect.y + 108, 210, 210)
    if enabled and self.info.qr_matrix:
      _draw_qr(self.info.qr_matrix, qr_rect)
    else:
      gui_label(
        qr_rect,
        tr("QR appears when enabled"),
        font_size=34,
        color=rl.Color(170, 170, 170, 255),
        font_weight=FontWeight.NORMAL,
        alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
        alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE,
      )


class SubiPilotPortalLayout(Widget):
  def __init__(self):
    super().__init__()
    self._status_card = PortalStatusCard()
    self._enable_toggle = toggle_item_sp(
      title=lambda: tr("Enable SubiPilot Portal"),
      description=lambda: tr(
        "Host the local SubiPilot Portal on this device. "
        + "The portal exposes route/log review and raw parameter editing on your local network.",
      ),
      initial_state=ui_state.params.get_bool(PORTAL_ENABLED_PARAM),
      param=PORTAL_ENABLED_PARAM,
    )
    self._refresh_button = button_item_sp(
      title=lambda: tr("Portal Address"),
      button_text=lambda: tr("REFRESH"),
      description=lambda: tr("Refresh the displayed local URL, QR code, and route count."),
      callback=lambda: self._status_card.refresh(force=True),
    )
    self._port_item = button_item_sp(
      title=lambda: tr("Portal Port"),
      button_text=lambda: tr("DEFAULT"),
      description=lambda: tr("The SubiPilot Portal listens on this port when enabled."),
      callback=None,
      enabled=False,
    )

    self._scroller = Scroller([
      self._status_card,
      LineSeparator(),
      self._enable_toggle,
      LineSeparator(),
      self._refresh_button,
      LineSeparator(),
      self._port_item,
    ], line_separator=False, spacing=0)

  def _update_state(self):
    self._enable_toggle.action_item.set_state(ui_state.params.get_bool(PORTAL_ENABLED_PARAM))
    self._refresh_button.action_item.set_value(self._status_card.url)
    self._port_item.action_item.set_value(str(get_port(ui_state.params)))

  def _render(self, rect: rl.Rectangle):
    self._scroller.render(rect)
