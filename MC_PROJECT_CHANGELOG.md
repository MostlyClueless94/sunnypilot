# MC Project Changelog

This file tracks the project-specific history for the dual-vehicle BluePilot fork.
It is intentionally separate from the upstream-style [CHANGELOG.md](/C:/Users/damen/OneDrive/Desktop/BluePilot/bluepilot-v1/CHANGELOG.md).

When we make meaningful project changes, add a new dated entry near the top with:
- what changed
- why it changed
- exact branch/install implications
- validation performed
- open follow-ups or blockers

## 2026-04-08

### `subaru/soft-capture engage blend` add a MostlyClueless-only steering handoff experiment

What changed:
- Added a Subaru angle-LKAS soft-capture experiment on `MostlyClueless` only.
- When enabled, fresh lateral engage blends from the current wheel angle toward the model target over a short ramp window instead of snapping immediately.
- Added `Soft-Capture Engage Blend` and `Soft-Capture Strength` to the TICI `MC Custom` Subaru section under `Advanced Tuning`.
- Added focused Subaru controller tests for engage-edge ramp start, disabled no-op behavior, strength scaling, ramp completion, and non-stacking behavior with the existing manual-yield reclaim ramp.

Why:
- The branch already has low-speed smoothing and manual-yield reclaim shaping, but fresh lateral engage can still feel abrupt when steering authority comes back to openpilot.
- This experiment isolates that first engage handoff without changing the existing driver-override reclaim path.

Branch/install implications:
- `MostlyClueless` only.
- Off by default.
- Not for `subi-staging`, `subi-1.0`, or other stable branches without separate road validation.

Validation guidance:
- Host validation should cover compile/lint plus focused Subaru controller and MC Custom source tests.
- Road-test checks should compare:
  - Level 1 against stock feel for a light engage blend
  - Level 3 as the default experimental reference
  - Level 5 for the softest handoff
- Confirm the existing manual-yield reclaim path still feels unchanged after steering override release.

## 2026-03-31

### `subaru/low-speed center damping` reduce sub-10 mph straight-tracking wheel chatter

What changed:
- Tightened the Subaru angle-control path on `MostlyClueless` only with a narrow low-speed, near-center damping layer.
- Kept the existing branch-local smoothing, straight-tracking stability logic, and manual-steer yield behavior intact.
- Added a small center deadband, stricter sign-flip clamping near zero angle, and light smoothing that all blend out by 10 mph.
- Added focused Subaru controller tests for tiny near-center requests, alternating sign flips, persistent small requests, real low-speed turns, high-speed bypass, and steering-pressed bypass.

Why:
- The current branch already had low-speed smoothing and straight-tracking stabilization, which means the remaining wheel chatter is most likely tiny near-center reversals still slipping through below 10 mph.
- This keeps the fix narrowly scoped to the known low-speed chatter zone without reviving broader lateral experiments that previously made the branch too sensitive.

Validation guidance:
- Recheck on the same repeatable Subaru route with:
  - straight crawl at 5-8 mph
  - light curve at 5-8 mph
  - transition through 8-12 mph
  - MADS touch/relax check
- Desired outcome is less visible wheel chatter around center with no sluggishness entering a gentle turn.
- This entry documents validation intent only and does not claim on-road testing has been completed.

## Current Topology

- Active repo and install surface: `install-mc/openpilot`
- Active development branch: `mc-dev`
- Stock comma installer target: `installer.comma.ai/install-mc/mc-dev`
- Base: `BluePilotDev/bluepilot@bp-6.0`
- Subaru donor scope: minimum bring-up for 2023-25 Outback angle-LKAS support
- Historical references to `MostlyClueless94/bluepilot` and the custom installer worker are legacy only and not part of the active path.

## 2026-03-27

### `ui/subaru hotfix` Subaru UI restart fix and next-drive debug pass

What changed:
- Fixed the BluePilot renderer override mismatch that was crashing `ui` on Subaru.
- Updated both BluePilot renderer subclasses to match the current base `_draw_path()` contract instead of the stale `_draw_path(sm)` form.
- Restored TICI path-style preparation before BluePilot path drawing so the preset path color work still flows through the current base renderer logic.
- Added narrow, transition-based Subaru angle-LKAS debug logs for:
  - `Steering_2` validity
  - `ES_Status` cruise activation
  - `ES_DashStatus` cruise state
  - ACC available/enabled transitions
  - steer fault transitions
  - Eyesight cruise fault transitions
  - angle-LKAS request/inhibit transitions in the controller
- Added a lightweight renderer-contract regression test so the old `_draw_path(sm)` shape cannot silently return.

Why:
- The Subaru rlog from the first road test showed constant `ui` restarts caused by:
  - `TypeError: ModelRenderer._draw_path() takes 1 positional argument but 2 were given`
- The same log showed the car fingerprinted as `SUBARU_OUTBACK_2023`, calibrated, and briefly engaged, which means the immediate blocker was UI stability, not a total Subaru bring-up failure.
- The later Eyesight deactivation is still not fully proven from that log, so the next safe step is to keep the Subaru port in place and make the next drive far more diagnosable.

Validation intent:
- Host checks for this wave should cover:
  - compile/import smoke on touched UI files
  - the new BluePilot renderer regression test
  - existing Subaru tests that already run on this host

Next retest defaults:
- Before the next Subaru drive, set:
  - `CustomModelPathColor=Stock`
  - `RainbowMode=off`
- The goal is to remove visual confounders while we verify UI stability and capture cleaner Subaru state logs if Eyesight still drops.

### `cleanup` active branch and installer path simplification

What changed:
- Retired the old `MostlyClueless94/bluepilot` path from active project tracking.
- Removed the obsolete `tools/bluepilot-installer` custom-installer tooling from the repo.
- Standardized the project log around a single active repo/branch path:
  - `install-mc/openpilot`
  - `mc-dev`
  - `installer.comma.ai/install-mc/mc-dev`

Why:
- Only `mc-dev` is in active use.
- The custom installer worker and old BluePilot repo references were creating unnecessary confusion during install/debug work.

Validation:
- Repo references were reduced to the active install path only.
- The cleanup does not change runtime code or vehicle behavior.

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
- Active push target: `install-mc/openpilot:mc-dev`

Recovery status:
- Before this hotfix, `installer.comma.ai/install-mc/mc-dev` was expected to boot into the manager traceback shown in the field photo.
- After this hotfix landed on the active install branch, the build should at least clear this specific import-time crash and reach normal UI startup.

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
- This work is part of the active `install-mc/openpilot:mc-dev` branch.

Open follow-ups:
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
- Historical only.
- Removed during later cleanup after the project standardized on the stock installer path via `install-mc/openpilot`.

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
