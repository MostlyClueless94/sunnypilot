"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from collections.abc import Callable

from openpilot.selfdrive.ui.mici.widgets.button import BigButton, BigParamControl, GreyBigButton
from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import CUSTOM_MODEL_PATH_COLOR_LABELS, DYNAMIC_PATH_COLOR_PALETTE_LABELS
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets.scroller import NavScroller


class SubaruLayoutMici(NavScroller):
  def __init__(self, back_callback: Callable):
    super().__init__()
    self.set_back_callback(back_callback)
    self.original_back_callback = back_callback
    self.focused_widget = None

    self._lateral_header = GreyBigButton("lateral\ntuning")
    self._visuals_header = GreyBigButton("visuals")

    self._subaru_smoothing_toggle = BigParamControl("subaru steering\nsmoothing", "MCSubaruSmoothingTune")
    self._subaru_smoothing_strength_btn = BigButton("smoothing\nstrength")
    self._subaru_smoothing_strength_btn.set_click_callback(
      lambda: self._show_value_selector(
        self._subaru_smoothing_strength_btn,
        "MCSubaruSmoothingStrength",
        list(range(-3, 5)),
        self._format_strength_label,
      )
    )

    self._subaru_center_damping_btn = BigButton("center\ndamping")
    self._subaru_center_damping_btn.set_click_callback(
      lambda: self._show_value_selector(
        self._subaru_center_damping_btn,
        "MCSubaruCenterDampingStrength",
        list(range(-3, 5)),
        self._format_strength_label,
      )
    )

    self._show_brake_status = BigParamControl("show brake\nstatus", "ShowBrakeStatus", desc="red when brake lights are on")
    self._dynamic_path_color = BigParamControl("dynamic path\ncolor", "DynamicPathColor")

    self._dynamic_path_palette_btn = BigButton("dynamic path\npalette")
    self._dynamic_path_palette_btn.set_click_callback(
      lambda: self._show_value_selector(
        self._dynamic_path_palette_btn,
        "DynamicPathColorPalette",
        list(range(len(DYNAMIC_PATH_COLOR_PALETTE_LABELS))),
        lambda value: DYNAMIC_PATH_COLOR_PALETTE_LABELS[value].lower(),
      )
    )

    self._custom_model_path_color_btn = BigButton("custom model\npath color")
    self._custom_model_path_color_btn.set_click_callback(
      lambda: self._show_value_selector(
        self._custom_model_path_color_btn,
        "CustomModelPathColor",
        list(range(len(CUSTOM_MODEL_PATH_COLOR_LABELS))),
        lambda value: CUSTOM_MODEL_PATH_COLOR_LABELS[value].lower(),
      )
    )

    self._true_v_ego_ui = BigParamControl("always use\ntrue speed", "TrueVEgoUI", desc="off: dash speed, on: true speed")
    self._hide_v_ego_ui = BigParamControl("hide\nspeedometer", "HideVEgoUI")

    self.main_items = [
      self._lateral_header,
      self._subaru_smoothing_toggle,
      self._subaru_smoothing_strength_btn,
      self._subaru_center_damping_btn,
      self._visuals_header,
      self._show_brake_status,
      self._dynamic_path_color,
      self._dynamic_path_palette_btn,
      self._custom_model_path_color_btn,
      self._true_v_ego_ui,
      self._hide_v_ego_ui,
    ]
    self._scroller.add_widgets(self.main_items)

    self._refresh_toggles = (
      ("MCSubaruSmoothingTune", self._subaru_smoothing_toggle),
      ("ShowBrakeStatus", self._show_brake_status),
      ("DynamicPathColor", self._dynamic_path_color),
      ("TrueVEgoUI", self._true_v_ego_ui),
      ("HideVEgoUI", self._hide_v_ego_ui),
    )

  @staticmethod
  def _format_strength_label(value: int) -> str:
    return "stock" if value == 0 else f"{value:+d}"

  @staticmethod
  def _get_int_param(key: str, default: int = 0) -> int:
    value = ui_state.params.get(key, return_default=True)
    try:
      return int(value)
    except (TypeError, ValueError):
      return default

  @staticmethod
  def _get_bool_param(key: str, default: bool = False) -> bool:
    value = ui_state.params.get(key, return_default=True)
    return default if value is None else bool(value)

  def _show_selection_view(self, items, back_callback: Callable):
    self._scroller._items = items
    for item in items:
      item.set_touch_valid_callback(lambda: self._scroller.scroll_panel.is_touch_valid() and self._scroller.enabled)
    self._scroller.scroll_panel.set_offset(0)
    self.set_back_callback(back_callback)

  def _show_value_selector(self, focused_widget: BigButton, param: str, values: list[int], label_callback: Callable[[int], str]):
    self.focused_widget = focused_widget
    current_value = self._get_int_param(param)
    header = GreyBigButton("", "tap a value to select")
    buttons = [header]
    for value in values:
      label = label_callback(value)
      btn = BigButton(label)
      if value == current_value:
        btn.set_value("selected")
      btn.set_click_callback(lambda value=value, param=param: self._select_value(param, value))
      buttons.append(btn)
    self._show_selection_view(buttons, self._reset_main_view)

  def _select_value(self, param: str, value: int):
    ui_state.params.put(param, value)
    self._reset_main_view()

  def _reset_main_view(self):
    self._scroller._items = self.main_items
    self.set_back_callback(self.original_back_callback)
    if self.focused_widget and self.focused_widget in self.main_items:
      x = self._scroller._pad
      for item in self.main_items:
        if not item.is_visible:
          continue
        if item == self.focused_widget:
          break
        x += item.rect.width + self._scroller._spacing
      self._scroller.scroll_panel.set_offset(0)
      self._scroller.scroll_to(x)
      self.focused_widget = None
    else:
      self._scroller.scroll_panel.set_offset(0)

  def _update_state(self):
    super()._update_state()

    for key, item in self._refresh_toggles:
      item.set_checked(self._get_bool_param(key))

    smoothing_enabled = ui_state.params.get_bool("MCSubaruSmoothingTune")
    self._subaru_smoothing_strength_btn.set_enabled(smoothing_enabled)
    self._subaru_center_damping_btn.set_enabled(smoothing_enabled)
    self._subaru_smoothing_strength_btn.set_value(self._format_strength_label(max(-3, min(self._get_int_param("MCSubaruSmoothingStrength"), 4))))
    self._subaru_center_damping_btn.set_value(self._format_strength_label(max(-3, min(self._get_int_param("MCSubaruCenterDampingStrength"), 4))))

    dynamic_path_enabled = ui_state.params.get_bool("DynamicPathColor")
    self._dynamic_path_palette_btn.set_enabled(dynamic_path_enabled)
    palette_index = max(0, min(self._get_int_param("DynamicPathColorPalette"), len(DYNAMIC_PATH_COLOR_PALETTE_LABELS) - 1))
    self._dynamic_path_palette_btn.set_value(DYNAMIC_PATH_COLOR_PALETTE_LABELS[palette_index].lower())

    model_color_index = max(0, min(self._get_int_param("CustomModelPathColor"), len(CUSTOM_MODEL_PATH_COLOR_LABELS) - 1))
    self._custom_model_path_color_btn.set_value(CUSTOM_MODEL_PATH_COLOR_LABELS[model_color_index].lower())

  def show_event(self):
    super().show_event()
    self._reset_main_view()
