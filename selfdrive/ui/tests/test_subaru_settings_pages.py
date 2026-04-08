from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_SUBARU = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/vehicle/brands/subaru.py"
TICI_FORD = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/vehicle/brands/ford.py"
MICI_VEHICLE = REPO_ROOT / "selfdrive/ui/bp/mici/layouts/settings/vehicle_mici.py"
MICI_SUBARU = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/layouts/subaru.py"
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_tici_subaru_brand_page_hosts_stop_and_go_only():
  source = _read(TICI_SUBARU)
  assert "class SubaruSettings(BrandSettings):" in source
  assert "def __init__(self):" in source
  assert "def update_settings(self):" in source
  assert 'param="SubaruStopAndGo"' in source
  assert 'param="SubaruStopAndGoManualParkingBrake"' in source
  assert "self.items = [" in source
  assert "self.stop_and_go_toggle," in source
  assert "self.stop_and_go_manual_parking_brake_toggle," in source
  assert 'param="MCSubaruAdvancedTuning"' not in source
  assert 'SectionHeader(tr("Lateral Tuning"))' not in source
  assert "Manual Yield Resume" not in source


def test_tici_subaru_brand_page_restores_stop_and_go_platform_logic():
  source = _read(TICI_SUBARU)
  assert "from openpilot.selfdrive.ui.sunnypilot.layouts.settings.vehicle.brands.base import BrandSettings" in source
  assert "from openpilot.selfdrive.ui.ui_state import ui_state" in source
  assert "from openpilot.system.ui.sunnypilot.widgets.list_view import toggle_item_sp" in source
  assert "from opendbc.car.subaru.values import CAR, SubaruFlags" in source
  assert "self.has_stop_and_go = False" in source
  assert "platform = bundle.get(\"platform\")" in source
  assert "config = CAR[platform].config" in source
  assert "self.has_stop_and_go = not (config.flags & (SubaruFlags.GLOBAL_GEN2 | SubaruFlags.HYBRID))" in source
  assert "toggle.action_item.set_enabled(self.has_stop_and_go and ui_state.is_offroad())" in source
  assert 'Enable "Always Offroad" in Device panel, or turn vehicle off to toggle.' in source
  assert "strict=True" in source
  assert 'action_item.set_state(ui_state.params.get_bool("SubaruStopAndGo"))' not in source
  assert 'action_item.set_state(' not in source


def test_ford_brand_page_does_not_gain_subaru_controls():
  source = _read(TICI_FORD)
  assert "MCSubaru" not in source
  assert "SubaruStopAndGo" not in source
  assert "Manual Yield Resume" not in source
  assert "Advanced Tuning" not in source


def test_mici_vehicle_menu_adds_subaru_entry_only_for_subaru_brand():
  source = _read(MICI_VEHICLE)
  assert "from openpilot.selfdrive.ui.sunnypilot.mici.layouts.subaru import SubaruLayoutMici" in source
  assert "def get_vehicle_brand() -> str:" in source
  assert 'self._btn_subaru = BigButtonBP(tr("subaru settings")' in source
  assert 'self._btn_subaru.set_click_callback(self._on_subaru_settings)' in source
  assert 'is_subaru = get_vehicle_brand() == "subaru"' in source
  assert "self._btn_subaru.set_visible(is_subaru)" in source
  assert "self._btn_subaru.set_enabled(is_subaru)" in source
  assert "gui_app.push_widget(SubaruLayoutMici(back_callback=gui_app.pop_widget))" in source


