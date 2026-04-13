"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from collections.abc import Callable

import pyray as rl

from openpilot.common.params import Params
from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import CUSTOM_MODEL_PATH_COLOR_LABELS
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.sunnypilot.lib.styles import style
from openpilot.system.ui.sunnypilot.widgets.list_view import multiple_button_item_sp, option_item_sp, toggle_item_sp
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.scroller_tici import Scroller


ANGLE_ONLY_DESC = "Angle-based Subaru only. Does not affect older torque-based Subaru models."
STAGING_EXPERIMENT_DESC = "Experiment - subi-staging only."
ADVANCED_TUNING_DESC = f"Show angle Subaru tuning controls. Hidden controls keep their saved values active. {ANGLE_ONLY_DESC}"
CUSTOM_YIELD_TORQUE_DESC = (
  "Enable a custom Subaru manual-yield torque threshold. When off, manual override detection falls back to "
  + "the stock Subaru threshold for your platform while keeping your saved test value. "
  + "Settings near the minimum may falsely detect manual override while openpilot is steering through turns. "
  + f"40 is the minimum allowed test value. {ANGLE_ONLY_DESC}"
)
YIELD_TORQUE_DESC = (
  "Adjust the steering torque required to count as manual yield. Lower values detect lighter steady driver "
  + "input sooner, but settings near the minimum may falsely detect manual override while openpilot is steering through turns. "
  + f"40 is the minimum allowed test value; 80 matches the stock threshold on modern Subaru angle-LKAS platforms. {ANGLE_ONLY_DESC}"
)
CUSTOM_RESUME_SOFTNESS_DESC = (
  "Enable a custom post-manual-yield steering reclaim ramp. When off, no SubiPilot reclaim ramp is applied "
  + f"and your saved softness selection is kept for later testing. {ANGLE_ONLY_DESC}"
)
RESUME_SOFTNESS_DESC = (
  "Adjust how gently the optional steering reclaim ramp re-engages after manual override. Higher levels reduce the initial reclaim bite. "
  + ANGLE_ONLY_DESC
)
RELEASE_GUARD_DESC = (
  "Keep Subaru manual-yield override active a bit longer after steering input briefly drops. "
  + f"This can reduce false reclaim jerks when you are still holding the wheel at a steady angle. {ANGLE_ONLY_DESC}"
)
RELEASE_GUARD_STRENGTH_DESC = (
  "Adjust how much confirmation Subaru waits for before reclaim begins after manual override. "
  + f"Higher levels wait longer for a clean release before the existing resume ramp starts. {ANGLE_ONLY_DESC}"
)
SOFT_CAPTURE_DESC = (
  "Smooth the transition when openpilot takes back steering control. "
  + "When enabled, the wheel angle blends gradually toward the model target "
  + f"instead of snapping instantly. {ANGLE_ONLY_DESC} {STAGING_EXPERIMENT_DESC}"
)
SOFT_CAPTURE_STRENGTH_DESC = (
  "Adjust how gently openpilot reclaims steering on engage. "
  + "Level 1 is a light blend (0.15 s). Level 5 is the most damped "
  + f"(0.50 s, near-zero start). Higher levels reduce snap-to-target feel but extend the handoff window. {ANGLE_ONLY_DESC}"
)
DYNAMIC_PATH_COLOR_DESC = (
  "Color the driving path by drive mode. Light gray when inactive or truly "
  + "overriding, teal when steering-only, and green for full control."
)
CUSTOM_MODEL_PATH_COLOR_DESC = (
  "Use preset colors for the driving path overlay. Stock keeps the normal "
  + "path behavior, and Dynamic Path Color still takes priority when enabled."
)
MATCH_VEHICLE_SPEED_DESC = (
  "When enabled, the Subaru on-road speedometer matches the vehicle dash or cluster speed when supported. "
  + "Turn it off to show true wheel-speed-based speed instead."
)

RESUME_SOFTNESS_LABELS = ["Standard", "Soft", "Softer", "Very Soft", "Extra Soft", "Softest", "Max Soft"]
RELEASE_GUARD_LEVEL_LABELS = ["Light", "Medium", "Strong"]
SOFT_CAPTURE_STRENGTH_LABELS = ["1 - Light", "2 - Mild", "3 - Medium", "4 - Strong", "5 - Max"]
MANUAL_YIELD_TORQUE_THRESHOLD_MIN = 40
MANUAL_YIELD_TORQUE_THRESHOLD_MAX = 80
MANUAL_YIELD_TORQUE_THRESHOLD_STEP = 5


