import importlib

import pytest


@pytest.mark.parametrize("module_name", (
  "openpilot.selfdrive.ui.onroad.augmented_road_view",
  "openpilot.selfdrive.ui.mici.onroad.augmented_road_view",
))
def test_onroad_entrypoint_imports(module_name):
  importlib.import_module(module_name)
