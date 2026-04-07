from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
UI_STATE = REPO_ROOT / "selfdrive/ui/sunnypilot/ui_state.py"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_override_longitudinal_with_mads_enabled_maps_to_lat_only():
  source = _read(UI_STATE)
  assert "override_longitudinal = any(e.overrideLongitudinal for e in onroad_evt)" in source
  assert 'return "lat_only" if mads.enabled else "override"' in source


def test_override_lateral_stays_override():
  source = _read(UI_STATE)
  assert "override_lateral = any(e.overrideLateral for e in onroad_evt)" in source
  assert "if override_lateral:" in source
  assert 'return "override"' in source


def test_mads_unavailable_override_stays_override():
  source = _read(UI_STATE)
  assert "if state == OpenpilotState.overriding:" in source
  assert "if not mads.available:" in source
  assert 'return "override"' in source
