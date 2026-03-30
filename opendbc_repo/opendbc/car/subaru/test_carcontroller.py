import unittest
from types import SimpleNamespace

from openpilot.common.params import Params
from openpilot.common.constants import CV
from opendbc.car import structs
from opendbc.car.subaru import subarucan
from opendbc.car.subaru.carcontroller import CarController, LONG_MESSAGE_STALE_MAX_FRAMES, LOW_SPEED_STRAIGHT_SIGN_RELEASE_FRAMES
from opendbc.car.subaru.carstate import CarState
from opendbc.car.subaru.interface import CarInterface
from opendbc.car.subaru.values import CAR, OUTBACK_ALPHA_LONG_PHASE, SubaruFlags


class TestSubaruCarController(unittest.TestCase):
  def setUp(self):
    self._set_custom_acc_params(False, 1, 5)
    params = Params()
    params.put_bool("IntelligentCruiseButtonManagement", True)
    params.put_bool("SubaruStockAccDevButtonsEnabled", False)
    params.put("SubaruStockAccDevButtonCommand", 0)

  @staticmethod
  def _set_custom_acc_params(enabled, short_increment, long_increment):
    params = Params()
    params.put_bool("CustomAccIncrementsEnabled", enabled)
    params.put("CustomAccShortPressIncrement", short_increment)
    params.put("CustomAccLongPressIncrement", long_increment)

  def test_subaru_import_smoke(self):
    self.assertIsNotNone(CarInterface)
    self.assertIsNotNone(CarController)
    self.assertGreaterEqual(OUTBACK_ALPHA_LONG_PHASE, 0)

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

  @staticmethod
  def _build_cc_torque(lat_active, torque):
    return SimpleNamespace(
      latActive=lat_active,
      enabled=True,
      actuators=SimpleNamespace(torque=torque),
    )

  @staticmethod
  def _build_cs_torque(v_ego_raw, steering_angle_deg, steering_pressed=False, steering_torque=0, steering_rate_deg=0):
    return SimpleNamespace(out=SimpleNamespace(
      vEgoRaw=v_ego_raw,
      steeringAngleDeg=steering_angle_deg,
      gearShifter=structs.CarState.GearShifter.drive,
      standstill=False,
      steeringPressed=steering_pressed,
      steeringTorque=steering_torque,
      steeringRateDeg=steering_rate_deg,
    ))

  def _build_controller(self):
    CP = CarInterface.get_non_essential_params(CAR.SUBARU_OUTBACK_2023)
    CP_SP = CarInterface.get_non_essential_params_sp(CP, CAR.SUBARU_OUTBACK_2023)
    return CarController({}, CP, CP_SP)

  @staticmethod
  def _build_long_controller():
    fingerprint = {0: {}, 1: {}, 2: {}}
    CP = CarInterface.get_params(CAR.SUBARU_OUTBACK_2023, fingerprint, [], True, False, False)
    CP_SP = CarInterface.get_params_sp(CP, CAR.SUBARU_OUTBACK_2023, fingerprint, [], True, False, False)
    return CarController({}, CP, CP_SP)

  @staticmethod
  def _build_parser(messages=None):
    return SimpleNamespace(vl=messages or {})

  @staticmethod
  def _build_carstate_stub(flags=0):
    return SimpleNamespace(CP=SimpleNamespace(flags=flags))

  @staticmethod
  def _build_long_source(counter=0):
    return {
      "CHECKSUM": 0,
      "Signal1": 0,
      "Cruise_Fault": 0,
      "Cruise_RPM": 600,
      "Cruise_Activated": 0,
      "Brake_Lights": 0,
      "Cruise_Hold": 0,
      "Signal3": 0,
      "COUNTER": counter,
    }, {
      "CHECKSUM": 0,
      "Signal1": 0,
      "Brake_Pressure": 0,
      "AEB_Status": 0,
      "Cruise_Brake_Lights": 0,
      "Cruise_Brake_Fault": 0,
      "Cruise_Brake_Active": 0,
      "Cruise_Activated": 0,
      "Signal3": 0,
      "COUNTER": counter,
    }, {
      "CHECKSUM": 0,
      "Signal1": 0,
      "Cruise_Fault": 0,
      "Cruise_Throttle": 1818,
      "Signal2": 0,
      "Car_Follow": 0,
      "Low_Speed_Follow": 0,
      "Cruise_Soft_Disable": 0,
      "Signal7": 0,
      "Cruise_Brake_Active": 0,
      "Distance_Swap": 0,
      "Cruise_EPB": 0,
      "Signal4": 0,
      "Close_Distance": 0,
      "Signal5": 0,
      "Cruise_Cancel": 0,
      "Cruise_Set": 0,
      "Cruise_Resume": 0,
      "Signal6": 0,
      "COUNTER": counter,
    }

  @staticmethod
  def _build_long_cs(gear=structs.CarState.GearShifter.drive, es_status_msg=None, es_brake_msg=None, es_distance_msg=None):
    return SimpleNamespace(
      out=SimpleNamespace(
        vEgoRaw=8.0,
        steeringAngleDeg=0.0,
        gearShifter=gear,
        standstill=False,
        steeringPressed=False,
        steeringTorque=0,
        steeringRateDeg=0,
      ),
      es_status_msg=es_status_msg or {},
      es_brake_msg=es_brake_msg or {},
      es_distance_msg=es_distance_msg or {},
      es_lkas_state_msg={},
      es_dashstatus_msg={},
    )

  @staticmethod
  def _build_long_cc(long_active, accel=0.5, cancel=False):
    return SimpleNamespace(
      latActive=False,
      enabled=True,
      longActive=long_active,
      actuators=SimpleNamespace(accel=accel, steeringAngleDeg=0.0, torque=0.0),
      hudControl=SimpleNamespace(leadVisible=False, visualAlert=0, leftLaneVisible=False, rightLaneVisible=False,
                                 leftLaneDepart=False, rightLaneDepart=False),
      cruiseControl=SimpleNamespace(cancel=cancel),
    )

  @staticmethod
  def _build_icbm_cc_sp(send_button, v_target):
    return SimpleNamespace(
      intelligentCruiseButtonManagement=SimpleNamespace(sendButton=send_button, vTarget=v_target),
    )

  @staticmethod
  def _build_icbm_cs(cruise_enabled, cluster_speed=30, es_distance_msg=None, button_events=None):
    return SimpleNamespace(
      out=SimpleNamespace(
        vEgoRaw=12.0,
        steeringAngleDeg=0.0,
        gearShifter=structs.CarState.GearShifter.drive,
        standstill=False,
        steeringPressed=False,
        steeringTorque=0,
        steeringRateDeg=0,
        cruiseState=SimpleNamespace(available=True, enabled=cruise_enabled, speedCluster=cluster_speed * CV.MPH_TO_MS),
      ),
      es_distance_msg=es_distance_msg or {},
      es_dashstatus_msg={},
      es_lkas_state_msg={},
      buttonEvents=button_events or [],
    )

  def test_mads_manual_override_still_wins(self):
    controller = self._build_controller()
    expected_controller = self._build_controller()
    cs = self._build_cs(9.5, 20.56, steering_pressed=True)
    cc = self._build_cc(True, False, 19.86)

    controller.apply_angle_last = cs.out.steeringAngleDeg

    msg = controller.handle_angle_lateral(cc, cs)
    expected = subarucan.create_steering_control_angle(expected_controller.packer, 0, cs.out.steeringAngleDeg, False)

    self.assertEqual(msg, expected)
    self.assertAlmostEqual(controller.apply_angle_last, cs.out.steeringAngleDeg)

  def test_angle_lkas_human_turn_detection_releases_control(self):
    params = Params()
    params.put_bool("enable_human_turn_detection", True)
    params.put_bool("disable_BP_lat_UI", False)

    controller = self._build_controller()
    expected_controller = self._build_controller()
    cs = self._build_cs(12.0, 55.0, steering_pressed=True)
    cc = self._build_cc(True, True, 40.0)

    controller.apply_angle_last = cs.out.steeringAngleDeg

    msg = controller.handle_angle_lateral(cc, cs)
    expected = subarucan.create_steering_control_angle(expected_controller.packer, 0, cs.out.steeringAngleDeg, False)

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

  def test_torque_human_turn_detection_zeroes_steer_request(self):
    params = Params()
    params.put_bool("enable_human_turn_detection", True)
    params.put_bool("disable_BP_lat_UI", False)

    CP = CarInterface.get_non_essential_params(CAR.SUBARU_OUTBACK)
    CP_SP = CarInterface.get_non_essential_params_sp(CP, CAR.SUBARU_OUTBACK)
    controller = CarController({}, CP, CP_SP)
    expected_controller = CarController({}, CP, CP_SP)

    cs = self._build_cs_torque(12.0, 55.0, steering_pressed=True)
    cc = self._build_cc_torque(True, 0.2)

    msg = controller.handle_torque_lateral(cc, cs)
    expected = subarucan.create_steering_control(expected_controller.packer, 0, False)

    self.assertEqual(msg, expected)
    self.assertEqual(controller.apply_torque_last, 0)

  def test_newer_angle_lkas_params_construct(self):
    newer_platforms = (
      CAR.SUBARU_FORESTER_2022,
      CAR.SUBARU_OUTBACK_2023,
      CAR.SUBARU_ASCENT_2023,
      CAR.SUBARU_CROSSTREK_2025,
    )

    for platform in newer_platforms:
      with self.subTest(platform=platform):
        CP = CarInterface.get_non_essential_params(platform)
        _ = CarInterface.get_non_essential_params_sp(CP, platform)

        self.assertEqual(CP.carFingerprint, platform)
        self.assertGreater(CP.maxLateralAccel, 0.0)

  def test_forester_2022_is_not_dashcam_only_on_mostlyclueless(self):
    CP = CarInterface.get_non_essential_params(CAR.SUBARU_FORESTER_2022)
    _ = CarInterface.get_non_essential_params_sp(CP, CAR.SUBARU_FORESTER_2022)

    self.assertFalse(CP.dashcamOnly)
    self.assertEqual(CP.steerControlType, structs.CarParams.SteerControlType.angle)

  def test_outback_2023_alpha_longitudinal_is_allowlisted_on_mostlyclueless(self):
    fingerprint = {0: {}, 1: {}, 2: {}}
    CP = CarInterface.get_params(CAR.SUBARU_OUTBACK_2023, fingerprint, [], True, False, False)

    self.assertTrue(CP.alphaLongitudinalAvailable)
    self.assertTrue(CP.openpilotLongitudinalControl)
    self.assertTrue(CP.flags & SubaruFlags.DISABLE_EYESIGHT)

  def test_non_outback_angle_lkas_platforms_remain_alpha_long_blocked(self):
    fingerprint = {0: {}, 1: {}, 2: {}}
    for platform in (CAR.SUBARU_ASCENT_2023, CAR.SUBARU_CROSSTREK_2025, CAR.SUBARU_FORESTER_2022):
      with self.subTest(platform=platform):
        CP = CarInterface.get_params(platform, fingerprint, [], True, False, False)
        self.assertFalse(CP.alphaLongitudinalAvailable)
        self.assertFalse(CP.openpilotLongitudinalControl)

  def test_icbm_is_only_available_for_outback_2023_on_mostlyclueless(self):
    outback_cp = CarInterface.get_non_essential_params(CAR.SUBARU_OUTBACK_2023)
    outback_cp_sp = CarInterface.get_non_essential_params_sp(outback_cp, CAR.SUBARU_OUTBACK_2023)
    self.assertTrue(outback_cp_sp.intelligentCruiseButtonManagementAvailable)

    for platform in (CAR.SUBARU_ASCENT_2023, CAR.SUBARU_CROSSTREK_2025, CAR.SUBARU_FORESTER_2022):
      with self.subTest(platform=platform):
        cp = CarInterface.get_non_essential_params(platform)
        cp_sp = CarInterface.get_non_essential_params_sp(cp, platform)
        self.assertFalse(cp_sp.intelligentCruiseButtonManagementAvailable)

  def test_crosstrek_2025_params_construct(self):
    CP = CarInterface.get_non_essential_params(CAR.SUBARU_CROSSTREK_2025)
    _ = CarInterface.get_non_essential_params_sp(CP, CAR.SUBARU_CROSSTREK_2025)

    self.assertEqual(CP.carFingerprint, CAR.SUBARU_CROSSTREK_2025)
    self.assertGreater(CP.maxLateralAccel, 0.0)

  def test_car_state_bp_prefers_es_status_brake_lights(self):
    car_state = self._build_carstate_stub()
    cp_cam = self._build_parser({"ES_Status": {"Brake_Lights": 1}, "ES_Brake": {"Cruise_Brake_Lights": 0}})
    cp_alt = self._build_parser()

    msg = CarState.update_car_state_bp(car_state, cp_cam, cp_alt, False)

    self.assertTrue(msg.carStateBP.brakeLightStatus.dataAvailable)
    self.assertTrue(msg.carStateBP.brakeLightStatus.brakeLightsOn)

  def test_car_state_bp_falls_back_to_es_brake_lights(self):
    car_state = self._build_carstate_stub()
    cp_cam = self._build_parser({"ES_Brake": {"Cruise_Brake_Lights": 1}})
    cp_alt = self._build_parser()

    msg = CarState.update_car_state_bp(car_state, cp_cam, cp_alt, False)

    self.assertTrue(msg.carStateBP.brakeLightStatus.dataAvailable)
    self.assertTrue(msg.carStateBP.brakeLightStatus.brakeLightsOn)

  def test_car_state_bp_uses_brake_pressed_when_no_signal_is_available(self):
    car_state = self._build_carstate_stub()
    cp_cam = self._build_parser()
    cp_alt = self._build_parser()

    msg = CarState.update_car_state_bp(car_state, cp_cam, cp_alt, True)

    self.assertTrue(msg.carStateBP.brakeLightStatus.dataAvailable)
    self.assertTrue(msg.carStateBP.brakeLightStatus.brakeLightsOn)

  def test_car_state_bp_uses_gen2_alt_bus_for_brake_lights(self):
    car_state = self._build_carstate_stub(SubaruFlags.GLOBAL_GEN2)
    cp_cam = self._build_parser({"ES_Status": {"Brake_Lights": 0}})
    cp_alt = self._build_parser({"ES_Status": {"Brake_Lights": 1}})

    msg = CarState.update_car_state_bp(car_state, cp_cam, cp_alt, False)

    self.assertTrue(msg.carStateBP.brakeLightStatus.dataAvailable)
    self.assertTrue(msg.carStateBP.brakeLightStatus.brakeLightsOn)

  def test_outback_long_skips_injection_until_all_source_messages_exist(self):
    controller = self._build_long_controller()
    es_status_msg, _, es_distance_msg = self._build_long_source()
    cs = self._build_long_cs(es_status_msg=es_status_msg, es_distance_msg=es_distance_msg)
    cc = self._build_long_cc(True)

    controller.frame = 5
    _, can_sends = controller.update(cc, None, cs, 0)

    sent_addrs = {msg[0] for msg in can_sends}
    self.assertNotIn(0x220, sent_addrs)
    self.assertNotIn(0x221, sent_addrs)
    self.assertNotIn(0x222, sent_addrs)

  def test_outback_long_uses_cached_messages_and_stales_after_timeout(self):
    controller = self._build_long_controller()
    es_status_msg, es_brake_msg, es_distance_msg = self._build_long_source(counter=3)
    cs = self._build_long_cs(es_status_msg=es_status_msg, es_brake_msg=es_brake_msg, es_distance_msg=es_distance_msg)

    valid, cached = controller._get_longitudinal_source_messages(cs)
    self.assertTrue(valid)
    self.assertTrue(all(msg is not None for msg in cached.values()))

    controller.frame += LONG_MESSAGE_STALE_MAX_FRAMES + 1
    valid, cached = controller._get_longitudinal_source_messages(self._build_long_cs())
    self.assertFalse(valid)
    self.assertTrue(all(msg is not None for msg in cached.values()))

  def test_outback_long_does_not_override_outside_drive(self):
    controller = self._build_long_controller()
    es_status_msg, es_brake_msg, es_distance_msg = self._build_long_source(counter=4)
    cs = self._build_long_cs(gear=structs.CarState.GearShifter.park, es_status_msg=es_status_msg,
                             es_brake_msg=es_brake_msg, es_distance_msg=es_distance_msg)
    cc = self._build_long_cc(True, accel=1.0)

    controller.frame = 5
    _, can_sends = controller.update(cc, None, cs, 0)

    expected_status = subarucan.create_es_status(controller.packer, controller.frame // 5, es_status_msg, 1, False, False, 0)
    expected_brake = subarucan.create_es_brake(controller.packer, controller.frame // 5, es_brake_msg, 1, False, False, 0)
    expected_distance = subarucan.create_es_distance(controller.packer, controller.frame // 5, es_distance_msg, 1, False, False, False, 3400)

    self.assertIn(expected_status, can_sends)
    self.assertIn(expected_brake, can_sends)
    self.assertIn(expected_distance, can_sends)

  def test_outback_long_cancel_preserves_cancel_behavior(self):
    controller = self._build_long_controller()
    es_status_msg, es_brake_msg, es_distance_msg = self._build_long_source(counter=6)
    cs = self._build_long_cs(es_status_msg=es_status_msg, es_brake_msg=es_brake_msg, es_distance_msg=es_distance_msg)
    cc = self._build_long_cc(False, cancel=True)

    controller.frame = 5
    _, can_sends = controller.update(cc, None, cs, 0)

    expected_distance = subarucan.create_es_distance(controller.packer, controller.frame // 5, es_distance_msg, 1, True, False, False, 1818)
    self.assertIn(expected_distance, can_sends)

  def test_icbm_does_not_press_buttons_when_stock_acc_is_not_engaged(self):
    controller = self._build_controller()
    _, _, es_distance_msg = self._build_long_source(counter=2)
    cs = self._build_icbm_cs(False, es_distance_msg=es_distance_msg)
    cc = self._build_long_cc(False)
    cc_sp = self._build_icbm_cc_sp(structs.IntelligentCruiseButtonManagement.SendButtonState.increase, 35)

    controller.frame = 10
    _, can_sends = controller.update(cc, cc_sp, cs, 0)

    sent_addrs = {msg[0] for msg in can_sends}
    self.assertNotIn(0x221, sent_addrs)

  def test_icbm_sends_resume_when_stock_acc_is_engaged(self):
    controller = self._build_controller()
    _, _, es_distance_msg = self._build_long_source(counter=4)
    cs = self._build_icbm_cs(True, es_distance_msg=es_distance_msg)
    cc = self._build_long_cc(False)
    cc_sp = self._build_icbm_cc_sp(structs.IntelligentCruiseButtonManagement.SendButtonState.increase, 35)

    controller.frame = 10
    _, can_sends = controller.update(cc, cc_sp, cs, 0)

    self.assertTrue(any(msg[0] == 0x221 for msg in can_sends))

  def test_icbm_small_gap_waits_for_cluster_feedback_before_retrying(self):
    Params().put_bool("IsMetric", False)
    controller = self._build_controller()
    _, _, es_distance_msg = self._build_long_source(counter=8)
    cs = self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg)
    cc = self._build_long_cc(False)
    cc_sp = self._build_icbm_cc_sp(structs.IntelligentCruiseButtonManagement.SendButtonState.increase, 34)

    controller.frame = 10
    _, first_send = controller.update(cc, cc_sp, cs, 0)
    for frame in range(11, 15):
      controller.frame = frame
      controller.update(cc, cc_sp, cs, 0)
    controller.frame = 15
    _, second_send = controller.update(cc, cc_sp, cs, 0)

    self.assertTrue(any(msg[0] == 0x221 for msg in first_send))
    self.assertFalse(any(msg[0] == 0x221 for msg in second_send))

  def test_icbm_exact_five_mph_gap_uses_continuous_hold(self):
    Params().put_bool("IsMetric", False)
    controller = self._build_controller()
    _, _, es_distance_msg = self._build_long_source(counter=9)
    cs = self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg)
    cc = self._build_long_cc(False)
    cc_sp = self._build_icbm_cc_sp(structs.IntelligentCruiseButtonManagement.SendButtonState.increase, 35)

    controller.frame = 10
    _, first_send = controller.update(cc, cc_sp, cs, 0)
    for frame in range(11, 15):
      controller.frame = frame
      controller.update(cc, cc_sp, cs, 0)
    controller.frame = 15
    _, second_send = controller.update(cc, cc_sp, cs, 0)

    self.assertTrue(any(msg[0] == 0x221 for msg in first_send))
    self.assertTrue(any(msg[0] == 0x221 for msg in second_send))

  def test_icbm_hold_releases_before_single_tap_cleanup(self):
    Params().put_bool("IsMetric", False)
    controller = self._build_controller()
    _, _, es_distance_msg = self._build_long_source(counter=10)
    cc = self._build_long_cc(False)
    cc_sp = self._build_icbm_cc_sp(structs.IntelligentCruiseButtonManagement.SendButtonState.increase, 36)

    controller.frame = 10
    _, hold_start = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg), 0)
    for frame in range(11, 15):
      controller.frame = frame
      controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg), 0)
    controller.frame = 15
    _, hold_continue = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg), 0)
    for frame in range(16, 20):
      controller.frame = frame
      controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=35, es_distance_msg=es_distance_msg), 0)
    controller.frame = 20
    _, release_gap = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=35, es_distance_msg=es_distance_msg), 0)
    controller.frame = 21
    _, cleanup_tap = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=35, es_distance_msg=es_distance_msg), 0)

    self.assertTrue(any(msg[0] == 0x221 for msg in hold_start))
    self.assertTrue(any(msg[0] == 0x221 for msg in hold_continue))
    self.assertFalse(any(msg[0] == 0x221 for msg in release_gap))
    self.assertTrue(any(msg[0] == 0x221 for msg in cleanup_tap))

  def test_icbm_manual_button_event_cancels_active_hold(self):
    Params().put_bool("IsMetric", False)
    controller = self._build_controller()
    _, _, es_distance_msg = self._build_long_source(counter=11)
    cc = self._build_long_cc(False)
    cc_sp = self._build_icbm_cc_sp(structs.IntelligentCruiseButtonManagement.SendButtonState.increase, 35)

    controller.frame = 10
    _, hold_start = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg), 0)
    for frame in range(11, 15):
      controller.frame = frame
      controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg), 0)
    controller.frame = 15
    _, canceled = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg,
                                                                   button_events=[SimpleNamespace(pressed=True)]), 0)

    self.assertTrue(any(msg[0] == 0x221 for msg in hold_start))
    self.assertFalse(any(msg[0] == 0x221 for msg in canceled))

  def test_icbm_custom_increments_disabled_preserves_fixed_oem_behavior(self):
    Params().put_bool("IsMetric", False)
    self._set_custom_acc_params(False, 3, 10)
    controller = self._build_controller()
    _, _, es_distance_msg = self._build_long_source(counter=12)
    cs = self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg)
    cc = self._build_long_cc(False)
    cc_sp = self._build_icbm_cc_sp(structs.IntelligentCruiseButtonManagement.SendButtonState.increase, 35)

    controller.frame = 10
    _, first_send = controller.update(cc, cc_sp, cs, 0)
    controller.frame = 15
    _, second_send = controller.update(cc, cc_sp, cs, 0)

    self.assertEqual(controller.icbm_interface._get_hold_increment(), 5)
    self.assertEqual(controller.icbm_interface._get_tap_increment(), 1)
    self.assertTrue(any(msg[0] == 0x221 for msg in first_send))
    self.assertTrue(any(msg[0] == 0x221 for msg in second_send))

  def test_icbm_custom_long_increment_10_releases_hold_below_custom_threshold(self):
    Params().put_bool("IsMetric", False)
    self._set_custom_acc_params(True, 1, 10)
    controller = self._build_controller()
    _, _, es_distance_msg = self._build_long_source(counter=13)
    cc = self._build_long_cc(False)
    cc_sp = self._build_icbm_cc_sp(structs.IntelligentCruiseButtonManagement.SendButtonState.increase, 55)

    controller.frame = 10
    _, hold_start = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg), 0)
    controller.frame = 15
    _, hold_continue = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=40, es_distance_msg=es_distance_msg), 0)
    controller.frame = 20
    _, release_gap = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=50, es_distance_msg=es_distance_msg), 0)

    self.assertEqual(controller.icbm_interface._get_hold_increment(), 10)
    self.assertTrue(any(msg[0] == 0x221 for msg in hold_start))
    self.assertTrue(any(msg[0] == 0x221 for msg in hold_continue))
    self.assertFalse(any(msg[0] == 0x221 for msg in release_gap))
    self.assertFalse(controller.icbm_interface.hold_active)

  def test_icbm_custom_short_increment_chunks_cleanup_without_overshoot(self):
    Params().put_bool("IsMetric", False)
    self._set_custom_acc_params(True, 3, 10)
    controller = self._build_controller()
    _, _, es_distance_msg = self._build_long_source(counter=14)
    cc = self._build_long_cc(False)
    cc_sp = self._build_icbm_cc_sp(structs.IntelligentCruiseButtonManagement.SendButtonState.increase, 34)

    controller.frame = 10
    _, first_send = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg), 0)
    first_target = controller.icbm_interface.tap_target_speed

    controller.frame = 15
    _, second_send = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=31, es_distance_msg=es_distance_msg), 0)
    second_target = controller.icbm_interface.tap_target_speed

    controller.frame = 20
    _, final_chunk_send = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=33, es_distance_msg=es_distance_msg), 0)
    final_target = controller.icbm_interface.tap_target_speed

    self.assertTrue(any(msg[0] == 0x221 for msg in first_send))
    self.assertTrue(any(msg[0] == 0x221 for msg in second_send))
    self.assertTrue(any(msg[0] == 0x221 for msg in final_chunk_send))
    self.assertEqual(first_target, 33)
    self.assertEqual(second_target, 33)
    self.assertEqual(final_target, 34)

  def test_icbm_custom_long_increment_one_falls_back_to_tap_only(self):
    Params().put_bool("IsMetric", False)
    self._set_custom_acc_params(True, 1, 1)
    controller = self._build_controller()
    _, _, es_distance_msg = self._build_long_source(counter=15)
    cc = self._build_long_cc(False)
    cc_sp = self._build_icbm_cc_sp(structs.IntelligentCruiseButtonManagement.SendButtonState.increase, 35)

    controller.frame = 10
    _, first_send = controller.update(cc, cc_sp, self._build_icbm_cs(True, cluster_speed=30, es_distance_msg=es_distance_msg), 0)

    self.assertTrue(any(msg[0] == 0x221 for msg in first_send))
    self.assertFalse(controller.icbm_interface.hold_active)
    self.assertEqual(controller.icbm_interface.tap_wait_direction,
                     structs.IntelligentCruiseButtonManagement.SendButtonState.increase)

  def test_icbm_dev_tap_increase_sends_once_and_clears_command(self):
    controller = self._build_controller()
    params = Params()
    params.put_bool("SubaruStockAccDevButtonsEnabled", True)
    params.put("SubaruStockAccDevButtonCommand", 1)
    _, _, es_distance_msg = self._build_long_source(counter=16)
    cs = self._build_icbm_cs(True, es_distance_msg=es_distance_msg)
    cc = self._build_long_cc(False)
    cc.enabled = False

    controller.frame = 10
    _, can_sends = controller.update(cc, SimpleNamespace(), cs, 0)

    self.assertTrue(any(msg[0] == 0x221 for msg in can_sends))
    self.assertEqual(int(params.get("SubaruStockAccDevButtonCommand", return_default=True) or 0), 0)

  def test_icbm_dev_hold_decrease_continues_until_released(self):
    controller = self._build_controller()
    params = Params()
    params.put_bool("SubaruStockAccDevButtonsEnabled", True)
    params.put("SubaruStockAccDevButtonCommand", 4)
    _, _, es_distance_msg = self._build_long_source(counter=17)
    cs = self._build_icbm_cs(True, es_distance_msg=es_distance_msg)
    cc = self._build_long_cc(False)

    controller.frame = 10
    _, first_send = controller.update(cc, SimpleNamespace(), cs, 0)
    controller.frame = 15
    _, second_send = controller.update(cc, SimpleNamespace(), cs, 0)
    params.put("SubaruStockAccDevButtonCommand", 0)
    controller.frame = 20
    _, released = controller.update(cc, SimpleNamespace(), cs, 0)

    self.assertTrue(any(msg[0] == 0x221 for msg in first_send))
    self.assertTrue(any(msg[0] == 0x221 for msg in second_send))
    self.assertFalse(any(msg[0] == 0x221 for msg in released))

  def test_icbm_dev_manual_button_event_cancels_hold(self):
    controller = self._build_controller()
    params = Params()
    params.put_bool("SubaruStockAccDevButtonsEnabled", True)
    params.put("SubaruStockAccDevButtonCommand", 3)
    _, _, es_distance_msg = self._build_long_source(counter=18)
    cc = self._build_long_cc(False)

    controller.frame = 10
    _, hold_start = controller.update(cc, SimpleNamespace(), self._build_icbm_cs(True, es_distance_msg=es_distance_msg), 0)
    controller.frame = 15
    _, canceled = controller.update(
      cc,
      SimpleNamespace(),
      self._build_icbm_cs(True, es_distance_msg=es_distance_msg, button_events=[SimpleNamespace(pressed=True)]),
      0,
    )

    self.assertTrue(any(msg[0] == 0x221 for msg in hold_start))
    self.assertFalse(any(msg[0] == 0x221 for msg in canceled))
    self.assertEqual(int(params.get("SubaruStockAccDevButtonCommand", return_default=True) or 0), 0)

  def test_icbm_dev_commands_do_not_send_when_stock_acc_is_not_engaged(self):
    controller = self._build_controller()
    params = Params()
    params.put_bool("SubaruStockAccDevButtonsEnabled", True)
    params.put("SubaruStockAccDevButtonCommand", 2)
    _, _, es_distance_msg = self._build_long_source(counter=19)
    cc = self._build_long_cc(False)

    controller.frame = 10
    _, can_sends = controller.update(cc, SimpleNamespace(), self._build_icbm_cs(False, es_distance_msg=es_distance_msg), 0)

    self.assertFalse(any(msg[0] == 0x221 for msg in can_sends))
    self.assertEqual(int(params.get("SubaruStockAccDevButtonCommand", return_default=True) or 0), 0)


if __name__ == "__main__":
  unittest.main()
