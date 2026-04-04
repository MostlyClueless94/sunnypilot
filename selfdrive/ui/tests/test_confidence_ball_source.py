from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_ONROAD = REPO_ROOT / "selfdrive/ui/onroad/augmented_road_view.py"
MICI_ONROAD = REPO_ROOT / "selfdrive/ui/mici/onroad/augmented_road_view.py"
SHARED_CONFIDENCE_BALL = REPO_ROOT / "selfdrive/ui/sunnypilot/onroad/confidence_ball.py"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_shared_staging_confidence_ball_module_is_removed():
  assert not SHARED_CONFIDENCE_BALL.exists()


def test_tici_onroad_no_longer_imports_staging_confidence_ball():
  source = _read(TICI_ONROAD)
  assert "openpilot.selfdrive.ui.sunnypilot.onroad.confidence_ball" not in source
  assert '"BPShowConfidenceBall"' not in source
  assert "self._hud_renderer.render(self._content_rect)" in source
  assert "self.alert_renderer.render(self._content_rect)" in source
  assert "self.driver_state_renderer.render(self._content_rect)" in source


def test_mici_onroad_uses_stock_confidence_ball_without_toggle():
  source = _read(MICI_ONROAD)
  assert 'from openpilot.selfdrive.ui.mici.onroad.confidence_ball import ConfidenceBall' in source
  assert "openpilot.selfdrive.ui.sunnypilot.onroad.confidence_ball" not in source
  assert '"BPShowConfidenceBall"' not in source
  assert "self._confidence_ball = ConfidenceBall()" in source
  assert "self._confidence_ball.render(self.rect)" in source
