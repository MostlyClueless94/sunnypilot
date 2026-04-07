"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.selfdrive.ui.bp.widgets.section_header import SectionHeader
from openpilot.selfdrive.ui.sunnypilot.layouts.settings.vehicle.brands.base import BrandSettings
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.sunnypilot.widgets.list_view import option_item_sp, toggle_item_sp
from opendbc.car.subaru.values import CAR, SubaruFlags


RESUME_SPEED_LABELS = ["Fastest", "Faster", "Fast", "Medium", "Slow", "Slower", "Slowest"]
RESUME_SOFTNESS_LABELS = ["Standard", "Soft", "Softer", "Very Soft", "Extra Soft", "Softest", "Max Soft"]
ADVANCED_TUNING_DESC = "Show Subaru lateral tuning controls. Hidden controls keep their saved values active."
SMOOTHING_TUNE_DESC = (
  "Enable Subaru low-speed steering tuning. When enabled, you can adjust smoothing and near-center damping below."
)
SMOOTHING_STRENGTH_DESC = (
  "Adjust low-speed Subaru smoothing. Positive values add more smoothing, "
  "negative values make it more responsive, and Stock keeps the current validated Subaru behavior."
)
CENTER_DAMPING_DESC = (
  "Adjust Subaru near-center damping and sign-flip control at low speed. "
  "Positive values add more damping, negative values make it more responsive, "
  "and Stock keeps the current validated Subaru behavior."
)
RESUME_SPEED_DESC = (
  "Adjust how quickly steering re-engages after you release the wheel during a confirmed manual override."
)
RESUME_SOFTNESS_DESC = (
  "Adjust how gently steering re-engages after manual override. Higher levels reduce the initial reclaim bite."
)