class SubaruSectionHeader(Widget):
  def __init__(self, title: str | Callable[[], str]):
    super().__init__()
    self._title = title
    self._font = gui_app.font(FontWeight.BOLD)
    self._rect.height = 72

  @property
  def title(self) -> str:
    return self._title() if callable(self._title) else self._title

  def _render(self, _):
    title = self.title
    text_size = measure_text_cached(self._font, title, 42)
    text_y = self._rect.y + max(0, (self._rect.height - text_size.y) / 2)
    rl.draw_text_ex(self._font, title, rl.Vector2(self._rect.x + style.ITEM_PADDING, text_y), 42, 0, rl.WHITE)


class SubaruLayout(Widget):
  def __init__(self):
    super().__init__()
    self._params = Params()
    self._items = self._initialize_items()
    self._scroller = Scroller(self._items, line_separator=True, spacing=0)

  def _get_int_param(self, key: str, default: int = 0) -> int:
    value = self._params.get(key, return_default=True)
    try:
      return int(value)
    except (TypeError, ValueError):
      return default

  def _get_bool_param(self, key: str, default: bool = False) -> bool:
    value = self._params.get(key, return_default=True)
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
    return tr(RESUME_SOFTNESS_LABELS[max(0, min(value, len(RESUME_SOFTNESS_LABELS) - 1))])

  @staticmethod
  def _format_release_guard_label(value: int) -> str:
    return tr(RELEASE_GUARD_LEVEL_LABELS[max(0, min(value - 1, len(RELEASE_GUARD_LEVEL_LABELS) - 1))])

  @staticmethod
  def _clamp_manual_yield_torque_threshold(value: int) -> int:
    clamped = max(MANUAL_YIELD_TORQUE_THRESHOLD_MIN, min(value, MANUAL_YIELD_TORQUE_THRESHOLD_MAX))
    rounded = ((clamped + (MANUAL_YIELD_TORQUE_THRESHOLD_STEP // 2)) // MANUAL_YIELD_TORQUE_THRESHOLD_STEP) * MANUAL_YIELD_TORQUE_THRESHOLD_STEP
    return max(MANUAL_YIELD_TORQUE_THRESHOLD_MIN, min(rounded, MANUAL_YIELD_TORQUE_THRESHOLD_MAX))

  @staticmethod
  def _format_manual_yield_torque_threshold_label(value: int) -> str:
    clamped = SubaruLayout._clamp_manual_yield_torque_threshold(value)
    return tr("80 - Stock") if clamped == MANUAL_YIELD_TORQUE_THRESHOLD_MAX else str(clamped)

  @staticmethod
  def _format_soft_capture_label(value: int) -> str:
    idx = max(0, min(value - 1, len(SOFT_CAPTURE_STRENGTH_LABELS) - 1))
    return tr(SOFT_CAPTURE_STRENGTH_LABELS[idx])

  def _set_advanced_tuning_visibility(self, enabled: bool) -> None:
    self._manual_yield_torque_threshold_enabled.set_visible(enabled)
    self._manual_yield_torque_threshold.set_visible(enabled)
    self._manual_yield_resume_softness_enabled.set_visible(enabled)
    self._manual_yield_resume_softness.set_visible(enabled)
    self._manual_yield_release_guard_enabled.set_visible(enabled)
    self._manual_yield_release_guard_level.set_visible(enabled)
    self._subaru_soft_capture.set_visible(enabled)
    self._subaru_soft_capture_strength.set_visible(enabled)

  def _initialize_items(self):
    self._subaru_match_vehicle_speed = toggle_item_sp(
      title=lambda: tr("Match Vehicle Speedometer"),
      description=lambda: tr(MATCH_VEHICLE_SPEED_DESC),
      param="MCSubaruMatchVehicleSpeedometer",
      initial_state=self._get_bool_param("MCSubaruMatchVehicleSpeedometer", True),
    )
    self._subaru_advanced_tuning = toggle_item_sp(
      title=lambda: tr("Advanced Tuning"),
      description=lambda: tr(ADVANCED_TUNING_DESC),
      param="MCSubaruAdvancedTuning",
      initial_state=self._get_bool_param("MCSubaruAdvancedTuning"),
    )
    self._manual_yield_torque_threshold_enabled = toggle_item_sp(
      title=lambda: tr("Custom Yield Torque"),
      description=lambda: tr(CUSTOM_YIELD_TORQUE_DESC),
      param="MCSubaruManualYieldTorqueThresholdEnabled",
      initial_state=self._get_bool_param("MCSubaruManualYieldTorqueThresholdEnabled"),
    )
    self._manual_yield_torque_threshold = option_item_sp(
      title=lambda: tr("Manual Yield Torque Threshold"),
      description=lambda: tr(YIELD_TORQUE_DESC),
      param="MCSubaruManualYieldTorqueThreshold",
      min_value=MANUAL_YIELD_TORQUE_THRESHOLD_MIN,
      max_value=MANUAL_YIELD_TORQUE_THRESHOLD_MAX,
      value_change_step=MANUAL_YIELD_TORQUE_THRESHOLD_STEP,
      label_callback=self._format_manual_yield_torque_threshold_label,
      inline=False,
    )
    self._manual_yield_resume_softness_enabled = toggle_item_sp(
      title=lambda: tr("Custom Resume Softness"),
      description=lambda: tr(CUSTOM_RESUME_SOFTNESS_DESC),
      param="MCSubaruManualYieldResumeSoftnessEnabled",
      initial_state=self._get_bool_param("MCSubaruManualYieldResumeSoftnessEnabled"),
    )
    self._manual_yield_resume_softness = option_item_sp(
      title=lambda: tr("Manual Yield Resume Softness"),
      description=lambda: tr(RESUME_SOFTNESS_DESC),
      param="MCSubaruManualYieldResumeSoftness",
      min_value=0,
      max_value=6,
      value_change_step=1,
      label_callback=self._format_resume_softness_label,
      inline=False,
    )
    self._manual_yield_release_guard_enabled = toggle_item_sp(
      title=lambda: tr("Manual Yield Release Guard"),
      description=lambda: tr(RELEASE_GUARD_DESC),
      param="MCSubaruManualYieldReleaseGuardEnabled",
      initial_state=self._get_bool_param("MCSubaruManualYieldReleaseGuardEnabled"),
    )
    self._manual_yield_release_guard_level = option_item_sp(
      title=lambda: tr("Release Guard Strength"),
      description=lambda: tr(RELEASE_GUARD_STRENGTH_DESC),
      param="MCSubaruManualYieldReleaseGuardLevel",
      min_value=1,
      max_value=3,
      value_change_step=1,
      label_callback=self._format_release_guard_label,
      inline=False,
    )
    self._subaru_soft_capture = toggle_item_sp(
      title=lambda: tr("Soft-Capture Engage Blend"),
      description=lambda: tr(SOFT_CAPTURE_DESC),
      param="MCSubaruSoftCaptureEnabled",
      initial_state=self._get_bool_param("MCSubaruSoftCaptureEnabled"),
    )
    self._subaru_soft_capture_strength = option_item_sp(
      title=lambda: tr("Soft-Capture Strength"),
      description=lambda: tr(SOFT_CAPTURE_STRENGTH_DESC),
      param="MCSubaruSoftCaptureLevel",
      min_value=1,
      max_value=5,
      value_change_step=1,
      label_callback=self._format_soft_capture_label,
      inline=False,
    )
    self._show_brake_status = toggle_item_sp(
      title=lambda: tr("Show Vehicle Brake Status"),
      description=lambda: tr("Display current speed in red when brake lights are on."),
      param="ShowBrakeStatus",
      initial_state=self._get_bool_param("ShowBrakeStatus"),
    )
    self._show_confidence_ball = toggle_item_sp(
      title=lambda: tr("Show Confidence Ball"),
      description=lambda: tr("Display the confidence ball on the driving view."),
      param="BPShowConfidenceBall",
      initial_state=self._get_bool_param("BPShowConfidenceBall"),
    )
    self._dynamic_path_color = toggle_item_sp(
      title=lambda: tr("Dynamic Path Color"),
      description=lambda: tr(DYNAMIC_PATH_COLOR_DESC),
      param="DynamicPathColor",
      initial_state=self._get_bool_param("DynamicPathColor"),
    )
    self._custom_model_path_color = multiple_button_item_sp(
      title=lambda: tr("Custom Model Path Color"),
      description=lambda: tr(CUSTOM_MODEL_PATH_COLOR_DESC),
      buttons=[lambda label=label: tr(label) for label in CUSTOM_MODEL_PATH_COLOR_LABELS],
      param="CustomModelPathColor",
      button_width=160,
      inline=False,
    )
    self._hide_v_ego_ui = toggle_item_sp(
      title=lambda: tr("Hide Speedometer"),
      description=lambda: tr("When enabled, the onroad speedometer is not displayed."),
      param="HideVEgoUI",
      initial_state=self._get_bool_param("HideVEgoUI"),
    )
    self._set_advanced_tuning_visibility(self._get_bool_param("MCSubaruAdvancedTuning"))

    return [
      SubaruSectionHeader(lambda: tr("Angle Subaru Tuning")),
      self._subaru_advanced_tuning,
      self._manual_yield_torque_threshold_enabled,
      self._manual_yield_torque_threshold,
      self._manual_yield_resume_softness_enabled,
      self._manual_yield_resume_softness,
      self._manual_yield_release_guard_enabled,
      self._manual_yield_release_guard_level,
      self._subaru_soft_capture,
      self._subaru_soft_capture_strength,
      SubaruSectionHeader(lambda: tr("Visuals")),
      self._subaru_match_vehicle_speed,
      self._show_brake_status,
      self._show_confidence_ball,
      self._dynamic_path_color,
      self._custom_model_path_color,
      self._hide_v_ego_ui,
    ]

  def _update_state(self):
    super()._update_state()

    advanced_tuning_enabled = self._get_bool_param("MCSubaruAdvancedTuning")
    torque_threshold_enabled = self._get_bool_param("MCSubaruManualYieldTorqueThresholdEnabled")
    resume_softness_enabled = self._get_bool_param("MCSubaruManualYieldResumeSoftnessEnabled")
    release_guard_enabled = self._get_bool_param("MCSubaruManualYieldReleaseGuardEnabled")
    soft_capture_enabled = self._get_bool_param("MCSubaruSoftCaptureEnabled")

    self._subaru_match_vehicle_speed.action_item.set_state(self._get_bool_param("MCSubaruMatchVehicleSpeedometer", True))
    self._subaru_advanced_tuning.action_item.set_state(advanced_tuning_enabled)
    self._manual_yield_torque_threshold_enabled.action_item.set_state(torque_threshold_enabled)
    self._manual_yield_resume_softness_enabled.action_item.set_state(resume_softness_enabled)
    self._manual_yield_release_guard_enabled.action_item.set_state(release_guard_enabled)
    self._subaru_soft_capture.action_item.set_state(soft_capture_enabled)

    self._manual_yield_torque_threshold.action_item.current_value = self._clamp_manual_yield_torque_threshold(
      self._get_int_param("MCSubaruManualYieldTorqueThreshold", MANUAL_YIELD_TORQUE_THRESHOLD_MAX)
    )
    self._manual_yield_resume_softness.action_item.current_value = max(0, min(self._get_int_param("MCSubaruManualYieldResumeSoftness", 4), 6))
    self._manual_yield_release_guard_level.action_item.current_value = max(1, min(self._get_int_param("MCSubaruManualYieldReleaseGuardLevel", 2), 3))
    self._subaru_soft_capture_strength.action_item.current_value = max(1, min(self._get_int_param("MCSubaruSoftCaptureLevel", 3), 5))

    self._set_advanced_tuning_visibility(advanced_tuning_enabled)
    self._manual_yield_torque_threshold.action_item.set_enabled(torque_threshold_enabled)
    self._manual_yield_resume_softness.action_item.set_enabled(resume_softness_enabled)
    self._manual_yield_release_guard_level.action_item.set_enabled(release_guard_enabled)
    self._subaru_soft_capture_strength.action_item.set_enabled(soft_capture_enabled)

    self._show_brake_status.action_item.set_state(self._get_bool_param("ShowBrakeStatus"))
    self._show_confidence_ball.action_item.set_state(self._get_bool_param("BPShowConfidenceBall"))
    self._dynamic_path_color.action_item.set_state(self._get_bool_param("DynamicPathColor"))
    self._custom_model_path_color.action_item.set_selected_button(
      max(0, min(self._get_int_param("CustomModelPathColor"), len(CUSTOM_MODEL_PATH_COLOR_LABELS) - 1))
    )
    self._hide_v_ego_ui.action_item.set_state(self._get_bool_param("HideVEgoUI"))

  def _render(self, rect):
    self._scroller.render(rect)

  def show_event(self):
    self._scroller.show_event()
