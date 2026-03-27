"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets import DialogResult
from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog
from openpilot.system.ui.widgets.list_view import ButtonAction
from openpilot.system.ui.widgets.scroller_tici import Scroller

from openpilot.sunnypilot.selfdrive.vehicle_profiles import delete_vehicle_profile, get_display_profile_key, get_profile_state_text, vehicle_profile_exists
from openpilot.selfdrive.ui.sunnypilot.layouts.settings.vehicle.brands.factory import BrandSettingsFactory
from openpilot.selfdrive.ui.sunnypilot.layouts.settings.vehicle.platform_selector import PlatformSelector, LegendWidget
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.sunnypilot.widgets.list_view import ListItemSP


class VehicleLayout(Widget):
  def __init__(self):
    super().__init__()
    self._brand_settings = None
    self._brand_items = []
    self._current_brand = None
    self._platform_selector = PlatformSelector(self._update_brand_settings)

    self._vehicle_item = ListItemSP(title=self._platform_selector.text, action_item=ButtonAction(text=tr("SELECT")),
                                    callback=self._platform_selector._on_clicked)
    self._vehicle_item.title_color = self._platform_selector.color
    self._legend_widget = LegendWidget(self._platform_selector)
    self._profile_status_item = ListItemSP(title=tr("Vehicle Profile"), description="", description_visible=True, inline=False)
    self._reset_profile_item = ListItemSP(
      title=tr("Reset Current Vehicle Profile"),
      description=tr("Delete the saved visual/info profile for the currently detected vehicle."),
      action_item=ButtonAction(text=tr("RESET"), enabled=self._can_reset_profile),
      callback=self._confirm_reset_profile,
      inline=False,
    )

    self.items = [self._vehicle_item, self._legend_widget, self._profile_status_item, self._reset_profile_item]
    self._scroller = Scroller(self.items, line_separator=True, spacing=0)

  @staticmethod
  def get_brand():
    if bundle := ui_state.params.get("CarPlatformBundle"):
      return bundle.get("brand", "")
    elif ui_state.CP is not None and ui_state.CP.carFingerprint != "MOCK":
      return ui_state.CP.brand
    return ""

  def _update_brand_settings(self):
    self._vehicle_item._title = self._platform_selector.text
    self._vehicle_item.title_color = self._platform_selector.color
    vehicle_text = tr("REMOVE") if ui_state.params.get("CarPlatformBundle") else tr("SELECT")
    self._vehicle_item.action_item.set_text(vehicle_text)
    self._profile_status_item.set_description(tr(get_profile_state_text(ui_state.params, self._get_profile_key())))
    self._profile_status_item.set_right_value(self._get_profile_key() or tr("Not detected"))

    brand = self.get_brand()
    if brand != self._current_brand:
      self._current_brand = brand
      self._brand_settings = BrandSettingsFactory.create_brand_settings(brand)
      self._brand_items = self._brand_settings.items if self._brand_settings else []

      self.items = [self._vehicle_item, self._legend_widget, self._profile_status_item, self._reset_profile_item] + self._brand_items
      self._scroller = Scroller(self.items, line_separator=True, spacing=0)

  def _update_state(self):
    self._update_brand_settings()
    if self._brand_settings:
      self._brand_settings.update_settings()
    self._platform_selector.refresh()

  def _render(self, rect):
    self._scroller.render(rect)

  def show_event(self):
    self._scroller.show_event()

  def _get_profile_key(self) -> str:
    detected_key = ui_state.CP.carFingerprint if ui_state.CP is not None and ui_state.CP.carFingerprint != "MOCK" else None
    return get_display_profile_key(ui_state.params, detected_key)

  def _can_reset_profile(self) -> bool:
    return vehicle_profile_exists(ui_state.params, self._get_profile_key())

  def _confirm_reset_profile(self):
    key = self._get_profile_key()
    if not vehicle_profile_exists(ui_state.params, key):
      return

    def _callback(result: DialogResult):
      if result == DialogResult.CONFIRM:
        delete_vehicle_profile(ui_state.params, key)
        self._update_brand_settings()

    gui_app.push_widget(ConfirmDialog(
      tr("Are you sure you want to delete the saved profile for this vehicle?"),
      tr("Reset"),
      callback=_callback,
    ))
