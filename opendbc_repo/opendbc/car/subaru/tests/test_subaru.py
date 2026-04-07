from pathlib import Path

from opendbc.car.subaru.fingerprints import FW_VERSIONS


REPO_ROOT = Path(__file__).resolve().parents[5]
FINGERPRINTS = REPO_ROOT / "opendbc_repo/opendbc/car/subaru/fingerprints.py"


class TestSubaruFingerprint:
  def test_fw_version_format(self):
    for platform, fws_per_ecu in FW_VERSIONS.items():
      for (ecu, _, _), fws in fws_per_ecu.items():
        fw_size = len(fws[0])
        for fw in fws:
          assert len(fw) == fw_size, f"{platform} {ecu}: {len(fw)} {fw_size}"

  def test_outback_2024_fingerprint_bytes_present(self):
    source = FINGERPRINTS.read_text(encoding="utf-8")
    assert "CAR.SUBARU_OUTBACK_2023" in source
    assert "b'\\xa1 $\\x17\\x00'" in source
    assert "b'\\x1a!\\x08\\x00C\\x0e!\\x08\\x018'" in source
    assert "b'\\xfb,\\xa2q\\x07'" in source
    assert "b'\\xa9\\x17w!r'" in source
