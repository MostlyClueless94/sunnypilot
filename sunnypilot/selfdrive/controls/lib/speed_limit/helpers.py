"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""

import platform
from pathlib import Path

from cereal import custom, car
from openpilot.common.constants import CV
from openpilot.common.params import Params
from openpilot.sunnypilot.selfdrive.controls.lib.speed_limit.common import Mode as SpeedLimitMode, Policy as SpeedLimitPolicy
from openpilot.system.hardware.hw import Paths

OSM_OFFLINE_MAPS_PATH = Path(Paths.mapd_root()) / "offline"

SUBARU_OSM_DEFAULT_COUNTRY_NAME = "US"
SUBARU_OSM_DEFAULT_COUNTRY_TITLE = "United States"
SUBARU_OSM_DEFAULT_STATE_NAME = "All"
SUBARU_OSM_DEFAULT_STATE_TITLE = "All states (~6.0 GB)"


def _get_params(params: Params | None = None) -> Params:
  return params if params is not None else Params()


def _get_mem_params(params: Params | None = None, mem_params: Params | None = None) -> Params:
  if mem_params is not None:
    return mem_params
  if platform.system() == "Linux":
    return Params("/dev/shm/params")
  return _get_params(params)


def has_osm_region_configured(params: Params | None = None) -> bool:
  params = _get_params(params)
  return bool(params.get("OsmLocationName", return_default=True))


def is_osm_download_pending(params: Params | None = None, mem_params: Params | None = None) -> bool:
  params = _get_params(params)
  mem_params = _get_mem_params(params, mem_params)
  return params.get_bool("OsmDbUpdatesCheck") or bool(mem_params.get("OSMDownloadLocations"))


def has_offline_osm_maps(offline_maps_path: Path | None = None) -> bool:
  path = offline_maps_path or OSM_OFFLINE_MAPS_PATH
  try:
    return path.exists() and any(path.iterdir())
  except OSError:
    return False


def ensure_subaru_stock_acc_osm_region(params: Params | None = None) -> bool:
  params = _get_params(params)
  if has_osm_region_configured(params):
    return False

  params.put_bool("OsmLocal", True)
  params.put("OsmLocationName", SUBARU_OSM_DEFAULT_COUNTRY_NAME)
  params.put("OsmLocationTitle", SUBARU_OSM_DEFAULT_COUNTRY_TITLE)
  params.put("OsmStateName", SUBARU_OSM_DEFAULT_STATE_NAME)
  params.put("OsmStateTitle", SUBARU_OSM_DEFAULT_STATE_TITLE)
  params.put_bool("OsmDbUpdatesCheck", True)
  return True


def is_subaru_stock_acc_osm_ready(params: Params | None = None, mem_params: Params | None = None,
                                  offline_maps_path: Path | None = None) -> bool:
  params = _get_params(params)
  return (
    params.get_bool("OsmLocal")
    and has_osm_region_configured(params)
    and not is_osm_download_pending(params, mem_params)
    and has_offline_osm_maps(offline_maps_path)
  )


def get_subaru_stock_acc_map_status(params: Params | None = None, mem_params: Params | None = None,
                                    offline_maps_path: Path | None = None) -> str:
  params = _get_params(params)
  if is_subaru_stock_acc_osm_ready(params, mem_params, offline_maps_path):
    return "ready"
  if is_osm_download_pending(params, mem_params):
    return "downloading"
  return "required"


def compare_cluster_target(v_cruise_cluster: float, target_set_speed: float, is_metric: bool) -> tuple[bool, bool]:
  speed_conv = CV.MS_TO_KPH if is_metric else CV.MS_TO_MPH
  v_cruise_cluster_conv = round(v_cruise_cluster * speed_conv)
  target_set_speed_conv = round(target_set_speed * speed_conv)

  req_plus = v_cruise_cluster_conv < target_set_speed_conv
  req_minus = v_cruise_cluster_conv > target_set_speed_conv

  return req_plus, req_minus


def set_speed_limit_assist_availability(CP: car.CarParams, CP_SP: custom.CarParamsSP, params: Params = None,
                                        mem_params: Params | None = None, offline_maps_path: Path | None = None) -> bool:
  if params is None:
    params = Params()

  is_release = params.get_bool("IsReleaseSpBranch")
  disallow_in_release = CP.brand == "tesla" and is_release
  always_disallow = CP.brand == "rivian"
  allowed = True

  if disallow_in_release or always_disallow:
    allowed = False

  if not CP.openpilotLongitudinalControl and CP_SP.pcmCruiseSpeed:
    allowed = False

  subaru_stock_acc_enabled = (
    CP.brand == "subaru"
    and CP_SP.intelligentCruiseButtonManagementAvailable
    and params.get_bool("IntelligentCruiseButtonManagement")
    and not CP.openpilotLongitudinalControl
  )

  if subaru_stock_acc_enabled:
    if params.get("SpeedLimitPolicy", return_default=True) != int(SpeedLimitPolicy.map_data_only):
      params.put("SpeedLimitPolicy", int(SpeedLimitPolicy.map_data_only))
    ensure_subaru_stock_acc_osm_region(params)
    if not is_subaru_stock_acc_osm_ready(params, mem_params, offline_maps_path):
      allowed = False

  if not allowed:
    if params.get("SpeedLimitMode", return_default=True) == SpeedLimitMode.assist:
      params.put("SpeedLimitMode", int(SpeedLimitMode.warning))

  return allowed
