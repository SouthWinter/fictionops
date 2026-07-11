#!/usr/bin/env python3
"""Replay stored benchmark reviews without making model API calls."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


RECEIPT_PREFIX = "FICTIONOPS_RUNNER_RECEIPT:"


def prompt_value(payload: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}:\s*(.+)$", payload, re.MULTILINE)
    if not match:
        raise ValueError(f"benchmark prompt is missing {name}")
    return match.group(1).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay reviews from a FictionOps benchmark evidence file.")
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    payload = sys.stdin.buffer.read().decode("utf-8")
    case_id = prompt_value(payload, "CASE_ID")
    mode = prompt_value(payload, "MODE")
    run_index = int(prompt_value(payload, "RUN_INDEX"))
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    matches = [
        row
        for row in evidence.get("rows") or []
        if row.get("case_id") == case_id and row.get("mode") == mode and int(row.get("run_index") or 0) == run_index
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one replay row for {case_id}/{mode}/run-{run_index}; found {len(matches)}")
    row = matches[0]
    if isinstance(row.get("telemetry"), dict):
        print(RECEIPT_PREFIX + json.dumps(row["telemetry"], ensure_ascii=False, separators=(",", ":")), file=sys.stderr)
    print(json.dumps(row["review"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
