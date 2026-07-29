#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from compiled_frame_core import compile_frame
from teacher_loop_eval import load_cases, score_case


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-root", required=True, type=Path)
    parser.add_argument("--swipl", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lab = args.lab_root.resolve()
    cases = load_cases(lab / "cases" / "teacher-loop-pilot-v0.jsonl")
    failures = []
    frames = []
    for case in cases:
        frame = compile_frame(case["questionRu"], args.swipl, lab)
        checks = score_case(case, frame["decision"], None)
        frames.append({"caseId": case["id"], "frame": frame, "checks": checks})
        if not checks["passed"]:
            failures.append(case["id"])
    if failures:
        raise AssertionError(f"compiled frame failed cases: {failures}")
    if len(frames) != 18:
        raise AssertionError(f"expected 18 frames, got {len(frames)}")
    print(json.dumps({
        "frames": len(frames),
        "passed": len(frames),
        "train": 6,
        "dev": 6,
        "holdout": 6,
    }))
    print("Compiled decision frame oracle passed: 18/18")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
