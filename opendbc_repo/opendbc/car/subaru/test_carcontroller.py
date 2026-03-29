import unittest
from types import SimpleNamespace

from openpilot.common.params import Params
from opendbc.car import structs
from opendbc.car.subaru import subarucan
from opendbc.car.subaru.carcontroller import CarController, LONG_MESSAGE_STALE_MAX_FRAMES
from opendbc.car.subaru.carstate import CarState
from opendbc.car.subaru.interface import CarInterface
from opendbc.car.subaru.values import CAR, SubaruFlags


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
    expected = subarucan.create_steering_control_angle(expected_controller.packer, cs.out.steeringAngleDeg, False)

    self.assertEqual(msg, expected)
    self.assertAlmostEqual(controller.apply_angle_last, cs.out.steeringAngleDeg)

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


if __name__ == "__main__":
  unittest.main()
