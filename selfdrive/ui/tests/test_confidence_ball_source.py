from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_ONROAD = REPO_ROOT / "selfdrive/ui/onroad/augmented_road_view.py"
MICI_ONROAD = REPO_ROOT / "selfdrive/ui/mici/onroad/augmented_road_view.py"
SHARED_CONFIDENCE_BALL = REPO_ROOT / "selfdrive/ui/sunnypilot/onroad/confidence_ball.py"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_shared_staging_confidence_ball_module_is_software_only():
  source = _read(SHARED_CONFIDENCE_BALL)
  assert "class ConfidenceBallBase" in source
  assert "class ConfidenceBallMiciSP" in source
  assert "class ConfidenceBallTiciSP" in source
  assert "draw_mads_beam" in source
  assert "draw_shader_circle_gradient" not in source


def test_tici_onroad_wires_confidence_ball_toggle_and_left_strip():
  source = _read(TICI_ONROAD)
  assert 'from openpilot.selfdrive.ui.sunnypilot.onroad.confidence_ball import ConfidenceBallTiciSP' in source
  assert '"BPShowConfidenceBall"' in source
  assert "ball_offset = (self._confidence_ball.BALL_WIDTH + BALL_BORDER_MARGIN) if self._show_confidence_ball and self._confidence_ball is not None else 0" in source
  assert "self._confidence_ball.render(ball_rect)" in source
  assert "self._hud_renderer.render(ui_rect)" in source
  assert "self.alert_renderer.render(ui_rect)" in source
  assert "self.driver_state_renderer.render(ui_rect)" in source


def test_mici_onroad_wires_confidence_ball_toggle():
  source = _read(MICI_ONROAD)
  assert 'from openpilot.selfdrive.ui.sunnypilot.onroad.confidence_ball import ConfidenceBallMiciSP' in source
  assert '"BPShowConfidenceBall"' in source
  assert "self._confidence_ball = ConfidenceBallMiciSP() if gui_app.sunnypilot_ui() else None" in source
  assert "if self._show_confidence_ball and self._confidence_ball is not None:" in source
  assert "self._confidence_ball.render(ball_rect)" in source
