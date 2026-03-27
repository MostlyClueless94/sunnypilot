from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from openpilot.common.params import Params

PROFILE_SOURCE_AUTO = "auto"
PROFILE_SOURCE_MANUAL = "manual"

PROFILE_SETTING_KEYS = (
  "CustomModelPathColor",
  "DynamicPathColor",
  "DynamicPathColorPalette",
  "ChevronInfo",
  "HideVEgoUI",
  "TrueVEgoUI",
  "RoadNameToggle",
  "ShowTurnSignals",
  "TorqueBar",
  "RocketFuel",
  "StandstillTimer",
  "BlindSpot",
  "DevUIInfo",
)

PROFILE_BOOL_KEYS = {
  "DynamicPathColor",
  "HideVEgoUI",
  "TrueVEgoUI",
  "RoadNameToggle",
  "ShowTurnSignals",
  "TorqueBar",
  "RocketFuel",
  "StandstillTimer",
  "BlindSpot",
}

RECALIBRATION_RESET_KEYS = (
  "CalibrationParams",
  "LiveTorqueParameters",
  "LiveParameters",
  "LiveParametersV2",
  "LiveDelay",
)


@dataclass
class VehicleProfileActivationResult:
  key: str
  source: str
  created: bool = False
  restored: bool = False
  switched: bool = False
  recalibration_required: bool = False


def _normalize_brand(brand: str | None) -> str:
  return "" if brand is None else str(brand)


def _get_setting_value(params: Params, key: str) -> bool | int:
  if key in PROFILE_BOOL_KEYS:
    return params.get_bool(key)
  return params.get(key, return_default=True)


def capture_profile_settings(params: Params) -> dict[str, bool | int]:
  return {key: _get_setting_value(params, key) for key in PROFILE_SETTING_KEYS}


def load_vehicle_profiles(params: Params) -> dict[str, dict[str, Any]]:
  profiles = params.get("VehicleProfiles")
  return profiles if isinstance(profiles, dict) else {}


def save_vehicle_profiles(params: Params, profiles: dict[str, dict[str, Any]]) -> None:
  params.put("VehicleProfiles", profiles)


def vehicle_profile_exists(params: Params, key: str | None) -> bool:
  return bool(key) and key in load_vehicle_profiles(params)


def get_display_profile_key(params: Params, detected_key: str | None = None) -> str:
  if bundle := params.get("CarPlatformBundle"):
    return bundle.get("platform", "") or ""
  if current_key := params.get("VehicleProfileCurrentKey"):
    return current_key
  return detected_key or ""


def get_profile_state_text(params: Params, key: str | None = None) -> str:
  if params.get("CarPlatformBundle") or params.get("VehicleProfileCurrentSource") == PROFILE_SOURCE_MANUAL:
    return "Manual selection active"
  if vehicle_profile_exists(params, key):
    return "Auto profile active"
  return "No profile yet"


def reset_vehicle_profile_recalibration(params: Params, request_onroad_cycle: bool = True) -> None:
  for key in RECALIBRATION_RESET_KEYS:
    params.remove(key)
  if request_onroad_cycle:
    params.put_bool("OnroadCycleRequested", True)


def delete_vehicle_profile(params: Params, key: str | None) -> bool:
  if not key:
    return False
  profiles = load_vehicle_profiles(params)
  if key not in profiles:
    return False
  del profiles[key]
  save_vehicle_profiles(params, profiles)
  return True


def _set_current_profile_state(params: Params, key: str | None, source: str | None) -> None:
  if key:
    params.put("VehicleProfileCurrentKey", key)
  else:
    params.remove("VehicleProfileCurrentKey")

  if source:
    params.put("VehicleProfileCurrentSource", source)
  else:
    params.remove("VehicleProfileCurrentSource")


def _profile_record(key: str, brand: str, settings: dict[str, bool | int], existing: dict[str, Any] | None = None) -> dict[str, Any]:
  record = dict(existing or {})
  record["key"] = key
  record["brand"] = brand
  record["last_used"] = int(time.time())
  record["settings"] = settings
  return record


def _restore_profile_settings(params: Params, settings: dict[str, Any]) -> None:
  for key in PROFILE_SETTING_KEYS:
    if key in settings and settings[key] is not None:
      params.put(key, settings[key])


def activate_vehicle_profile(params: Params, key: str | None, brand: str | None, manual: bool = False) -> VehicleProfileActivationResult | None:
  if not key:
    _set_current_profile_state(params, None, None)
    return None

  source = PROFILE_SOURCE_MANUAL if manual else PROFILE_SOURCE_AUTO
  _set_current_profile_state(params, key, source)
  result = VehicleProfileActivationResult(key=key, source=source)
  if manual:
    return result

  normalized_brand = _normalize_brand(brand)
  profiles = load_vehicle_profiles(params)
  existing_profile = profiles.get(key)
  if existing_profile is None:
    profiles[key] = _profile_record(key, normalized_brand, capture_profile_settings(params))
    save_vehicle_profiles(params, profiles)
    result.created = True
  else:
    profiles[key] = _profile_record(key, normalized_brand, existing_profile.get("settings", {}), existing_profile)
    _restore_profile_settings(params, profiles[key]["settings"])
    save_vehicle_profiles(params, profiles)
    result.restored = True

  last_auto_key = params.get("VehicleProfileLastAutoKey")
  if not last_auto_key:
    params.put("VehicleProfileLastAutoKey", key)
    return result

  if last_auto_key != key:
    params.put("VehicleProfileLastAutoKey", key)
    reset_vehicle_profile_recalibration(params)
    result.switched = True
    result.recalibration_required = True

  return result


class VehicleProfileManager:
  def __init__(self, params: Params, poll_interval: float = 1.0):
    self.params = params
    self.poll_interval = poll_interval
    self._last_poll = 0.0
    self._last_key: str | None = None
    self._last_snapshot: dict[str, bool | int] | None = None

  def _reset_cache(self) -> None:
    self._last_key = None
    self._last_snapshot = None

  def update(self, is_offroad: bool) -> None:
    if not is_offroad:
      self._reset_cache()
      return

    now = time.monotonic()
    if now - self._last_poll < self.poll_interval:
      return
    self._last_poll = now

    current_key = self.params.get("VehicleProfileCurrentKey")
    current_source = self.params.get("VehicleProfileCurrentSource")
    if current_source != PROFILE_SOURCE_AUTO or not current_key:
      self._reset_cache()
      return

    profiles = load_vehicle_profiles(self.params)
    profile = profiles.get(current_key)
    if not profile:
      self._reset_cache()
      self._last_key = current_key
      return

    snapshot = capture_profile_settings(self.params)
    if current_key != self._last_key:
      self._last_key = current_key
      self._last_snapshot = snapshot
      return

    if snapshot != self._last_snapshot:
      profiles[current_key] = _profile_record(current_key, profile.get("brand", ""), snapshot, profile)
      save_vehicle_profiles(self.params, profiles)
      self._last_snapshot = snapshot
