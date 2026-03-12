# MostlyClueless94 SunnyPilot Subaru Fork Changelog

This file tracks all custom fork changes for Subaru angle-LKAS support and related fixes.

## Active Install URLs

- Master (current primary): `https://installer.comma.ai/MostlyClueless94/master`
- Alpha (staging/testing): `https://installer.comma.ai/MostlyClueless94/alpha`

## Branch Policy

- `master`: primary install branch.
- `alpha`: staging branch for new Subaru changes before promoting to `master`.
- Current state on 2026-03-06: `master` and `alpha` point to the same superproject commit (`f0b31f1`).

## Current Commit Map (2026-03-06)

### Superproject (`MostlyClueless94/sunnypilot`)

- `master` -> `f0b31f163fb10d7fd9e92661b2b7d10f23e286bb`
- `alpha` -> `f0b31f163fb10d7fd9e92661b2b7d10f23e286bb`

### Submodule (`opendbc_repo`)

- In-tree pointer: `72981fd0876c69401e6cdf4fe78d732eb0c65d41` (`opendbc-alpha-submodule`)
- Reference tag for pre-mitigation state: `5e57cb77dd1ec5843bcf841ff465b2fa3ece9632` (`opendbc-master-submodule`)

## Changelog

### 2026-03-12 (Outback Alpha Longitudinal Enablement)

#### Branch target

- `alpha` only (`master` unchanged)

#### Submodule (`opendbc_repo`) commit

- `b9debfd` - `subaru: enable outback angle-long with gen2 message safety`

#### What changed

- Enabled alpha longitudinal only for `SUBARU_OUTBACK_2023` (2023-25 Outback) on non-release builds.
- Preserved existing low-speed angle-LKAS fault hardening logic in lateral control:
  - MADS-only 5 mph guard
  - low-speed/high-angle guard
  - post-non-drive cooldown guard
- Added robust longitudinal source-message caching and stale-message fallback for:
  - `ES_Status`
  - `ES_Brake`
  - `ES_Distance`
- Corrected GEN2 angle-long message routing:
  - `ES_Status`, `ES_Brake`, `ES_Distance` now sent on the computed long bus (`CanBus.alt` on GEN2).
- Added Subaru safety test coverage for GEN2 + LKAS_ANGLE + LONG:
  - `TestSubaruGen2AngleLongitudinalSafety`
- Added CI guardrail workflow for `alpha` branch:
  - `.github/workflows/alpha-opendbc-guardrails.yaml`

#### Validation done

- `python -m py_compile` passed for modified Subaru files:
  - `carcontroller.py`
  - `subarucan.py`
  - `interface.py`
  - `test_subaru.py`
- Full Subaru safety tests not runnable locally in this Windows environment (`Python 3.10`); CI/Linux validation required.

### 2026-03-12

#### Branch target

- `alpha` only (based from `master` baseline `654b656`)

#### Submodule (`opendbc_repo`) commit

- `4d26129` - `subaru: harden angle LKAS around low-speed maneuver edges`

#### What changed

- Added global low-speed/high-angle LKAS request guard in Subaru angle lateral control:
  - speed threshold: `< 2.7 m/s` (6 mph)
  - steering angle threshold: `> 135 deg`
- Added post-non-drive cooldown guard for angle LKAS request:
  - cooldown window: `1.5 s` (`150` control frames at `100 Hz`)
  - active only below `4.4704 m/s` (10 mph)
- Preserved existing MADS-only safety guard:
  - `MADS_ONLY_MIN_SPEED = 2.24 m/s` (5 mph)
  - `MADS_ONLY_MAX_STEER_ANGLE = 120 deg`
- No longitudinal behavior was modified.

#### Validation done

- `python -m py_compile opendbc_repo/opendbc/car/subaru/carcontroller.py` passed.
- In-car validation pending on `alpha` (driveway/parking-lot low-speed fault reproduction scenarios).

### 2026-03-06

#### Superproject commits

- `f0b31f1` - `subaru: reduce angle LKAS faults in low-speed mads`
- `7405a43` - `subaru: fix angle LKAS cruise state handling`

#### Submodule (`opendbc_repo`) commits

- `72981fd` - `subaru: allow mads above 5mph with low-speed angle guard`
- `da845de` - `subaru: keep mads angle control above low-speed threshold`
- `3001604` - `subaru: gate angle LKAS requests to full-control drive state`
- `67e6381` - `subaru: use ES_Status cruise state for angle LKAS`

### 2026-03-05

#### Superproject commits

- `01e52bc` - `subaru: include 2025 outback fw fingerprint update`
- `f574e18` - `subaru: show 2025 outback in platform selector`

#### Submodule (`opendbc_repo`) commits

- `5e57cb7` - `subaru: add 2025 outback fw fingerprints`
- `5d3f9bc` - `subaru: expose outback 2025 in selector`
- `170e1de` - `subaru: port angle LKAS support and 2025 crosstrek platform`

## Functional Summary

- Added support path for modern Subaru angle-based steering.
- Added/updated 2025 Outback visibility and firmware fingerprint handling.
- Added low-speed/high-angle fault mitigation while preserving MADS behavior above 5 mph.
- No intentional changes were made to remove SunnyPilot features like MADS.

## Validation Notes

- Branches install correctly via installer URL.
- In-car behavior verified enough to detect and reproduce low-speed LKAS fault condition; mitigation patches added after log-driven debugging.
- Full long-duration, multi-cycle in-car validation is still required after each promoted change.

## Update Template (append for each new change set)

Use this section format for every future update:

```
### YYYY-MM-DD
- Branches updated: <master|alpha|both>
- Superproject commit(s): <hash> - <message>
- Submodule commit(s): <hash> - <message>
- Why changed: <short reason>
- Validation done: <road test / bench test / build check>
- Known risks: <if any>
```
