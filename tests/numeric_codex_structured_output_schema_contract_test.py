#!/usr/bin/env python3
"""Verify the numeric Codex response schema stays in the strict output subset."""
from __future__ import annotations

import json
from pathlib import Path

from codex_structured_output_schema_contract_test import validate_node

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (
    ROOT
    / "contracts"
    / "progressive-management-numeric-codex-response-v0.schema.json"
)

EXPECTED_FIELDS = {
    "schemaVersion",
    "answer",
    "epistemicStatus",
    "action",
    "abstain",
    "usedVerifiedFrame",
    "usedRawObservation",
    "observationId",
    "modelKind",
    "comparisonOperator",
    "baseUnit",
    "normalizedPoint",
    "normalizedLower",
    "normalizedUpper",
    "normalizedMean",
    "normalizedStandardDeviation",
    "normalizedThresholdValue",
    "normalizedThresholdLower",
    "normalizedThresholdUpper",
    "preservedInterval",
    "preservedDistribution",
    "introducedProbabilityPolicy",
    "interpretationFlags",
    "warnings",
    "scopeStatement",
}


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validate_node(schema, "root")
    actual = set(schema["properties"])
    if actual != EXPECTED_FIELDS:
        raise AssertionError(
            f"numeric response fields changed: "
            f"expected={sorted(EXPECTED_FIELDS)} actual={sorted(actual)}"
        )
    if set(schema["required"]) != EXPECTED_FIELDS:
        raise AssertionError("every numeric response field must remain required")
    print("Numeric Codex structured-output schema contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
