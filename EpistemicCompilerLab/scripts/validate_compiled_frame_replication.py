#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from compiled_frame_core import compile_frame, parse_date, parse_revision
from teacher_loop_eval import load_cases, score_case


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-root", required=True, type=Path)
    parser.add_argument("--swipl", required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = parse_args()
    lab = args.lab_root.resolve()
    cases_path = lab / "cases" / "compiled-frame-replication-v0.jsonl"
    manifest_path = lab / "cases" / "compiled-frame-replication-v0.manifest.json"
    parser_path = lab / "scripts" / "compiled_frame_core.py"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = load_cases(cases_path)
    if manifest.get("status") != "frozen_before_qwen_evaluation":
        raise AssertionError("replication manifest is not frozen")
    if sha256(cases_path) != manifest["casesSha256"]:
        raise AssertionError("frozen replication cases hash changed")
    if sha256(parser_path) != manifest["parserSha256"]:
        raise AssertionError("compiled-frame parser changed after generation")
    if len(cases) != 24 or len({case["id"] for case in cases}) != 24:
        raise AssertionError("replication set must contain 24 unique cases")
    kinds = Counter(case["annotation"]["caseKind"] for case in cases)
    if set(kinds.values()) != {6} or len(kinds) != 4:
        raise AssertionError(f"bad replication kind balance: {dict(kinds)}")
    styles = Counter(case["annotation"]["dateStyle"] for case in cases)
    if any(styles.get(style) != 6 for style in ("words", "dotted", "iso")):
        raise AssertionError(f"bad replication date balance: {dict(styles)}")
    if sum(bool(case["annotation"]["hasDistractor"]) for case in cases) != 12:
        raise AssertionError("replication distractor balance changed")
    passed = 0
    for case in cases:
        annotation = case["annotation"]
        revision = parse_revision(case["questionRu"])
        date = parse_date(case["questionRu"])
        expected_revision = None if annotation["revision"] == "missing" else annotation["revision"]
        expected_date = None if annotation["date"] == 0 else annotation["date"]
        if revision != expected_revision or date != expected_date:
            raise AssertionError(f"parser annotation mismatch: {case['id']}")
        frame = compile_frame(case["questionRu"], args.swipl, lab)
        checks = score_case(case, frame["decision"], None)
        if not checks["passed"]:
            raise AssertionError(f"compiled frame mismatch: {case['id']} {frame['decision']}")
        passed += 1
    print(json.dumps({"cases": len(cases), "passed": passed, "kinds": kinds}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
