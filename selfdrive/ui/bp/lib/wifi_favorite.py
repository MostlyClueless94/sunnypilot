"""
BluePilot: WiFi favorite network auto-connect manager.

Periodically checks if the user's preferred WiFi network (set via WifiFavoriteSSID param)
is in range and auto-connects to it if the device is connected to a different network.
"""

import threading
import time

from jeepney import DBusAddress
from jeepney.wrappers import Properties

from openpilot.common.swaglog import cloudlog
from openpilot.system.ui.lib.networkmanager import (NM, NM_ACTIVE_CONNECTION_IFACE, 
                                                    NM_ACCESS_POINT_IFACE)

try:
  from openpilot.common.params import Params
except Exception:
  Params = None

FAVORITE_CHECK_PERIOD_SECONDS = 30
INITIAL_CHECK_DELAY = 5.0  # Wait 5 seconds after startup for networks to be scanned


class WifiFavoriteManager:
  """Monitors for a favorite WiFi network and auto-connects when in range."""

  def __init__(self, wifi_manager):
    self._wifi_manager = wifi_manager
    self._exit = False
    self._thread = threading.Thread(target=self._run, daemon=True)

  def start(self):
    """Start the favorite network monitoring thread."""
    self._thread.start()

  def stop(self):
    """Signal the thread to stop and wait for it."""
    self._exit = True
    if self._thread.is_alive():
      self._thread.join()

  def _run(self):
    """Main loop: check for favorite network and auto-connect."""
    last_check_time = 0.0
    startup_time = time.monotonic()
    initial_check_done = False
    
    while not self._exit:
      current_time = time.monotonic()
      
      # Do an initial check after a short delay on startup
      if not initial_check_done:
        if current_time - startup_time < INITIAL_CHECK_DELAY:
          time.sleep(1)
          continue
        initial_check_done = True
        # Force immediate check on startup
        last_check_time = 0.0
      
      # Regular interval checks after initial check
      if initial_check_done and current_time - last_check_time < FAVORITE_CHECK_PERIOD_SECONDS:
        time.sleep(1)
        continue
      
      last_check_time = current_time
      
      try:
        if Params is None:
          continue
        
        # Check if DBus is available
        if self._wifi_manager._router_main is None:
          continue
        
        params = Params()
        favorite_value = params.get("WifiFavoriteSSID")
        favorite_ssid = ""
        if favorite_value:
          if isinstance(favorite_value, bytes):
            favorite_ssid = favorite_value.decode('utf-8', errors='replace').strip('\x00')
          else:
            favorite_ssid = str(favorite_value).strip('\x00')
        
        if not favorite_ssid:
          # No favorite set, skip
          continue
        
        # Verify favorite network is saved in NetworkManager
        saved_connections = self._wifi_manager._get_connections()
        if favorite_ssid not in saved_connections:
          cloudlog.debug(f"BluePilot: Favorite network '{favorite_ssid}' is not saved in NetworkManager")
          continue
        
        # Check NetworkManager's active connections directly (more reliable than scan results)
        active_connections = self._wifi_manager._get_active_connections()
        current_connected_ssid = None
        for conn_path in active_connections:
          try:
            conn_addr = DBusAddress(conn_path, bus_name=NM, interface=NM_ACTIVE_CONNECTION_IFACE)
            conn_type = self._wifi_manager._router_main.send_and_get_reply(Properties(conn_addr).get('Type')).body[0][1]
            if conn_type == '802-11-wireless':
              specific_obj_path = self._wifi_manager._router_main.send_and_get_reply(Properties(conn_addr).get('SpecificObject')).body[0][1]
              if specific_obj_path != "/":
                ap_addr = DBusAddress(specific_obj_path, bus_name=NM, interface=NM_ACCESS_POINT_IFACE)
                ap_ssid_bytes = self._wifi_manager._router_main.send_and_get_reply(Properties(ap_addr).get('Ssid')).body[0][1]
                current_connected_ssid = bytes(ap_ssid_bytes).decode("utf-8", "replace")
                break
          except Exception:
            continue
        
        # If favorite is already connected, nothing to do
        if current_connected_ssid == favorite_ssid:
          cloudlog.debug(f"BluePilot: Favorite network '{favorite_ssid}' is already connected")
          continue
        
        # If we're connected to something other than the favorite, try to switch
        if current_connected_ssid and current_connected_ssid != favorite_ssid:
          # Check if favorite is in scan results (optional - helps but not required)
          favorite_in_scan = False
          with self._wifi_manager._lock:
            for network in self._wifi_manager._networks:
              if network.ssid == favorite_ssid:
                favorite_in_scan = True
                break
          
          # Try to activate favorite network (NetworkManager will handle if it's in range)
          # We know it's saved, so NetworkManager can attempt to connect
          cloudlog.info(f"BluePilot: Connected to '{current_connected_ssid}', switching to favorite '{favorite_ssid}' (in scan: {favorite_in_scan})...")
          try:
            # Disconnect from current network first
            self._wifi_manager._deactivate_connection(current_connected_ssid)
            time.sleep(2)
            # Try to activate favorite network
            self._wifi_manager.activate_connection(favorite_ssid, block=False)
          except Exception as e:
            cloudlog.warning(f"BluePilot: Failed to switch to favorite network '{favorite_ssid}': {e}")
      
      except Exception as e:
        cloudlog.exception(f"BluePilot: Error checking favorite network: {e}")
      
      time.sleep(1)  # Small sleep to prevent tight loop
