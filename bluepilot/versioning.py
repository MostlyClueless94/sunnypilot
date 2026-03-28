from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SUBIPILOT_VERSION_FILE = _REPO_ROOT / "SUBIPILOT_VERSION"


def read_subipilot_version() -> str:
  try:
    return _SUBIPILOT_VERSION_FILE.read_text().strip()
  except Exception:
    return ""


def format_subipilot_version(include_v: bool = True) -> str:
  version = read_subipilot_version()
  if not version:
    return "SubiPilot"
  return f"SubiPilot v{version}" if include_v else f"SubiPilot {version}"
