from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_RENDERER = REPO_ROOT / "selfdrive/ui/onroad/model_renderer.py"
MICI_RENDERER = REPO_ROOT / "selfdrive/ui/mici/onroad/model_renderer.py"
MC_CUSTOM = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/mc_custom.py"
UI_STATE = REPO_ROOT / "selfdrive/ui/sunnypilot/ui_state.py"
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"
STATSD = REPO_ROOT / "sunnypilot/sunnylink/statsd.py"
SUNNYLINKD = REPO_ROOT / "sunnypilot/sunnylink/athena/sunnylinkd.py"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_ui_state_reads_only_active_dynamic_path_toggle():
  source = _read(UI_STATE)
  assert 'self.dynamic_path_color = self.params.get_bool("DynamicPathColor")' in source
  assert 'self.dynamic_path_color_palette = self._get_int_param("DynamicPathColorPalette")' not in source


def test_ui_state_drops_legacy_dynamic_path_status_helper():
  source = _read(UI_STATE)
  assert "def get_dynamic_path_status(" not in source


def test_base_renderers_reference_single_palette_dynamic_helpers():
  for renderer_path in (TICI_RENDERER, MICI_RENDERER):
    source = _read(renderer_path)
    assert "get_dynamic_path_colors" in source
    assert "get_dynamic_edge_color" in source
    assert "ui_state.get_dynamic_path_status(" not in source
    assert "dynamic_colors = get_dynamic_path_colors(ui_state.status)" in source
    assert "self._active_path_edge_color = get_dynamic_edge_color(ui_state.status)" in source
    assert "dynamic_path_color_palette" not in source


def test_renderers_draw_path_edges_without_palette_gate():
  for renderer_path in (TICI_RENDERER, MICI_RENDERER):
    source = _read(renderer_path)
    assert "self._draw_path_edges()" in source
  mici_source = _read(MICI_RENDERER)
  assert "if ui_state.dynamic_path_color:\n      self._draw_path_edges()" not in mici_source


def test_mc_custom_contains_only_active_pathing_controls():
  source = _read(MC_CUSTOM)
  assert 'param="DynamicPathColor"' in source
  assert 'param="CustomModelPathColor"' in source
  assert 'param="DynamicPathColorPalette"' not in source
  assert "Dynamic Path Color Palette" not in source


def test_legacy_palette_param_is_kept_out_of_runtime_metadata_and_stats():
  params_source = _read(PARAMS_KEYS)
  metadata_source = _read(PARAMS_METADATA)
  statsd_source = _read(STATSD)
  sunnylinkd_source = _read(SUNNYLINKD)

  assert 'DynamicPathColorPalette' in params_source
  assert "Legacy compatibility key" in params_source
  assert '"DynamicPathColorPalette"' not in metadata_source
  assert "'DynamicPathColorPalette'" not in statsd_source
  assert '"DynamicPathColorPalette"' in sunnylinkd_source
