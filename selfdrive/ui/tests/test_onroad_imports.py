import importlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SP_MODEL_RENDERER = REPO_ROOT / "selfdrive/ui/sunnypilot/onroad/model_renderer.py"


@pytest.mark.parametrize("module_name", (
  "openpilot.selfdrive.ui.onroad.augmented_road_view",
  "openpilot.selfdrive.ui.mici.onroad.augmented_road_view",
))
def test_onroad_entrypoint_imports(module_name):
  importlib.import_module(module_name)


def test_sunnypilot_model_renderer_exports_chevron_metrics():
  source = SP_MODEL_RENDERER.read_text(encoding="utf-8")
  assert "from openpilot.selfdrive.ui.sunnypilot.onroad.chevron_metrics import ChevronMetrics" in source
