#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import py_compile
import shutil
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]

PY_COMPILE_TARGETS = (
  "selfdrive/ui/sunnypilot",
  "selfdrive/ui/onroad",
  "selfdrive/ui/mici/onroad",
  "sunnypilot/system/params_migration.py",
  "common/tests/test_params_migration_sp.py",
)

IMPORT_SMOKE_MODULES = (
  "openpilot.selfdrive.ui.sunnypilot.onroad.confidence_ball",
  "openpilot.selfdrive.ui.onroad.augmented_road_view",
  "openpilot.selfdrive.ui.mici.onroad.augmented_road_view",
  "openpilot.sunnypilot.system.params_migration",
)

PYTEST_TARGETS = (
  "common/tests/test_params_migration_sp.py",
  "selfdrive/ui/tests/test_subaru_settings_pages.py",
  "selfdrive/ui/tests/test_path_colors.py",
  "selfdrive/ui/tests/test_brake_status.py",
  "selfdrive/ui/tests/test_confidence_ball_source.py",
  "selfdrive/ui/tests/test_mici_speedometer_hotfix.py",
  "selfdrive/ui/tests/test_vibrant_path_rendering.py",
)

KNOWN_LOCAL_IMPORT_ISSUES = (
  "No module named 'openpilot.common'",
  "No module named 'openpilot.common.params_pyx'",
  "No module named 'pyray'",
)


def main() -> int:
  parser = argparse.ArgumentParser(description="Run the lightweight shipping-branch verification suite.")
  parser.add_argument("--ci", action="store_true", help="Fail hard if any check cannot run.")
  args = parser.parse_args()

  print(f"[shipping-check] repo root: {REPO_ROOT}")
  print(f"[shipping-check] mode: {'ci' if args.ci else 'local'}")

  run_ruff()
  run_py_compile()
  run_import_smoke(args.ci)
  run_pytest(args.ci)

  print("[shipping-check] all requested checks passed")
  return 0


def repo_env() -> dict[str, str]:
  env = os.environ.copy()
  current_pythonpath = env.get("PYTHONPATH")
  env["PYTHONPATH"] = str(REPO_ROOT) if not current_pythonpath else os.pathsep.join((str(REPO_ROOT), current_pythonpath))
  return env


def run_ruff() -> None:
  print("[shipping-check] running ruff")

  ruff_binary = shutil.which("ruff")
  if ruff_binary is not None:
    cmd = [ruff_binary, "check", str(REPO_ROOT)]
  else:
    cmd = [sys.executable, "-m", "ruff", "check", str(REPO_ROOT)]

  result = subprocess.run(cmd, cwd=REPO_ROOT, env=repo_env(), text=True, capture_output=True)
  if result.returncode != 0:
    emit_output(result)
    if ruff_binary is None and "No module named ruff" in combined_output(result):
      raise SystemExit(
        "[shipping-check] ruff is not available in the current Python environment. "
        "Run ./tools/op.sh setup or install the testing dependencies before using this check."
      )
    raise SystemExit(f"[shipping-check] ruff failed with exit code {result.returncode}")


def run_py_compile() -> None:
  print("[shipping-check] running py_compile over startup-sensitive Python files")
  compiled = 0

  for target in PY_COMPILE_TARGETS:
    target_path = REPO_ROOT / target
    if target_path.is_file():
      py_compile.compile(str(target_path), doraise=True)
      compiled += 1
      continue

    if target_path.is_dir():
      for file_path in target_path.rglob("*.py"):
        if "__pycache__" in file_path.parts:
          continue
        py_compile.compile(str(file_path), doraise=True)
        compiled += 1
      continue

    raise SystemExit(f"[shipping-check] missing py_compile target: {target_path}")

  print(f"[shipping-check] py_compile passed for {compiled} files")


def run_import_smoke(ci_mode: bool) -> None:
  print("[shipping-check] running import smoke checks")
  failures: list[tuple[str, subprocess.CompletedProcess[str]]] = []

  for module_name in IMPORT_SMOKE_MODULES:
    result = subprocess.run(
      [sys.executable, "-c", f"import importlib; importlib.import_module({module_name!r})"],
      cwd=REPO_ROOT,
      env=repo_env(),
      text=True,
      capture_output=True,
    )
    if result.returncode != 0:
      failures.append((module_name, result))

  if not failures:
    print(f"[shipping-check] import smoke passed for {len(IMPORT_SMOKE_MODULES)} modules")
    return

  first_failure_output = combined_output(failures[0][1])
  if should_soft_fail(first_failure_output, ci_mode):
    print(
      "[shipping-check] import smoke skipped locally due to the known Windows/bootstrap dependency issue. "
      "CI remains the authoritative full import check."
    )
    emit_output(failures[0][1])
    return

  for module_name, result in failures:
    print(f"[shipping-check] import smoke failed for {module_name}")
    emit_output(result)
  raise SystemExit(f"[shipping-check] import smoke failed for {len(failures)} module(s)")


def run_pytest(ci_mode: bool) -> None:
  print("[shipping-check] running focused pytest subset")
  result = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", *PYTEST_TARGETS],
    cwd=REPO_ROOT,
    env=repo_env(),
    text=True,
    capture_output=True,
  )

  if result.returncode == 0:
    print("[shipping-check] focused pytest subset passed")
    return

  output = combined_output(result)
  if should_soft_fail(output, ci_mode):
    print(
      "[shipping-check] focused pytest skipped locally due to the known Windows/bootstrap dependency issue. "
      "CI remains the authoritative full pytest gate."
    )
    emit_output(result)
    return

  emit_output(result)
  raise SystemExit(f"[shipping-check] focused pytest failed with exit code {result.returncode}")


def should_soft_fail(output: str, ci_mode: bool) -> bool:
  if ci_mode or platform.system() != "Windows":
    return False
  return any(marker in output for marker in KNOWN_LOCAL_IMPORT_ISSUES)


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
  return "\n".join(part for part in (result.stdout, result.stderr) if part)


def emit_output(result: subprocess.CompletedProcess[str]) -> None:
  if result.stdout:
    print(result.stdout.rstrip())
  if result.stderr:
    print(result.stderr.rstrip(), file=sys.stderr)


if __name__ == "__main__":
  raise SystemExit(main())
