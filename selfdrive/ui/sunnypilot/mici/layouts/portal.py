"""
SubiPilot Portal settings page for MICI.
"""

from collections.abc import Callable

import pyray as rl

from openpilot.selfdrive.ui.mici.widgets.button import BigButton, BigParamControl
from openpilot.selfdrive.ui.sunnypilot.layouts.settings.portal_common import (
  CachedPortalInfo,
  FEATURE_SUMMARY,
  NETWORK_SAFETY_NOTE,
  PORTAL_ENABLED_PARAM,
  get_port,
)
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets.scroller import NavScroller


def _draw_qr(matrix: list[list[bool]], rect: rl.Rectangle) -> None:
  if not matrix:
    return

  size = len(matrix)
  cell = max(1, int(min(rect.width, rect.height) // size))
  qr_size = cell * size
  x0 = int(rect.x + (rect.width - qr_size) / 2)
  y0 = int(rect.y + (rect.height - qr_size) / 2)
  rl.draw_rectangle(x0 - 6, y0 - 6, qr_size + 12, qr_size + 12, rl.WHITE)
  for y, row in enumerate(matrix):
    for x, filled in enumerate(row):
      if filled:
        rl.draw_rectangle(x0 + x * cell, y0 + y * cell, cell, cell, rl.BLACK)


class PortalQRButton(BigButton):
  QR_RESERVED_WIDTH = 146
  QR_SIZE = 112
  QR_TOP_OFFSET = 24

  def __init__(self, info: CachedPortalInfo):
    super().__init__(tr("portal\naddress"), "", scroll=True)
    self.info = info

  def _should_draw_qr(self) -> bool:
    return ui_state.params.get_bool(PORTAL_ENABLED_PARAM) and bool(self.info.qr_matrix)

  def _width_hint(self) -> int:
    width = super()._width_hint()
    return max(120, width - self.QR_RESERVED_WIDTH) if self._should_draw_qr() else width

  def _draw_content(self, btn_y: float):
    super()._draw_content(btn_y)
    if self._should_draw_qr():
      _draw_qr(
        self.info.qr_matrix,
        rl.Rectangle(self._rect.x + self._rect.width - self.QR_RESERVED_WIDTH, btn_y + self.QR_TOP_OFFSET, self.QR_SIZE, self.QR_SIZE),
      )


class SubiPilotPortalLayoutMici(NavScroller):
  def __init__(self, back_callback: Callable):
    super().__init__()
    self.set_back_callback(back_callback)
    self.info = CachedPortalInfo(ui_state.params)

    self.enable_btn = BigParamControl(
      text=tr("enable\nportal"),
      param=PORTAL_ENABLED_PARAM,
      desc=tr("Host the SubiPilot Portal on your local network."),
    )
    self.url_btn = PortalQRButton(self.info)
    self.url_btn.set_click_callback(lambda: self.info.refresh(force=True))

    self.stats_btn = BigButton(tr("route\nstats"), "")
    self.stats_btn.set_click_callback(lambda: self.info.refresh(force=True))

    self.features_btn = BigButton(tr("portal\nfeatures"), tr("routes, logs, videos, params"), scroll=True)
    self.safety_btn = BigButton(tr("network\nsafety"), tr(NETWORK_SAFETY_NOTE), scroll=True)
    self.port_btn = BigButton(tr("portal\nport"), str(get_port(ui_state.params)))

    self._scroller.add_widgets([
      self.enable_btn,
      self.url_btn,
      self.stats_btn,
      self.features_btn,
      self.safety_btn,
      self.port_btn,
    ])

  def _update_state(self):
    super()._update_state()
    self.info.refresh()
    enabled = ui_state.params.get_bool(PORTAL_ENABLED_PARAM)
    self.enable_btn.refresh()
    self.url_btn.set_value(self.info.url if enabled else tr("enable portal first"))
    self.stats_btn.set_value(self.info.route_stats)
    self.features_btn.set_value(tr(FEATURE_SUMMARY))
    self.safety_btn.set_value(tr(NETWORK_SAFETY_NOTE))
    self.port_btn.set_value(str(get_port(ui_state.params)))
