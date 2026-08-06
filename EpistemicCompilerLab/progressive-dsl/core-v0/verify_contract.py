#!/usr/bin/env python3
"""Verify the experimental Epistemic DSL core on frozen CTO-course cases."""
from __future__ import annotations

import importlib.util
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
RUNTIME_PATH = ROOT / "runtime.py"
SCHEMA_PATH = ROOT / "case-v0.schema.json"
CASES_PATH = ROOT / "management-course-cases-v0.jsonl"
D2_RUNTIME_PATH = ROOT.parent / "opinion-d2" / "runtime.py"
EXPECTED = {
    "management.core.a.cto-strategy": {"dslLevel": "DSL-A", "status": "supported"},
    "management.core.a.pm-backlog-unknown": {
        "dslLevel": "DSL-A",
        "status": "unknown",
        "withholdsAssertiveDecision": True,
    },
    "management.core.b.cto-risk-escalation": {
        "dslLevel": "DSL-B",
        "status": "supported",
        "withholdsAssertiveDecision": False,
    },
    "management.core.c.availability-boundary": {
        "dslLevel": "DSL-C",
        "status": "unknown",
        "withholdsAssertiveDecision": True,
    },
    "management.core.d2.dependent-duplicates": {
        "dslLevel": "DSL-D2",
        "conclusion": "qualified_uncertain",
        "operatorPlan": "average_within_group",
        "exactPositiveEvidence": "4",
    },
    "management.core.d2.independent-corroboration": {
        "dslLevel": "DSL-D2",
        "conclusion": "assert_with_evidence",
        "operatorPlan": "cumulative_across_groups",
        "exactPositiveEvidence": "8",
    },
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rational_frame(value: Any) -> dict[str, int]:
    fraction = Fraction(str(value))
    return {"numerator": fraction.numerator, "denominator": fraction.denominator}


def d2_bundle(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "fusionId": case["caseId"],
        "proposition": case["caseId"],
        "opinionSubjectLevel": "claim",
        "priorWeight": rational_frame(case["priorWeight"]),
        "reports": [
            {
                "reportId": report["reportId"],
                "dependencyGroup": report["dependencyGroup"],
                "positiveEvidence": rational_frame(report["positiveEvidence"]),
                "negativeEvidence": rational_frame(report["negativeEvidence"]),
                "baseRate": rational_frame(report["baseRate"]),
                "provenance": [f"management-course:{report['reportId']}"],
            }
            for report in case["reports"]
        ],
    }


def main() -> int:
    runtime = load_module("epistemic_core_v0", RUNTIME_PATH)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    rows = [
        json.loads(line)
        for line in CASES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    ids = [row["caseId"] for row in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(EXPECTED):
        raise AssertionError("frozen core case set mismatch")

    for row in rows:
        errors = sorted(validator.iter_errors(row), key=lambda error: list(error.path))
        if errors:
            details = "; ".join(
                f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
                for error in errors[:10]
            )
            raise AssertionError(f"{row.get('caseId')}: schema failure: {details}")

    frames = {row["caseId"]: runtime.evaluate_case(row) for row in rows}
    repeated = {row["caseId"]: runtime.evaluate_case(row) for row in rows}
    if frames != repeated:
        raise AssertionError("core runtime is not deterministic")
    if len({frame["inputHash"] for frame in frames.values()}) != len(frames):
        raise AssertionError("core input hashes are not unique across the frozen cases")

    for case_id, expected in EXPECTED.items():
        frame = frames[case_id]
        for field, value in expected.items():
            if frame.get(field) != value:
                raise AssertionError(
                    f"{case_id}: expected {field}={value!r}, got {frame.get(field)!r}"
                )
        if frame["runtime"]["weakModelPerformsArithmetic"]:
            raise AssertionError(f"{case_id}: weak model arithmetic boundary violated")
        if frame["runtime"]["unknownIsFalse"]:
            raise AssertionError(f"{case_id}: unknown collapsed to false")
        if frame["runtime"]["conflictCollapsed"]:
            raise AssertionError(f"{case_id}: conflict collapse enabled")

    dependent = frames["management.core.d2.dependent-duplicates"]
    independent = frames["management.core.d2.independent-corroboration"]
    if dependent["exactPositiveEvidence"] == independent["exactPositiveEvidence"]:
        raise AssertionError("dependency metadata did not change effective evidence")
    if dependent["exactOpinion"]["belief"] != "2/3":
        raise AssertionError("dependent duplicate opinion mismatch")
    if independent["exactOpinion"]["belief"] != "4/5":
        raise AssertionError("independent corroboration opinion mismatch")

    if D2_RUNTIME_PATH.exists():
        d2_runtime = load_module("epistemic_d2_reference", D2_RUNTIME_PATH)
        rows_by_id = {row["caseId"]: row for row in rows}
        for case_id in (
            "management.core.d2.dependent-duplicates",
            "management.core.d2.independent-corroboration",
        ):
            legacy_frame, _ = d2_runtime.compute(d2_bundle(rows_by_id[case_id]))
            core_frame = frames[case_id]
            for field in (
                "operatorPlan",
                "exactPositiveEvidence",
                "exactNegativeEvidence",
                "exactOpinion",
                "exactProjectedProbability",
                "exactConflictIndex",
                "conclusion",
                "action",
                "withholdsAssertiveDecision",
                "implicitFusionPerformed",
            ):
                if core_frame[field] != legacy_frame[field]:
                    raise AssertionError(
                        f"{case_id}: core/D2 drift in {field}: "
                        f"core={core_frame[field]!r} d2={legacy_frame[field]!r}"
                    )

    print("Experimental Epistemic DSL core CTO-course contract passed")
    print(f"Cases: {len(frames)}")
    for case_id in sorted(frames):
        frame = frames[case_id]
        outcome = frame.get("status", frame.get("conclusion"))
        print(f"{case_id}: {frame['dslLevel']} -> {outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
