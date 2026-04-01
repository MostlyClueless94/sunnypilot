import unittest
from types import SimpleNamespace

from opendbc.car import structs
from opendbc.car.subaru import subarucan
from opendbc.car.subaru.carcontroller import (
  CarController,
  LOW_SPEED_SMOOTH_MAX_SPEED,
  LOW_SPEED_STRAIGHT_SIGN_RELEASE_FRAMES,
)
from opendbc.car.subaru.interface import CarInterface
from opendbc.car.subaru.values import CAR


class TestSubaruCarController(unittest.TestCase):
  @staticmethod
  def _build_cs(v_ego_raw, steering_angle_deg, steering_pressed=False):
    return SimpleNamespace(out=SimpleNamespace(
      vEgoRaw=v_ego_raw,
      steeringAngleDeg=steering_angle_deg,
      gearShifter=structs.CarState.GearShifter.drive,
      standstill=False,
      steeringPressed=steering_pressed,
    ))

  @staticmethod
  def _build_cc(lat_active, enabled, steering_angle_deg):
    return SimpleNamespace(
      latActive=lat_active,
      enabled=enabled,
      actuators=SimpleNamespace(steeringAngleDeg=steering_angle_deg),
    )

  def _build_controller(self):
    CP = CarInterface.get_non_essential_params(CAR.SUBARU_OUTBACK_2023)
    CP_SP = CarInterface.get_non_essential_params_sp(CP, CAR.SUBARU_OUTBACK_2023)
    return CarController({}, CP, CP_SP)

  def test_mads_manual_override_still_wins(self):
    controller = self._build_controller()
    expected_controller = self._build_controller()
    cs = self._build_cs(9.5, 20.56, steering_pressed=True)
    cc = self._build_cc(True, False, 19.86)

    controller.apply_angle_last = cs.out.steeringAngleDeg

    msg = controller.handle_angle_lateral(cc, cs)
    expected = subarucan.create_steering_control_angle(expected_controller.packer, cs.out.steeringAngleDeg, False)

    self.assertEqual(msg, expected)
    self.assertAlmostEqual(controller.apply_angle_last, cs.out.steeringAngleDeg)

  def test_low_speed_straight_stability_holds_alternating_small_requests_centered(self):
    controller = self._build_controller()
    cs = self._build_cs(3.0, 0.2)

    held_targets = [
      controller._get_low_speed_stable_angle_target(target, cs)
      for target in (1.6, -1.6, 1.6, -1.6)
    ]

    self.assertEqual(held_targets, [0.0, 0.0, 0.0, 0.0])

  def test_low_speed_straight_stability_requires_persistence_before_leaving_center(self):
    controller = self._build_controller()
    cs = self._build_cs(3.0, 0.2)

    held_targets = [
      controller._get_low_speed_stable_angle_target(1.8, cs)
      for _ in range(LOW_SPEED_STRAIGHT_SIGN_RELEASE_FRAMES - 1)
    ]
    released_target = controller._get_low_speed_stable_angle_target(1.8, cs)

    self.assertTrue(all(target == 0.0 for target in held_targets))
    self.assertAlmostEqual(released_target, 1.8)

  def test_low_speed_straight_stability_bypasses_real_turn_requests(self):
    controller = self._build_controller()
    cs = self._build_cs(3.0, 0.5)

    stabilized_target = controller._get_low_speed_stable_angle_target(12.0, cs)

    self.assertAlmostEqual(stabilized_target, 12.0)

  def test_low_speed_straight_stability_bypasses_driver_input(self):
    controller = self._build_controller()
    cs = self._build_cs(3.0, 0.2, steering_pressed=True)

    stabilized_target = controller._get_low_speed_stable_angle_target(1.6, cs)

    self.assertAlmostEqual(stabilized_target, 1.6)

  def test_low_speed_center_damping_zeroes_tiny_requests_inside_deadband(self):
    controller = self._build_controller()
    cs = self._build_cs(3.0, 0.2)

    damped_target, active, sign_flip_clamped = controller._get_low_speed_center_damped_angle_target(0.4, cs)

    self.assertTrue(active)
    self.assertFalse(sign_flip_clamped)
    self.assertAlmostEqual(damped_target, 0.0)

  def test_low_speed_center_damping_clamps_near_center_sign_flips(self):
    controller = self._build_controller()
    controller.apply_angle_last = 0.5
    cs = self._build_cs(3.0, 0.2)

    damped_target, active, sign_flip_clamped = controller._get_low_speed_center_damped_angle_target(-1.6, cs)

    self.assertTrue(active)
    self.assertTrue(sign_flip_clamped)
    self.assertGreater(damped_target, 0.0)

  def test_low_speed_center_damping_preserves_persistent_small_progress(self):
    controller = self._build_controller()
    cs = self._build_cs(3.0, 0.2)

    damped_targets = []
    for _ in range(4):
      damped_target, active, sign_flip_clamped = controller._get_low_speed_center_damped_angle_target(1.8, cs)
      self.assertTrue(active)
      self.assertFalse(sign_flip_clamped)
      damped_targets.append(damped_target)
      controller.apply_angle_last = damped_target

    self.assertTrue(all(left < right for left, right in zip(damped_targets, damped_targets[1:])))
    self.assertGreater(damped_targets[-1], 1.0)

  def test_low_speed_center_damping_bypasses_real_turn_requests(self):
    controller = self._build_controller()
    cs = self._build_cs(3.0, 0.5)

    damped_target, active, sign_flip_clamped = controller._get_low_speed_center_damped_angle_target(5.0, cs)

    self.assertFalse(active)
    self.assertFalse(sign_flip_clamped)
    self.assertAlmostEqual(damped_target, 5.0)

  def test_low_speed_center_damping_bypasses_high_speed_behavior(self):
    controller = self._build_controller()
    cs = self._build_cs(LOW_SPEED_SMOOTH_MAX_SPEED, 0.2)

    damped_target, active, sign_flip_clamped = controller._get_low_speed_center_damped_angle_target(1.6, cs)

    self.assertFalse(active)
    self.assertFalse(sign_flip_clamped)
    self.assertAlmostEqual(damped_target, 1.6)

  def test_low_speed_center_damping_bypasses_driver_input(self):
    controller = self._build_controller()
    cs = self._build_cs(3.0, 0.2, steering_pressed=True)

    damped_target, active, sign_flip_clamped = controller._get_low_speed_center_damped_angle_target(1.6, cs)

    self.assertFalse(active)
    self.assertFalse(sign_flip_clamped)
    self.assertAlmostEqual(damped_target, 1.6)


if __name__ == "__main__":
  unittest.main()
