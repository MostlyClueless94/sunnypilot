"""
BluePilot: WiFi favorite network auto-connect manager.

Periodically checks if the user's preferred WiFi network (set via WifiFavoriteSSID param)
is in range and auto-connects to it if the device is connected to a different network.
"""

import threading
import time

from openpilot.common.swaglog import cloudlog

try:
  from openpilot.common.params import Params
except Exception:
  Params = None

FAVORITE_CHECK_PERIOD_SECONDS = 30


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
    while not self._exit:
      try:
        if Params is not None:
          favorite_ssid = Params().get("WifiFavoriteSSID")
          if favorite_ssid:
            favorite_ssid = favorite_ssid.decode("utf-8").strip() if isinstance(favorite_ssid, bytes) else str(favorite_ssid).strip()

            if favorite_ssid:
              self._try_connect(favorite_ssid)
      except Exception:
        cloudlog.exception("BluePilot: Error checking favorite network")

      time.sleep(FAVORITE_CHECK_PERIOD_SECONDS)

  def _try_connect(self, favorite_ssid: str):
    """Check if favorite is in range but not connected, and connect if so."""
    with self._wifi_manager._lock:
      current_networks = list(self._wifi_manager._networks)

    # Already connected to the favorite - nothing to do
    if any(n.ssid == favorite_ssid and n.is_connected for n in current_networks):
      return

    # Check if favorite is in range and is a saved network
    if any(n.ssid == favorite_ssid and n.is_saved for n in current_networks):
      cloudlog.info(f"BluePilot: Auto-connecting to favorite network: {favorite_ssid}")
      self._wifi_manager.activate_connection(favorite_ssid, block=True)
