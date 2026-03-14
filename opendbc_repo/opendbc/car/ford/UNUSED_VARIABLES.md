# Unused variables in carcontroller.py

Variables that are **defined or calculated but never read**. Safe to remove if you don't need them for future use or debugging.

---

## Module-level (top of file)

| Variable | Line | Notes |
|----------|------|--------|
| `CONTROL_N` | 36 | Only used to build `T_IDXS`. |
| `IDX_N` | 37 | Only used to build `T_IDXS`. |
| `T_IDXS` | 38 | Built from `index_function`; **never used** in this file (code uses `ModelConstants.T_IDXS`). |
| `index_function` | 24 | Only used to build `T_IDXS`; **dead if T_IDXS is removed**. |

---

## `__init__` – instance attributes never read

| Attribute | Line | Notes |
|-----------|------|--------|
| `self.brake_request` | 106 | Set to `False`, never read or updated. |
| `self.accel_pitch_compensated` | 116 | Set to `0.0`; local `accel_pitch_compensated` exists in long block, this one unused. |
| `self.steering_wheel_delta_adjusted` | 117 | Set to `0.0`, never read. |
| `self.steer_warning_count` | 139 | Set to `0`, never read (only `steer_warning` is read at 1004). |
| `self.steering_limited` | 140 | Set to `0`, never read. |
| `self.enable_high_curvature_mode` | 135 | Set to `False`, never read. |
| `self.path_angle_wheel_angle_conversion` | 195 | Set to `(np.pi/180)`, never read. |
| `self.lane_width_tolerance_factor` | 188 | Set to `0.75`, never read. |
| `self.curvature_rate` | 220 | Set to `0`, never read (`curvature_rate_last` is written/used elsewhere). |
| `self.curvature_rate_last` | 217, 691 | Written in `__init__` and in lateral block; **never read**. Could be for future use. |
| `self.LC_PID_gain` | 199, 420, 424 | Set from `LC_PID_GAIN` or `LC_PID_gain_UI`; **never read** (only `LC_PID_gain_UI` is used in path_offset_error). |
| `self.distance_bar_frame` | 115, 968 | Set in `__init__` and when bars flip; **never read**. |

---

## `__init__` – written but only as “always same value”

| Attribute | Line | Notes |
|-----------|------|--------|
| `self.steer_warning` | 138 | Only ever set to `False` in `__init__`; read at 1004 for `torqueOutputCan`. So output is always `0.0`. Logic that would set it `True` may have been removed. |

---

## Inside `update()` – local variables

| Variable | Line | Notes |
|----------|------|--------|
| `path_angle_high_c` | 627 | Set to `0.0`; only used in `path_angle = path_angle_low_c + path_angle_high_c`. Can inline as `path_angle = path_angle_low_c`. |
| `large_curve_factor` | 557 | Set to `1.0` **after** last use (553). This assignment is dead; the variable is only used earlier. |

---

## Dead branch (logic bug)

| Location | Line | Notes |
|----------|------|--------|
| `if lead == 0:` | 878–883 | `lead` is either `None` or a lead object, never `0`. This block is **never run**. “No lead” is already handled by defaults before the gaining/pacing/trailing block. |

---

## Summary

- **Module:** `CONTROL_N`, `IDX_N`, `T_IDXS`, `index_function` – unused (or only used to build unused `T_IDXS`).
- **Instance (init only, never read):** `brake_request`, `accel_pitch_compensated`, `steering_wheel_delta_adjusted`, `steer_warning_count`, `steering_limited`, `enable_high_curvature_mode`, `path_angle_wheel_angle_conversion`, `lane_width_tolerance_factor`, `curvature_rate`, `curvature_rate_last`, `LC_PID_gain`, `distance_bar_frame`.
- **Instance (effectively constant):** `steer_warning` is only ever `False`.
- **Locals:** `path_angle_high_c` can be inlined; `large_curve_factor = 1.0` at 557 is dead.
- **Dead branch:** `if lead == 0:` block (878–883) can be removed.
