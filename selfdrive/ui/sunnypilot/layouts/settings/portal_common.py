"""
Shared helpers for the SubiPilot Portal settings surfaces.
"""

import os
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

import qrcode

PORTAL_ENABLED_PARAM = "SubiPilotPortalEnabled"
PORTAL_PORT_PARAM = "SubiPilotPortalPort"
DEFAULT_PORT = 8088

FEATURE_SUMMARY = (
  "Open the local SubiPilot Portal to review routes, browse video/log data, "
  + "watch live manager logs when WebSocket support is available, and edit raw params."
)

NETWORK_SAFETY_NOTE = (
  "The portal is disabled by default. Enable it only on a trusted local Wi-Fi or hotspot network."
)


def get_port(params: Any) -> int:
  try:
    raw_port = params.get(PORTAL_PORT_PARAM, return_default=True)
    return max(1, min(int(raw_port), 65535))
  except Exception:
    return DEFAULT_PORT


def get_wifi_ip() -> str | None:
  for args in (["ip", "-4", "addr", "show", "scope", "global"], ["ip", "addr", "show", "wlan0"]):
    try:
      result = subprocess.run(args, capture_output=True, text=True, timeout=1)
      for line in result.stdout.splitlines():
        match = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+)/", line)
        if match and not match.group(1).startswith("127."):
          return match.group(1)
    except Exception:
      continue

  try:
    ip_addr = socket.gethostbyname(socket.gethostname())
    if ip_addr and not ip_addr.startswith("127."):
      return ip_addr
  except Exception:
    pass
  return None


def get_portal_url(params: Any) -> str:
  ip_addr = get_wifi_ip()
  if not ip_addr:
    return "Connect Wi-Fi or hotspot to show the portal URL."
  return f"http://{ip_addr}:{get_port(params)}"


def get_route_stats_text() -> str:
  route_root = Path("/data/media/0/realdata") if os.path.exists("/data/media/0/realdata") else Path.home() / "comma_data" / "media" / "0" / "realdata"
  try:
    segments = [path.name for path in route_root.iterdir() if path.is_dir()]
  except Exception:
    return "Route storage unavailable."

  routes = {segment.rsplit("--", 1)[0] for segment in segments if segment}
  if not segments:
    return "No local route segments detected."
  return f"{len(routes)} routes / {len(segments)} segments available locally."


def make_qr_matrix(text: str) -> list[list[bool]]:
  if not text.startswith("http"):
    return []

  qr = qrcode.QRCode(border=1, box_size=1)
  qr.add_data(text)
  qr.make(fit=True)
  matrix = qr.get_matrix()
  return [[bool(cell) for cell in row] for row in matrix]


class CachedPortalInfo:
  def __init__(self, params: Any):
    self.params = params
    self.last_update = 0.0
    self.url = ""
    self.route_stats = ""
    self.qr_matrix: list[list[bool]] = []

  def refresh(self, force: bool = False) -> None:
    now = time.monotonic()
    if not force and now - self.last_update < 5.0:
      return

    self.url = get_portal_url(self.params)
    self.route_stats = get_route_stats_text()
    self.qr_matrix = make_qr_matrix(self.url)
    self.last_update = now
