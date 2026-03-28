import unittest
from types import SimpleNamespace

from opendbc.car import structs
from opendbc.car.subaru import subarucan
from opendbc.car.subaru.carcontroller import CarController
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

  def _build_controller(self):
    CP = CarInterface.get_non_essential_params(CAR.SUBARU_OUTBACK_2023)
    CP_SP = CarInterface.get_non_essential_params_sp(CP, CAR.SUBARU_OUTBACK_2023)
    return CarController({}, CP, CP_SP)

  @staticmethod
  def _build_parser(messages=None):
    return SimpleNamespace(vl=messages or {})

  @staticmethod
  def _build_carstate_stub(flags=0):
    return SimpleNamespace(CP=SimpleNamespace(flags=flags))

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


if __name__ == "__main__":
  unittest.main()
