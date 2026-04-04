"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from collections.abc import Callable

import pyray as rl

from openpilot.common.params import Params
from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import CUSTOM_MODEL_PATH_COLOR_LABELS, DYNAMIC_PATH_COLOR_PALETTE_LABELS
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.sunnypilot.lib.styles import style
from openpilot.system.ui.sunnypilot.widgets.list_view import multiple_button_item_sp, option_item_sp, toggle_item_sp
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.scroller_tici import Scroller


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

  @staticmethod
  def _format_subaru_strength_label(value: int) -> str:
    return tr("Stock") if value == 0 else f"{value:+d}"

  def _initialize_items(self):
    self._subaru_smoothing_tune = toggle_item_sp(
      title=lambda: tr("Subaru Steering Smoothing"),
      description=lambda: tr("Enable Subaru low-speed steering tuning so you can adjust smoothing and near-center damping below."),
      param="MCSubaruSmoothingTune",
      initial_state=self._params.get_bool("MCSubaruSmoothingTune"),
    )
    self._subaru_smoothing_strength = option_item_sp(
      title=lambda: tr("Smoothing Strength"),
      description=lambda: tr("Adjust low-speed Subaru smoothing. Positive values add more smoothing, negative values make it more responsive, and Stock keeps the current validated Subaru behavior."),
      param="MCSubaruSmoothingStrength",
      min_value=-3,
      max_value=4,
      value_change_step=1,
      label_callback=self._format_subaru_strength_label,
      inline=False,
    )
    self._subaru_center_damping_strength = option_item_sp(
      title=lambda: tr("Center Damping"),
      description=lambda: tr("Adjust Subaru near-center damping and sign-flip control at low speed. Positive values add more damping, negative values make it more responsive, and Stock keeps the current validated Subaru behavior."),
      param="MCSubaruCenterDampingStrength",
      min_value=-3,
      max_value=4,
      value_change_step=1,
      label_callback=self._format_subaru_strength_label,
      inline=False,
    )
    self._show_brake_status = toggle_item_sp(
      title=lambda: tr("Show Vehicle Brake Status"),
      description=lambda: tr("Display current speed in red when brake lights are on."),
      param="ShowBrakeStatus",
      initial_state=self._params.get_bool("ShowBrakeStatus"),
    )
    self._dynamic_path_color = toggle_item_sp(
      title=lambda: tr("Dynamic Path Color"),
      description=lambda: tr("Color the driving path by drive mode. Gray when inactive or overriding, blue for steering-only, and green for full control."),
      param="DynamicPathColor",
      initial_state=self._params.get_bool("DynamicPathColor"),
    )
    self._dynamic_path_color_palette = multiple_button_item_sp(
      title=lambda: tr("Dynamic Path Color Palette"),
      description=lambda: tr("Choose whether Dynamic Path Color uses the custom palette or the stock-themed palette."),
      buttons=[lambda label=label: tr(label) for label in DYNAMIC_PATH_COLOR_PALETTE_LABELS],
      param="DynamicPathColorPalette",
      button_width=160,
      inline=False,
    )
    self._custom_model_path_color = multiple_button_item_sp(
      title=lambda: tr("Custom Model Path Color"),
      description=lambda: tr("Use preset colors for the driving path overlay. Stock keeps the normal path behavior, and Dynamic Path Color still takes priority when enabled."),
      buttons=[lambda label=label: tr(label) for label in CUSTOM_MODEL_PATH_COLOR_LABELS],
      param="CustomModelPathColor",
      button_width=160,
      inline=False,
    )
    self._true_v_ego_ui = toggle_item_sp(
      title=lambda: tr("Always Display True Speed"),
      description=lambda: tr("When off, comma uses dash or cluster speed when supported. Enable to force true wheel-speed-based speed."),
      param="TrueVEgoUI",
      initial_state=self._params.get_bool("TrueVEgoUI"),
    )
    self._hide_v_ego_ui = toggle_item_sp(
      title=lambda: tr("Hide Speedometer"),
      description=lambda: tr("When enabled, the onroad speedometer is not displayed."),
      param="HideVEgoUI",
      initial_state=self._params.get_bool("HideVEgoUI"),
    )

    return [
      SubaruSectionHeader(lambda: tr("Lateral Tuning")),
      self._subaru_smoothing_tune,
      self._subaru_smoothing_strength,
      self._subaru_center_damping_strength,
      SubaruSectionHeader(lambda: tr("Visuals")),
      self._show_brake_status,
      self._dynamic_path_color,
      self._dynamic_path_color_palette,
      self._custom_model_path_color,
      self._true_v_ego_ui,
      self._hide_v_ego_ui,
    ]

  def _update_state(self):
    super()._update_state()

    smoothing_enabled = self._params.get_bool("MCSubaruSmoothingTune")
    self._subaru_smoothing_tune.action_item.set_state(smoothing_enabled)
    self._subaru_smoothing_strength.action_item.current_value = max(-3, min(self._get_int_param("MCSubaruSmoothingStrength"), 4))
    self._subaru_center_damping_strength.action_item.current_value = max(-3, min(self._get_int_param("MCSubaruCenterDampingStrength"), 4))
    self._subaru_smoothing_strength.action_item.set_enabled(smoothing_enabled)
    self._subaru_center_damping_strength.action_item.set_enabled(smoothing_enabled)

    self._show_brake_status.action_item.set_state(self._params.get_bool("ShowBrakeStatus"))
    self._dynamic_path_color.action_item.set_state(self._params.get_bool("DynamicPathColor"))
    self._dynamic_path_color_palette.action_item.set_selected_button(
      max(0, min(self._get_int_param("DynamicPathColorPalette"), len(DYNAMIC_PATH_COLOR_PALETTE_LABELS) - 1))
    )
    self._dynamic_path_color_palette.action_item.set_enabled(self._params.get_bool("DynamicPathColor"))
    self._custom_model_path_color.action_item.set_selected_button(
      max(0, min(self._get_int_param("CustomModelPathColor"), len(CUSTOM_MODEL_PATH_COLOR_LABELS) - 1))
    )
    self._true_v_ego_ui.action_item.set_state(self._params.get_bool("TrueVEgoUI"))
    self._hide_v_ego_ui.action_item.set_state(self._params.get_bool("HideVEgoUI"))

  def _render(self, rect):
    self._scroller.render(rect)

  def show_event(self):
    self._scroller.show_event()
