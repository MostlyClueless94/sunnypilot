from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
CARSTATE = REPO_ROOT / "opendbc_repo/opendbc/car/subaru/carstate.py"
CARCONTROLLER = REPO_ROOT / "opendbc_repo/opendbc/car/subaru/carcontroller.py"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_carstate_fault_logs_include_steering_and_cruise_context():
  source = _read(CARSTATE)
  assert 'steerFaultTemporary={ret.steerFaultTemporary} angle={ret.steeringAngleDeg:.2f}' in source
  assert 'steerFaultPermanent={ret.steerFaultPermanent} angle={ret.steeringAngleDeg:.2f}' in source
  assert 'rate={ret.steeringRateDeg:.2f}' in source
  assert 'torque={ret.steeringTorque:.2f}' in source
  assert 'torqueEps={ret.steeringTorqueEps:.2f}' in source
  assert 'cruiseEnabled={ret.cruiseState.enabled}' in source
  assert 'cruiseAvailable={ret.cruiseState.available}' in source


def test_carcontroller_request_logs_include_target_and_basic_state_context():
  source = _read(CARCONTROLLER)
  assert 'angle LKAS request={lkas_request} inhibit={inhibit_reason} target={steer_target:.2f}' in source
  assert 'lastApplied={self.apply_angle_last:.2f}' in source
  assert 'measuredAngle={CS.out.steeringAngleDeg:.2f}' in source
  assert 'measuredRate={CS.out.steeringRateDeg:.2f}' in source
  assert 'latActive={CC.latActive} enabled={CC.enabled}' in source


def test_carcontroller_logs_center_damping_state_but_no_manual_override_reclaim_state():
  source = _read(CARCONTROLLER)
  assert 'angle LKAS low-speed center damping active={center_damping_active}' in source
  assert 'angle LKAS center sign-flip clamp active={sign_flip_clamped}' in source
  assert 'angle driver override hold active=' not in source
  assert 'angle driver override ramp active=' not in source
  assert 'MCSubaruManualYieldResumeSpeed' not in source
  assert 'MCSubaruManualYieldResumeSoftness' not in source
  assert 'handoffActive={handoff_active}' not in source
  assert 'rampActive={manual_override_ramp_active}' not in source


def test_carcontroller_no_longer_reads_chatter_toggle_param():
  source = _read(CARCONTROLLER)
  assert "MCSubaruChatterFix" not in source
  assert "mc_subaru_chatter_fix" not in source
