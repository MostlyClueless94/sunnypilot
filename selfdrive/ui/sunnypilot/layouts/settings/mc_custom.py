"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.common.params import Params
from openpilot.selfdrive.ui.bp.widgets.section_header import SectionHeader
from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import CUSTOM_MODEL_PATH_COLOR_LABELS, DYNAMIC_PATH_COLOR_PALETTE_LABELS
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.sunnypilot.widgets.list_view import multiple_button_item_sp, option_item_sp, toggle_item_sp
from openpilot.system.ui.widgets import DialogResult
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog
from openpilot.system.ui.widgets.scroller_tici import Scroller


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

  @staticmethod
  def _format_subaru_strength_label(value: int) -> str:
    return tr("Stock") if value == 0 else f"{value:+d}"

  @staticmethod
  def _get_subaru_delay_description(is_offroad: bool) -> str:
    if is_offroad:
      return tr("Restart-required Subaru angle steering delay test. "
                "Lowers actuator delay from 0.10s to 0.08s to help the wheel unwind sooner after larger turns. "
                "A system reboot is required for changes to take effect.")
    return tr("Please go offroad or turn off the vehicle to adjust this restart-required Subaru delay test.")

  def _initialize_items(self):
    self._dynamic_path_color = toggle_item_sp(
      title=lambda: tr("Dynamic Path Color"),
      description=lambda: tr("Color the driving path by drive mode. "
                             "Custom uses the BP gray, blue, and green palette. "
                             "Stock uses stock-themed fill colors with a vibrant outline. "
                             "Dynamic Path Color changes the path fill and outline, "
                             "overrides Rainbow Mode and Custom Model Path Color, "
                             "and keeps the current BP lane line and road edge rendering."),
      param="DynamicPathColor",
      initial_state=self._params.get_bool("DynamicPathColor"),
    )
    self._dynamic_path_color_palette = multiple_button_item_sp(
      title=lambda: tr("Dynamic Path Color Palette"),
      description=lambda: tr("Choose whether Dynamic Path Color uses the custom BP palette "
                             "or stock-themed fill colors with a vibrant outline."),
      buttons=[lambda label=label: tr(label) for label in DYNAMIC_PATH_COLOR_PALETTE_LABELS],
      param="DynamicPathColorPalette",
      button_width=160,
      inline=False
    )
    self._custom_model_path_color = multiple_button_item_sp(
      title=lambda: tr("Custom Model Path Color"),
      description=lambda: tr("Use BluePilot-style preset colors for the driving path overlay. "
                             "Lane lines and road edges follow the selected color family. "
                             "Stock keeps the normal BluePilot behavior. "
                             "When a preset is selected, it overrides Rainbow Mode. "
                             "Dynamic Path Color takes priority when enabled."),
      buttons=[lambda label=label: tr(label) for label in CUSTOM_MODEL_PATH_COLOR_LABELS],
      param="CustomModelPathColor",
      button_width=160,
      inline=False
    )
    self._show_vehicle_brake_status = toggle_item_sp(
      title=lambda: tr("Show Vehicle Brake Status"),
      description=lambda: tr("Display current speed in red whenever the vehicle is braking, "
                             "including ACC/openpilot braking when available."),
      param="MCShowVehicleBrakeStatus",
      initial_state=self._params.get_bool("MCShowVehicleBrakeStatus"),
    )
    self._subaru_actuator_delay_test = toggle_item_sp(
      title=lambda: tr("Subaru Delay Tweak (Test)"),
      description=lambda: self._get_subaru_delay_description(ui_state.is_offroad()),
      initial_state=self._params.get_bool("MCSubaruActuatorDelayTest"),
      callback=self._on_subaru_actuator_delay_toggled,
    )
    self._subaru_smoothing_tune = toggle_item_sp(
      title=lambda: tr("Subaru Steering Smoothing"),
      description=lambda: tr("Enable MC-owned Subaru low-speed steering tuning. "
                             "This keeps the current MostlyClueless controller structure and lets you adjust smoothing "
                             "and near-center damping strength with the controls below."),
      param="MCSubaruSmoothingTune",
      initial_state=self._params.get_bool("MCSubaruSmoothingTune"),
    )
    self._subaru_smoothing_strength = option_item_sp(
      title=lambda: tr("Smoothing Strength"),
      description=lambda: tr("Adjust low-speed Subaru smoothing. "
                             "Positive values add more smoothing, negative values make it more responsive, "
                             "and Stock keeps the current MostlyClueless behavior."),
      param="MCSubaruSmoothingStrength",
      min_value=-8,
      max_value=8,
      value_change_step=1,
      label_callback=self._format_subaru_strength_label,
      inline=True,
    )
    self._subaru_center_damping_strength = option_item_sp(
      title=lambda: tr("Center Damping"),
      description=lambda: tr("Adjust Subaru near-center damping and sign-flip control at low speed. "
                             "Positive values add more damping, negative values make it more responsive, "
                             "and Stock keeps the current MostlyClueless behavior."),
      param="MCSubaruCenterDampingStrength",
      min_value=-8,
      max_value=8,
      value_change_step=1,
      label_callback=self._format_subaru_strength_label,
      inline=True,
    )

    return [
      SectionHeader(tr("Pathing")),
      self._dynamic_path_color,
      self._dynamic_path_color_palette,
      self._custom_model_path_color,
      SectionHeader(tr("Driving Status")),
      self._show_vehicle_brake_status,
      SectionHeader(tr("Subaru")),
      self._subaru_actuator_delay_test,
      self._subaru_smoothing_tune,
      self._subaru_smoothing_strength,
      self._subaru_center_damping_strength,
    ]

  def _handle_subaru_actuator_delay_reboot(self, result):
    if result == DialogResult.CONFIRM:
      ui_state.params.put_bool("MCSubaruActuatorDelayTest", self._subaru_actuator_delay_test.action_item.get_state())
      ui_state.params.put_bool("DoReboot", True)
    else:
      self._subaru_actuator_delay_test.action_item.set_state(self._params.get_bool("MCSubaruActuatorDelayTest"))

  def _on_subaru_actuator_delay_toggled(self, enabled):
    dialog = ConfirmDialog(tr("System reboot required for changes to take effect. Reboot now?"),
                           tr("Reboot"), callback=self._handle_subaru_actuator_delay_reboot)
    gui_app.push_widget(dialog)

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
    self._subaru_actuator_delay_test.action_item.set_state(self._params.get_bool("MCSubaruActuatorDelayTest"))
    self._subaru_actuator_delay_test.action_item.set_enabled(ui_state.is_offroad())
    self._subaru_actuator_delay_test.set_description(self._get_subaru_delay_description(ui_state.is_offroad()))
    subaru_smoothing_tune_enabled = self._params.get_bool("MCSubaruSmoothingTune")
    self._subaru_smoothing_tune.action_item.set_state(subaru_smoothing_tune_enabled)
    self._subaru_smoothing_strength.action_item.current_value = max(-8, min(self._get_int_param("MCSubaruSmoothingStrength"), 8))
    self._subaru_center_damping_strength.action_item.current_value = max(-8, min(self._get_int_param("MCSubaruCenterDampingStrength"), 8))
    self._subaru_smoothing_strength.action_item.set_enabled(subaru_smoothing_tune_enabled)
    self._subaru_center_damping_strength.action_item.set_enabled(subaru_smoothing_tune_enabled)

  def _render(self, rect):
    self._scroller.render(rect)

  def show_event(self):
    self._scroller.show_event()
