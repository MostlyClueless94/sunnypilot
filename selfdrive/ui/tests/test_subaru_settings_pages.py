from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_SETTINGS = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/settings.py"
TICI_SUBARU = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/subaru.py"
TICI_VISUALS = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/visuals.py"
MICI_SETTINGS = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/layouts/settings.py"
MICI_SUBARU = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/layouts/subaru.py"
MICI_TOGGLES = REPO_ROOT / "selfdrive/ui/mici/layouts/settings/toggles.py"
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_tici_settings_root_exposes_dedicated_subaru_panel():
  source = _read(TICI_SETTINGS)
  assert 'from openpilot.selfdrive.ui.sunnypilot.layouts.settings.subaru import SubaruLayout' in source
  assert '"SUBARU"' in source
  assert 'PanelInfo(tr_noop("Subaru"), SubaruLayout()' in source


def test_tici_subaru_page_contains_lateral_tuning_and_visuals_controls():
  source = _read(TICI_SUBARU)
  assert 'tr("Lateral Tuning")' in source
  assert 'tr("Visuals")' in source
  assert 'param="MCSubaruSmoothingTune"' in source
  assert 'param="MCSubaruSmoothingStrength"' in source
  assert 'param="MCSubaruCenterDampingStrength"' in source
  assert 'min_value=-3' in source
  assert 'max_value=4' in source
  assert 'param="ShowBrakeStatus"' in source
  assert 'param="BPShowConfidenceBall"' in source
  assert 'param="DynamicPathColor"' in source
  assert 'param="DynamicPathColorPalette"' in source
  assert 'param="CustomModelPathColor"' in source
  assert 'param="TrueVEgoUI"' in source
  assert 'param="HideVEgoUI"' in source
  assert 'Display current speed in red when brake lights are on.' in source
  assert 'Display the confidence ball on the driving view.' in source
  assert 'When off, comma uses dash or cluster speed when supported. Enable to force true wheel-speed-based speed.' in source
  assert source.index('param="ShowBrakeStatus"') < source.index('param="BPShowConfidenceBall"') < source.index('param="DynamicPathColor"')


def test_tici_visuals_page_no_longer_duplicates_subaru_visual_controls():
  source = _read(TICI_VISUALS)
  assert '"DynamicPathColor"' not in source
  assert '"ShowBrakeStatus"' not in source
  assert '"TrueVEgoUI"' not in source
  assert '"HideVEgoUI"' not in source
  assert '"CustomModelPathColor"' not in source
  assert '"DynamicPathColorPalette"' not in source


def test_mici_settings_root_exposes_subaru_entry():
  source = _read(MICI_SETTINGS)
  assert 'from openpilot.selfdrive.ui.sunnypilot.mici.layouts.subaru import SubaruLayoutMici' in source
  assert 'subaru_panel = SubaruLayoutMici(back_callback=gui_app.pop_widget)' in source
  assert 'subaru_btn = BigButton("subaru"' in source
  assert 'items.insert(3, subaru_btn)' in source


def test_mici_subaru_page_uses_device_native_controls():
  source = _read(MICI_SUBARU)
  assert 'GreyBigButton("lateral\\ntuning")' in source
  assert 'GreyBigButton("visuals")' in source
  assert 'BigParamControl("subaru steering\\nsmoothing", "MCSubaruSmoothingTune")' in source
  assert 'BigButton("smoothing\\nstrength")' in source
  assert 'BigButton("center\\ndamping")' in source
  assert 'list(range(-3, 5))' in source
  assert 'BigParamControl("show brake\\nstatus", "ShowBrakeStatus", desc="red when brake lights are on")' in source
  assert 'BigParamControl("show confidence\\nball", "BPShowConfidenceBall", desc="display onroad confidence ball")' in source
  assert 'BigParamControl("dynamic path\\ncolor", "DynamicPathColor")' in source
  assert 'BigButton("dynamic path\\npalette")' in source
  assert 'BigButton("custom model\\npath color")' in source
  assert 'BigParamControl("always use\\ntrue speed", "TrueVEgoUI", desc="off: dash speed, on: true speed")' in source
  assert 'BigParamControl("hide\\nspeedometer", "HideVEgoUI")' in source
  assert source.index('"ShowBrakeStatus"') < source.index('"BPShowConfidenceBall"') < source.index('"DynamicPathColor"')


def test_mici_general_toggles_no_longer_duplicate_brake_status():
  source = _read(MICI_TOGGLES)
  assert "ShowBrakeStatus" not in source


def test_subaru_smoothing_params_are_declared_for_staging():
  params_source = _read(PARAMS_KEYS)
  metadata_source = _read(PARAMS_METADATA)
  for key in ("MCSubaruSmoothingTune", "MCSubaruSmoothingStrength", "MCSubaruCenterDampingStrength"):
    assert key in params_source
    assert f'"{key}"' in metadata_source
  assert '{ "value": -3, "label": "-3" }' in metadata_source
  assert '{ "value": 4, "label": "+4" }' in metadata_source
  assert '{ "value": 5, "label": "+5" }' not in metadata_source
  assert '{ "value": -4, "label": "-4" }' not in metadata_source
  assert '"BPShowConfidenceBall"' in params_source
  assert '"BPShowConfidenceBall"' in metadata_source
  assert 'Show Confidence Ball' in metadata_source
  assert 'Display the confidence ball on the driving view.' in metadata_source
  assert '"ShowBrakeStatus"' in metadata_source
  assert 'Display current speed in red when brake lights are on.' in metadata_source
  assert '"TrueVEgoUI"' in metadata_source
  assert 'When off, comma uses dash or cluster speed when supported. Enable to force true wheel-speed-based speed.' in metadata_source
