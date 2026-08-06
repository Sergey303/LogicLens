#!/usr/bin/env python3
"""Verify the hash-frozen synthetic semantic kernel and its independent D2 oracle."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
RUNTIME_PATH = ROOT / "runtime.py"
SCHEMA_PATH = ROOT / "case-v0.schema.json"
CASES_PATH = ROOT / "synthetic-cases-v0.jsonl"
EXPECTED_PATH = ROOT / "expected-frames-v0.jsonl"
MANIFEST_PATH = ROOT / "manifest-v0.json"
D2_RUNTIME_PATH = ROOT.parent / "opinion-d2" / "runtime.py"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument(
        "--skip-prolog",
        action="store_true",
        help="Local syntax/debug escape hatch only; CI and acceptance must not use it.",
    )
    return parser.parse_args()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def schema_errors(validator: Draft202012Validator, value: Any) -> list[str]:
    return [
        f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    ]


def assert_schema_rejects(
    validator: Draft202012Validator, value: dict[str, Any], label: str
) -> None:
    if not schema_errors(validator, value):
        raise AssertionError(f"schema accepted adversarial case: {label}")


def assert_runtime_rejects(runtime: Any, value: dict[str, Any], label: str) -> None:
    try:
        runtime.evaluate_case(value)
    except runtime.CoreError:
        return
    raise AssertionError(f"runtime accepted adversarial case: {label}")


def rational_frame(value: Any) -> dict[str, int]:
    fraction = Fraction(str(value))
    return {"numerator": fraction.numerator, "denominator": fraction.denominator}


def d2_bundle(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": "0.1",
        "fusionId": case["caseId"],
        "proposition": case["caseId"],
        "opinionSubjectLevel": case["opinionSubjectLevel"],
        "priorWeight": rational_frame(case["priorWeight"]),
        "reports": [
            {
                "reportId": report["reportId"],
                "dependencyGroup": report["dependencyGroup"],
                "positiveEvidence": rational_frame(report["positiveEvidence"]),
                "negativeEvidence": rational_frame(report["negativeEvidence"]),
                "baseRate": rational_frame(report["baseRate"]),
                "provenance": report["provenance"],
            }
            for report in case["reports"]
        ],
    }


def verify_manifest() -> dict[str, Any]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("artifactClass") != "synthetic-semantic-kernel":
        raise AssertionError("manifest artifact class mismatch")
    if manifest.get("courseDataIncluded") is not False:
        raise AssertionError("synthetic kernel must not claim course data")
    if manifest.get("sourceRepository") is not None:
        raise AssertionError("synthetic kernel must not bind an external source repository")
    expected_paths = {
        "runtime.py": RUNTIME_PATH,
        "case-v0.schema.json": SCHEMA_PATH,
        "synthetic-cases-v0.jsonl": CASES_PATH,
        "expected-frames-v0.jsonl": EXPECTED_PATH,
    }
    if set(manifest.get("files", {})) != set(expected_paths):
        raise AssertionError("manifest file set mismatch")
    for name, path in expected_paths.items():
        actual = sha256(path)
        expected = manifest["files"][name]
        if actual != expected:
            raise AssertionError(f"hash drift for {name}: expected {expected}, got {actual}")
    return manifest


def verify_adversarial(
    runtime: Any,
    validator: Draft202012Validator,
    rows_by_id: dict[str, dict[str, Any]],
) -> None:
    malformed = copy.deepcopy(rows_by_id["synthetic.d2.dependent"])
    malformed["reports"][0]["positiveEvidence"] = "1/2.3"
    assert_schema_rejects(validator, malformed, "malformed rational 1/2.3")

    negative = copy.deepcopy(rows_by_id["synthetic.d2.dependent"])
    negative["reports"][0]["positiveEvidence"] = -1
    assert_schema_rejects(validator, negative, "negative evidence")

    out_of_range = copy.deepcopy(rows_by_id["synthetic.d2.dependent"])
    out_of_range["reports"][0]["baseRate"] = "1.1"
    assert_schema_rejects(validator, out_of_range, "base rate above one")

    missing_provenance = copy.deepcopy(rows_by_id["synthetic.d2.dependent"])
    del missing_provenance["reports"][0]["provenance"]
    assert_schema_rejects(validator, missing_provenance, "missing report provenance")

    missing_dependency = copy.deepcopy(rows_by_id["synthetic.d2.dependent"])
    del missing_dependency["reports"][0]["dependencyGroup"]
    assert_schema_rejects(validator, missing_dependency, "missing dependency metadata")

    duplicate_reports = copy.deepcopy(rows_by_id["synthetic.d2.dependent"])
    duplicate_reports["reports"][1]["reportId"] = duplicate_reports["reports"][0]["reportId"]
    if schema_errors(validator, duplicate_reports):
        raise AssertionError("duplicate report test must reach runtime identity check")
    assert_runtime_rejects(runtime, duplicate_reports, "duplicate reportId")

    duplicate_premises = copy.deepcopy(rows_by_id["synthetic.b.all-supported"])
    duplicate_premises["premises"][1]["premiseId"] = duplicate_premises["premises"][0]["premiseId"]
    if schema_errors(validator, duplicate_premises):
        raise AssertionError("duplicate premise test must reach runtime identity check")
    assert_runtime_rejects(runtime, duplicate_premises, "duplicate premiseId")

    cross_stance = copy.deepcopy(rows_by_id["synthetic.a.conflicting"])
    cross_stance["opposeEvidence"][0]["evidenceId"] = cross_stance["supportEvidence"][0]["evidenceId"]
    if schema_errors(validator, cross_stance):
        raise AssertionError("cross-stance duplicate test must reach runtime identity check")
    assert_runtime_rejects(runtime, cross_stance, "evidence reused across stances")

    unit_mismatch = copy.deepcopy(rows_by_id["synthetic.c.point-supported"])
    unit_mismatch["threshold"]["unit"] = "percent"
    if schema_errors(validator, unit_mismatch):
        raise AssertionError("unit mismatch test must reach runtime dimension check")
    assert_runtime_rejects(runtime, unit_mismatch, "numeric unit dimension mismatch")


def main() -> int:
    args = arguments()
    if args.timeout_seconds < 1 or args.timeout_seconds > 300:
        raise AssertionError("timeout must be between 1 and 300 seconds")

    manifest = verify_manifest()
    runtime = load_module("synthetic_semantic_kernel_v0", RUNTIME_PATH)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    rows = jsonl(CASES_PATH)
    expected_rows = jsonl(EXPECTED_PATH)

    ids = [row["caseId"] for row in rows]
    if len(ids) != len(set(ids)):
        raise AssertionError("duplicate case IDs")
    if len(rows) != manifest["expectedCaseCount"]:
        raise AssertionError("case count does not match manifest")
    expected_by_id = {row["caseId"]: row for row in expected_rows}
    if set(ids) != set(expected_by_id):
        raise AssertionError("expected frame case set mismatch")

    for row in rows:
        errors = schema_errors(validator, row)
        if errors:
            raise AssertionError(f"{row.get('caseId')}: schema failure: {'; '.join(errors[:10])}")

    frames = {row["caseId"]: runtime.evaluate_case(row) for row in rows}
    repeated = {row["caseId"]: runtime.evaluate_case(row) for row in rows}
    if frames != repeated:
        raise AssertionError("synthetic kernel is not deterministic")
    if len({frame["inputHash"] for frame in frames.values()}) != len(frames):
        raise AssertionError("input hashes are not unique")

    for case_id, frame in frames.items():
        if frame != expected_by_id[case_id]:
            raise AssertionError(f"expected-frame drift for {case_id}")
        flags = frame["runtime"]
        if not flags["syntheticKernel"] or flags["trustedPackageVerified"]:
            raise AssertionError(f"{case_id}: trusted-package claim boundary violated")
        if flags["weakModelPerformsArithmetic"]:
            raise AssertionError(f"{case_id}: weak model arithmetic boundary violated")
        if flags["unknownIsFalse"] or flags["conflictCollapsed"]:
            raise AssertionError(f"{case_id}: strict epistemic distinctions collapsed")

    strict_statuses = {
        frames[case_id]["status"]
        for case_id in (
            "synthetic.a.supported",
            "synthetic.a.unknown",
            "synthetic.a.refuted",
            "synthetic.a.conflicting",
        )
    }
    if strict_statuses != {"supported", "unknown", "refuted", "conflicting"}:
        raise AssertionError("strict status coverage is incomplete")

    rows_by_id = {row["caseId"]: row for row in rows}
    verify_adversarial(runtime, validator, rows_by_id)

    d2_runtime = load_module("epistemic_d2_reference", D2_RUNTIME_PATH)
    compare_fields = (
        "opinionSubjectLevel",
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
        "provenance",
    )
    for case_id in (
        "synthetic.d2.dependent",
        "synthetic.d2.independent",
        "synthetic.d2.incompatible-base-rates",
        "synthetic.d2.conflict",
    ):
        legacy_frame = d2_runtime.build_frame(
            d2_bundle(rows_by_id[case_id]),
            reports_hash=manifest["files"]["synthetic-cases-v0.jsonl"],
            swipl=args.swipl,
            timeout_seconds=args.timeout_seconds,
            skip_prolog=args.skip_prolog,
        )
        core_frame = frames[case_id]
        for field in compare_fields:
            if core_frame.get(field) != legacy_frame.get(field):
                raise AssertionError(
                    f"{case_id}: synthetic/D2 drift in {field}: "
                    f"synthetic={core_frame.get(field)!r} d2={legacy_frame.get(field)!r}"
                )
        if not args.skip_prolog and not legacy_frame["runtime"]["verifiedAgainstPrologKernel"]:
            raise AssertionError(f"{case_id}: SWI-Prolog verification was not recorded")

    if args.skip_prolog:
        print("WARNING: SWI-Prolog verification skipped; this run is not acceptance evidence")
    else:
        print("Independent SWI-Prolog D2 verification passed")
    print("Synthetic Epistemic semantic-kernel contract passed")
    print(f"Cases: {len(frames)}")
    print(f"Manifest: {sha256(MANIFEST_PATH)}")
    for case_id in sorted(frames):
        frame = frames[case_id]
        outcome = frame.get("status", frame.get("conclusion"))
        print(f"{case_id}: {frame['dslLevel']} -> {outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
