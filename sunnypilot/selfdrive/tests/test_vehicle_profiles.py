from __future__ import annotations

from copy import deepcopy

from openpilot.sunnypilot.selfdrive.vehicle_profiles import (
  PROFILE_BOOL_KEYS,
  PROFILE_SETTING_KEYS,
  VehicleProfileManager,
  activate_vehicle_profile,
  capture_profile_settings,
  delete_vehicle_profile,
  load_vehicle_profiles,
)


PROFILE_DEFAULTS = {
  "CustomModelPathColor": 0,
  "DynamicPathColor": False,
  "DynamicPathColorPalette": 0,
  "ChevronInfo": 4,
  "HideVEgoUI": False,
  "TrueVEgoUI": False,
  "RoadNameToggle": False,
  "ShowTurnSignals": False,
  "TorqueBar": False,
  "RocketFuel": False,
  "StandstillTimer": False,
  "BlindSpot": False,
  "DevUIInfo": 0,
}


class FakeParams:
  def __init__(self):
    self.data = deepcopy(PROFILE_DEFAULTS)

  def get(self, key, block: bool = False, return_default: bool = False):
    if key in self.data:
      return deepcopy(self.data[key])
    if return_default:
      return deepcopy(PROFILE_DEFAULTS.get(key))
    return None

  def get_bool(self, key):
    return bool(self.data.get(key, False))

  def put(self, key, value):
    self.data[key] = deepcopy(value)

  def put_bool(self, key, value):
    self.data[key] = bool(value)

  def remove(self, key):
    self.data.pop(key, None)


def test_first_auto_detect_creates_profile_without_recalibration():
  params = FakeParams()

  result = activate_vehicle_profile(params, "SUBARU_OUTBACK_2023", "subaru")

  assert result is not None
  assert result.created
  assert not result.recalibration_required
  assert params.get("VehicleProfileLastAutoKey") == "SUBARU_OUTBACK_2023"
  assert params.get("OnroadCycleRequested") is None

  profiles = load_vehicle_profiles(params)
  assert profiles["SUBARU_OUTBACK_2023"]["brand"] == "subaru"
  assert profiles["SUBARU_OUTBACK_2023"]["settings"] == capture_profile_settings(params)


def test_same_vehicle_restores_existing_profile_settings():
  params = FakeParams()
  activate_vehicle_profile(params, "SUBARU_OUTBACK_2023", "subaru")

  profiles = load_vehicle_profiles(params)
  profiles["SUBARU_OUTBACK_2023"]["settings"]["RocketFuel"] = True
  params.put("VehicleProfiles", profiles)
  params.put_bool("RocketFuel", False)

  result = activate_vehicle_profile(params, "SUBARU_OUTBACK_2023", "subaru")

  assert result is not None
  assert result.restored
  assert not result.recalibration_required
  assert params.get_bool("RocketFuel")


def test_switch_vehicle_clears_recalibration_state_once():
  params = FakeParams()
  activate_vehicle_profile(params, "SUBARU_OUTBACK_2023", "subaru")

  for key in ("CalibrationParams", "LiveTorqueParameters", "LiveParameters", "LiveParametersV2", "LiveDelay"):
    params.put(key, {"present": True})

  result = activate_vehicle_profile(params, "FORD_F_150_MK14", "ford")

  assert result is not None
  assert result.created
  assert result.switched
  assert result.recalibration_required
  assert params.get("VehicleProfileLastAutoKey") == "FORD_F_150_MK14"
  assert params.get_bool("OnroadCycleRequested")
  for key in ("CalibrationParams", "LiveTorqueParameters", "LiveParameters", "LiveParametersV2", "LiveDelay"):
    assert params.get(key) is None


def test_manual_session_skips_profiles_and_recalibration():
  params = FakeParams()

  result = activate_vehicle_profile(params, "FORD_F_150_MK14", "ford", manual=True)

  assert result is not None
  assert result.source == "manual"
  assert load_vehicle_profiles(params) == {}
  assert params.get("VehicleProfileLastAutoKey") is None
  assert params.get("OnroadCycleRequested") is None


def test_profile_manager_syncs_existing_profiles_without_recreating_deleted_ones():
  params = FakeParams()
  activate_vehicle_profile(params, "SUBARU_OUTBACK_2023", "subaru")

  manager = VehicleProfileManager(params, poll_interval=0.0)
  manager.update(True)

  params.put_bool("BlindSpot", True)
  manager.update(True)
  assert load_vehicle_profiles(params)["SUBARU_OUTBACK_2023"]["settings"]["BlindSpot"] is True

  delete_vehicle_profile(params, "SUBARU_OUTBACK_2023")
  params.put_bool("BlindSpot", False)
  manager.update(True)
  assert load_vehicle_profiles(params) == {}


def test_allowlist_capture_types_match_expected_defaults():
  params = FakeParams()
  captured = capture_profile_settings(params)

  assert set(captured) == set(PROFILE_SETTING_KEYS)
  for key, value in captured.items():
    if key in PROFILE_BOOL_KEYS:
      assert isinstance(value, bool)
    else:
      assert isinstance(value, int)
