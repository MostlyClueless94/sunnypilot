from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LIST_VIEW = REPO_ROOT / "system/ui/sunnypilot/widgets/list_view.py"
DEVELOPER = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/developer.py"
SOFTWARE = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/software.py"
CRUISE = REPO_ROOT / "selfdrive/ui/sunnypilot/layouts/settings/cruise.py"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def test_toggle_item_sp_keeps_callback_on_toggle_action_only():
  source = _read(LIST_VIEW)
  assert "action = ToggleActionSP(initial_state=initial_state, enabled=enabled, callback=callback, param=param)" in source
  assert "return ListItemSP(title=title, description=description, action_item=action, icon=icon)" in source
  assert "return ListItemSP(title=title, description=description, action_item=action, icon=icon, callback=callback)" not in source


def test_other_helpers_keep_their_existing_callback_paths():
  source = _read(LIST_VIEW)
  assert 'return ListItemSP(title="", callback=callback, description="", action_item=action)' in source
  assert "action = MultipleButtonActionSP(buttons, button_width, selected_index, callback=callback, param=param)" in source
  assert "return ListItemSP(title=title, description=description, icon=icon, action_item=action, inline=inline)" in source
  assert "return ListItemSP(title=title, description=description, action_item=action, callback=callback)" in source


def test_state_accepting_toggle_callbacks_remain_in_existing_settings_layouts():
  developer_source = _read(DEVELOPER)
  software_source = _read(SOFTWARE)
  cruise_source = _read(CRUISE)

  assert 'callback=self._on_prebuilt_toggled' in developer_source
  assert "def _on_prebuilt_toggled(state):" in developer_source

  assert 'callback=self._on_disable_updates_toggled' in software_source
  assert "def _on_disable_updates_toggled(self, enabled):" in software_source

  assert 'callback=self._on_custom_acc_toggle' in cruise_source
  assert "def _on_custom_acc_toggle(self, state):" in cruise_source
