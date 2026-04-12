from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PARAMS_KEYS = REPO_ROOT / "common/params_keys.h"
PARAMS_METADATA = REPO_ROOT / "sunnypilot/sunnylink/params_metadata.json"
PROCESS_CONFIG = REPO_ROOT / "system/manager/process_config.py"
PORTAL_BACKEND = REPO_ROOT / "sunnypilot/portal/backend/bp_portal.py"
PORTAL_PARAMS_MANAGER = REPO_ROOT / "sunnypilot/portal/backend/params/params_manager.py"
PORTAL_CONFIG = REPO_ROOT / "sunnypilot/portal/backend/config.py"
PORTAL_TICI = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/portal.py"
PORTAL_MICI = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/layouts/portal.py"
TICI_SETTINGS = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/settings.py"
MICI_SETTINGS = REPO_ROOT / "selfdrive/ui/sunnypilot/mici/layouts/settings.py"
WEB_SETTINGS = REPO_ROOT / "sunnypilot/portal/web/src/views/SettingsView.tsx"
WEB_VITE = REPO_ROOT / "sunnypilot/portal/web/vite.config.ts"
PYPROJECT = REPO_ROOT / "pyproject.toml"


PORTAL_PARAM_KEYS = [
  "SubiPilotPortalEnabled",
  "SubiPilotPortalPort",
  "SubiPilotPortalCrashCount",
  "SubiPilotPortalLastCrash",
]


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_subipilot_portal_params_registered_and_described():
  params_source = _read(PARAMS_KEYS)
  metadata_source = _read(PARAMS_METADATA)

  assert '{"SubiPilotPortalEnabled", {PERSISTENT | BACKUP, BOOL, "0"}}' in params_source
  assert '{"SubiPilotPortalPort", {PERSISTENT | BACKUP, INT, "8088"}}' in params_source
  assert '{"SubiPilotPortalCrashCount", {PERSISTENT | BACKUP, INT, "0"}}' in params_source
  assert '{"SubiPilotPortalLastCrash", {PERSISTENT | BACKUP, INT, "0"}}' in params_source
  for param in PORTAL_PARAM_KEYS:
    assert f'"{param}"' in metadata_source


def test_subipilot_portal_processes_use_subipilot_gate_only():
  source = _read(PROCESS_CONFIG)

  assert 'PythonProcess("subipilot_portal", "sunnypilot.portal.backend.subipilot_portal", use_subipilot_portal)' in source
  assert 'PythonProcess("subipilot_route_preprocessor", "sunnypilot.portal.backend.subipilot_route_preprocessor", use_subipilot_route_preprocessor)' in source
  assert 'params.get_bool("SubiPilotPortalEnabled")' in source
  assert "EnableWebRoutesServer" not in source
  assert "BPPortalPort" not in source


def test_subipilot_portal_backend_keeps_params_and_settings_fallback_available():
  backend_source = _read(PORTAL_BACKEND)
  params_source = _read(PORTAL_PARAMS_MANAGER)
  config_source = _read(PORTAL_CONFIG)

  assert "sunnypilot.portal.backend" in backend_source
  assert "elif path == '/api/params':" in backend_source
  assert "elif path == '/api/params/set':" in backend_source
  assert "elif path == '/api/manager-logs':" in backend_source
  assert "elif path == '/api/routes':" in backend_source
  assert "Curated SubiPilot web settings panels are not bundled" in backend_source
  assert "fallback': 'parameters'" in backend_source
  assert "EnableWebRoutesServer" not in backend_source
  assert "BPPortalPort" not in backend_source
  assert "/data/subipilot/portal" in config_source
  assert "PARAM_CATEGORIES" in params_source
  assert "repo_root / \"bluepilot\"" not in params_source


def test_subipilot_portal_device_settings_entries_are_present():
  tici_source = _read(TICI_SETTINGS)
  mici_source = _read(MICI_SETTINGS)
  tici_portal_source = _read(PORTAL_TICI)
  mici_portal_source = _read(PORTAL_MICI)

  assert 'from openpilot.selfdrive.ui.sunnypilot.layouts.settings.portal import SubiPilotPortalLayout' in tici_source
  assert 'PanelInfo(tr_noop("SubiPilot Portal"), SubiPilotPortalLayout()' in tici_source
  assert 'from openpilot.selfdrive.ui.sunnypilot.mici.layouts.portal import SubiPilotPortalLayoutMici' in mici_source
  assert 'portal_panel = SubiPilotPortalLayoutMici(back_callback=gui_app.pop_widget)' in mici_source
  assert 'portal_btn = BigButton("subipilot\\nportal"' in mici_source
  assert 'param=PORTAL_ENABLED_PARAM' in tici_portal_source
  assert 'BigParamControl(' in mici_portal_source
  assert 'param=PORTAL_ENABLED_PARAM' in mici_portal_source
  assert "SubiPilot Portal" in tici_portal_source
  assert "portal\\naddress" in mici_portal_source


def test_subipilot_portal_web_branding_and_settings_fallback():
  settings_source = _read(WEB_SETTINGS)
  vite_source = _read(WEB_VITE)
  pyproject_source = _read(PYPROJECT)

  assert "Use Parameters for This Build" in settings_source
  assert "navigate('/parameters')" in settings_source
  assert "Curated SubiPilot web settings panels are not bundled" in settings_source
  assert "name: 'SubiPilot Portal'" in vite_source
  assert "short_name: 'SubiPilot'" in vite_source
  assert '"websockets"' in pyproject_source
