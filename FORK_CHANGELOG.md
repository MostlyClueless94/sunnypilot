# MostlyClueless94 SunnyPilot Subaru Fork Changelog

This file tracks custom fork changes for Subaru angle-LKAS compatibility and branch promotion flow.

## Active Install URLs

- Stable (`master`): `https://install.sunnypilot.ai/fork/MostlyClueless94/master`
- Integration (`staging`): `https://install.sunnypilot.ai/fork/MostlyClueless94/staging`
- Experimental (`alpha`): `https://install.sunnypilot.ai/fork/MostlyClueless94/alpha`

## Branch Policy

- `master`: production/stable installs only.
- `staging`: latest SunnyPilot upstream + replayed stable Subaru compatibility queue.
- `alpha`: experimental branch (longitudinal and other high-risk tests); never auto-promoted.

## Historical Baseline (2026-03-06 stable set)

### Superproject commits

- `f0b31f1` - `subaru: reduce angle LKAS faults in low-speed mads`
- `7405a43` - `subaru: fix angle LKAS cruise state handling`
- `01e52bc` - `subaru: include 2025 outback fw fingerprint update`
- `f574e18` - `subaru: show 2025 outback in platform selector`

### `opendbc_repo` commits

- `72981fd` - `subaru: allow mads above 5mph with low-speed angle guard`
- `da845de` - `subaru: keep mads angle control above low-speed threshold`
- `3001604` - `subaru: gate angle LKAS requests to full-control drive state`
- `67e6381` - `subaru: use ES_Status cruise state for angle LKAS`
- `5e57cb7` - `subaru: add 2025 outback fw fingerprints`
- `5d3f9bc` - `subaru: expose outback 2025 in selector`
- `170e1de` - `subaru: port angle LKAS support and 2025 crosstrek platform`

## Changelog

### 2026-03-13

- Branches updated: `staging` only.
- Upstream baseline: `upstream/master` at `2e82908`.
- Replayed stable Subaru compatibility queue in `opendbc_repo`:
  - `132652762` (cherry-pick of `170e1de2f`)
  - `2bb3d7c93` (cherry-pick of `5d3f9bc83`)
  - `000314946` (cherry-pick of `5e57cb77d`)
  - `253dba999` (cherry-pick of `67e6381bc`)
  - `353d4948a` (cherry-pick of `3001604b0`)
  - `822d12f9a` (cherry-pick of `da845de19`)
  - `fe2cd2926` (cherry-pick of `72981fd08`)
- Why changed: establish `staging` as monthly integration branch (latest SunnyPilot + stable Subaru baseline).
- Validation done:
  - `python -m py_compile` passed on modified Subaru Python files.
  - `pytest opendbc/safety/tests/test_subaru.py` attempted locally; blocked on Python 3.10 `ReprEnum` import (needs Python 3.11+ CI/Linux).
- Known risks:
  - In-car validation still required before promoting `staging` to `master`.
  - `f574e189` was intentionally not replayed directly because it is a root-style broad-tree commit; equivalent Subaru compatibility is covered via the replayed `opendbc` queue.

## Update Template

Use this section format for each future update:

```text
### YYYY-MM-DD
- Branches updated: <master|staging|alpha|multiple>
- Superproject commit(s): <hash> - <message>
- Submodule commit(s): <hash> - <message>
- Why changed: <short reason>
- Validation done: <road test / bench test / build check / CI>
- Known risks: <if any>
```
