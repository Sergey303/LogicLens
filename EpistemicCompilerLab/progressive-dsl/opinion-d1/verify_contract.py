#!/usr/bin/env python3
"""Freeze and validate DSL-D1 exact-rational boundary fixtures."""
from __future__ import annotations

import hashlib
import importlib.util
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
EXPECTED_OPINIONS_HASH = "sha256:efa8664833f621bfca077c26f73c926782b3275be9b369678b47b0da8d359e6f"
EXPECTED_CASES_HASH = "sha256:f2efb45fabb580d76e30ae376b8740478fbb3b63b3d11b375954965eac222947"


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
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise AssertionError(f"JSON object expected: {path}:{number}")
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
    def visit(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            return
        if "const" in node and "type" not in node:
            raise AssertionError(f"provider schema const lacks type: {path}")
        if node.get("type") == "object":
            if node.get("additionalProperties") is not False:
                raise AssertionError(f"provider object must close properties: {path}")
            props = node.get("properties")
            required = node.get("required")
            if not isinstance(props, dict) or set(required or []) != set(props):
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


def load_runtime():
    spec = importlib.util.spec_from_file_location("dsl_d1_runtime", ROOT / "runtime.py")
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load DSL-D1 runtime")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    opinions = load_jsonl(OPINIONS)
    cases = load_jsonl(CASES)
    validate_rows(opinions, load_json(OPINION_SCHEMA), "opinion")
    validate_rows(cases, load_json(CASE_SCHEMA), "case")
    validate_provider_schema(load_json(RESPONSE_SCHEMA))

    if digest(OPINIONS) != EXPECTED_OPINIONS_HASH:
        raise AssertionError(
            f"opinions hash mismatch: expected={EXPECTED_OPINIONS_HASH} actual={digest(OPINIONS)}"
        )
    if digest(CASES) != EXPECTED_CASES_HASH:
        raise AssertionError(
            f"cases hash mismatch: expected={EXPECTED_CASES_HASH} actual={digest(CASES)}"
        )

    opinion_ids = {row["opinionId"] for row in opinions}
    case_ids = {row["caseId"] for row in cases}
    if opinion_ids != case_ids or len(opinion_ids) != 11:
        raise AssertionError("expected 11 unique matched opinion/case IDs")

    by_opinion = {row["opinionId"]: row for row in opinions}
    runtime = load_runtime()
    frames = {}
    for case in cases:
        if EXPECTED_OPINIONS_HASH not in case["sourceHashes"]:
            raise AssertionError(
                f"case is not bound to frozen opinions: {case['caseId']}"
            )
        fixture = by_opinion[case["opinionId"]]
        frame = runtime.build_frame(
            fixture,
            opinions_hash=EXPECTED_OPINIONS_HASH,
            skip_prolog=True,
        )
        frames[case["caseId"]] = frame
        expected = case["expected"]
        for key, frame_key in (
            ("exactConclusion", "exactConclusion"),
            ("exactAction", "exactAction"),
            ("exactWithholdsAssertiveDecision", "exactWithholdsAssertiveDecision"),
            ("roundedConclusion", "roundedConclusion"),
            ("roundedAction", "roundedAction"),
            ("roundedWithholdsAssertiveDecision", "roundedWithholdsAssertiveDecision"),
            ("roundedProjectedProbability", "roundedProjectedProbability"),
        ):
            if expected[key] != frame[frame_key]:
                raise AssertionError(
                    f"frozen expectation mismatch {case['caseId']} {key}: "
                    f"expected={expected[key]!r} frame={frame[frame_key]!r}"
                )
        actual_exact_p = ""
        if frame["exactProjectedProbability"] is not None:
            actual_exact_p = (
                f"{frame['exactProjectedProbability']['numerator']}/"
                f"{frame['exactProjectedProbability']['denominator']}"
            )
        if expected["exactProjectedProbability"] != actual_exact_p:
            raise AssertionError(f"exact projection mismatch: {case['caseId']}")
        if expected["roundingChangesConclusion"] != (
            frame["exactConclusion"] != frame["roundedConclusion"]
        ):
            raise AssertionError(f"rounding-change flag mismatch: {case['caseId']}")

    pairs = {
        "p-boundary": ("management.d1.p-below", "management.d1.p-above"),
        "uncertainty-boundary": ("management.d1.u-below", "management.d1.u-above"),
        "conflict-boundary": (
            "management.d1.conflict-below",
            "management.d1.conflict-above",
        ),
        "belief-boundary": (
            "management.d1.belief-below",
            "management.d1.belief-above",
        ),
    }
    for name, (left_id, right_id) in pairs.items():
        left = frames[left_id]
        right = frames[right_id]
        if left["exactConclusion"] == right["exactConclusion"]:
            raise AssertionError(f"exact pair is not distinguished: {name}")
        if left["roundedConclusion"] != right["roundedConclusion"]:
            raise AssertionError(f"rounded pair unexpectedly distinguished: {name}")

    answer = frames["management.d1.answer-repeating"]
    if answer["exactProjectedProbability"] != {"numerator": 3, "denominator": 4}:
        raise AssertionError("answer-level exact p must be 3/4")
    if answer["roundedInvariantPreserved"] is not False:
        raise AssertionError("answer-level rounded invariant drift was not preserved")

    rounded_only = frames["management.d1.rounded-only-control"]
    if rounded_only["exactConclusion"] != "request_exact_opinion":
        raise AssertionError("rounded-only control must request exact opinion")

    forbidden_question_tokens = (
        "p=0.75",
        "ниже границы",
        "выше границы",
        "высокий конфликт",
        "низкий конфликт",
        "high conflict",
        "prior-dominant",
    )
    for case in cases:
        lower = case["question"].lower()
        if any(token.lower() in lower for token in forbidden_question_tokens):
            raise AssertionError(f"question leaks boundary label: {case['caseId']}")

    print("DSL-D1 exact-rational contract passed")
    print(f"Opinions: {len(opinions)}")
    print(f"Cases: {len(cases)}")
    print(f"Opinions hash: {digest(OPINIONS)}")
    print(f"Cases hash: {digest(CASES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
