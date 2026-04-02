import unittest

try:
  from openpilot.tools.lib.subaru_fault_diagnose import (
    format_subaru_fault_summary,
    is_relevant_subaru_log,
    summarize_first_subaru_lkas_fault,
  )
except ModuleNotFoundError:
  from tools.lib.subaru_fault_diagnose import (
    format_subaru_fault_summary,
    is_relevant_subaru_log,
    summarize_first_subaru_lkas_fault,
  )


class TestSubaruFaultDiagnose(unittest.TestCase):
  def test_is_relevant_subaru_log_matches_expected_tokens(self):
    self.assertTrue(is_relevant_subaru_log("angle LKAS request=True inhibit=none"))
    self.assertTrue(is_relevant_subaru_log("steerFaultPermanent=True angle=12.0"))
    self.assertFalse(is_relevant_subaru_log("unrelated manager status"))

  def test_summarize_first_subaru_lkas_fault_collects_state_and_transitions(self):
    events = [
      {"kind": "carState", "time_ns": 1_000_000_000, "steer_fault_temporary": False, "steer_fault_permanent": False,
       "steering_angle_deg": 1.0, "steering_rate_deg": 0.1, "steering_torque": 0.2, "steering_torque_eps": 0.3,
       "cruise_enabled": True, "cruise_available": True},
      {"kind": "logMessage", "time_ns": 1_100_000_000, "channel": "logMessage",
       "message": "angle LKAS request=True inhibit=none target=4.00 lastApplied=3.50 measuredAngle=1.00 measuredRate=0.10 handoffActive=False rampActive=False"},
      {"kind": "logMessage", "time_ns": 1_200_000_000, "channel": "logMessage",
       "message": "ES_Status Cruise_Activated=1"},
      {"kind": "carState", "time_ns": 1_300_000_000, "steer_fault_temporary": True, "steer_fault_permanent": False,
       "steering_angle_deg": 5.0, "steering_rate_deg": 2.0, "steering_torque": 1.2, "steering_torque_eps": 2.3,
       "cruise_enabled": False, "cruise_available": True},
      {"kind": "logMessage", "time_ns": 1_350_000_000, "channel": "errorLogMessage",
       "message": "Eyesight cruise fault=True"},
      {"kind": "carState", "time_ns": 1_400_000_000, "steer_fault_temporary": True, "steer_fault_permanent": False,
       "steering_angle_deg": 5.5, "steering_rate_deg": 1.7, "steering_torque": 1.0, "steering_torque_eps": 2.0,
       "cruise_enabled": False, "cruise_available": False},
    ]

    summary = summarize_first_subaru_lkas_fault(events)

    self.assertIsNotNone(summary)
    self.assertEqual(summary.fault_kind, "temporary")
    self.assertEqual(summary.fault_state.time_ns, 1_300_000_000)
    self.assertEqual(len(summary.preceding_states), 1)
    self.assertEqual(len(summary.following_states), 1)
    self.assertEqual(len(summary.nearby_transitions), 3)

    formatted = format_subaru_fault_summary(summary)
    self.assertIn("First Subaru LKAS temporary fault", formatted)
    self.assertIn("Nearby Subaru transitions:", formatted)
    self.assertIn("Eyesight cruise fault=True", formatted)

  def test_summarize_first_subaru_lkas_fault_returns_none_when_no_fault_exists(self):
    events = [
      {"kind": "carState", "time_ns": 1, "steer_fault_temporary": False, "steer_fault_permanent": False,
       "steering_angle_deg": 0.0, "steering_rate_deg": 0.0, "steering_torque": 0.0, "steering_torque_eps": 0.0,
       "cruise_enabled": False, "cruise_available": False},
      {"kind": "logMessage", "time_ns": 2, "channel": "logMessage", "message": "angle LKAS request=False inhibit=lat_inactive"},
    ]

    summary = summarize_first_subaru_lkas_fault(events)

    self.assertIsNone(summary)
    self.assertEqual(format_subaru_fault_summary(summary), "No Subaru LKAS steer fault found.")


if __name__ == "__main__":
  unittest.main()
