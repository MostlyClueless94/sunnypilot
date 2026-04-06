"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from collections.abc import Callable

from openpilot.selfdrive.ui.mici.widgets.button import BigButton, BigParamControl, GreyBigButton
from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import CUSTOM_MODEL_PATH_COLOR_LABELS
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets.scroller import NavScroller

RESUME_SPEED_LABELS = ["Fastest", "Faster", "Fast", "Medium", "Slow", "Slower", "Slowest"]
RESUME_SOFTNESS_LABELS = ["Standard", "Soft", "Softer", "Very Soft", "Extra Soft", "Softest", "Max Soft"]


class SubaruLayoutMici(NavScroller):
  def __init__(self, back_callback: Callable):
    super().__init__()
    self.set_back_callback(back_callback)
    self.original_back_callback = back_callback
    self.focused_widget = None

    self._lateral_header = GreyBigButton("lateral\ntuning")
    self._visuals_header = GreyBigButton("visuals")

    self._subaru_advanced_tuning_toggle = BigParamControl("advanced\ntuning", "MCSubaruAdvancedTuning",
                                                          desc="show Subaru lateral tuning controls")
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
    self._manual_yield_resume_speed_btn = BigButton("manual yield\nresume speed")
    self._manual_yield_resume_speed_btn.set_click_callback(
      lambda: self._show_value_selector(
        self._manual_yield_resume_speed_btn,
        "MCSubaruManualYieldResumeSpeed",
        list(range(7)),
        self._format_resume_speed_label,
      )
    )
    self._manual_yield_resume_softness_btn = BigButton("manual yield\nresume softness")
    self._manual_yield_resume_softness_btn.set_click_callback(
      lambda: self._show_value_selector(
        self._manual_yield_resume_softness_btn,
        "MCSubaruManualYieldResumeSoftness",
        list(range(7)),
        self._format_resume_softness_label,
      )
    )

    self._show_brake_status = BigParamControl("show brake\nstatus", "ShowBrakeStatus", desc="red when brake lights are on")
    self._show_confidence_ball = BigParamControl("show confidence\nball", "BPShowConfidenceBall", desc="display onroad confidence ball")
    self._dynamic_path_color = BigParamControl("dynamic path\ncolor", "DynamicPathColor",
                                               desc="light gray inactive, teal steering-only, green full control")

    self._custom_model_path_color_btn = BigButton("custom model\npath color")
    self._custom_model_path_color_btn.set_click_callback(
      lambda: self._show_value_selector(
        self._custom_model_path_color_btn,
        "CustomModelPathColor",
        list(range(len(CUSTOM_MODEL_PATH_COLOR_LABELS))),
        lambda value: CUSTOM_MODEL_PATH_COLOR_LABELS[value].lower(),
      )
    )

    self._match_vehicle_speed = BigParamControl(
      "match vehicle\nspeedometer",
      "MatchVehicleSpeedometer",
      desc="on: dash speed, off: true speed",
    )
    self._hide_v_ego_ui = BigParamControl("hide\nspeedometer", "HideVEgoUI")

    self.main_items = [
      self._lateral_header,
      self._subaru_advanced_tuning_toggle,
      self._subaru_smoothing_toggle,
      self._subaru_smoothing_strength_btn,
      self._subaru_center_damping_btn,
      self._manual_yield_resume_speed_btn,
      self._manual_yield_resume_softness_btn,
      self._visuals_header,
      self._show_brake_status,
      self._show_confidence_ball,
      self._dynamic_path_color,
      self._custom_model_path_color_btn,
      self._match_vehicle_speed,
      self._hide_v_ego_ui,
    ]
    self._scroller.add_widgets(self.main_items)

    self._refresh_toggles = (
      ("MCSubaruAdvancedTuning", self._subaru_advanced_tuning_toggle),
      ("MCSubaruSmoothingTune", self._subaru_smoothing_toggle),
      ("ShowBrakeStatus", self._show_brake_status),
      ("BPShowConfidenceBall", self._show_confidence_ball),
      ("DynamicPathColor", self._dynamic_path_color),
      ("MatchVehicleSpeedometer", self._match_vehicle_speed),
      ("HideVEgoUI", self._hide_v_ego_ui),
    )

  @staticmethod
  def _format_strength_label(value: int) -> str:
    return "stock" if value == 0 else f"{value:+d}"

  @staticmethod
  def _format_resume_speed_label(value: int) -> str:
    return RESUME_SPEED_LABELS[max(0, min(value, len(RESUME_SPEED_LABELS) - 1))]

  @staticmethod
  def _format_resume_softness_label(value: int) -> str:
    return RESUME_SOFTNESS_LABELS[max(0, min(value, len(RESUME_SOFTNESS_LABELS) - 1))]

  def _set_advanced_tuning_visibility(self, enabled: bool) -> None:
    self._subaru_smoothing_toggle.set_visible(enabled)
    self._subaru_smoothing_strength_btn.set_visible(enabled)
    self._subaru_center_damping_btn.set_visible(enabled)
    self._manual_yield_resume_speed_btn.set_visible(enabled)
    self._manual_yield_resume_softness_btn.set_visible(enabled)

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
      item.set_checked(self._get_bool_param(key, True) if key == "MatchVehicleSpeedometer" else self._get_bool_param(key))

    advanced_tuning_enabled = ui_state.params.get_bool("MCSubaruAdvancedTuning")
    smoothing_enabled = ui_state.params.get_bool("MCSubaruSmoothingTune")
    self._set_advanced_tuning_visibility(advanced_tuning_enabled)
    self._subaru_smoothing_strength_btn.set_enabled(smoothing_enabled)
    self._subaru_center_damping_btn.set_enabled(smoothing_enabled)
    self._subaru_smoothing_strength_btn.set_value(self._format_strength_label(max(-3, min(self._get_int_param("MCSubaruSmoothingStrength"), 4))))
    self._subaru_center_damping_btn.set_value(self._format_strength_label(max(-3, min(self._get_int_param("MCSubaruCenterDampingStrength"), 4))))
    self._manual_yield_resume_speed_btn.set_value(self._format_resume_speed_label(max(0, min(self._get_int_param("MCSubaruManualYieldResumeSpeed", 4), 6))))
    self._manual_yield_resume_softness_btn.set_value(self._format_resume_softness_label(max(0, min(self._get_int_param("MCSubaruManualYieldResumeSoftness", 4), 6))))

    model_color_index = max(0, min(self._get_int_param("CustomModelPathColor"), len(CUSTOM_MODEL_PATH_COLOR_LABELS) - 1))
    self._custom_model_path_color_btn.set_value(CUSTOM_MODEL_PATH_COLOR_LABELS[model_color_index].lower())

  def show_event(self):
    super().show_event()
    self._set_advanced_tuning_visibility(ui_state.params.get_bool("MCSubaruAdvancedTuning"))
    self._reset_main_view()
