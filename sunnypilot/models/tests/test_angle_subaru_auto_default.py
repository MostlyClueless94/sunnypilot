from types import SimpleNamespace

from cereal import car

from openpilot.sunnypilot.models.helpers import (
  ANGLE_SUBARU_NNMV2_INTERNAL_NAME,
  find_bundle_by_internal_name,
  is_angle_subaru_car_params,
  select_angle_subaru_auto_default_bundle,
)


def _cp(brand: str, steer_control_type):
  return SimpleNamespace(brand=brand, steerControlType=steer_control_type)


def _bundle(name: str):
  return SimpleNamespace(internalName=name)


def test_is_angle_subaru_car_params_only_matches_subaru_angle():
  assert is_angle_subaru_car_params(_cp("subaru", car.CarParams.SteerControlType.angle))
  assert not is_angle_subaru_car_params(_cp("subaru", car.CarParams.SteerControlType.torque))
  assert not is_angle_subaru_car_params(_cp("ford", car.CarParams.SteerControlType.angle))
  assert not is_angle_subaru_car_params(None)


def test_find_bundle_by_internal_name_finds_nnmv2():
  bundles = [_bundle("CHV2"), _bundle(ANGLE_SUBARU_NNMV2_INTERNAL_NAME)]
  selected = find_bundle_by_internal_name(bundles, ANGLE_SUBARU_NNMV2_INTERNAL_NAME)

  assert selected is bundles[1]


def test_select_angle_subaru_auto_default_bundle_returns_nnmv2_when_expected():
  bundles = [_bundle("CHV2"), _bundle(ANGLE_SUBARU_NNMV2_INTERNAL_NAME)]

  selected = select_angle_subaru_auto_default_bundle(
    bundles,
    is_angle_subaru=True,
    active_bundle=None,
    download_index=None,
    opt_out=False,
    auto_failed=False,
  )

  assert selected is bundles[1]


def test_select_angle_subaru_auto_default_bundle_skips_when_policy_says_no():
  bundles = [_bundle("CHV2"), _bundle(ANGLE_SUBARU_NNMV2_INTERNAL_NAME)]

  assert select_angle_subaru_auto_default_bundle(
    bundles,
    is_angle_subaru=False,
    active_bundle=None,
    download_index=None,
    opt_out=False,
    auto_failed=False,
  ) is None
  assert select_angle_subaru_auto_default_bundle(
    bundles,
    is_angle_subaru=True,
    active_bundle=_bundle("CHV2"),
    download_index=None,
    opt_out=False,
    auto_failed=False,
  ) is None
  assert select_angle_subaru_auto_default_bundle(
    bundles,
    is_angle_subaru=True,
    active_bundle=None,
    download_index=38,
    opt_out=False,
    auto_failed=False,
  ) is None
  assert select_angle_subaru_auto_default_bundle(
    bundles,
    is_angle_subaru=True,
    active_bundle=None,
    download_index=None,
    opt_out=True,
    auto_failed=False,
  ) is None
  assert select_angle_subaru_auto_default_bundle(
    bundles,
    is_angle_subaru=True,
    active_bundle=None,
    download_index=None,
    opt_out=False,
    auto_failed=True,
  ) is None
