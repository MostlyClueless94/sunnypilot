"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.common.params import Params
from openpilot.selfdrive.ui.bp.widgets.section_header import SectionHeader
from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import CUSTOM_MODEL_PATH_COLOR_LABELS, DYNAMIC_PATH_COLOR_PALETTE_LABELS
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.sunnypilot.widgets.list_view import multiple_button_item_sp, option_item_sp, toggle_item_sp
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.scroller_tici import Scroller
from opendbc.car.subaru.values import CAR, SubaruFlags


RESUME_SPEED_LABELS = ["Fastest", "Faster", "Fast", "Medium", "Slow", "Slower", "Slowest"]
RESUME_SOFTNESS_LABELS = ["Standard", "Soft", "Softer", "Very Soft", "Extra Soft", "Softest", "Max Soft"]
ADVANCED_TUNING_DESC = "Show Subaru lateral tuning controls. Hidden controls keep their saved values active."
SMOOTHING_TUNE_DESC = (
  "Enable Subaru low-speed steering tuning. When enabled, you can adjust smoothing and near-center damping below."
)
SMOOTHING_STRENGTH_DESC = (
  "Adjust low-speed Subaru smoothing. Positive values add more smoothing, "
  + "negative values make it more responsive, and Stock keeps the current validated Subaru behavior."
)
CENTER_DAMPING_DESC = (
  "Adjust Subaru near-center damping and sign-flip control at low speed. "
  + "Positive values add more damping, negative values make it more responsive, "
  + "and Stock keeps the current validated Subaru behavior."
)
RESUME_SPEED_DESC = (
  "Adjust how quickly steering re-engages after you release the wheel during a confirmed manual override."
)
RESUME_SOFTNESS_DESC = (
  "Adjust how gently steering re-engages after manual override. Higher levels reduce the initial reclaim bite."
)
STOP_AND_GO_DESC = "Experimental feature to enable auto-resume during stop-and-go for certain supported Subaru platforms."
STOP_AND_GO_MANUAL_BRAKE_DESC = (
  "Experimental feature to enable stop and go for Subaru Global models with manual handbrake. "
  + "Models with electric parking brake should keep this disabled. Thanks to martinl for this implementation!"
)
DYNAMIC_PATH_COLOR_DESC = (
  "Color the driving path by drive mode. "
  + "Custom uses the BP gray, blue, and green palette. "
  + "Stock uses stock-themed fill colors with a vibrant outline. "
  + "Dynamic Path Color changes the path fill and outline, "
  + "overrides Rainbow Mode and Custom Model Path Color, "
  + "and keeps the current BP lane line and road edge rendering."
)
DYNAMIC_PATH_COLOR_PALETTE_DESC = (
  "Choose whether Dynamic Path Color uses the custom BP palette "
  + "or stock-themed fill colors with a vibrant outline."
)
CUSTOM_MODEL_PATH_COLOR_DESC = (
  "Use BluePilot-style preset colors for the driving path overlay. "
  + "Lane lines and road edges follow the selected color family. "
  + "Stock keeps the normal BluePilot behavior. "
  + "When a preset is selected, it overrides Rainbow Mode. "
  + "Dynamic Path Color takes priority when enabled."
)
SHOW_VEHICLE_BRAKE_STATUS_DESC = (
  "Display current speed in red whenever the vehicle is braking, "
  + "including ACC/openpilot braking when available."
)


