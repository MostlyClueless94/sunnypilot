import unittest

from openpilot.common.params import Params
from opendbc.car.subaru.interface import CarInterface
from opendbc.car.subaru.values import CAR, SubaruFlags


class TestSubaruInterface(unittest.TestCase):
  def setUp(self):
    self.params = Params()
    self.params.remove("MCSubaruActuatorDelayTest")

  def tearDown(self):
    self.params.remove("MCSubaruActuatorDelayTest")

  def test_subaru_delay_toggle_off_keeps_angle_delay_default(self):
    CP = CarInterface.get_non_essential_params(CAR.SUBARU_OUTBACK_2023)

    self.assertTrue(bool(CP.flags & SubaruFlags.LKAS_ANGLE))
    self.assertAlmostEqual(CP.steerActuatorDelay, 0.1)

  def test_subaru_delay_toggle_on_lowers_angle_delay(self):
    self.params.put_bool("MCSubaruActuatorDelayTest", True)

    CP = CarInterface.get_non_essential_params(CAR.SUBARU_OUTBACK_2023)

    self.assertTrue(bool(CP.flags & SubaruFlags.LKAS_ANGLE))
    self.assertAlmostEqual(CP.steerActuatorDelay, 0.08)

  def test_subaru_delay_toggle_does_not_change_torque_subaru(self):
    self.params.put_bool("MCSubaruActuatorDelayTest", True)

    CP = CarInterface.get_non_essential_params(CAR.SUBARU_FORESTER)

    self.assertFalse(bool(CP.flags & SubaruFlags.LKAS_ANGLE))
    self.assertNotAlmostEqual(CP.steerActuatorDelay, 0.08)


if __name__ == "__main__":
  unittest.main()
