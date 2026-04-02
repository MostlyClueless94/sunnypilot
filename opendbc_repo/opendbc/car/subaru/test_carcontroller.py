import unittest
from types import SimpleNamespace

from opendbc.car import structs
from opendbc.car.subaru.fingerprints import FW_VERSIONS
from opendbc.car.subaru import subarucan
from opendbc.car.subaru.carcontroller import (
  CarController,
  LOW_SPEED_SMOOTH_MAX_SPEED,
  LOW_SPEED_STRAIGHT_SIGN_RELEASE_FRAMES,
  MADS_MANUAL_OVERRIDE_HOLD_FRAMES,
  MADS_MANUAL_OVERRIDE_RAMP_FRAMES,
  SUBARU_ANGLE_RATE_LIMIT_DOWN_STOCK,
)
from opendbc.car.subaru.interface import CarInterface
from opendbc.car.subaru.values import CAR
from opendbc.car.tests.routes import routes


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

  def _prime_mads_manual_override_ramp(self, controller, cc, v_ego_raw=8.0, measured_angle=10.0):
    controller.apply_angle_last = measured_angle

    controller.handle_angle_lateral(cc, self._build_cs(v_ego_raw, measured_angle, steering_pressed=True))
    released_cs = self._build_cs(v_ego_raw, measured_angle, steering_pressed=False)
    for _ in range(MADS_MANUAL_OVERRIDE_HOLD_FRAMES):
      controller.handle_angle_lateral(cc, released_cs)

    self.assertEqual(controller.mads_manual_override_hold_frames, 0)
    self.assertEqual(controller.mads_manual_override_ramp_frames, MADS_MANUAL_OVERRIDE_RAMP_FRAMES)
    return released_cs

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

  def test_mads_manual_override_hold_persists_after_steering_pressed_clears(self):
    controller = self._build_controller()
    cs_pressed = self._build_cs(8.0, 10.0, steering_pressed=True)
    cc = self._build_cc(True, False, 14.0)

    controller.apply_angle_last = cs_pressed.out.steeringAngleDeg
    controller.handle_angle_lateral(cc, cs_pressed)

    cs_released = self._build_cs(8.0, 10.0, steering_pressed=False)
    msg = controller.handle_angle_lateral(cc, cs_released)
    expected = subarucan.create_steering_control_angle(controller.packer, cs_released.out.steeringAngleDeg, False)

    self.assertEqual(msg, expected)
    self.assertEqual(controller.mads_manual_override_hold_frames, MADS_MANUAL_OVERRIDE_HOLD_FRAMES - 1)
    self.assertEqual(controller.mads_manual_override_ramp_frames, 0)
    self.assertAlmostEqual(controller.apply_angle_last, cs_released.out.steeringAngleDeg)

  def test_mads_manual_override_ramp_progresses_monotonically_toward_target(self):
    controller = self._build_controller()
    cc = self._build_cc(True, False, 14.0)
    cs_released = self._prime_mads_manual_override_ramp(controller, cc)

    ramped_angles = []
    for _ in range(4):
      controller.handle_angle_lateral(cc, cs_released)
      ramped_angles.append(controller.apply_angle_last)

    self.assertTrue(all(left <= right for left, right in zip(ramped_angles, ramped_angles[1:])))
    self.assertGreater(ramped_angles[-1], cs_released.out.steeringAngleDeg)
    self.assertLessEqual(ramped_angles[-1], cc.actuators.steeringAngleDeg)

  def test_mads_manual_override_ramp_target_is_captured_at_hold_exit(self):
    controller = self._build_controller()
    cc_release = self._build_cc(True, False, 14.0)
    cs_released = self._prime_mads_manual_override_ramp(controller, cc_release)

    self.assertAlmostEqual(controller.mads_manual_override_ramp_target_angle, 14.0)

    cc_changed = self._build_cc(True, False, 18.0)
    controller.handle_angle_lateral(cc_changed, cs_released)

    self.assertAlmostEqual(controller.mads_manual_override_ramp_target_angle, 14.0)
    self.assertLess(controller.apply_angle_last, 14.0)

  def test_mads_manual_override_ramp_heads_toward_frozen_hold_exit_target(self):
    controller = self._build_controller()
    cc_release = self._build_cc(True, False, 14.0)
    cs_released = self._prime_mads_manual_override_ramp(controller, cc_release)
    cc_changed = self._build_cc(True, False, 18.0)

    ramped_angles = []
    for _ in range(4):
      controller.handle_angle_lateral(cc_changed, cs_released)
      ramped_angles.append(controller.apply_angle_last)

    self.assertTrue(all(left <= right for left, right in zip(ramped_angles, ramped_angles[1:])))
    self.assertLessEqual(ramped_angles[-1], 14.0)
    self.assertLess(ramped_angles[-1], cc_changed.actuators.steeringAngleDeg)

  def test_mads_manual_override_ramp_cancels_when_driver_input_returns(self):
    controller = self._build_controller()
    cc = self._build_cc(True, False, 14.0)
    cs_released = self._prime_mads_manual_override_ramp(controller, cc)

    controller.handle_angle_lateral(cc, cs_released)
    self.assertLess(controller.mads_manual_override_ramp_frames, MADS_MANUAL_OVERRIDE_RAMP_FRAMES)

    cs_pressed = self._build_cs(8.0, 10.0, steering_pressed=True)
    msg = controller.handle_angle_lateral(cc, cs_pressed)
    expected = subarucan.create_steering_control_angle(controller.packer, cs_pressed.out.steeringAngleDeg, False)

    self.assertEqual(msg, expected)
    self.assertEqual(controller.mads_manual_override_hold_frames, MADS_MANUAL_OVERRIDE_HOLD_FRAMES)
    self.assertEqual(controller.mads_manual_override_ramp_frames, 0)
    self.assertAlmostEqual(controller.apply_angle_last, cs_pressed.out.steeringAngleDeg)

  def test_mads_manual_override_release_logic_does_not_change_full_engaged_behavior(self):
    controller = self._build_controller()
    cs = self._build_cs(8.0, 10.0, steering_pressed=True)
    cc = self._build_cc(True, True, 30.0)

    controller.apply_angle_last = cs.out.steeringAngleDeg
    controller.handle_angle_lateral(cc, cs)

    self.assertEqual(controller.mads_manual_override_hold_frames, 0)
    self.assertEqual(controller.mads_manual_override_ramp_frames, 0)
    self.assertNotAlmostEqual(controller.apply_angle_last, cs.out.steeringAngleDeg)

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

  def test_low_speed_smoothing_tune_toggle_off_is_noop(self):
    baseline = self._build_controller()
    tuned = self._build_controller()
    baseline.apply_angle_last = 0.5
    tuned.apply_angle_last = 0.5
    tuned.mc_subaru_smoothing_tune = False
    tuned.mc_subaru_smoothing_strength = 3

    baseline_target = baseline._get_low_speed_smoothed_angle_target(1.8, 0.5)
    tuned_target = tuned._get_low_speed_smoothed_angle_target(1.8, 0.5)

    self.assertAlmostEqual(tuned_target, baseline_target)

  def test_low_speed_smoothing_tune_zero_strength_matches_baseline(self):
    baseline = self._build_controller()
    tuned = self._build_controller()
    baseline.apply_angle_last = 0.5
    tuned.apply_angle_last = 0.5
    tuned.mc_subaru_smoothing_tune = True
    tuned.mc_subaru_smoothing_strength = 0

    baseline_target = baseline._get_low_speed_smoothed_angle_target(1.8, 0.5)
    tuned_target = tuned._get_low_speed_smoothed_angle_target(1.8, 0.5)

    self.assertAlmostEqual(tuned_target, baseline_target)

  def test_low_speed_smoothing_strength_positive_adds_more_smoothing(self):
    baseline = self._build_controller()
    tuned = self._build_controller()
    baseline.apply_angle_last = 0.0
    tuned.apply_angle_last = 0.0
    tuned.mc_subaru_smoothing_tune = True
    tuned.mc_subaru_smoothing_strength = 3

    baseline_target = baseline._get_low_speed_smoothed_angle_target(1.8, 0.5)
    tuned_target = tuned._get_low_speed_smoothed_angle_target(1.8, 0.5)

    self.assertLess(tuned_target, baseline_target)

  def test_low_speed_smoothing_strength_negative_is_more_responsive(self):
    baseline = self._build_controller()
    tuned = self._build_controller()
    baseline.apply_angle_last = 0.0
    tuned.apply_angle_last = 0.0
    tuned.mc_subaru_smoothing_tune = True
    tuned.mc_subaru_smoothing_strength = -3

    baseline_target = baseline._get_low_speed_smoothed_angle_target(1.8, 0.5)
    tuned_target = tuned._get_low_speed_smoothed_angle_target(1.8, 0.5)

    self.assertGreater(tuned_target, baseline_target)

  def test_center_damping_tune_toggle_off_is_noop(self):
    baseline = self._build_controller()
    tuned = self._build_controller()
    baseline.apply_angle_last = 0.5
    tuned.apply_angle_last = 0.5
    tuned.mc_subaru_smoothing_tune = False
    tuned.mc_subaru_center_damping_strength = 3
    cs = self._build_cs(3.0, 0.2)

    baseline_target, baseline_active, baseline_clamped = baseline._get_low_speed_center_damped_angle_target(-1.6, cs)
    tuned_target, tuned_active, tuned_clamped = tuned._get_low_speed_center_damped_angle_target(-1.6, cs)

    self.assertEqual(tuned_active, baseline_active)
    self.assertEqual(tuned_clamped, baseline_clamped)
    self.assertAlmostEqual(tuned_target, baseline_target)

  def test_center_damping_tune_zero_strength_matches_baseline(self):
    baseline = self._build_controller()
    tuned = self._build_controller()
    baseline.apply_angle_last = 0.5
    tuned.apply_angle_last = 0.5
    tuned.mc_subaru_smoothing_tune = True
    tuned.mc_subaru_center_damping_strength = 0
    cs = self._build_cs(3.0, 0.2)

    baseline_target, baseline_active, baseline_clamped = baseline._get_low_speed_center_damped_angle_target(-1.6, cs)
    tuned_target, tuned_active, tuned_clamped = tuned._get_low_speed_center_damped_angle_target(-1.6, cs)

    self.assertEqual(tuned_active, baseline_active)
    self.assertEqual(tuned_clamped, baseline_clamped)
    self.assertAlmostEqual(tuned_target, baseline_target)

  def test_center_damping_strength_positive_adds_more_damping(self):
    baseline = self._build_controller()
    tuned = self._build_controller()
    baseline.apply_angle_last = 0.5
    tuned.apply_angle_last = 0.5
    tuned.mc_subaru_smoothing_tune = True
    tuned.mc_subaru_center_damping_strength = 3
    cs = self._build_cs(3.0, 0.2)

    baseline_target, baseline_active, baseline_clamped = baseline._get_low_speed_center_damped_angle_target(-1.6, cs)
    tuned_target, tuned_active, tuned_clamped = tuned._get_low_speed_center_damped_angle_target(-1.6, cs)

    self.assertTrue(baseline_active)
    self.assertTrue(tuned_active)
    self.assertTrue(baseline_clamped)
    self.assertTrue(tuned_clamped)
    self.assertGreater(tuned_target, baseline_target)

  def test_center_damping_strength_negative_is_more_responsive(self):
    baseline = self._build_controller()
    tuned = self._build_controller()
    baseline.apply_angle_last = 0.0
    tuned.apply_angle_last = 0.0
    tuned.mc_subaru_smoothing_tune = True
    tuned.mc_subaru_center_damping_strength = -3
    cs = self._build_cs(3.0, 0.2)

    baseline_target, baseline_active, _ = baseline._get_low_speed_center_damped_angle_target(0.4, cs)
    tuned_target, tuned_active, _ = tuned._get_low_speed_center_damped_angle_target(0.4, cs)

    self.assertTrue(baseline_active)
    self.assertTrue(tuned_active)
    self.assertAlmostEqual(baseline_target, 0.0)
    self.assertGreater(tuned_target, 0.0)

  def test_low_speed_delta_deadzone_is_noop_when_toggle_off(self):
    controller = self._build_controller()
    controller.apply_angle_last = 0.5
    cs = self._build_cs(3.0, 0.2)

    filtered_target, active, deadzone = controller._get_low_speed_delta_deadzone_target(1.2, cs, True)

    self.assertFalse(active)
    self.assertEqual(deadzone, 0.0)
    self.assertAlmostEqual(filtered_target, 1.2)

  def test_low_speed_delta_deadzone_stays_independent_from_smoothing_tune(self):
    controller = self._build_controller()
    controller.mc_subaru_smoothing_tune = True
    controller.mc_subaru_smoothing_strength = 3
    controller.mc_subaru_center_damping_strength = 3
    controller.apply_angle_last = 0.5
    cs = self._build_cs(3.0, 0.2)

    filtered_target, active, deadzone = controller._get_low_speed_delta_deadzone_target(1.2, cs, True)

    self.assertFalse(active)
    self.assertEqual(deadzone, 0.0)
    self.assertAlmostEqual(filtered_target, 1.2)

  def test_low_speed_delta_deadzone_filters_small_delta_when_enabled(self):
    controller = self._build_controller()
    controller.mc_subaru_chatter_fix = True
    controller.apply_angle_last = 0.5
    cs = self._build_cs(3.0, 0.2)

    filtered_target, active, deadzone = controller._get_low_speed_delta_deadzone_target(1.0, cs, True)

    self.assertTrue(active)
    self.assertGreater(deadzone, 0.0)
    self.assertAlmostEqual(filtered_target, 0.5)

  def test_low_speed_delta_deadzone_bypasses_real_turn_requests(self):
    controller = self._build_controller()
    controller.mc_subaru_chatter_fix = True
    cs = self._build_cs(3.0, 0.5)

    filtered_target, active, deadzone = controller._get_low_speed_delta_deadzone_target(5.0, cs, True)

    self.assertFalse(active)
    self.assertEqual(deadzone, 0.0)
    self.assertAlmostEqual(filtered_target, 5.0)

  def test_low_speed_delta_deadzone_bypasses_driver_input(self):
    controller = self._build_controller()
    controller.mc_subaru_chatter_fix = True
    cs = self._build_cs(3.0, 0.2, steering_pressed=True)

    filtered_target, active, deadzone = controller._get_low_speed_delta_deadzone_target(1.2, cs, True)

    self.assertFalse(active)
    self.assertEqual(deadzone, 0.0)
    self.assertAlmostEqual(filtered_target, 1.2)

  def test_low_speed_delta_deadzone_bypasses_high_speed_window(self):
    controller = self._build_controller()
    controller.mc_subaru_chatter_fix = True
    cs = self._build_cs(LOW_SPEED_SMOOTH_MAX_SPEED, 0.2)

    filtered_target, active, deadzone = controller._get_low_speed_delta_deadzone_target(1.2, cs, True)

    self.assertFalse(active)
    self.assertEqual(deadzone, 0.0)
    self.assertAlmostEqual(filtered_target, 1.2)

  def test_low_speed_delta_deadzone_is_noop_when_lkas_not_requested(self):
    controller = self._build_controller()
    controller.mc_subaru_chatter_fix = True
    controller.apply_angle_last = 0.5
    cs = self._build_cs(3.0, 0.2)

    filtered_target, active, deadzone = controller._get_low_speed_delta_deadzone_target(1.2, cs, False)

    self.assertFalse(active)
    self.assertEqual(deadzone, 0.0)
    self.assertAlmostEqual(filtered_target, 1.2)

  def test_subaru_unwind_params_keep_stock_down_table(self):
    controller = self._build_controller()

    controller.mc_subaru_unwind_rate_test = False
    controller.mc_subaru_unwind_rate_mode = 2
    controller._apply_subaru_unwind_rate_limit_test()

    self.assertEqual(controller.p.ANGLE_LIMITS.ANGLE_RATE_LIMIT_UP, ([0., 5., 35.], [5., .8, .15]))
    self.assertEqual(controller.p.ANGLE_LIMITS.ANGLE_RATE_LIMIT_DOWN, SUBARU_ANGLE_RATE_LIMIT_DOWN_STOCK)

  def test_subaru_unwind_params_stay_inert_even_when_enabled(self):
    controller = self._build_controller()

    controller.mc_subaru_unwind_rate_test = True
    controller.mc_subaru_unwind_rate_mode = 0
    controller._apply_subaru_unwind_rate_limit_test()

    self.assertEqual(controller.p.ANGLE_LIMITS.ANGLE_RATE_LIMIT_UP, ([0., 5., 35.], [5., .8, .15]))
    self.assertEqual(controller.p.ANGLE_LIMITS.ANGLE_RATE_LIMIT_DOWN, SUBARU_ANGLE_RATE_LIMIT_DOWN_STOCK)

  def test_subaru_unwind_params_stay_inert_across_all_legacy_modes(self):
    controller = self._build_controller()

    for mode in (0, 1, 2):
      controller.mc_subaru_unwind_rate_test = True
      controller.mc_subaru_unwind_rate_mode = mode
      controller._apply_subaru_unwind_rate_limit_test()
      self.assertEqual(controller.p.ANGLE_LIMITS.ANGLE_RATE_LIMIT_DOWN, SUBARU_ANGLE_RATE_LIMIT_DOWN_STOCK)

    self.assertEqual(controller.p.ANGLE_LIMITS.ANGLE_RATE_LIMIT_UP, ([0., 5., 35.], [5., .8, .15]))

  def test_crosstrek_2025_support_metadata_present(self):
    self.assertIn(CAR.SUBARU_CROSSTREK_2025, FW_VERSIONS)
    self.assertTrue(any(route.car_model == CAR.SUBARU_CROSSTREK_2025 for route in routes))


if __name__ == "__main__":
  unittest.main()
