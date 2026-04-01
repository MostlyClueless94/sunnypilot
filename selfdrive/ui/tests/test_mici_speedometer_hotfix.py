from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MICI_HUD = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/onroad/hud_renderer.py"
MICI_SPEED = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/onroad/speed_renderer.py"
FORK_CHANGELOG = REPO_ROOT / "FORK_CHANGELOG.md"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_mici_hud_uses_dedicated_speed_renderer():
  source = _read(MICI_HUD)
  assert "from openpilot.selfdrive.ui.sunnypilot.mici.onroad.speed_renderer import SpeedRenderer" in source
  assert "self.speed_renderer = SpeedRenderer()" in source
  assert "self.speed_renderer.update()" in source
  assert "self.speed_renderer.render(rect)" in source
  assert "FONT_SIZES.current_speed" not in source
  assert "FONT_SIZES.speed_unit" not in source


def test_mici_speed_renderer_uses_smaller_mici_layout_and_existing_features():
  source = _read(MICI_SPEED)
  assert "CURRENT_SPEED_FONT_SIZE = 112" in source
  assert "SPEED_UNIT_FONT_SIZE = 36" in source
  assert "CURRENT_SPEED_CENTER_Y = 92" in source
  assert "SPEED_UNIT_CENTER_Y = 146" in source
  assert "ui_state.true_v_ego_ui" in source
  assert "ui_state.hide_v_ego_ui" in source
  assert "\"ShowBrakeStatus\"" in source


def test_fork_changelog_top_block_mentions_c4_speedometer_hotfix():
  top_block = _read(FORK_CHANGELOG).split("\n\n", 1)[0]
  assert "# SubiPilot 1.0 Hotfix" in top_block
  assert "subi-1.0" in top_block
  assert "subi-staging" in top_block
  assert "C4/MICI speedometer hotfix" in top_block
  assert "comma 4" in top_block
  assert "C3X/TICI" in top_block
  assert "True speed" in top_block
  assert "brake-red speed" in top_block
  assert "Hide Speed" in top_block
