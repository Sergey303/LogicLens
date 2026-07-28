#!/usr/bin/env python3
"""Create and verify human review records for passed Builder candidates.

This tool never activates a candidate and never changes an active epoch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from active_epoch.hashing import canonical_json_bytes


UTF8 = "utf-8"
REVIEW_HASH_DOMAIN = b"LogicLensCandidateReview\0"
REVIEW_HASH_VERSION = bytes((1,))
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
REQUIRED_COMPARISON_VALIDATIONS = {
    "baselineIntegrity",
    "proposalSchema",
    "pathAndSizePolicy",
    "staticSafety",
    "uiVocabulary",
    "prologLoad",
    "candidateTests",
    "portableSmoke",
    "activePackageUnchanged",
}


class CandidateReviewError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    add_common_inputs(create)
    create.add_argument("--review-id", required=True)
    create.add_argument("--reviewer", required=True)
    create.add_argument("--decision", choices=("recommend", "reject"), required=True)
    create.add_argument("--reason", required=True)
    create.add_argument("--output", required=True, type=Path)

    verify = subparsers.add_parser("verify")
    add_common_inputs(verify)
    verify.add_argument("--review", required=True, type=Path)

    return parser.parse_args()


def add_common_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--comparison", required=True, type=Path)
    parser.add_argument("--candidate-manifest", required=True, type=Path)
    parser.add_argument("--run-schema", required=True, type=Path)
    parser.add_argument("--review-schema", required=True, type=Path)


def main() -> int:
    args = parse_args()
    if args.command == "create":
        record = create_review_record(
            run_path=args.run,
            comparison_path=args.comparison,
            candidate_manifest_path=args.candidate_manifest,
            run_schema_path=args.run_schema,
            review_schema_path=args.review_schema,
            review_id=args.review_id,
            reviewer=args.reviewer,
            decision=args.decision,
            reason=args.reason,
        )
        output = args.output.resolve()
        if output.exists():
            raise CandidateReviewError(f"output already exists: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical_json_bytes(record))
        print(f"Created candidate review: {record['reviewId']}")
        print(f"Decision: {record['decision']}")
        print(f"Candidate: {record['subject']['candidateHash']}")
        print("Activation: not performed")
        print(f"Output: {output}")
        return 0

    verify_review_record(
        review_path=args.review,
        run_path=args.run,
        comparison_path=args.comparison,
        candidate_manifest_path=args.candidate_manifest,
        run_schema_path=args.run_schema,
        review_schema_path=args.review_schema,
    )
    print(f"Verified candidate review: {args.review.resolve()}")
    print("Activation: not performed")
    return 0


def create_review_record(
    *,
    run_path: Path,
    comparison_path: Path,
    candidate_manifest_path: Path,
    run_schema_path: Path,
    review_schema_path: Path,
    review_id: str,
    reviewer: str,
    decision: str,
    reason: str,
) -> dict[str, Any]:
    validate_identifier(review_id, "review ID")
    reviewer = validate_text(reviewer, "reviewer", 256)
    reason = validate_text(reason, "reason", 2000, minimum=10)
    if decision not in {"recommend", "reject"}:
        raise CandidateReviewError("decision must be recommend or reject")

    run, run_bytes = read_json_object(run_path, "Builder run")
    comparison, comparison_bytes = read_json_object(comparison_path, "comparison report")
    candidate, candidate_bytes = read_json_object(
        candidate_manifest_path,
        "candidate manifest",
    )
    run_schema, _ = read_json_object(run_schema_path, "Builder run schema")
    review_schema, _ = read_json_object(review_schema_path, "candidate review schema")
    validate_schema(run, run_schema, "Builder run")

    checks = validate_passed_candidate(run, comparison, candidate, comparison_bytes)
    subject = {
        "runId": run["runId"],
        "taskId": run["taskId"],
        "provider": deepcopy(run["provider"]),
        "taskHash": run["taskHash"],
        "oracleHash": run["oracleHash"],
        "basePackageHash": run["basePackageHash"],
        "proposalHash": run["proposalHash"],
        "candidateHash": run["candidateHash"],
        "candidatePackageHash": run["candidatePackageHash"],
        "comparisonReportHash": run["comparisonReportHash"],
    }
    record: dict[str, Any] = {
        "schemaVersion": "0.1",
        "stage": "candidate-review",
        "reviewId": review_id,
        "decision": decision,
        "reviewer": {
            "kind": "human",
            "id": reviewer,
        },
        "reason": reason,
        "subject": subject,
        "metrics": deepcopy(run["metrics"]),
        "evidence": {
            "runEnvelopeFileHash": sha256(run_bytes),
            "comparisonReportFileHash": sha256(comparison_bytes),
            "candidateManifestFileHash": sha256(candidate_bytes),
        },
        "checks": checks,
        "activation": {
            "status": "not-performed",
        },
    }
    record["reviewHash"] = compute_review_hash(record)
    validate_schema(record, review_schema, "candidate review")
    return record


def verify_review_record(
    *,
    review_path: Path,
    run_path: Path,
    comparison_path: Path,
    candidate_manifest_path: Path,
    run_schema_path: Path,
    review_schema_path: Path,
) -> dict[str, Any]:
    record, _ = read_json_object(review_path, "candidate review")
    review_schema, _ = read_json_object(review_schema_path, "candidate review schema")
    validate_schema(record, review_schema, "candidate review")

    expected_hash = compute_review_hash(record)
    if record.get("reviewHash") != expected_hash:
        raise CandidateReviewError("candidate review hash does not match its canonical payload")

    expected = create_review_record(
        run_path=run_path,
        comparison_path=comparison_path,
        candidate_manifest_path=candidate_manifest_path,
        run_schema_path=run_schema_path,
        review_schema_path=review_schema_path,
        review_id=required_string(record, "reviewId"),
        reviewer=required_string(record.get("reviewer"), "id", "reviewer"),
        decision=required_string(record, "decision"),
        reason=required_string(record, "reason"),
    )
    if record != expected:
        raise CandidateReviewError(
            "candidate review does not match the supplied run, comparison, and manifest"
        )
    return record


def validate_passed_candidate(
    run: dict[str, Any],
    comparison: dict[str, Any],
    candidate: dict[str, Any],
    comparison_bytes: bytes,
) -> dict[str, bool]:
    provider = required_object(run, "provider")
    metrics = required_object(run, "metrics")
    validation = required_object(run, "validation")
    comparison_provider = required_object(comparison, "provider")
    comparison_candidate = required_object(comparison, "candidate")
    comparison_baseline = required_object(comparison, "baseline")
    comparison_result = required_object(comparison, "comparison")
    candidate_provider = required_object(candidate, "provider")
    candidate_metrics = required_object(candidate, "metrics")

    identity_consistent = all(
        (
            comparison.get("taskId") == run.get("taskId"),
            candidate.get("taskId") == run.get("taskId"),
            comparison.get("candidateId") == candidate.get("candidateId"),
            comparison_provider.get("runId") == run.get("runId"),
            candidate_provider.get("runId") == run.get("runId"),
            provider_triplet(comparison_provider) == provider_triplet(provider),
            provider_triplet(candidate_provider) == provider_triplet(provider),
            comparison_candidate.get("candidateHash") == run.get("candidateHash"),
            candidate.get("candidateHash") == run.get("candidateHash"),
            comparison_candidate.get("candidatePackageHash")
            == run.get("candidatePackageHash"),
            candidate.get("candidatePackageHash") == run.get("candidatePackageHash"),
            candidate_metrics == metrics,
            comparison.get("metrics") == metrics,
        )
    )
    baseline_consistent = all(
        (
            comparison_baseline.get("packageHash") == run.get("basePackageHash"),
            candidate.get("basePackageHash") == run.get("basePackageHash"),
            comparison_baseline.get("epoch") == candidate.get("baseEpoch"),
            comparison_baseline.get("revision") == candidate.get("baseRevision"),
            run.get("comparisonReportHash") == sha256(comparison_bytes),
        )
    )
    candidate_passed = validation.get("candidate") == "passed"
    oracle_passed = validation.get("oracle") == "passed"

    validation_rows = comparison.get("validation")
    validation_names = (
        [row.get("name") for row in validation_rows]
        if isinstance(validation_rows, list)
        and all(isinstance(row, dict) for row in validation_rows)
        else []
    )
    comparison_validations_passed = (
        isinstance(validation_rows, list)
        and len(validation_rows) == len(REQUIRED_COMPARISON_VALIDATIONS)
        and len(set(validation_names)) == len(validation_names)
        and set(validation_names) == REQUIRED_COMPARISON_VALIDATIONS
        and all(row.get("status") == "passed" for row in validation_rows)
    )
    runtime_equal = comparison_result.get("runtimeOutputsEqual") is True
    active_unchanged = (
        comparison_result.get("modifiedActiveFiles") == []
        and comparison_result.get("removedActiveFiles") == []
    )
    checks = {
        "identityConsistent": identity_consistent,
        "baselineConsistent": baseline_consistent,
        "candidateValidationPassed": candidate_passed,
        "oracleValidationPassed": oracle_passed,
        "comparisonValidationsPassed": comparison_validations_passed,
        "runtimeOutputsEqual": runtime_equal,
        "activeFilesUnchanged": active_unchanged,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise CandidateReviewError(
            "candidate is not eligible for reviewed recommendation: "
            + ", ".join(failed)
        )
    return checks


def compute_review_hash(record: dict[str, Any]) -> str:
    payload = deepcopy(record)
    payload.pop("reviewHash", None)
    digest = hashlib.sha256()
    digest.update(REVIEW_HASH_DOMAIN)
    digest.update(REVIEW_HASH_VERSION)
    digest.update(canonical_json_bytes(payload))
    return "sha256:" + digest.hexdigest()


def provider_triplet(value: dict[str, Any]) -> tuple[Any, Any, Any]:
    return value.get("kind"), value.get("name"), value.get("model")


def read_json_object(path: Path, context: str) -> tuple[dict[str, Any], bytes]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise CandidateReviewError(f"{context} does not exist: {resolved}")
    try:
        content = resolved.read_bytes()
        value = json.loads(content.decode(UTF8))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateReviewError(f"cannot read {context}: {exc}") from exc
    if not isinstance(value, dict):
        raise CandidateReviewError(f"{context} must be a JSON object")
    return value, content


def validate_schema(value: dict[str, Any], schema: dict[str, Any], context: str) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors[:10]
        )
        raise CandidateReviewError(f"{context} schema validation failed: {details}")


def required_object(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise CandidateReviewError(f"required object {key!r} is missing")
    return result


def required_string(
    value: Any,
    key: str,
    context: str = "record",
) -> str:
    if not isinstance(value, dict):
        raise CandidateReviewError(f"{context} is not an object")
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise CandidateReviewError(f"{context} field {key!r} is missing")
    return result


def validate_identifier(value: str, context: str) -> None:
    if not IDENTIFIER.fullmatch(value):
        raise CandidateReviewError(f"{context} is not a safe identifier")


def validate_text(
    value: str,
    context: str,
    maximum: int,
    *,
    minimum: int = 1,
) -> str:
    if (
        not isinstance(value, str)
        or len(value) < minimum
        or len(value) > maximum
        or any(ord(character) < 32 and character not in "\n\t" for character in value)
        or any(ord(character) == 127 for character in value)
    ):
        raise CandidateReviewError(
            f"{context} must be {minimum}..{maximum} safe characters"
        )
    return value


def sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CandidateReviewError, OSError, ValueError) as exc:
        print(f"Candidate review failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
