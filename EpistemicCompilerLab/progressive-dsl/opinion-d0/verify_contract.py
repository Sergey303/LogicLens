#!/usr/bin/env python3
"""Freeze and validate DSL-D0 opinion fixtures and pilot cases."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
OPINIONS = ROOT / "opinions-v0.jsonl"
CASES = ROOT / "cases-v0.jsonl"
OPINION_SCHEMA = ROOT / "opinion-v0.schema.json"
CASE_SCHEMA = ROOT / "case-v0.schema.json"
RESPONSE_SCHEMA = ROOT / "codex-response-v0.schema.json"
EXPECTED_OPINIONS_HASH = "sha256:7da7d9209c506bce40040004a36041f58a81cf2031f22eaf44c4fa54cdfb48d2"
EXPECTED_CASES_HASH = "sha256:1595ebd64ea0d5057d6e1a256881796eed04ac1ee18c35420850148faf49d68c"
EXPECTED_IDS = {
    "management.d0.evidence-dominant-same-p",
    "management.d0.prior-dominant-same-p",
    "management.d0.low-base-rate",
    "management.d0.high-base-rate",
    "management.d0.low-conflict-same-p",
    "management.d0.high-conflict-same-p",
    "management.d0.explicit-refutation",
    "management.d0.answer-profile-evidence-counts",
    "management.d0.missing-opinion-control",
}


def canonical_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    raw.decode("utf-8", errors="strict")
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(path)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object expected: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise AssertionError(f"JSON object expected: {path}:{line_number}")
        rows.append(value)
    return rows


def validate_rows(rows: list[dict[str, Any]], schema: dict[str, Any], label: str) -> None:
    validator = Draft202012Validator(schema)
    for index, row in enumerate(rows, 1):
        errors = sorted(validator.iter_errors(row), key=lambda item: list(item.path))
        if errors:
            details = "; ".join(
                f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
                for error in errors[:10]
            )
            raise AssertionError(f"{label} {index} schema failure: {details}")


def validate_provider_schema(schema: dict[str, Any]) -> None:
    """Check the strict subset used by Codex Structured Outputs."""
    def visit(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            return
        if "const" in node and "type" not in node:
            raise AssertionError(f"provider schema const lacks type: {path}")
        if node.get("type") == "object":
            if node.get("additionalProperties") is not False:
                raise AssertionError(f"provider object must close properties: {path}")
            properties = node.get("properties")
            required = node.get("required")
            if not isinstance(properties, dict) or set(required or []) != set(properties):
                raise AssertionError(f"provider object must require every property: {path}")
        if node.get("type") == "array" and "items" not in node:
            raise AssertionError(f"provider array lacks items: {path}")
        for key, value in node.items():
            if isinstance(value, dict):
                visit(value, f"{path}/{key}")
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    visit(item, f"{path}/{key}/{index}")

    visit(schema, "<root>")


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected={expected!r} actual={actual!r}")


def main() -> int:
    opinions = load_jsonl(OPINIONS)
    cases = load_jsonl(CASES)
    validate_rows(opinions, load_json(OPINION_SCHEMA), "opinion")
    validate_rows(cases, load_json(CASE_SCHEMA), "case")
    validate_provider_schema(load_json(RESPONSE_SCHEMA))

    assert_equal(digest(OPINIONS), EXPECTED_OPINIONS_HASH, "opinion fixture hash")
    assert_equal(digest(CASES), EXPECTED_CASES_HASH, "case fixture hash")

    opinion_ids = {row["opinionId"] for row in opinions}
    case_ids = {row["caseId"] for row in cases}
    assert_equal(opinion_ids, EXPECTED_IDS, "opinion IDs")
    assert_equal(case_ids, EXPECTED_IDS, "case IDs")
    if len(opinions) != len(opinion_ids) or len(cases) != len(case_ids):
        raise AssertionError("duplicate opinion or case ID")

    by_opinion = {row["opinionId"]: row for row in opinions}
    by_case = {row["caseId"]: row for row in cases}
    for identifier in EXPECTED_IDS:
        case = by_case[identifier]
        if case["opinionId"] != identifier:
            raise AssertionError(f"case/opinion mismatch: {identifier}")
        if EXPECTED_OPINIONS_HASH not in case["sourceHashes"]:
            raise AssertionError(f"case is not bound to frozen opinions: {identifier}")
        opinion = by_opinion[identifier]
        if opinion["sourceMode"] != "missing" and not opinion["provenance"]:
            raise AssertionError(f"opinion provenance is missing: {identifier}")
        if case["privateOpinionAvailableToDirect"] is not False:
            raise AssertionError(f"Direct leaks the private opinion: {identifier}")

    assert_equal(
        by_case["management.d0.evidence-dominant-same-p"]["expected"]["projectedProbability"],
        by_case["management.d0.prior-dominant-same-p"]["expected"]["projectedProbability"],
        "equal-projection 0.85 fixture",
    )
    low_base = by_case["management.d0.low-base-rate"]["expected"]
    high_base = by_case["management.d0.high-base-rate"]["expected"]
    for key in ("belief", "disbelief", "uncertainty"):
        assert_equal(low_base["opinion"][key], high_base["opinion"][key], f"same-bdu {key}")
    if low_base["projectedProbability"] == high_base["projectedProbability"]:
        raise AssertionError("base-rate contrast must change projected probability")
    low_conflict = by_case["management.d0.low-conflict-same-p"]["expected"]
    high_conflict = by_case["management.d0.high-conflict-same-p"]["expected"]
    assert_equal(low_conflict["opinion"], high_conflict["opinion"], "same-opinion conflict pair")
    assert_equal(
        low_conflict["projectedProbability"],
        high_conflict["projectedProbability"],
        "same-projection conflict pair",
    )
    if low_conflict["conflictIndex"] == high_conflict["conflictIndex"]:
        raise AssertionError("conflict contrast is not distinct")

    answer = by_opinion["management.d0.answer-profile-evidence-counts"]
    if answer["level"] != "answer" or answer["sourceMode"] != "evidence-counts":
        raise AssertionError("answer-level evidence-count fixture is malformed")
    if not answer.get("aggregationPolicyId"):
        raise AssertionError("answer-level fixture has no declared aggregation policy")

    print("DSL-D0 opinion contract passed")
    print(f"Opinions: {len(opinions)}")
    print(f"Cases: {len(cases)}")
    print(f"Opinions hash: {digest(OPINIONS)}")
    print(f"Cases hash: {digest(CASES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
