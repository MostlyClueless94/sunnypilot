"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from collections.abc import Callable

from openpilot.selfdrive.ui.mici.widgets.button import BigButton, BigParamControl, GreyBigButton
from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import CUSTOM_MODEL_PATH_COLOR_LABELS
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.widgets.scroller import NavScroller


ANGLE_ONLY_DESC = "angle-based Subaru only; older torque models unaffected"
RESUME_SOFTNESS_LABELS = ["standard", "soft", "softer", "very soft", "extra soft", "softest", "max soft"]
RELEASE_GUARD_LEVEL_LABELS = ["light", "medium", "strong"]
SOFT_CAPTURE_STRENGTH_LABELS = ["1 - Light", "2 - Mild", "3 - Medium", "4 - Strong", "5 - Max"]
MANUAL_YIELD_TORQUE_THRESHOLD_MIN = 40
MANUAL_YIELD_TORQUE_THRESHOLD_MAX = 80
MANUAL_YIELD_TORQUE_THRESHOLD_STEP = 5


class SubaruLayoutMici(NavScroller):
  def __init__(self, back_callback: Callable):
    super().__init__()
    self.set_back_callback(back_callback)
    self.original_back_callback = back_callback
    self.focused_widget = None

    self._lateral_header = GreyBigButton("angle subaru\ntuning")
    self._visuals_header = GreyBigButton("visuals")

    self._match_vehicle_speed = BigParamControl(
      "match vehicle\nspeedometer",
      "MCSubaruMatchVehicleSpeedometer",
      desc="Subaru dash speed when supported; off uses true speed",
    )
    self._subaru_advanced_tuning_toggle = BigParamControl(
      "advanced\ntuning",
      "MCSubaruAdvancedTuning",
      desc=f"show angle Subaru tuning controls; {ANGLE_ONLY_DESC}",
    )
    self._manual_yield_torque_threshold_toggle = BigParamControl(
      "custom yield\ntorque",
      "MCSubaruManualYieldTorqueThresholdEnabled",
      desc=f"custom manual-yield torque threshold; values near 40 may false-trigger override in turns; {ANGLE_ONLY_DESC}",
    )
    self._manual_yield_resume_softness_toggle = BigParamControl(
      "custom resume\nsoftness",
      "MCSubaruManualYieldResumeSoftnessEnabled",
      desc=f"optional post-manual-yield steering reclaim ramp; off means no SubiPilot reclaim ramp; {ANGLE_ONLY_DESC}",
    )
    self._manual_yield_release_guard_toggle = BigParamControl(
      "manual yield\nrelease guard",
      "MCSubaruManualYieldReleaseGuardEnabled",
      desc=f"wait for a cleaner release after manual yield; {ANGLE_ONLY_DESC}",
    )
    self._subaru_soft_capture_toggle = BigParamControl(
      "soft-capture\nengage blend",
      "MCSubaruSoftCaptureEnabled",
      desc=f"smooth steering handoff on engage; {ANGLE_ONLY_DESC}",
    )

    self._manual_yield_torque_threshold_btn = BigButton("manual yield\ntorque")
    self._manual_yield_torque_threshold_btn.set_click_callback(
      lambda: self._show_value_selector(
        self._manual_yield_torque_threshold_btn,
        "MCSubaruManualYieldTorqueThreshold",
        list(range(
          MANUAL_YIELD_TORQUE_THRESHOLD_MIN,
          MANUAL_YIELD_TORQUE_THRESHOLD_MAX + MANUAL_YIELD_TORQUE_THRESHOLD_STEP,
          MANUAL_YIELD_TORQUE_THRESHOLD_STEP,
        )),
        self._format_manual_yield_torque_threshold_label,
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
    self._manual_yield_release_guard_btn = BigButton("release guard\nstrength")
    self._manual_yield_release_guard_btn.set_click_callback(
      lambda: self._show_value_selector(
        self._manual_yield_release_guard_btn,
        "MCSubaruManualYieldReleaseGuardLevel",
        list(range(1, 4)),
        self._format_release_guard_label,
      )
    )
    self._subaru_soft_capture_strength_btn = BigButton("soft-capture\nstrength")
    self._subaru_soft_capture_strength_btn.set_click_callback(
      lambda: self._show_value_selector(
        self._subaru_soft_capture_strength_btn,
        "MCSubaruSoftCaptureLevel",
        list(range(1, 6)),
        self._format_soft_capture_label,
      )
    )

    self._show_brake_status = BigParamControl("show brake\nstatus", "ShowBrakeStatus", desc="red when brake lights are on")
    self._show_confidence_ball = BigParamControl("show confidence\nball", "BPShowConfidenceBall", desc="display onroad confidence ball")
    self._dynamic_path_color = BigParamControl(
      "dynamic path\ncolor",
      "DynamicPathColor",
      desc="light gray inactive, teal steering-only, green full control",
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
    self._hide_v_ego_ui = BigParamControl("hide\nspeedometer", "HideVEgoUI")

    self.main_items = [
      self._lateral_header,
      self._subaru_advanced_tuning_toggle,
      self._manual_yield_torque_threshold_toggle,
      self._manual_yield_torque_threshold_btn,
      self._manual_yield_resume_softness_toggle,
      self._manual_yield_resume_softness_btn,
      self._manual_yield_release_guard_toggle,
      self._manual_yield_release_guard_btn,
      self._subaru_soft_capture_toggle,
      self._subaru_soft_capture_strength_btn,
      self._visuals_header,
      self._match_vehicle_speed,
      self._show_brake_status,
      self._show_confidence_ball,
      self._dynamic_path_color,
      self._custom_model_path_color_btn,
      self._hide_v_ego_ui,
    ]
    self._scroller.add_widgets(self.main_items)

    self._refresh_toggles = (
      ("MCSubaruMatchVehicleSpeedometer", self._match_vehicle_speed, True),
      ("MCSubaruAdvancedTuning", self._subaru_advanced_tuning_toggle, False),
      ("MCSubaruManualYieldTorqueThresholdEnabled", self._manual_yield_torque_threshold_toggle, False),
      ("MCSubaruManualYieldResumeSoftnessEnabled", self._manual_yield_resume_softness_toggle, False),
      ("MCSubaruManualYieldReleaseGuardEnabled", self._manual_yield_release_guard_toggle, False),
      ("MCSubaruSoftCaptureEnabled", self._subaru_soft_capture_toggle, False),
      ("ShowBrakeStatus", self._show_brake_status, False),
      ("BPShowConfidenceBall", self._show_confidence_ball, False),
      ("DynamicPathColor", self._dynamic_path_color, False),
      ("HideVEgoUI", self._hide_v_ego_ui, False),
    )

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
    if value is None:
      return default
    if isinstance(value, bool):
      return value
    if isinstance(value, bytes):
      return value not in (b"", b"0")
    if isinstance(value, str):
      return value not in ("", "0", "false", "False")
    return bool(value)

  @staticmethod
  def _format_resume_softness_label(value: int) -> str:
    return RESUME_SOFTNESS_LABELS[max(0, min(value, len(RESUME_SOFTNESS_LABELS) - 1))]

  @staticmethod
  def _format_release_guard_label(value: int) -> str:
    return RELEASE_GUARD_LEVEL_LABELS[max(0, min(value - 1, len(RELEASE_GUARD_LEVEL_LABELS) - 1))]

  @staticmethod
  def _clamp_manual_yield_torque_threshold(value: int) -> int:
    clamped = max(MANUAL_YIELD_TORQUE_THRESHOLD_MIN, min(value, MANUAL_YIELD_TORQUE_THRESHOLD_MAX))
    rounded = ((clamped + (MANUAL_YIELD_TORQUE_THRESHOLD_STEP // 2)) // MANUAL_YIELD_TORQUE_THRESHOLD_STEP) * MANUAL_YIELD_TORQUE_THRESHOLD_STEP
    return max(MANUAL_YIELD_TORQUE_THRESHOLD_MIN, min(rounded, MANUAL_YIELD_TORQUE_THRESHOLD_MAX))

  @staticmethod
  def _format_manual_yield_torque_threshold_label(value: int) -> str:
    clamped = SubaruLayoutMici._clamp_manual_yield_torque_threshold(value)
    return "80 - Stock" if clamped == MANUAL_YIELD_TORQUE_THRESHOLD_MAX else str(clamped)

  @staticmethod
  def _format_soft_capture_label(value: int) -> str:
    return SOFT_CAPTURE_STRENGTH_LABELS[max(0, min(value - 1, len(SOFT_CAPTURE_STRENGTH_LABELS) - 1))]

  def _set_advanced_tuning_visibility(self, enabled: bool) -> None:
    self._manual_yield_torque_threshold_toggle.set_visible(enabled)
    self._manual_yield_torque_threshold_btn.set_visible(enabled)
    self._manual_yield_resume_softness_toggle.set_visible(enabled)
    self._manual_yield_resume_softness_btn.set_visible(enabled)
    self._manual_yield_release_guard_toggle.set_visible(enabled)
    self._manual_yield_release_guard_btn.set_visible(enabled)
    self._subaru_soft_capture_toggle.set_visible(enabled)
    self._subaru_soft_capture_strength_btn.set_visible(enabled)

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

    for key, item, default in self._refresh_toggles:
      item.set_checked(self._get_bool_param(key, default))

    advanced_tuning_enabled = self._get_bool_param("MCSubaruAdvancedTuning")
    torque_threshold_enabled = self._get_bool_param("MCSubaruManualYieldTorqueThresholdEnabled")
    resume_softness_enabled = self._get_bool_param("MCSubaruManualYieldResumeSoftnessEnabled")
    release_guard_enabled = self._get_bool_param("MCSubaruManualYieldReleaseGuardEnabled")
    soft_capture_enabled = self._get_bool_param("MCSubaruSoftCaptureEnabled")
    self._set_advanced_tuning_visibility(advanced_tuning_enabled)
    self._manual_yield_torque_threshold_btn.set_enabled(torque_threshold_enabled)
    self._manual_yield_resume_softness_btn.set_enabled(resume_softness_enabled)
    self._manual_yield_release_guard_btn.set_enabled(release_guard_enabled)
    self._subaru_soft_capture_strength_btn.set_enabled(soft_capture_enabled)
    self._manual_yield_torque_threshold_btn.set_value(
      self._format_manual_yield_torque_threshold_label(
        self._clamp_manual_yield_torque_threshold(self._get_int_param("MCSubaruManualYieldTorqueThreshold", MANUAL_YIELD_TORQUE_THRESHOLD_MAX))
      )
    )
    self._manual_yield_resume_softness_btn.set_value(
      self._format_resume_softness_label(max(0, min(self._get_int_param("MCSubaruManualYieldResumeSoftness", 4), 6)))
    )
    self._manual_yield_release_guard_btn.set_value(
      self._format_release_guard_label(max(1, min(self._get_int_param("MCSubaruManualYieldReleaseGuardLevel", 2), 3)))
    )
    self._subaru_soft_capture_strength_btn.set_value(
      self._format_soft_capture_label(max(1, min(self._get_int_param("MCSubaruSoftCaptureLevel", 3), 5)))
    )

    model_color_index = max(0, min(self._get_int_param("CustomModelPathColor"), len(CUSTOM_MODEL_PATH_COLOR_LABELS) - 1))
    self._custom_model_path_color_btn.set_value(CUSTOM_MODEL_PATH_COLOR_LABELS[model_color_index].lower())

  def show_event(self):
    super().show_event()
    self._set_advanced_tuning_visibility(self._get_bool_param("MCSubaruAdvancedTuning"))
    self._reset_main_view()
