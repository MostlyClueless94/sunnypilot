from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
UI_STATE_SP = REPO_ROOT / "selfdrive/ui/sunnypilot/ui_state.py"


def test_ui_status_treats_longitudinal_override_with_lateral_control_as_lat_only():
  source = UI_STATE_SP.read_text(encoding="utf-8")
  assert "override_longitudinal = any(e.overrideLongitudinal for e in onroad_evt)" in source
  assert "override_lateral = any(e.overrideLateral for e in onroad_evt)" in source
  assert "if override_lateral:" in source
  assert 'return "override"' in source
  assert 'return "lat_only" if mads.enabled else "override"' in source
