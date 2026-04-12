from openpilot.system.version import (
  build_metadata_from_dict,
  get_release_notes,
  migrate_branch,
  order_branches_for_ui,
)
from openpilot.system.updated.updated import parse_release_notes


def make_build_metadata(channel: str):
  return build_metadata_from_dict({
    "channel": channel,
    "openpilot": {
      "version": "1.0.0",
      "release_notes": "notes",
      "git_commit": "abc123",
      "git_origin": "https://github.com/MostlyClueless94/openpilot.git",
      "git_commit_date": "now",
      "build_style": "test",
    },
  })


def test_subipilot_channel_classification():
  release = make_build_metadata("subi-1.0")
  assert release.release_channel
  assert release.channel_type == "release"

  staging = make_build_metadata("subi-staging")
  assert staging.tested_channel
  assert not staging.release_channel
  assert staging.channel_type == "staging"

  personal = make_build_metadata("MostlyClueless")
  assert not personal.tested_channel
  assert not personal.release_channel
  assert personal.channel_type == "feature"


def test_migrate_branch_maps_legacy_stable_names():
  for device_type in ("tici", "tizi", "mici"):
    assert migrate_branch(device_type, "master") == "subi-0.9"
    assert migrate_branch(device_type, "mc-0.9") == "subi-0.9"

  assert migrate_branch("mici", "MostlyClueless") == "MostlyClueless"


def test_order_branches_for_ui_prioritizes_subipilot_lanes():
  ordered = order_branches_for_ui(
    ["feature-x", "subi-0.9", "MostlyClueless", "subi-staging", "other"],
    "feature-x",
  )
  assert ordered[:5] == ["feature-x", "subi-staging", "subi-0.9", "MostlyClueless", "other"]


def test_get_release_notes_prefers_fork_changelog(tmp_path, monkeypatch):
  (tmp_path / "FORK_CHANGELOG.md").write_text("# Fork Notes\n- personal branch summary\n\n## Older\n- details\n")
  (tmp_path / "CHANGELOG.md").write_text("# Upstream Notes\n\nOther\n")

  monkeypatch.setattr("openpilot.system.version.get_origin", lambda cwd=None: "https://github.com/MostlyClueless94/openpilot.git")

  assert get_release_notes(str(tmp_path)) == "# Fork Notes\n- personal branch summary"
  assert parse_release_notes(str(tmp_path)) == b"<h1>Fork Notes</h1>\n<p>- personal branch summary</p>"


def test_get_release_notes_falls_back_to_changelog(tmp_path, monkeypatch):
  (tmp_path / "CHANGELOG.md").write_text("# Upstream Notes\n- stable summary\n\nOlder\n")

  monkeypatch.setattr("openpilot.system.version.get_origin", lambda cwd=None: "https://github.com/MostlyClueless94/openpilot.git")

  assert get_release_notes(str(tmp_path)) == "# Upstream Notes\n- stable summary"