class MCCustomLayout(Widget):
  def __init__(self):
    super().__init__()

    self._params = Params()
    items = self._initialize_items()
    self._scroller = Scroller(items, line_separator=True, spacing=0)

  def _get_int_param(self, key: str, default: int = 0) -> int:
    value = self._params.get(key, return_default=True)
    try:
      return int(value)
    except (TypeError, ValueError):
      return default

  def _initialize_items(self):
    self._dynamic_path_color = toggle_item_sp(
      title=lambda: tr("Dynamic Path Color"),
      description=lambda: tr(DYNAMIC_PATH_COLOR_DESC),
      param="DynamicPathColor",
      initial_state=self._params.get_bool("DynamicPathColor"),
    )
    self._dynamic_path_color_palette = multiple_button_item_sp(
      title=lambda: tr("Dynamic Path Color Palette"),
      description=lambda: tr(DYNAMIC_PATH_COLOR_PALETTE_DESC),
      buttons=[lambda label=label: tr(label) for label in DYNAMIC_PATH_COLOR_PALETTE_LABELS],
      param="DynamicPathColorPalette",
      button_width=160,
      inline=False
    )
    self._custom_model_path_color = multiple_button_item_sp(
      title=lambda: tr("Custom Model Path Color"),
      description=lambda: tr(CUSTOM_MODEL_PATH_COLOR_DESC),
      buttons=[lambda label=label: tr(label) for label in CUSTOM_MODEL_PATH_COLOR_LABELS],
      param="CustomModelPathColor",
      button_width=160,
      inline=False
    )
    self._show_vehicle_brake_status = toggle_item_sp(
      title=lambda: tr("Show Vehicle Brake Status"),
      description=lambda: tr(SHOW_VEHICLE_BRAKE_STATUS_DESC),
      param="MCShowVehicleBrakeStatus",
      initial_state=self._params.get_bool("MCShowVehicleBrakeStatus"),
    )
    self._subaru_header = SectionHeader(tr("Subaru"))
    self._subaru_stop_and_go = toggle_item_sp(
      title=lambda: tr("Stop and Go (Beta)"),
      description=lambda: tr(STOP_AND_GO_DESC),
      param="SubaruStopAndGo",
      initial_state=self._params.get_bool("SubaruStopAndGo"),
      callback=self._on_subaru_toggle_changed,
    )
    self._subaru_stop_and_go_manual_parking_brake = toggle_item_sp(
      title=lambda: tr("Stop and Go for Manual Parking Brake (Beta)"),
      description=lambda: tr(STOP_AND_GO_MANUAL_BRAKE_DESC),
      param="SubaruStopAndGoManualParkingBrake",
      initial_state=self._params.get_bool("SubaruStopAndGoManualParkingBrake"),
      callback=self._on_subaru_toggle_changed,
    )
    self._subaru_advanced_tuning = toggle_item_sp(
      title=lambda: tr("Advanced Tuning"),
      description=lambda: tr(ADVANCED_TUNING_DESC),
      param="MCSubaruAdvancedTuning",
      initial_state=self._params.get_bool("MCSubaruAdvancedTuning"),
      callback=self._on_subaru_toggle_changed,
    )
    self._subaru_smoothing_tune = toggle_item_sp(
      title=lambda: tr("Subaru Steering Smoothing"),
      description=lambda: tr(SMOOTHING_TUNE_DESC),
      param="MCSubaruSmoothingTune",
      initial_state=self._params.get_bool("MCSubaruSmoothingTune"),
      callback=self._on_subaru_toggle_changed,
    )
    self._subaru_smoothing_strength = option_item_sp(
      title=lambda: tr("Smoothing Strength"),
      description=lambda: tr(SMOOTHING_STRENGTH_DESC),
      param="MCSubaruSmoothingStrength",
      min_value=-3,
      max_value=4,
      value_change_step=1,
      label_callback=self._format_subaru_strength_label,
      inline=False,
    )
    self._subaru_center_damping = option_item_sp(
      title=lambda: tr("Center Damping"),
      description=lambda: tr(CENTER_DAMPING_DESC),
      param="MCSubaruCenterDampingStrength",
      min_value=-3,
      max_value=4,
      value_change_step=1,
      label_callback=self._format_subaru_strength_label,
      inline=False,
    )
    self._manual_yield_resume_speed = option_item_sp(
      title=lambda: tr("Manual Yield Resume Speed"),
      description=lambda: tr(RESUME_SPEED_DESC),
      param="MCSubaruManualYieldResumeSpeed",
      min_value=0,
      max_value=6,
      value_change_step=1,
      label_callback=self._format_resume_speed_label,
      inline=False,
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

    return [
      SectionHeader(tr("Pathing")),
      self._dynamic_path_color,
      self._dynamic_path_color_palette,
      self._custom_model_path_color,
      SectionHeader(tr("Driving Status")),
      self._show_vehicle_brake_status,
      self._subaru_header,
      self._subaru_stop_and_go,
      self._subaru_stop_and_go_manual_parking_brake,
      self._subaru_advanced_tuning,
      self._subaru_smoothing_tune,
      self._subaru_smoothing_strength,
      self._subaru_center_damping,
      self._manual_yield_resume_speed,
      self._manual_yield_resume_softness,
    ]

  def _on_subaru_toggle_changed(self, _):
    self._update_subaru_settings()

  @staticmethod
  def _format_subaru_strength_label(value: int) -> str:
    return tr("Stock") if value == 0 else f"{value:+d}"

  @staticmethod
  def _format_resume_speed_label(value: int) -> str:
    return tr(RESUME_SPEED_LABELS[max(0, min(value, len(RESUME_SPEED_LABELS) - 1))])

  @staticmethod
  def _format_resume_softness_label(value: int) -> str:
    return tr(RESUME_SOFTNESS_LABELS[max(0, min(value, len(RESUME_SOFTNESS_LABELS) - 1))])

  def _get_current_brand(self) -> str:
    if bundle := ui_state.params.get("CarPlatformBundle"):
      brand = bundle.get("brand", "")
      if isinstance(brand, bytes):
        brand = brand.decode("utf-8", errors="replace")
      return str(brand)
    if ui_state.CP is not None and ui_state.CP.carFingerprint != "MOCK":
      brand = ui_state.CP.brand
      if isinstance(brand, bytes):
        brand = brand.decode("utf-8", errors="replace")
      return str(brand)
    return ""

  def _is_subaru_active(self) -> bool:
    return self._get_current_brand() == "subaru"

  def _get_subaru_stop_and_go_available(self) -> bool:
    bundle = ui_state.params.get("CarPlatformBundle")
    if bundle:
      platform = bundle.get("platform")
      config = CAR[platform].config
      return not (config.flags & (SubaruFlags.GLOBAL_GEN2 | SubaruFlags.HYBRID))
    if ui_state.CP is not None:
      return not (ui_state.CP.flags & (SubaruFlags.GLOBAL_GEN2 | SubaruFlags.HYBRID))
    return False

  @staticmethod
  def _get_subaru_stop_and_go_disabled_msg(has_stop_and_go: bool) -> str:
    if not has_stop_and_go:
      return tr("This feature is currently not available on this platform.")
    if not ui_state.is_offroad():
      return tr('Enable "Always Offroad" in Device panel, or turn vehicle off to toggle.')
    return ""

  def _set_subaru_section_visibility(self, is_subaru: bool, advanced_tuning_enabled: bool) -> None:
    self._subaru_header.set_visible(is_subaru)
    self._subaru_stop_and_go.set_visible(is_subaru)
    self._subaru_stop_and_go_manual_parking_brake.set_visible(is_subaru)
    self._subaru_advanced_tuning.set_visible(is_subaru)
    self._subaru_smoothing_tune.set_visible(is_subaru and advanced_tuning_enabled)
    self._subaru_smoothing_strength.set_visible(is_subaru and advanced_tuning_enabled)
    self._subaru_center_damping.set_visible(is_subaru and advanced_tuning_enabled)
    self._manual_yield_resume_speed.set_visible(is_subaru and advanced_tuning_enabled)
    self._manual_yield_resume_softness.set_visible(is_subaru and advanced_tuning_enabled)

  def _update_subaru_settings(self) -> None:
    is_subaru = self._is_subaru_active()
    advanced_tuning_enabled = self._params.get_bool("MCSubaruAdvancedTuning")
    smoothing_enabled = self._params.get_bool("MCSubaruSmoothingTune")
    has_stop_and_go = self._get_subaru_stop_and_go_available()
    disabled_msg = self._get_subaru_stop_and_go_disabled_msg(has_stop_and_go)

    self._subaru_stop_and_go.action_item.set_state(self._params.get_bool("SubaruStopAndGo"))
    self._subaru_stop_and_go_manual_parking_brake.action_item.set_state(
      self._params.get_bool("SubaruStopAndGoManualParkingBrake")
    )
    for toggle, desc in [
      (self._subaru_stop_and_go, tr(STOP_AND_GO_DESC)),
      (self._subaru_stop_and_go_manual_parking_brake, tr(STOP_AND_GO_MANUAL_BRAKE_DESC)),
    ]:
      toggle.action_item.set_enabled(has_stop_and_go and ui_state.is_offroad())
      toggle.set_description(f"<b>{disabled_msg}</b><br><br>{desc}" if disabled_msg else desc)

    self._subaru_advanced_tuning.action_item.set_state(advanced_tuning_enabled)
    self._subaru_smoothing_tune.action_item.set_state(smoothing_enabled)
    self._subaru_smoothing_strength.action_item.current_value = max(-3, min(self._get_int_param("MCSubaruSmoothingStrength", 2), 4))
    self._subaru_center_damping.action_item.current_value = max(-3, min(self._get_int_param("MCSubaruCenterDampingStrength", 2), 4))
    self._manual_yield_resume_speed.action_item.current_value = max(0, min(self._get_int_param("MCSubaruManualYieldResumeSpeed", 4), 6))
    self._manual_yield_resume_softness.action_item.current_value = max(0, min(self._get_int_param("MCSubaruManualYieldResumeSoftness", 4), 6))
    self._subaru_smoothing_strength.action_item.set_enabled(smoothing_enabled)
    self._subaru_center_damping.action_item.set_enabled(smoothing_enabled)
    self._set_subaru_section_visibility(is_subaru, advanced_tuning_enabled)

  def _update_state(self):
    super()._update_state()

    self._dynamic_path_color.action_item.set_state(self._params.get_bool("DynamicPathColor"))
    self._dynamic_path_color_palette.action_item.set_selected_button(
      max(0, min(self._get_int_param("DynamicPathColorPalette"), len(DYNAMIC_PATH_COLOR_PALETTE_LABELS) - 1))
    )
    self._dynamic_path_color_palette.action_item.set_enabled(self._params.get_bool("DynamicPathColor"))
    selected_color = max(0, min(self._get_int_param("CustomModelPathColor"), len(CUSTOM_MODEL_PATH_COLOR_LABELS) - 1))
    self._custom_model_path_color.action_item.set_selected_button(selected_color)
    self._show_vehicle_brake_status.action_item.set_state(self._params.get_bool("MCShowVehicleBrakeStatus"))
    self._update_subaru_settings()

  def _render(self, rect):
    self._scroller.render(rect)

  def show_event(self):
    self._scroller.show_event()
