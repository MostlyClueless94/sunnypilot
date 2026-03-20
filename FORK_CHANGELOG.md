# MostlyClueless94 SunnyPilot Subaru Fork Changelog

This file tracks the maintained Subaru patch queue that sits on top of current SunnyPilot.

## Active Install URLs

- Stable: `https://install.sunnypilot.ai/fork/MostlyClueless94/master`
- Testing: `https://install.sunnypilot.ai/fork/MostlyClueless94/MostlyClueless`

## Branch Policy

- `master`: stable/public branch, updated only after validating `MostlyClueless`.
- `MostlyClueless`: current-upstream integration/testing branch.
- Longitudinal experimentation is intentionally excluded from this rebuilt branch line.

## 2026-03-19 (MostlyClueless Reset to Current SunnyPilot)

### Base

- Rebuilt `MostlyClueless` from `sunnypilot/sunnypilot` `upstream/master` commit `1658898498b8867dca06b22be85bc650e6a284f9`.
- Rebased custom Subaru work onto `sunnypilot/opendbc` commit `b178bc5d4e7cd15c50eb3e148cc2648b9379ca86`.
- Moved `opendbc_repo` to dedicated repo: `https://github.com/MostlyClueless94/opendbc.git`.
- Current rebuilt `opendbc_repo` pointer: `c3708c7c260d12ae4be71597878c624b94433ef5`.

### Retained Subaru Patch Queue

- Base Subaru compatibility:
  - `170e1de2f` modern angle-LKAS Subaru support and 2025 Crosstrek platform
  - `5d3f9bc83` expose 2025 Outback in selector
  - `5e57cb77d` add 2025 Outback FW fingerprints
  - `67e6381bc` use `ES_Status` cruise state for angle LKAS
  - `3001604b0` gate angle LKAS requests to full-control drive state
  - `da845de19` keep MADS angle control above low-speed threshold
  - `72981fd08` allow MADS above 5 mph with low-speed angle guard
  - `4d26129a1` harden angle LKAS around low-speed maneuver edges
- Stable lateral behavior tuning:
  - `7b9764be2` low-speed smoothing below 10 mph
  - `2b55f0563` MADS manual-steer yield
- `MostlyClueless` testing extras:
  - `a25cfc8b7` soft-capture engage/recovery smoothing
  - `3c03b639f` Jacob `v2_limits` engage-gap gate port

### Explicitly Excluded

- Old alpha-long / Outback longitudinal experiments
- Old branch rename and cleanup commits
- Old `master-tici` / staging documentation churn

### Validation Done

- `python -m py_compile opendbc_repo/opendbc/car/subaru/carcontroller.py`
- `python -m py_compile opendbc_repo/opendbc/car/subaru/interface.py`
- `python -m py_compile opendbc_repo/opendbc/car/subaru/values.py`
- `python -m py_compile opendbc_repo/opendbc/car/subaru/test_carcontroller.py`

### Known Follow-Up

- `master` stays unchanged until this rebuilt `MostlyClueless` branch is validated in-car.
- Full pytest/safety coverage still needs a Linux/Python 3.11+ environment.
