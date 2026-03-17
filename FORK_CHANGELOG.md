# MostlyClueless94 SunnyPilot Subaru Fork Changelog

This file tracks all custom fork changes for Subaru angle-LKAS support and related fixes.

## Active Install URLs

- Stable 3X: `https://install.sunnypilot.ai/fork/MostlyClueless94/master`
- Stable C4: `https://install.sunnypilot.ai/fork/MostlyClueless94/master-tici`
- Alpha (staging/testing): `https://install.sunnypilot.ai/fork/MostlyClueless94/alpha`

## Branch Policy

- `master`: primary stable install branch for comma 3X.
- `master-tici`: comma 4 compatible mirror of `master`.
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

### 2026-03-17

- Branches updated: `master`, `master-tici`.
- Why changed: add a comma 4 compatible stable branch name without changing Subaru or hardware logic.
- Mirror rule: `master-tici` is a strict mirror of `master`, including the same `opendbc_repo` pointer.
- Install guidance:
  - comma 3X users should install `master`
  - comma 4 users should install `master-tici`
- Validation done:
  - confirmed `master` points to `opendbc_repo` commit `c527da39a`
  - confirmed SunnyPilot classifies `master-tici` as `channel_type == "tici"` by existing branch naming rules
  - confirmed existing installer/updater migration logic already maps TICI `master` -> `master-tici`

### 2026-03-13

- Branches updated: `master`.
- Submodule commit(s): `c527da39a` - `subaru: smooth low-speed angle steering below 10mph`
- Why changed: promote low-speed angle smoothing (0-10 mph) into stable Subaru lateral path to reduce twitchy left-right corrections.
- Validation done: `python -m py_compile opendbc_repo/opendbc/car/subaru/carcontroller.py`.
- Known risks: requires in-car validation to confirm no regression in low-speed LKAS fault behavior.

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