def test_mici_subaru_layout_contains_driving_only_subaru_controls():
  source = _read(MICI_SUBARU)
  assert 'GreyBigButton("stop and\\ngo")' in source
  assert 'GreyBigButton("lateral\\ntuning")' in source
  assert 'BigParamControl("stop and go\\n(beta)", "SubaruStopAndGo")' in source
  assert '"SubaruStopAndGoManualParkingBrake"' in source
  assert 'BigParamControl("advanced\\ntuning", "MCSubaruAdvancedTuning")' in source
  assert 'BigParamControl("subaru steering\\nsmoothing", "MCSubaruSmoothingTune")' in source
  assert 'BigButton("smoothing\\nstrength")' in source
  assert 'BigButton("center\\ndamping")' in source
  assert 'BigButton("manual yield\\nresume speed")' in source
  assert 'BigButton("manual yield\\nresume softness")' in source
  assert 'list(range(-3, 5))' in source
  assert 'list(range(7))' in source
  assert 'ShowBrakeStatus' not in source
  assert 'DynamicPathColor' not in source
  assert 'BPShowConfidenceBall' not in source
  assert 'MatchVehicleSpeedometer' not in source
  assert 'HideVEgoUI' not in source


def test_mici_subaru_layout_has_safe_grey_header_fallback_for_bp_branch():
  source = _read(MICI_SUBARU)
  assert "try:" in source
  assert "from openpilot.selfdrive.ui.mici.widgets.button import BigButton, BigParamControl, GreyBigButton" in source
  assert "except ImportError:" in source
  assert "from openpilot.selfdrive.ui.bp.mici.widgets.button_bp import BigButtonBP as BigButton, BigParamControlBP as BigParamControl" in source
  assert "class GreyBigButton(BigButton):" in source
  assert "tint=rl.Color(0x66, 0x66, 0x66, 0xFF)" in source
  assert "self.set_touch_valid_callback(lambda: False)" in source


def test_mici_subaru_layout_preserves_scroll_restore_selector_stack():
  source = _read(MICI_SUBARU)
  assert "def _show_selection_view(self, items, back_callback: Callable):" in source
  assert "def _show_value_selector(self, focused_widget: BigButton, param: str, values: list[int], label_callback: Callable[[int], str]):" in source
  assert "def _select_value(self, param: str, value: int):" in source
  assert "def _reset_main_view(self):" in source
  assert "self.focused_widget = focused_widget" in source
  assert "self._show_selection_view(buttons, self._reset_main_view)" in source
  assert "self._scroller.scroll_to(x)" in source


def test_mici_subaru_layout_uses_safe_bool_reads_and_advanced_tuning_visibility():
  source = _read(MICI_SUBARU)
  assert "return ui_state.params.get_bool(key, default)" in source
  assert "self._set_advanced_tuning_visibility(advanced_tuning_enabled)" in source
  assert 'self._subaru_smoothing_strength_btn.set_enabled(smoothing_enabled)' in source
  assert 'self._subaru_center_damping_btn.set_enabled(smoothing_enabled)' in source
  assert 'self._format_strength_label(max(-3, min(self._get_int_param("MCSubaruSmoothingStrength", 2), 4)))' in source
  assert 'self._format_resume_softness_label(max(0, min(self._get_int_param("MCSubaruManualYieldResumeSoftness", 4), 6)))' in source


def test_subaru_params_and_metadata_match_brand_scoped_defaults():
  params_source = _read(PARAMS_KEYS)
  metadata_source = _read(PARAMS_METADATA)
  assert '{"MCSubaruAdvancedTuning", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"MCSubaruSmoothingTune", {PERSISTENT | BACKUP, BOOL, "1"}}' in params_source
  assert '{"MCSubaruSmoothingStrength", {PERSISTENT | BACKUP, INT, "2"}}' in params_source
  assert '{"MCSubaruCenterDampingStrength", {PERSISTENT | BACKUP, INT, "2"}}' in params_source
  assert '{"MCSubaruManualYieldResumeSpeed", {PERSISTENT | BACKUP, INT, "4"}}' in params_source
  assert '{"MCSubaruManualYieldResumeSoftness", {PERSISTENT | BACKUP, INT, "4"}}' in params_source
  assert '"MCSubaruAdvancedTuning"' in metadata_source
  assert '"MCSubaruManualYieldResumeSpeed"' in metadata_source
  assert '"MCSubaruManualYieldResumeSoftness"' in metadata_source
  assert '"label": "Fastest"' in metadata_source
  assert '"label": "Slowest"' in metadata_source
  assert '"label": "Standard"' in metadata_source
  assert '"label": "Max Soft"' in metadata_source
