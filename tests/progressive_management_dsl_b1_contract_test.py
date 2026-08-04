#!/usr/bin/env python3
"""Freeze and validate the non-guessable management DSL-B1 tranche."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "EpistemicCompilerLab" / "progressive-dsl" / "management-course"
CASE_SCHEMA = ROOT / "contracts" / "progressive-epistemic-case-v0.schema.json"
RULE_SCHEMA = ROOT / "contracts" / "epistemic-logical-rule-v0.schema.json"
CASES = BASE / "cases-dsl-b1-v0.jsonl"
RULES = BASE / "dsl-b1-logical-rules-v0.jsonl"

EXPECTED_CASE_SHA256 = "sha256:83f5f582aaf49e49690c64a730335ac8dae45f40e5ed92d1224f5562b6aae552"
EXPECTED_RULE_SHA256 = "sha256:828c4cb274cc48a7149ea8138c9c0a67131f550e46934f9439c73de92400b7eb"
EXPECTED_CASE_IDS = {
    "management.b1.northstar-project-governance-refuted",
    "management.b1.northstar-delivery-two-hop",
    "management.b1.northstar-technical-risk-conflict",
    "management.b1.northstar-backlog-any",
    "management.b1.northstar-team-health-not-explicit",
    "management.b1.northstar-product-value-unknown-control",
}
EXPECTED_DSL_B_STATUSES = {
    "supported": 3,
    "refuted": 1,
    "conflicting": 1,
    "unknown": 1,
}


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


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate_rows(
    rows: list[dict[str, Any]],
    schema: dict[str, Any],
    label: str,
) -> None:
    validator = Draft202012Validator(schema)
    for index, row in enumerate(rows, 1):
        errors = sorted(validator.iter_errors(row), key=lambda item: list(item.path))
        if errors:
            details = "; ".join(
                f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
                for error in errors[:10]
            )
            raise AssertionError(f"{label} {index} schema failure: {details}")


def main() -> int:
    cases = load_jsonl(CASES)
    rules = load_jsonl(RULES)
    validate_rows(cases, load_json(CASE_SCHEMA), "case")
    validate_rows(rules, load_json(RULE_SCHEMA), "rule")

    if digest(CASES) != EXPECTED_CASE_SHA256:
        raise AssertionError(f"DSL-B1 cases changed: {digest(CASES)}")
    if digest(RULES) != EXPECTED_RULE_SHA256:
        raise AssertionError(f"DSL-B1 rules changed: {digest(RULES)}")

    case_ids = {row["caseId"] for row in cases}
    if case_ids != EXPECTED_CASE_IDS:
        raise AssertionError(
            f"DSL-B1 case IDs changed: expected={sorted(EXPECTED_CASE_IDS)} actual={sorted(case_ids)}"
        )

    statuses: dict[str, int] = {}
    for case in cases:
        if case["minimumDslLevel"] != "DSL-B":
            raise AssertionError(f"non-DSL-B case in B1 tranche: {case['caseId']}")
        expected_a = case["expectedByLevel"]["DSL-A"]
        expected_b = case["expectedByLevel"]["DSL-B"]
        if expected_a["status"] != "unknown":
            raise AssertionError(f"DSL-A control must remain unknown: {case['caseId']}")
        status = expected_b["status"]
        statuses[status] = statuses.get(status, 0) + 1
        if case["publicContext"].get("policyTextAvailableToDirect") is not False:
            raise AssertionError(f"B1 Direct condition leaks policy text: {case['caseId']}")
        if EXPECTED_RULE_SHA256 not in case["sourceHashes"]:
            raise AssertionError(f"B1 rules hash is not bound to case: {case['caseId']}")

    if statuses != EXPECTED_DSL_B_STATUSES:
        raise AssertionError(
            f"DSL-B status distribution changed: expected={EXPECTED_DSL_B_STATUSES} actual={statuses}"
        )

    rule_ids = [rule["ruleId"] for rule in rules]
    if len(rule_ids) != 7 or len(rule_ids) != len(set(rule_ids)):
        raise AssertionError("DSL-B1 must contain seven unique rules")
    if any(rule["generalisability"] != "local" for rule in rules):
        raise AssertionError("every DSL-B1 policy rule must remain local")

    any_rules = [rule for rule in rules if "any" in rule["body"]]
    not_explicit_rules = [
        rule
        for rule in rules
        if any("notExplicit" in condition for condition in rule["body"].get("all", []))
    ]
    if len(any_rules) != 1:
        raise AssertionError("DSL-B1 must exercise exactly one any rule")
    if len(not_explicit_rules) != 1:
        raise AssertionError("DSL-B1 must exercise exactly one notExplicit rule")

    technical_risk_heads = [
        rule
        for rule in rules
        if rule["head"]["target"]
        == {
            "predicate": "may_delegate",
            "arguments": ["role.cto", "outcome.technical_risk", "role.team_lead"],
        }
    ]
    if {rule["head"]["stance"] for rule in technical_risk_heads} != {"support", "oppose"}:
        raise AssertionError("DSL-B1 technical-risk conflict fixture is incomplete")

    intermediate_target = {
        "predicate": "contributes_to",
        "arguments": ["role.cto", "outcome.delivery_commitments"],
    }
    if not any(rule["head"]["target"] == intermediate_target for rule in rules):
        raise AssertionError("DSL-B1 intermediate derived claim is missing")
    if not any(
        any(condition.get("claim") == intermediate_target for condition in rule["body"].get("all", []))
        for rule in rules
    ):
        raise AssertionError("DSL-B1 two-hop consumer rule is missing")

    print("Progressive management DSL-B1 contract passed")
    print(f"Cases: {len(cases)}")
    print(f"Rules: {len(rules)}")
    print(f"DSL-B statuses: {json.dumps(statuses, sort_keys=True)}")
    print(f"Cases hash: {digest(CASES)}")
    print(f"Rules hash: {digest(RULES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
