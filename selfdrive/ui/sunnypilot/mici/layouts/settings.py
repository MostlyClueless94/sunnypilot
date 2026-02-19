"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from enum import IntEnum

from openpilot.selfdrive.ui.mici.layouts.settings import settings as OP
from openpilot.selfdrive.ui.mici.widgets.button import BigButton
from openpilot.selfdrive.ui.sunnypilot.mici.layouts.sunnylink import SunnylinkLayoutMici
from openpilot.selfdrive.ui.sunnypilot.mici.layouts.models import ModelsLayoutMici
# BluePilot: START - BP settings tab import
from openpilot.selfdrive.ui.bp.mici.layouts.settings.bluepilot import BluePilotLayoutMici
# BluePilot: END - BP settings tab import

ICON_SIZE = 70

OP.PanelType = IntEnum(
  "PanelType",
  [es.name for es in OP.PanelType] + [
    "SUNNYLINK",
    "MODELS",
    "BLUEPILOT",  # BluePilot: START/END - BP settings panel type
  ],
  start=0,
)


class SettingsLayoutSP(OP.SettingsLayout):
  def __init__(self):
    OP.SettingsLayout.__init__(self)

    sunnylink_btn = BigButton("sunnylink", "", "icons_mici/settings/developer/ssh.png")
    sunnylink_btn.set_click_callback(lambda: self._set_current_panel(OP.PanelType.SUNNYLINK))

    models_btn = BigButton("models", "", "../../sunnypilot/selfdrive/assets/offroad/icon_models.png")
    models_btn.set_click_callback(lambda: self._set_current_panel(OP.PanelType.MODELS))

    # BluePilot: START - BP settings button and panel
    bluepilot_btn = BigButton("BluePilot", "", "icons/chffr_wheel.png")
    bluepilot_btn.set_click_callback(lambda: self._set_current_panel(OP.PanelType.BLUEPILOT))
    # BluePilot: END - BP settings button and panel

    self._panels.update({
      OP.PanelType.SUNNYLINK: OP.PanelInfo("sunnylink", SunnylinkLayoutMici(back_callback=lambda: self._set_current_panel(None))),
      OP.PanelType.MODELS: OP.PanelInfo("models", ModelsLayoutMici(back_callback=lambda: self._set_current_panel(None))),
      # BluePilot: START - BP settings panel entry
      OP.PanelType.BLUEPILOT: OP.PanelInfo("BluePilot", BluePilotLayoutMici(back_callback=lambda: self._set_current_panel(None))),
      # BluePilot: END - BP settings panel entry
    })

    items = self._scroller._items.copy()

    items.insert(1, sunnylink_btn)
    items.insert(2, models_btn)
    # BluePilot: START - insert BP button into scroller
    items.insert(3, bluepilot_btn)
    # BluePilot: END - insert BP button into scroller
    self._scroller._items.clear()
    for item in items:
      self._scroller.add_widget(item)
