#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

try:
  from openpilot.tools.lib.logreader import LogReader
  from openpilot.tools.lib.subaru_fault_diagnose import (
    format_subaru_fault_summary,
    iter_normalized_subaru_fault_events,
    summarize_first_subaru_lkas_fault,
  )
except ModuleNotFoundError:
  from tools.lib.logreader import LogReader
  from tools.lib.subaru_fault_diagnose import (
    format_subaru_fault_summary,
    iter_normalized_subaru_fault_events,
    summarize_first_subaru_lkas_fault,
  )


def main() -> int:
  parser = argparse.ArgumentParser(description="Summarize the first Subaru LKAS steer fault in a local rlog/qlog file.")
  parser.add_argument("log_path", help="Local route log path")
  args = parser.parse_args()

  try:
    log_reader = LogReader(args.log_path, sort_by_time=True)
  except Exception as exc:
    print(f"Failed to open log '{args.log_path}': {exc}", file=sys.stderr)
    return 2

  try:
    summary = summarize_first_subaru_lkas_fault(iter_normalized_subaru_fault_events(log_reader))
  except Exception as exc:
    print(f"Failed to analyze Subaru LKAS fault data from '{args.log_path}': {exc}", file=sys.stderr)
    return 2

  print(format_subaru_fault_summary(summary))
  return 0 if summary is not None else 1


if __name__ == "__main__":
  raise SystemExit(main())
