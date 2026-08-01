#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from strict_epistemic_benchmark_core import oracle_frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-root", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--swipl", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = [
        json.loads(line) for line in args.cases.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(cases) != 56 or len({case["id"] for case in cases}) != 56:
        raise AssertionError("benchmark candidate must contain 56 unique cases")
    splits = Counter(case["split"] for case in cases)
    if any(splits[name] != 14 for name in ("train", "dev", "holdout", "replication")):
        raise AssertionError(f"bad split balance: {dict(splits)}")
    primary = [case for case in cases if case["caseKind"] == "epistemic"]
    statuses = Counter(case["expected"]["status"] for case in primary)
    if any(statuses[name] != 12 for name in ("supported", "refuted", "unknown", "conflicting")):
        raise AssertionError(f"bad status balance: {dict(statuses)}")
    questions = [case["questionRu"] for case in cases]
    if len(set(questions)) != 56:
        raise AssertionError("questions must be unique")
    if any("probab" in json.dumps(case).lower() or "fuzzy" in json.dumps(case).lower()
           for case in cases):
        raise AssertionError("probability/fuzzy constructs are forbidden")

    for case in cases:
        annotation = case["annotation"]
        frame = oracle_frame(
            args.swipl, args.lab_root,
            annotation["revision"], annotation["material"],
        )
        expected = case["expected"]
        for field in ("status", "action", "reason"):
            if expected[field] != frame[field]:
                raise AssertionError(f"{case['id']} {field} mismatch")
        if expected["askField"] != frame.get("askField"):
            raise AssertionError(f"{case['id']} askField mismatch")
        visible_ids = {item["id"] for item in case["sourceContext"]}
        if not set(expected["evidence"]).issubset(visible_ids):
            raise AssertionError(f"{case['id']} evidence is not visible")
        if case["caseKind"] == "epistemic":
            aliases = annotation.get("evidenceAliasMap") or {}
            oracle_evidence = frame.get("evidence") or []
            mapped = sorted(aliases[item] for item in oracle_evidence)
            if expected["evidence"] != mapped:
                raise AssertionError(f"{case['id']} evidence alias mismatch")
        if expected["status"] == "unknown" and expected["evidence"]:
            raise AssertionError(f"{case['id']} unknown must have no evidence")
        if expected["status"] == "conflicting" and len(expected["evidence"]) != 2:
            raise AssertionError(f"{case['id']} conflict must preserve two evidence IDs")

    print(json.dumps({
        "cases": len(cases),
        "sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        "splits": splits,
        "statuses": statuses,
        "clarificationCases": len(cases) - len(primary),
        "passed": len(cases),
    }, ensure_ascii=False, default=dict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
