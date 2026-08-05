#!/usr/bin/env python3
"""Freeze and validate the management DSL-C typed-observation tranche."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "EpistemicCompilerLab" / "progressive-dsl" / "management-course"
CASE_SCHEMA = ROOT / "contracts" / "progressive-epistemic-case-v0.schema.json"
OBSERVATION_SCHEMA = ROOT / "contracts" / "epistemic-observation-v0.schema.json"
CASES = BASE / "cases-dsl-c-v0.jsonl"
OBSERVATIONS = BASE / "dsl-c-observations-v0.jsonl"

EXPECTED_CASE_SHA256 = "sha256:3996d549c8bd1af1846f76ac78e5f507150aff67a8844599510d0b9493277a32"
EXPECTED_OBSERVATION_SHA256 = "sha256:8e7f6e0c6d0ecfab5074a7f4b4140b79ff1fab48cd8fd5425fd62a15c815b8ae"
EXPECTED_CASE_IDS = {
    "management.c.northstar-lead-time-supported",
    "management.c.northstar-mttr-refuted",
    "management.c.northstar-change-failure-overlap",
    "management.c.northstar-availability-supported",
    "management.c.northstar-budget-variance-refuted",
    "management.c.northstar-deployment-normal-unknown",
    "management.c.northstar-sev1-between-supported",
    "management.c.northstar-predictability-overlap",
    "management.c.northstar-missing-observation",
}
EXPECTED_STATUSES = {
    "supported": 3,
    "refuted": 2,
    "unknown": 4,
}
MISSING_CASE = "management.c.northstar-missing-observation"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON object expected: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        1,
    ):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise AssertionError(f"JSON object expected: {path}:{line_number}")
        rows.append(value)
    return rows


def canonical_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    try:
        raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AssertionError(f"frozen file is not UTF-8: {path}") from exc
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(path)).hexdigest()


def raw_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def assert_frozen(path: Path, expected: str, label: str) -> str:
    actual = digest(path)
    if actual != expected:
        raise AssertionError(
            f"{label} changed\n"
            f"path: {path.relative_to(ROOT)}\n"
            f"expected canonical UTF-8/LF: {expected}\n"
            f"actual canonical UTF-8/LF:   {actual}\n"
            f"actual checkout bytes:       {raw_digest(path)}"
        )
    return actual


def validate_rows(
    rows: list[dict[str, Any]],
    schema: dict[str, Any],
    label: str,
) -> None:
    validator = Draft202012Validator(schema)
    for index, row in enumerate(rows, 1):
        errors = sorted(
            validator.iter_errors(row),
            key=lambda item: list(item.path),
        )
        if errors:
            details = "; ".join(
                f"{'/'.join(str(part) for part in error.path) or '<root>'}: "
                f"{error.message}"
                for error in errors[:10]
            )
            raise AssertionError(f"{label} {index} schema failure: {details}")


def target_key(target: dict[str, Any]) -> str:
    return json.dumps(
        target,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def main() -> int:
    cases = load_jsonl(CASES)
    observations = load_jsonl(OBSERVATIONS)
    validate_rows(cases, load_json(CASE_SCHEMA), "case")
    validate_rows(observations, load_json(OBSERVATION_SCHEMA), "observation")

    cases_hash = assert_frozen(CASES, EXPECTED_CASE_SHA256, "DSL-C cases")
    observations_hash = assert_frozen(
        OBSERVATIONS,
        EXPECTED_OBSERVATION_SHA256,
        "DSL-C observations",
    )

    case_ids = [row["caseId"] for row in cases]
    if len(case_ids) != len(set(case_ids)):
        raise AssertionError("duplicate DSL-C case ID")
    if set(case_ids) != EXPECTED_CASE_IDS:
        raise AssertionError(
            f"DSL-C case IDs changed: expected={sorted(EXPECTED_CASE_IDS)} "
            f"actual={sorted(case_ids)}"
        )

    observation_ids = [row["observationId"] for row in observations]
    if len(observation_ids) != len(set(observation_ids)):
        raise AssertionError("duplicate DSL-C observation ID")
    observation_targets = {
        target_key(row["target"]): row
        for row in observations
    }
    if len(observation_targets) != len(observations):
        raise AssertionError("duplicate DSL-C observation target")

    model_counts: dict[str, int] = {}
    for row in observations:
        kind = row["model"]["kind"]
        model_counts[kind] = model_counts.get(kind, 0) + 1
        if row["generalisability"] != "local":
            raise AssertionError("every DSL-C fixture must remain local")
        if row["provenance"][0].split("#", 1)[0] != "northstar-kpi-snapshot-c0":
            raise AssertionError("DSL-C observation provenance changed")
    if model_counts != {"point": 3, "bounded": 4, "normal": 1}:
        raise AssertionError(f"observation model distribution changed: {model_counts}")

    statuses: dict[str, int] = {}
    seen_between = False
    seen_cross_unit = False
    seen_normal_unknown = False
    for case in cases:
        if case["minimumDslLevel"] != "DSL-C":
            raise AssertionError(f"non-DSL-C case in tranche: {case['caseId']}")
        if case["publicContext"].get("measurementTextAvailableToDirect") is not False:
            raise AssertionError(f"Direct condition leaks measurement: {case['caseId']}")
        if EXPECTED_OBSERVATION_SHA256 not in case["sourceHashes"]:
            raise AssertionError(f"observation hash is not bound: {case['caseId']}")

        expected_b = case["expectedByLevel"]["DSL-B"]
        if expected_b["status"] != "unknown":
            raise AssertionError(f"DSL-B baseline must be unknown: {case['caseId']}")
        expected_c = case["expectedByLevel"]["DSL-C"]
        status = expected_c["status"]
        statuses[status] = statuses.get(status, 0) + 1

        queries = case["goldQueries"]
        if len(queries) != 1 or queries[0]["operation"] != "numeric-comparison":
            raise AssertionError(f"case must have one numeric query: {case['caseId']}")
        target = queries[0]["target"]
        key = target_key(target)
        if case["caseId"] == MISSING_CASE:
            if key in observation_targets:
                raise AssertionError("missing-observation control unexpectedly has data")
        elif key not in observation_targets:
            raise AssertionError(f"case has no observation: {case['caseId']}")

        comparison = queries[0]["comparison"]
        seen_between = seen_between or comparison["operator"] == "between"
        if key in observation_targets:
            source_unit = observation_targets[key]["model"]["unit"]
            seen_cross_unit = seen_cross_unit or source_unit != comparison["unit"]
            seen_normal_unknown = seen_normal_unknown or (
                observation_targets[key]["model"]["kind"] == "normal"
                and status == "unknown"
            )

    if statuses != EXPECTED_STATUSES:
        raise AssertionError(
            f"DSL-C status distribution changed: "
            f"expected={EXPECTED_STATUSES} actual={statuses}"
        )
    if not seen_between:
        raise AssertionError("DSL-C tranche does not exercise between")
    if not seen_cross_unit:
        raise AssertionError("DSL-C tranche does not exercise unit conversion")
    if not seen_normal_unknown:
        raise AssertionError("normal observation is not preserved as unknown")

    print("Progressive management DSL-C contract passed")
    print(f"Cases: {len(cases)}")
    print(f"Observations: {len(observations)}")
    print(f"Models: {json.dumps(model_counts, sort_keys=True)}")
    print(f"DSL-C statuses: {json.dumps(statuses, sort_keys=True)}")
    print(f"Cases hash: {cases_hash}")
    print(f"Observations hash: {observations_hash}")
    print(f"Checkout cases bytes hash: {raw_digest(CASES)}")
    print(f"Checkout observations bytes hash: {raw_digest(OBSERVATIONS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