class SubaruSettings(BrandSettings):
  def __init__(self):
    super().__init__()
    self.has_stop_and_go = False

    self.stop_and_go_toggle = toggle_item_sp(
      tr("Stop and Go (Beta)"),
      "",
      param="SubaruStopAndGo",
      callback=self._on_toggle_changed,
    )
    self.stop_and_go_manual_parking_brake_toggle = toggle_item_sp(
      tr("Stop and Go for Manual Parking Brake (Beta)"),
      "",
      param="SubaruStopAndGoManualParkingBrake",
      callback=self._on_toggle_changed,
    )

    self.lateral_tuning_header = SectionHeader(tr("Lateral Tuning"))
    self.advanced_tuning_toggle = toggle_item_sp(
      lambda: tr("Advanced Tuning"),
      description=lambda: tr(ADVANCED_TUNING_DESC),
      param="MCSubaruAdvancedTuning",
      initial_state=ui_state.params.get_bool("MCSubaruAdvancedTuning"),
      callback=self._on_toggle_changed,
    )
    self.subaru_smoothing_tune = toggle_item_sp(
      lambda: tr("Subaru Steering Smoothing"),
      description=lambda: tr(SMOOTHING_TUNE_DESC),
      param="MCSubaruSmoothingTune",
      initial_state=ui_state.params.get_bool("MCSubaruSmoothingTune"),
      callback=self._on_toggle_changed,
    )
    self.subaru_smoothing_strength = option_item_sp(
      title=lambda: tr("Smoothing Strength"),
      description=lambda: tr(SMOOTHING_STRENGTH_DESC),
      param="MCSubaruSmoothingStrength",
      min_value=-3,
      max_value=4,
      value_change_step=1,
      label_callback=self._format_subaru_strength_label,
      inline=False,
    )
    self.subaru_center_damping_strength = option_item_sp(
      title=lambda: tr("Center Damping"),
      description=lambda: tr(CENTER_DAMPING_DESC),
      param="MCSubaruCenterDampingStrength",
      min_value=-3,
      max_value=4,
      value_change_step=1,
      label_callback=self._format_subaru_strength_label,
      inline=False,
    )
    self.manual_yield_resume_speed = option_item_sp(
      title=lambda: tr("Manual Yield Resume Speed"),
      description=lambda: tr(RESUME_SPEED_DESC),
      param="MCSubaruManualYieldResumeSpeed",
      min_value=0,
      max_value=6,
      value_change_step=1,
      label_callback=self._format_resume_speed_label,
      inline=False,
    )
    self.manual_yield_resume_softness = option_item_sp(
      title=lambda: tr("Manual Yield Resume Softness"),
      description=lambda: tr(RESUME_SOFTNESS_DESC),
      param="MCSubaruManualYieldResumeSoftness",
      min_value=0,
      max_value=6,
      value_change_step=1,
      label_callback=self._format_resume_softness_label,
      inline=False,
    )

    self.items = [
      self.stop_and_go_toggle,
      self.stop_and_go_manual_parking_brake_toggle,
      self.lateral_tuning_header,
      self.advanced_tuning_toggle,
      self.subaru_smoothing_tune,
      self.subaru_smoothing_strength,
      self.subaru_center_damping_strength,
      self.manual_yield_resume_speed,
      self.manual_yield_resume_softness,
    ]

  def _on_toggle_changed(self, _):
    self.update_settings()

  @staticmethod
  def _get_int_param(key: str, default: int = 0) -> int:
    value = ui_state.params.get(key, return_default=True)
    try:
      return int(value)
    except (TypeError, ValueError):
      return default

  @staticmethod
  def _format_subaru_strength_label(value: int) -> str:
    return tr("Stock") if value == 0 else f"{value:+d}"

  @staticmethod
  def _format_resume_speed_label(value: int) -> str:
    return tr(RESUME_SPEED_LABELS[max(0, min(value, len(RESUME_SPEED_LABELS) - 1))])

  @staticmethod
  def _format_resume_softness_label(value: int) -> str:
    return tr(RESUME_SOFTNESS_LABELS[max(0, min(value, len(RESUME_SOFTNESS_LABELS) - 1))])

  def _set_advanced_tuning_visibility(self, enabled: bool) -> None:
    self.subaru_smoothing_tune.set_visible(enabled)
    self.subaru_smoothing_strength.set_visible(enabled)
    self.subaru_center_damping_strength.set_visible(enabled)
    self.manual_yield_resume_speed.set_visible(enabled)
    self.manual_yield_resume_softness.set_visible(enabled)

  def stop_and_go_disabled_msg(self):
    if not self.has_stop_and_go:
      return tr("This feature is currently not available on this platform.")
    if not ui_state.is_offroad():
      return tr('Enable "Always Offroad" in Device panel, or turn vehicle off to toggle.')
    return ""

  def update_settings(self):
    bundle = ui_state.params.get("CarPlatformBundle")
    if bundle:
      platform = bundle.get("platform")
      config = CAR[platform].config
      self.has_stop_and_go = not (config.flags & (SubaruFlags.GLOBAL_GEN2 | SubaruFlags.HYBRID))
    elif ui_state.CP is not None:
      self.has_stop_and_go = not (ui_state.CP.flags & (SubaruFlags.GLOBAL_GEN2 | SubaruFlags.HYBRID))
    else:
      self.has_stop_and_go = False

    disabled_msg = self.stop_and_go_disabled_msg()
    descriptions = [
      tr("Experimental feature to enable auto-resume during stop-and-go for certain supported Subaru platforms."),
      tr(
        "Experimental feature to enable stop and go for Subaru Global models with manual handbrake. "
        "Models with electric parking brake should keep this disabled. Thanks to martinl for this implementation!"
      ),
    ]

    self.stop_and_go_toggle.action_item.set_state(ui_state.params.get_bool("SubaruStopAndGo"))
    self.stop_and_go_manual_parking_brake_toggle.action_item.set_state(
      ui_state.params.get_bool("SubaruStopAndGoManualParkingBrake")
    )
    for toggle, desc in zip([self.stop_and_go_toggle, self.stop_and_go_manual_parking_brake_toggle], descriptions, strict=True):
      toggle.action_item.set_enabled(self.has_stop_and_go and ui_state.is_offroad())
      toggle.set_description(f"<b>{disabled_msg}</b><br><br>{desc}" if disabled_msg else desc)

    advanced_tuning_enabled = ui_state.params.get_bool("MCSubaruAdvancedTuning")
    smoothing_enabled = ui_state.params.get_bool("MCSubaruSmoothingTune")
    self.advanced_tuning_toggle.action_item.set_state(advanced_tuning_enabled)
    self.subaru_smoothing_tune.action_item.set_state(smoothing_enabled)
    self.subaru_smoothing_strength.action_item.current_value = max(-3, min(self._get_int_param("MCSubaruSmoothingStrength", 2), 4))
    self.subaru_center_damping_strength.action_item.current_value = max(-3, min(self._get_int_param("MCSubaruCenterDampingStrength", 2), 4))
    self.manual_yield_resume_speed.action_item.current_value = max(0, min(self._get_int_param("MCSubaruManualYieldResumeSpeed", 4), 6))
    self.manual_yield_resume_softness.action_item.current_value = max(0, min(self._get_int_param("MCSubaruManualYieldResumeSoftness", 4), 6))
    self._set_advanced_tuning_visibility(advanced_tuning_enabled)
    self.subaru_smoothing_strength.action_item.set_enabled(smoothing_enabled)
    self.subaru_center_damping_strength.action_item.set_enabled(smoothing_enabled)
