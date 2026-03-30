import pyray as rl
from collections.abc import Callable

from openpilot.system.ui.widgets.scroller import Scroller
from openpilot.sunnypilot.selfdrive.controls.lib.speed_limit.common import Mode as SpeedLimitMode, OffsetType as SpeedLimitOffsetType, Policy as SpeedLimitPolicy
from openpilot.selfdrive.ui.bp.mici.widgets.button_bp import BigButtonBP, BigParamControlBP, BigMultiToggleBP, BigMultiParamToggleBP
from openpilot.selfdrive.ui.sunnypilot.onroad.path_colors import CUSTOM_MODEL_PATH_COLOR_LABELS
from openpilot.selfdrive.ui.bp.mici.widgets.floatbutton import BigParamFloatControl, BigParamIntControl
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.widgets.nav_widget import NavWidget
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.sunnypilot.selfdrive.controls.lib.speed_limit.helpers import ensure_subaru_stock_acc_osm_region, get_subaru_stock_acc_map_status, \
                                                                          is_subaru_stock_acc_osm_ready
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.lib.wifi_manager import WifiManager, Network
from openpilot.system.ui.widgets.label import UnifiedLabel
from openpilot.system.ui.widgets import DialogResult
from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog
from openpilot.selfdrive.ui.bp.mici.widgets.preferred_network_select import PreferredNetworkSelectMici

