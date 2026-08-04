#!/usr/bin/env python3
"""Validate and freeze progressive Epistemic DSL benchmark cases."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts" / "progressive-epistemic-case-v0.schema.json"
CASES_PATH = (
    ROOT
    / "EpistemicCompilerLab"
    / "progressive-dsl"
    / "management-course"
    / "cases-dsl-a-v0.jsonl"
)
EXPECTED_CASE_IDS = {
    "management.a.po-product-value",
    "management.a.po-backlog",
    "management.a.pm-backlog-unknown",
    "management.a.tl-performance-refuted",
    "management.a.synthetic-conflict",
    "management.a.cto-strategy",
    "management.a.em-team-health",
    "management.a.po-vs-pm-hybrid",
}
EXPECTED_STATUS_COUNTS = {
    "supported": 5,
    "refuted": 1,
    "unknown": 1,
    "conflicting": 1,
}
EXPECTED_FILE_SHA256 = "TO_BE_FROZEN_AFTER_FIRST_LOCAL_PASS"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object expected: {path}")
    return value


def main() -> int:
    schema = read_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    lines = [
        line
        for line in CASES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    cases: list[dict[str, Any]] = []
    for index, line in enumerate(lines, 1):
        value = json.loads(line)
        errors = sorted(validator.iter_errors(value), key=lambda item: list(item.path))
        if errors:
            details = "; ".join(
                f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
                for error in errors[:10]
            )
            raise AssertionError(f"case {index} schema failure: {details}")
        cases.append(value)

    case_ids = [case["caseId"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise AssertionError("duplicate progressive benchmark case ID")
    if set(case_ids) != EXPECTED_CASE_IDS:
        raise AssertionError(
            f"case set mismatch: expected={sorted(EXPECTED_CASE_IDS)} actual={sorted(case_ids)}"
        )

    status_counts: dict[str, int] = {}
    for case in cases:
        if case["minimumDslLevel"] != "DSL-A":
            raise AssertionError(f"DSL-A baseline contains later case: {case['caseId']}")
        expected = case["expectedByLevel"].get("DSL-A")
        if not isinstance(expected, dict) or not isinstance(expected.get("status"), str):
            raise AssertionError(f"DSL-A expectation missing: {case['caseId']}")
        status = expected["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        if case.get("requiredAbstention") and status not in {"unknown", "conflicting"}:
            raise AssertionError(
                f"abstention case has non-abstaining status: {case['caseId']}"
            )

    if status_counts != EXPECTED_STATUS_COUNTS:
        raise AssertionError(
            f"status distribution mismatch: expected={EXPECTED_STATUS_COUNTS} actual={status_counts}"
        )

    content_hash = "sha256:" + hashlib.sha256(CASES_PATH.read_bytes()).hexdigest()
    if EXPECTED_FILE_SHA256 != "TO_BE_FROZEN_AFTER_FIRST_LOCAL_PASS" and content_hash != EXPECTED_FILE_SHA256:
        raise AssertionError(
            f"frozen benchmark hash mismatch: expected={EXPECTED_FILE_SHA256} actual={content_hash}"
        )

    print("Progressive Epistemic DSL management benchmark contract passed")
    print(f"Cases: {len(cases)}")
    print(f"Status counts: {json.dumps(status_counts, sort_keys=True)}")
    print(f"Benchmark hash: {content_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
