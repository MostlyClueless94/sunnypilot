"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""

from pathlib import Path
from types import SimpleNamespace

from openpilot.sunnypilot.selfdrive.controls.lib.speed_limit.common import Mode as SpeedLimitMode, Policy as SpeedLimitPolicy
from openpilot.sunnypilot.selfdrive.controls.lib.speed_limit.helpers import (
  SUBARU_OSM_DEFAULT_COUNTRY_NAME,
  SUBARU_OSM_DEFAULT_COUNTRY_TITLE,
  SUBARU_OSM_DEFAULT_STATE_NAME,
  SUBARU_OSM_DEFAULT_STATE_TITLE,
  ensure_subaru_stock_acc_osm_region,
  is_subaru_stock_acc_osm_ready,
  set_speed_limit_assist_availability,
)


class FakeParams:
  def __init__(self, initial: dict | None = None):
    self._store = dict(initial or {})

  def get(self, key, return_default=False):
    return self._store.get(key)

  def get_bool(self, key):
    return bool(self._store.get(key, False))

  def put(self, key, value):
    self._store[key] = value

  def put_bool(self, key, value):
    self._store[key] = bool(value)


def test_ensure_subaru_stock_acc_osm_region_sets_us_defaults_when_unconfigured():
  params = FakeParams()

  changed = ensure_subaru_stock_acc_osm_region(params)

  assert changed
  assert params.get_bool("OsmLocal")
  assert params.get("OsmLocationName") == SUBARU_OSM_DEFAULT_COUNTRY_NAME
  assert params.get("OsmLocationTitle") == SUBARU_OSM_DEFAULT_COUNTRY_TITLE
  assert params.get("OsmStateName") == SUBARU_OSM_DEFAULT_STATE_NAME
  assert params.get("OsmStateTitle") == SUBARU_OSM_DEFAULT_STATE_TITLE
  assert params.get_bool("OsmDbUpdatesCheck")


def test_ensure_subaru_stock_acc_osm_region_preserves_existing_selection():
  params = FakeParams({
    "OsmLocal": True,
    "OsmLocationName": "CA",
    "OsmLocationTitle": "Canada",
    "OsmStateName": "",
    "OsmStateTitle": "",
  })

  changed = ensure_subaru_stock_acc_osm_region(params)

  assert not changed
  assert params.get("OsmLocationName") == "CA"
  assert params.get("OsmLocationTitle") == "Canada"


def test_is_subaru_stock_acc_osm_ready_requires_download_complete(tmp_path: Path):
  params = FakeParams({
    "OsmLocal": True,
    "OsmLocationName": SUBARU_OSM_DEFAULT_COUNTRY_NAME,
    "OsmLocationTitle": SUBARU_OSM_DEFAULT_COUNTRY_TITLE,
    "OsmStateName": SUBARU_OSM_DEFAULT_STATE_NAME,
    "OsmStateTitle": SUBARU_OSM_DEFAULT_STATE_TITLE,
    "OsmDbUpdatesCheck": False,
  })
  mem_params = FakeParams({"OSMDownloadLocations": ""})
  offline_path = tmp_path / "offline"
  offline_path.mkdir()
  (offline_path / "map.bin").write_text("ready", encoding="utf-8")

  assert is_subaru_stock_acc_osm_ready(params, mem_params, offline_path)

  params.put_bool("OsmDbUpdatesCheck", True)
  assert not is_subaru_stock_acc_osm_ready(params, mem_params, offline_path)


def test_set_speed_limit_assist_availability_forces_warning_until_maps_ready(tmp_path: Path):
  cp = SimpleNamespace(brand="subaru", openpilotLongitudinalControl=False)
  cp_sp = SimpleNamespace(intelligentCruiseButtonManagementAvailable=True, pcmCruiseSpeed=False)
  params = FakeParams({
    "IntelligentCruiseButtonManagement": True,
    "SpeedLimitMode": int(SpeedLimitMode.assist),
    "SpeedLimitPolicy": int(SpeedLimitPolicy.combined),
  })
  mem_params = FakeParams({"OSMDownloadLocations": ""})

  allowed = set_speed_limit_assist_availability(cp, cp_sp, params, mem_params, tmp_path / "offline")

  assert not allowed
  assert params.get("OsmLocationName") == SUBARU_OSM_DEFAULT_COUNTRY_NAME
  assert params.get("OsmStateName") == SUBARU_OSM_DEFAULT_STATE_NAME
  assert params.get("SpeedLimitPolicy") == int(SpeedLimitPolicy.map_data_only)
  assert params.get("SpeedLimitMode") == int(SpeedLimitMode.warning)


def test_set_speed_limit_assist_availability_allows_subaru_stock_acc_when_maps_ready(tmp_path: Path):
  cp = SimpleNamespace(brand="subaru", openpilotLongitudinalControl=False)
  cp_sp = SimpleNamespace(intelligentCruiseButtonManagementAvailable=True, pcmCruiseSpeed=False)
  params = FakeParams({
    "IntelligentCruiseButtonManagement": True,
    "SpeedLimitMode": int(SpeedLimitMode.assist),
    "OsmLocal": True,
    "OsmLocationName": SUBARU_OSM_DEFAULT_COUNTRY_NAME,
    "OsmLocationTitle": SUBARU_OSM_DEFAULT_COUNTRY_TITLE,
    "OsmStateName": SUBARU_OSM_DEFAULT_STATE_NAME,
    "OsmStateTitle": SUBARU_OSM_DEFAULT_STATE_TITLE,
    "OsmDbUpdatesCheck": False,
  })
  mem_params = FakeParams({"OSMDownloadLocations": ""})
  offline_path = tmp_path / "offline"
  offline_path.mkdir()
  (offline_path / "map.bin").write_text("ready", encoding="utf-8")

  allowed = set_speed_limit_assist_availability(cp, cp_sp, params, mem_params, offline_path)

  assert allowed
  assert params.get("SpeedLimitMode") == int(SpeedLimitMode.assist)