class BluePilotLayoutMici(NavWidget):
  @staticmethod
  def _get_active_brand() -> str:
    if (bundle := ui_state.params.get("CarPlatformBundle")) and hasattr(bundle, "get"):
      return str(bundle.get("brand", "")).lower()
    if ui_state.CP is not None and ui_state.CP.carFingerprint != "MOCK":
      return str(ui_state.CP.brand).lower()
    return ""

  @classmethod
  def _show_ford_lateral_settings(cls) -> bool:
    return cls._get_active_brand() in {"ford", "subaru"}

  @classmethod
  def _show_advanced_lateral_tuning(cls) -> bool:
    return cls._get_active_brand() == "ford"

  @classmethod
  def _show_lateral_section_frame(cls) -> bool:
    return cls._get_active_brand() != "subaru"

  @classmethod
  def _show_subaru_stock_acc_controls(cls) -> bool:
    return cls._get_active_brand() == "subaru" and bool(
      ui_state.CP_SP is not None and ui_state.CP_SP.intelligentCruiseButtonManagementAvailable
    )

  def __init__(self, back_callback: Callable):
    super().__init__()
    self.set_back_callback(back_callback)
    self._params = Params()
    self.lane_change_factor_high = float(self._params.get("lane_change_factor_high", return_default=True))

    # WifiManager for preferred network selector (same pattern as TICI BluePilotLayout)
    self._wifi_manager = WifiManager()
    self._wifi_manager.set_active(False)  # Don't scan unless menu is shown
    self._saved_networks: list[Network] = []
    self._wifi_manager.add_callbacks(networks_updated=self._on_network_updated)

    # Preferred WiFi network selector (same as TICI - list of saved networks)
    self.preferred_network_btn = BigButtonBP(
      tr("Preferred WiFi Network"),
      "",
      "icons_mici/settings/network/wifi_strength_full.png"
    )
    self.preferred_network_btn.set_click_callback(self._select_preferred_network)

    # ******** Main Scroller ********
    self.enable_web_routes = BigParamControlBP("enable web routes server", "EnableWebRoutesServer")
    self.show_web_routes_qr = BigButtonBP("show QR code", "", "icons_mici/settings/network/wifi_strength_full.png")
    self.show_web_routes_qr.set_click_callback(self._show_qr_dialog)
    self.show_lead_vehicle = BigMultiParamToggleBP("Lower Right Display", "mici_complication", ["off", "lead car speed", "speed", "lead car distance", "time to lead car"])
    self.show_brake_status = BigParamControlBP("show brake status", "ShowBrakeStatus")
    self.show_blindspot_ui = BigParamControlBP("show blindspot overlay", "ShowBlindspotOverlay")
    self.rainbow_mode = BigParamControlBP("rainbow mode", "RainbowMode")
    self.custom_model_path_color = BigMultiParamToggleBP("custom model path color", "CustomModelPathColor", CUSTOM_MODEL_PATH_COLOR_LABELS)
    self.stock_acc_master = BigParamControlBP("allow SubiPilot to control stock ACC", "IntelligentCruiseButtonManagement", toggle_callback=self._on_stock_acc_toggle)
    self.custom_acc_toggle = BigParamControlBP("custom ACC speed increments", "CustomAccIncrementsEnabled", toggle_callback=lambda _state: self._update_buttons())
    self.custom_acc_short_increment = BigParamIntControl("short press increment", "CustomAccShortPressIncrement", min=1, max=10, step=1)
    self.custom_acc_long_increment = BigButtonBP("long press increment", "")
    self.custom_acc_long_increment.set_click_callback(self._cycle_custom_acc_long_increment)
    self.stock_acc_speed_limit_mode = BigMultiParamToggleBP("speed limit", "SpeedLimitMode", ["off", "info", "warning", "assist"])
    self.stock_acc_speed_limit_source = BigButtonBP("speed limit source", tr("map only"))
    self.stock_acc_speed_limit_offset_type = BigMultiParamToggleBP("speed limit offset", "SpeedLimitOffsetType", ["none", "fixed", "%"])
    self.stock_acc_speed_limit_offset_value = BigParamIntControl("speed limit offset value", "SpeedLimitValueOffset", min=-30, max=30, step=1)
    self.enable_human_turn_detection = BigParamControlBP("enable human turn detection", "enable_human_turn_detection")
    self.lane_change_factor_high = BigParamFloatControl("lane change factor high", "lane_change_factor_high", min=0.5, max=1.0)
    self.enable_lane_positioning = BigParamControlBP("enable lane positioning", "enable_lane_positioning", tint=rl.GREEN)
    self.custom_path_offset = BigParamFloatControl("in-lane offset", "custom_path_offset", is_active_param="enable_lane_positioning", min=-0.5, max=0.5, tint=rl.GREEN)
    self.custom_profile = BigParamControlBP("use custom tuning profile", "custom_profile", tint=rl.BLUE)
    self.pc_blend_ratio_high_C = BigParamFloatControl("predicted curvature blend ratio high", "pc_blend_ratio_high_C_UI", is_active_param="custom_profile", min=0.0, max=1.0, tint=rl.BLUE)
    self.pc_blend_ratio_low_C = BigParamFloatControl("predicted curvature blend ratio low", "pc_blend_ratio_low_C_UI", is_active_param="custom_profile", min=0.0, max=1.0, tint=rl.BLUE)
    self.LC_PID_gain = BigParamFloatControl(
      "low curvature PID gain",
      "LC_PID_gain_UI",
      is_active=lambda: self._params.get_bool("enable_lane_positioning") and self._params.get_bool("custom_profile"),
      min=0.0,
      max=5.0,
      tint=rl.BLUE,
    )
    self.disable_lane_change_under_speed = BigParamControlBP("disable auto lane change under speed", "BlinkerPauseLaneChange")
    self.blinker_min_speed = BigParamIntControl("blinker min lane change speed", "BlinkerMinLateralControlSpeed", min=5, max=50, step=5.0)
    self.animate_steering_wheel = BigParamControlBP("animate steering wheel", "BPAnimateSteeringWheel")
    self.hide_fade = BigParamControlBP("hide onroad fade", "mici_hide_onroad_fade")
    self.hide_border = BigParamControlBP("hide screen border", "mici_hide_onroad_border")
    self.disable_BP_lat = BigParamControlBP("disable SubiPilot lateral control", "disable_BP_lat_UI")
    self.clear_model_cache = BigButtonBP("clear crashed model", "", "icons_mici/settings/device/reboot.png")
    self.clear_model_cache.set_click_callback(self._clear_model_cache)
    self.ui_debug_log = BigParamControlBP("ui debug logging", "BPUIDebugLog")
    self.vbatt_pause_charging = BigParamFloatControl("12V battery limit", "vbatt_pause_charging", min=11.0, max=14.0, step=0.1)
    self.lateral_warning = UnifiedLabel(
      tr("Experimental settings. May have unintended results."),
      font_size=30,
      text_color=rl.Color(255, 96, 96, 255),
      max_width=1070,
      elide=False,
      wrap_text=True,
      line_height=1.05,
    )
    self.lateral_warning.set_visible(self._show_lateral_section_frame)
    self.disable_BP_lat.set_visible(self._show_ford_lateral_settings)

    advanced_lateral_items = (
      self.enable_human_turn_detection,
      self.lane_change_factor_high,
      self.enable_lane_positioning,
      self.custom_path_offset,
      self.custom_profile,
      self.pc_blend_ratio_high_C,
      self.pc_blend_ratio_low_C,
      self.LC_PID_gain,
    )
    for item in advanced_lateral_items:
      item.set_visible(self._show_advanced_lateral_tuning)

    subaru_stock_acc_items = (
      self.stock_acc_master,
      self.stock_acc_speed_limit_mode,
      self.stock_acc_speed_limit_source,
      self.stock_acc_speed_limit_offset_type,
      self.stock_acc_speed_limit_offset_value,
      self.custom_acc_toggle,
      self.custom_acc_short_increment,
      self.custom_acc_long_increment,
    )
    for item in subaru_stock_acc_items:
      item.set_visible(self._show_subaru_stock_acc_controls)
    self.stock_acc_speed_limit_source.set_enabled(False)

    #self.charging_btn = BigButton("charging", "", "icons_mici/settings/charge_icon.png")
    #self.charging_btn.set_click_callback(lambda: self._show_charging_view())

    self._scroller = Scroller(snap_items=False)
    self._scroller._scroller.add_widgets([
      self.enable_web_routes,
      self.show_web_routes_qr,
      self.preferred_network_btn,
      self.show_lead_vehicle,
      self.show_brake_status,
      self.show_blindspot_ui,
      self.rainbow_mode,
      self.custom_model_path_color,
      self.stock_acc_master,
      self.stock_acc_speed_limit_mode,
      self.stock_acc_speed_limit_source,
      self.stock_acc_speed_limit_offset_type,
      self.stock_acc_speed_limit_offset_value,
      self.custom_acc_toggle,
      self.custom_acc_short_increment,
      self.custom_acc_long_increment,
      self.lateral_warning,
      self.enable_human_turn_detection,
      self.lane_change_factor_high,
      self.disable_lane_change_under_speed,
      self.blinker_min_speed,
      self.enable_lane_positioning,
      self.custom_path_offset,
      self.custom_profile,
      self.pc_blend_ratio_high_C,
      self.pc_blend_ratio_low_C,
      self.LC_PID_gain,
      self.animate_steering_wheel,
      self.hide_fade,
      self.hide_border,
      self.vbatt_pause_charging,
      self.disable_BP_lat,
      self.clear_model_cache,
      self.ui_debug_log,
    ])

    # Toggle lists
    self._refresh_toggles = (
      ("EnableWebRoutesServer", self.enable_web_routes),
      ("ShowBrakeStatus", self.show_brake_status),
      ("ShowBlindspotOverlay", self.show_blindspot_ui),
      ("RainbowMode", self.rainbow_mode),
      ("IntelligentCruiseButtonManagement", self.stock_acc_master),
      ("CustomAccIncrementsEnabled", self.custom_acc_toggle),
      ("enable_human_turn_detection", self.enable_human_turn_detection),
      ("BlinkerPauseLaneChange", self.disable_lane_change_under_speed),
      ("enable_lane_positioning", self.enable_lane_positioning),
      ("custom_profile", self.custom_profile),
      ("disable_BP_lat_UI", self.disable_BP_lat),
      ("BPAnimateSteeringWheel", self.animate_steering_wheel),
      ("BPUIDebugLog", self.ui_debug_log),
      ("mici_hide_onroad_fade", self.hide_fade),
      ("BPHideOnroadBorder", self.hide_border),
    )

    ui_state.add_offroad_transition_callback(self._update_toggles)

  def _get_int_param(self, param: str, default: int) -> int:
    try:
      return int(self._params.get(param, return_default=True))
    except (TypeError, ValueError):
      return default

  def _stock_acc_enabled(self) -> bool:
    return self._show_subaru_stock_acc_controls() and self._params.get_bool("IntelligentCruiseButtonManagement")

  def _custom_acc_enabled(self) -> bool:
    return self._stock_acc_enabled() and self._params.get_bool("CustomAccIncrementsEnabled")

  def _enforce_subaru_stock_acc_constraints(self):
    if not self._show_subaru_stock_acc_controls():
      return

    if self._get_int_param("SpeedLimitPolicy", int(SpeedLimitPolicy.map_data_only)) != int(SpeedLimitPolicy.map_data_only):
      self._params.put("SpeedLimitPolicy", int(SpeedLimitPolicy.map_data_only))

    maps_ready = False
    if self._stock_acc_enabled():
      ensure_subaru_stock_acc_osm_region(self._params)
      maps_ready = is_subaru_stock_acc_osm_ready(self._params)

    if not self._stock_acc_enabled() or not maps_ready:
      if self._get_int_param("SpeedLimitMode", int(SpeedLimitMode.warning)) == int(SpeedLimitMode.assist):
        self._params.put("SpeedLimitMode", int(SpeedLimitMode.warning))

    if not self._stock_acc_enabled():
      if self._params.get_bool("CustomAccIncrementsEnabled"):
        self._params.put_bool("CustomAccIncrementsEnabled", False)

  def _on_stock_acc_toggle(self, enabled: bool):
    if enabled:
      ensure_subaru_stock_acc_osm_region(self._params)
    if not enabled and self._get_int_param("SpeedLimitMode", int(SpeedLimitMode.warning)) == int(SpeedLimitMode.assist):
      self._params.put("SpeedLimitMode", int(SpeedLimitMode.warning))
    if not enabled and self._params.get_bool("CustomAccIncrementsEnabled"):
      self._params.put_bool("CustomAccIncrementsEnabled", False)
    self._enforce_subaru_stock_acc_constraints()
    self._update_buttons()

  def _get_custom_acc_long_increment_label(self) -> str:
    return {1: "1", 2: "5", 3: "10"}.get(self._get_int_param("CustomAccLongPressIncrement", 2), "5")

  def _cycle_custom_acc_long_increment(self):
    current = self._get_int_param("CustomAccLongPressIncrement", 2)
    next_value = 1 if current >= 3 else current + 1
    self._params.put("CustomAccLongPressIncrement", next_value)
    self.custom_acc_long_increment.set_value(self._get_custom_acc_long_increment_label())
    self._update_buttons()

  # def _show_charging_view(self):
  #   dlg = BigChargingDialog()
  #   gui_app.set_modal_overlay(dlg)

  def show_event(self):
    super().show_event()
    self._scroller.show_event()
    self._update_toggles()
    self._update_buttons()
    # Enable WiFi scanning when BluePilot menu is shown
    self._wifi_manager.set_active(True)
    self.preferred_network_btn.set_value(self._get_preferred_network_display())

  def hide_event(self):
    super().hide_event()
    # Disable WiFi scanning when BluePilot menu is hidden
    self._wifi_manager.set_active(False)

  def _render(self, rect: rl.Rectangle):
    self._wifi_manager.process_callbacks()
    self._scroller.render(rect)

  def _clear_model_cache(self):
    """Clear ModelRunnerTypeCache and ModelManager_ActiveBundle, then reboot."""

    def handle_confirm(result: DialogResult):
      if result == DialogResult.CONFIRM:
        try:
          self._params.remove("ModelRunnerTypeCache")
        except Exception:
          pass
        try:
          self._params.remove("ModelManager_ActiveBundle")
        except Exception:
          pass
        self._params.put_bool_nonblocking("DoReboot", True)
        cloudlog.info("BluePilot: Cleared model cache (ModelRunnerTypeCache, ModelManager_ActiveBundle), triggered reboot")

    dialog = ConfirmDialog(
      tr("Clear crashed model runner cache and reboot? This fixes 'Communication Issue' when modeld fails to start."),
      tr("Clear & Reboot"),
      callback=handle_confirm
    )
    gui_app.push_widget(dialog)

  def _show_qr_dialog(self):
    """Show QR code dialog for webserver access. MICI uses push_widget/pop_widget (no set_modal_overlay)."""
    if not self._params.get_bool("EnableWebRoutesServer"):
      return
    try:
      qr_dialog = WebServerQRDialog(back_callback=gui_app.pop_widget)
      gui_app.push_widget(qr_dialog)
    except Exception as e:
      from openpilot.common.swaglog import cloudlog
      cloudlog.warning(f"Failed to show QR dialog: {e}")

  def _update_state(self):
    super()._update_state()
    self.show_lead_vehicle._load_value()
    self.custom_model_path_color._load_value()
    self.stock_acc_speed_limit_mode._load_value()
    self.stock_acc_speed_limit_offset_type._load_value()
    self.stock_acc_master.refresh()
    self.custom_acc_toggle.refresh()
    # Refresh dependent control enabled state (e.g. after toggling enable_lane_positioning)
    self._update_buttons()

  def _update_buttons(self):
    """Update button enabled state based on server status and parameter dependencies (see MICI_MENU.csv)."""
    self._enforce_subaru_stock_acc_constraints()
    ui_state.update_params()
    p = self._params

    # Web routes QR: only when server enabled
    server_enabled = ui_state.params.get_bool("EnableWebRoutesServer")
    self.show_web_routes_qr.set_enabled(server_enabled)

    # Lane positioning–dependent controls (prereq: Enable Advanced Lane Positioning)
    lane_positioning_enabled = p.get_bool("enable_lane_positioning")
    self.custom_path_offset.set_enabled(lane_positioning_enabled)

    # Custom profile–dependent controls (prereq: Use Custom Tuning Profile)
    custom_profile_enabled = p.get_bool("custom_profile")
    self.pc_blend_ratio_high_C.set_enabled(custom_profile_enabled)
    self.pc_blend_ratio_low_C.set_enabled(custom_profile_enabled)

    # Low Curvature PID Gain: requires BOTH lane positioning AND custom profile
    self.LC_PID_gain.set_enabled(lane_positioning_enabled and custom_profile_enabled)

    # Preferred WiFi Network: enable when saved networks exist, refresh display value
    self.preferred_network_btn.set_enabled(len(self._saved_networks) > 0)
    self.preferred_network_btn.set_value(self._get_preferred_network_display())

    show_stock_acc = self._show_subaru_stock_acc_controls()
    stock_acc_enabled = self._stock_acc_enabled()
    custom_acc_enabled = self._custom_acc_enabled()
    offset_type = self._get_int_param("SpeedLimitOffsetType", int(SpeedLimitOffsetType.off))
    maps_ready = is_subaru_stock_acc_osm_ready(self._params) if show_stock_acc else False
    map_status = get_subaru_stock_acc_map_status(self._params) if show_stock_acc else "required"

    self.stock_acc_master.set_visible(show_stock_acc)
    self.custom_acc_toggle.set_visible(show_stock_acc)
    self.custom_acc_short_increment.set_visible(show_stock_acc)
    self.custom_acc_long_increment.set_visible(show_stock_acc)
    self.stock_acc_speed_limit_mode.set_visible(show_stock_acc)
    self.stock_acc_speed_limit_source.set_visible(show_stock_acc)
    self.stock_acc_speed_limit_offset_type.set_visible(show_stock_acc)
    self.stock_acc_speed_limit_offset_value.set_visible(show_stock_acc)

    self.custom_acc_toggle.set_enabled(stock_acc_enabled)
    self.custom_acc_short_increment.set_enabled(custom_acc_enabled)
    self.custom_acc_long_increment.set_enabled(custom_acc_enabled)
    self.stock_acc_speed_limit_offset_value.set_enabled(show_stock_acc and offset_type != int(SpeedLimitOffsetType.off))
    self.custom_acc_long_increment.set_value(self._get_custom_acc_long_increment_label())
    self.stock_acc_speed_limit_source.set_value(
      tr("map only") if map_status == "ready" else tr("maps downloading") if map_status == "downloading" else tr("maps required")
    )

    speed_limit_mode = self._get_int_param("SpeedLimitMode", int(SpeedLimitMode.warning))
    self.stock_acc_speed_limit_mode.set_enabled_buttons(
      {0, 1, 2, 3} if stock_acc_enabled and maps_ready else {0, 1, 2}
    )

    if (not stock_acc_enabled or not maps_ready) and speed_limit_mode == int(SpeedLimitMode.assist):
      self._params.put("SpeedLimitMode", int(SpeedLimitMode.warning))
      self.stock_acc_speed_limit_mode._load_value()

  def _on_network_updated(self, networks: list[Network]):
    """Update saved networks list when WiFi networks are updated (callback from WifiManager)."""
    self._saved_networks = [n for n in networks if self._wifi_manager.is_connection_saved(n.ssid)]
    self.preferred_network_btn.set_enabled(len(self._saved_networks) > 0)
    self.preferred_network_btn.set_value(self._get_preferred_network_display())

    # Clear preferred if network was forgotten in NetworkManager
    try:
      favorite_value = self._params.get("WifiFavoriteSSID")
      current_favorite = ""
      if favorite_value:
        if isinstance(favorite_value, bytes):
          current_favorite = favorite_value.decode("utf-8", errors="replace").strip("\x00")
        else:
          current_favorite = str(favorite_value).strip("\x00")
      if current_favorite:
        saved_connections = self._wifi_manager._get_connections()
        if current_favorite not in saved_connections:
          self._params.put("WifiFavoriteSSID", "")
          cloudlog.info(f"Cleared preferred network '{current_favorite}' - network no longer saved in NetworkManager")
    except Exception as e:
      cloudlog.debug(f"Error checking preferred network: {e}")

  def _get_preferred_network_display(self) -> str:
    """Get the display text for preferred network."""
    try:
      favorite_value = self._params.get("WifiFavoriteSSID")
      if favorite_value:
        if isinstance(favorite_value, bytes):
          favorite_ssid = favorite_value.decode("utf-8", errors="replace").strip("\x00")
        else:
          favorite_ssid = str(favorite_value).strip("\x00")
        if favorite_ssid:
          if len(favorite_ssid) > 20:
            return favorite_ssid[:17] + "..."
          return favorite_ssid
    except Exception:
      pass
    return tr("None")

  def _select_preferred_network(self):
    """Open horizontal-scroll panel to select preferred network (same pattern as WiFi network panel)."""
    if len(self._saved_networks) == 0:
      return

    panel = PreferredNetworkSelectMici(
      self._wifi_manager,
      self._saved_networks,
      on_dismiss=lambda: self.preferred_network_btn.set_value(self._get_preferred_network_display())
    )
    gui_app.push_widget(panel)

  def _update_toggles(self):
    ui_state.update_params()

    # Refresh toggles from params to mirror external changes
    for key, item in self._refresh_toggles:
      item.set_checked(ui_state.params.get_bool(key))

    # Also update button state
    self._update_buttons()

# class BigChargingDialog(BigDialogBase):
#   def __init__(self):
#     super().__init__(None, None)

#     self._watt_label = MiciLabel("120kW", font_size=90)
#     self._watt_label.set_position(150,75)

#   def _render(self, _):
#     self._watt_label.render()
#     return self._ret

#   def _update_state(self):
#     super()._update_state()
#     if self._swiping_away:
#       self._ret = DialogResult.CANCEL
