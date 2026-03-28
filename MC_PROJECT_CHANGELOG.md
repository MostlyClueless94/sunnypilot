# MC Project Changelog

This file tracks the project-specific history for the dual-vehicle BluePilot fork.
It is intentionally separate from the upstream-style [CHANGELOG.md](/C:/Users/damen/OneDrive/Desktop/BluePilot/bluepilot-v1/CHANGELOG.md).

When we make meaningful project changes, add a new dated entry near the top with:
- what changed
- why it changed
- exact branch/install implications
- validation performed
- open follow-ups or blockers

## Current Topology

- Working repo: `MostlyClueless94/bluepilot`
- Install mirror repo: `install-mc/openpilot`
- Active development branch: `mc-dev`
- Stock comma installer target: `installer.comma.ai/install-mc/mc-dev`
- Base: `BluePilotDev/bluepilot@bp-6.0`
- Subaru donor scope: minimum bring-up for 2023-25 Outback angle-LKAS support

## 2026-03-27

### Pending local hotfix: path color startup crash recovery

What changed:
- Hardened `pyray`-based UI type annotations with `from __future__ import annotations` in the affected modules:
  - `selfdrive/ui/sunnypilot/onroad/path_colors.py`
  - `selfdrive/ui/onroad/model_renderer.py`
  - `selfdrive/ui/mici/onroad/model_renderer.py`
  - `selfdrive/ui/onroad/cameraview.py`
  - `selfdrive/ui/mici/onroad/cameraview.py`

Root cause:
- The restored path color selector introduced `rl.Color | None` and `Gradient | None` annotations.
- On device, `pyray` exposes `rl.Color` as a callable object rather than a runtime type.
- Python tried to evaluate `function | NoneType` during import, which crashed `manager` before the UI fully booted.

Why:
- This is a boot-critical hotfix for the currently active install branch.
- The intent is to preserve the path color selector and only stop runtime annotation evaluation.

Validation on host:
- Passed `py -3.12 -m compileall` on all five touched UI files.
- Passed a stubbed direct-import check for:
  - `path_colors.py`
  - both `model_renderer.py` modules
  - both `cameraview.py` modules
- The stubbed import harness was used because this Windows host does not have the full device/runtime environment.

Branch / push priority:
- First push target: `install-mc/openpilot:mc-dev`
- Second push target: `MostlyClueless94/bluepilot:mc-dev` after GitHub auth is corrected on this machine

Recovery status:
- Before this hotfix, `installer.comma.ai/install-mc/mc-dev` was expected to boot into the manager traceback shown in the field photo.
- After this hotfix lands on the install mirror, the build should at least clear this specific import-time crash and reach normal UI startup.

### `2dec547d2` `ui: restore preset path color selector`

What changed:
- Restored the SubiPilot preset-only path color selector in BluePilot.
- Added `CustomModelPathColor` back to runtime params as an integer enum with default `0`.
- Replaced the stale BluePilot string-style param metadata with the integer enum version.
- Added the selector to both settings surfaces:
  - TICI `Visuals`
  - MICI `BluePilot`
- Added a shared preset helper at `selfdrive/ui/sunnypilot/onroad/path_colors.py`.
- Ported preset coloring into both onroad renderers without bringing back dynamic path color.
- Added defensive parsing in the shared TICI/MICI multi-select widgets so old string-valued params do not crash the selector.
- Added a small helper test file for the preset color definitions.

Why:
- The custom preset path color selector from SubiPilot was missing from this BluePilot build.
- The goal was to bring back only the preset selector, not the broader dynamic path color feature.
- The port was kept narrow so stock BluePilot visuals remain unchanged when the selector stays on `Stock`.

Behavioral intent:
- Experimental path coloring keeps priority and stays unchanged.
- If `CustomModelPathColor != 0`, the selected preset colors the path, lane lines, and road edges.
- If `CustomModelPathColor == 0`, BluePilot keeps current stock or Rainbow behavior.
- When a preset is active, it overrides `RainbowMode`.
- MICI-specific torque-orange lane cue remains intact.

Validation on this Windows host:
- `py -3.12 -m compileall ...` passed for all edited Python files.
- Direct JSON/helper assertions passed for:
  - `bluepilot/params/params.json`
  - `sunnypilot/sunnylink/params_metadata.json`
  - `selfdrive/ui/sunnypilot/onroad/path_colors.py`
- Full `pytest` coverage for `sunnypilot/sunnylink/tests/test_params_sync.py` and `test_params_metadata.py` was blocked because this checkout is missing the built `common.params_pyx` extension.
- Direct import-based execution of the helper test was also blocked until a temporary `pyray` stub was used, because `pyray` is not installed on this Windows host.

Branch / push status:
- Commit exists locally in `bluepilot-v1` on `mc-dev`.
- Push to `MostlyClueless94/bluepilot` failed with `403` because GitHub auth on this machine is currently cached as `install-mc`.
- This means the development source-of-truth remote is currently behind this local commit until auth is corrected.

Open follow-ups:
- Push this commit to `install-mc/openpilot` so the install branch can pick it up if desired.
- Re-auth the `mc` remote before pushing back to `MostlyClueless94/bluepilot`.
- Bench-verify that both settings pages show `Custom Model Path Color`.
- Device-verify that `Stock` matches current visuals and that presets recolor path, lane lines, and road edges as intended.

### `af21c1fda` `subaru: expose outback 2023 in manual selector`

What changed:
- Exposed `SUBARU_OUTBACK_2023` in the manual vehicle selector.
- Kept other angle-LKAS Subaru entries hidden.
- Regenerated the manual selector list and added selector-focused coverage.

Why:
- The 2023-25 Outback platform was already present in the Subaru bring-up work, but it was not visible in the manual selector.

Validation:
- Subaru bring-up tests passed on host.
- Full selector UI verification still requires device/bench confirmation.

### `d2c39dd76` `tools: add bluepilot installer worker`

What changed:
- Added a custom installer-worker toolchain under `tools/bluepilot-installer`.

Why:
- This was the first attempt to solve the installer mismatch before moving to the `install-mc/openpilot` mirror approach.

Current status:
- Kept in the repo as fallback tooling.
- Not required for the current stock installer path via `install-mc/openpilot`.

### `07d7ba756` `subaru: add minimal outback angle-lkas bring-up`

What changed:
- Ported the minimum Subaru changes needed for 2023-25 Outback angle-LKAS support.
- Updated Subaru values, interface, carstate, controller, fingerprints, and safety mode wiring.

Why:
- Preserve BluePilot 6.0 Ford behavior while enabling Subaru Outback bring-up with the smallest practical port.

Validation:
- Subaru-targeted automated checks available on host passed where environment allowed.
- Full in-car validation is still pending.

## Outstanding Project Risks

- Ford regression still needs real in-car validation after the Subaru and UI work.
- Subaru fingerprinting, calibration, engage behavior, and angle steering still need full in-car validation.
- The `mc` remote currently cannot be updated from this machine until GitHub auth is switched away from `install-mc`.
- This Windows host is not a complete verification environment for the repo because it is missing:
  - built `common.params_pyx`
  - `pyray`
  - a working openpilot symlink-style Python package layout

## Next Recommended Maintenance Rule

For each future wave, add a new top entry with:
- date
- commit hash
- scope
- files/subsystems touched
- validation run
- install impact
- unresolved risks
