#!/usr/bin/env python3
"""Create and verify deterministic Presentation Decision artifacts for benchmark v0."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from active_epoch.hashing import append_field, canonical_json_bytes
from dataset_profile_artifact import (
    DatasetProfileArtifactError,
    verify_artifact as verify_dataset_profile_artifact,
)
from semantic_claims_artifact import (
    FROZEN_MANIFEST_SHA256,
    SemanticClaimsArtifactError,
    load_case,
    verify_artifact as verify_semantic_claims_artifact,
)

SCHEMA_VERSION = "presentation-decision-artifact-v0"
HASH_DOMAIN = b"LogicLensPresentationDecisionArtifact\0"
HASH_VERSION = bytes((1,))
PLANNER_ID = "comparison-planner-v0"
GENERIC_FALLBACK = "generic_property_sections"


class PresentationDecisionArtifactError(RuntimeError):
    pass


def sha256_prefixed(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def artifact_hash(record_without_hash: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(HASH_DOMAIN)
    digest.update(HASH_VERSION)
    append_field(digest, canonical_json_bytes(record_without_hash))
    return "sha256:" + digest.hexdigest()


def read_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PresentationDecisionArtifactError(f"cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise PresentationDecisionArtifactError(f"{label} must be a JSON object: {path}")
    return value, raw


def exact_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = required - set(value)
    extra = set(value) - required
    if missing:
        raise PresentationDecisionArtifactError(f"{label} missing keys: {sorted(missing)}")
    if extra:
        raise PresentationDecisionArtifactError(f"{label} has unknown keys: {sorted(extra)}")


def claims_by_id(claims: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {claim["claimId"]: claim for claim in claims}


def excluded_dimension_reason(
    dimension: dict[str, Any],
    claim_index: dict[str, dict[str, Any]],
) -> str:
    referenced = [claim_index[claim_id] for claim_id in dimension["semanticClaimIds"]]
    roles = {claim["role"] for claim in referenced}
    statuses = {claim["status"] for claim in referenced}
    if statuses == {"possible"} and "time_value" in roles and any(
        role.endswith("_time") for role in roles if role != "time_value"
    ):
        return "ambiguous_time_semantics"
    return dimension.get(
        "ineligibilityReason",
        "required_semantic_claim_not_supported",
    )


def constraint(constraint_id: str, passed: bool) -> dict[str, str]:
    return {"id": constraint_id, "result": "passed" if passed else "failed"}


def compute_presentation_decision(
    case: dict[str, Any],
    claims: list[dict[str, Any]],
    profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Compute a fail-closed comparison decision without reading expectedPresentation."""
    claim_index = claims_by_id(claims)
    mandatory = list(profile["mandatoryFactIds"])
    eligible_dimensions = [
        dimension for dimension in profile["candidateDimensions"] if dimension["eligible"]
    ]
    ineligible_dimensions = [
        dimension for dimension in profile["candidateDimensions"] if not dimension["eligible"]
    ]

    enough_entities = profile["entityCount"] >= 2
    repeated_shape = profile["repeatedRecordShape"] is True
    comparison_goal = str(case["task"]["goal"]).startswith("compare")
    has_shared_dimensions = bool(eligible_dimensions)
    has_row_label = profile["candidateRowLabelPredicate"] is not None

    constraints = [
        constraint("minimum_two_entities", enough_entities),
        constraint("repeated_record_shape", repeated_shape),
        constraint("comparison_task_requested", comparison_goal),
        constraint("shared_semantic_dimension_available", has_shared_dimensions),
        constraint("row_label_available", has_row_label),
        constraint(
            "selected_dimensions_supported",
            all(
                all(
                    claim_index[claim_id]["status"] == "supported"
                    for claim_id in dimension["semanticClaimIds"]
                )
                for dimension in eligible_dimensions
            ),
        ),
        constraint("generic_fallback_attached", True),
    ]

    if not enough_entities or not repeated_shape:
        reason = "repeated_records_required"
        decision = {
            "acceptableDecisions": [
                {
                    "kind": "fallback",
                    "component": GENERIC_FALLBACK,
                    "reason": reason,
                }
            ],
            "requiredRejectedCandidates": [
                {"component": "comparison_table", "reason": reason}
            ],
            "requiredCoveredFactIds": mandatory,
            "mustExposeFallback": True,
        }
        coverage = {
            "mandatoryFactIds": mandatory,
            "primaryFactIds": mandatory,
            "fallbackOnlyFactIds": [],
            "complete": True,
        }
        evaluation = {
            "candidate": "comparison_table",
            "constraints": constraints,
            "outcome": "rejected",
            "reason": reason,
        }
        constraints.append(constraint("complete_fact_coverage_with_fallback", True))
        return decision, evaluation, coverage

    if not comparison_goal:
        reason = "comparison_task_required"
        decision = {
            "acceptableDecisions": [
                {
                    "kind": "fallback",
                    "component": GENERIC_FALLBACK,
                    "reason": reason,
                }
            ],
            "requiredRejectedCandidates": [
                {"component": "comparison_table", "reason": reason}
            ],
            "requiredCoveredFactIds": mandatory,
            "mustExposeFallback": True,
        }
        coverage = {
            "mandatoryFactIds": mandatory,
            "primaryFactIds": mandatory,
            "fallbackOnlyFactIds": [],
            "complete": True,
        }
        constraints.append(constraint("complete_fact_coverage_with_fallback", True))
        evaluation = {
            "candidate": "comparison_table",
            "constraints": constraints,
            "outcome": "rejected",
            "reason": reason,
        }
        return decision, evaluation, coverage

    if not has_shared_dimensions:
        reason = "insufficient_shared_semantic_dimensions"
        decision = {
            "acceptableDecisions": [
                {
                    "kind": "fallback",
                    "component": GENERIC_FALLBACK,
                    "reason": reason,
                }
            ],
            "requiredRejectedCandidates": [
                {"component": "comparison_table", "reason": reason}
            ],
            "requiredCoveredFactIds": mandatory,
            "mustExposeFallback": True,
        }
        coverage = {
            "mandatoryFactIds": mandatory,
            "primaryFactIds": mandatory,
            "fallbackOnlyFactIds": [],
            "complete": True,
        }
        evaluation = {
            "candidate": "comparison_table",
            "constraints": constraints,
            "outcome": "rejected",
            "reason": reason,
        }
        constraints.append(constraint("complete_fact_coverage_with_fallback", True))
        return decision, evaluation, coverage

    if not has_row_label:
        raise PresentationDecisionArtifactError(
            "comparison candidate has shared dimensions but no supported row label"
        )

    selected_predicates = [
        profile["candidateRowLabelPredicate"],
        *[dimension["predicate"] for dimension in eligible_dimensions],
    ]
    selected_set = set(selected_predicates)
    primary_fact_ids = [
        fact["factId"]
        for fact in case["canonicalFacts"]
        if fact["predicate"] in selected_set
    ]
    primary_set = set(primary_fact_ids)
    fallback_only = [fact_id for fact_id in mandatory if fact_id not in primary_set]

    acceptable: dict[str, Any] = {
        "kind": "select",
        "component": "comparison_table",
        "entityIds": list(profile["entityIds"]),
        "rowLabelPredicate": profile["candidateRowLabelPredicate"],
        "dimensionPredicates": [
            dimension["predicate"] for dimension in eligible_dimensions
        ],
    }
    rejected: list[dict[str, str]] = []
    if ineligible_dimensions:
        excluded = [
            {
                "predicate": dimension["predicate"],
                "reason": excluded_dimension_reason(dimension, claim_index),
            }
            for dimension in ineligible_dimensions
        ]
        acceptable["excludedPredicates"] = excluded
        if any(item["reason"] == "ambiguous_time_semantics" for item in excluded):
            rejected.append(
                {"component": "timeline", "reason": "ambiguous_time_semantics"}
            )
    acceptable["fallback"] = GENERIC_FALLBACK

    decision = {
        "acceptableDecisions": [acceptable],
        "requiredRejectedCandidates": rejected,
        "requiredCoveredFactIds": primary_fact_ids,
    }
    if fallback_only:
        decision["factsRequiredOnlyInFallback"] = fallback_only
    decision["mustExposeFallback"] = True

    coverage = {
        "mandatoryFactIds": mandatory,
        "primaryFactIds": primary_fact_ids,
        "fallbackOnlyFactIds": fallback_only,
        "complete": set(mandatory) == primary_set | set(fallback_only),
    }
    constraints.append(
        constraint("complete_fact_coverage_with_fallback", coverage["complete"])
    )
    evaluation = {
        "candidate": "comparison_table",
        "constraints": constraints,
        "outcome": "selected",
        "reason": None,
    }
    return decision, evaluation, coverage


def build_artifact(
    benchmark_root: Path,
    semantic_claims_path: Path,
    dataset_profile_path: Path,
    *,
    expected_manifest_sha256: str | None = FROZEN_MANIFEST_SHA256,
) -> dict[str, Any]:
    try:
        claims_artifact = verify_semantic_claims_artifact(
            benchmark_root.resolve(),
            semantic_claims_path.resolve(),
            expected_manifest_sha256=expected_manifest_sha256,
        )
        profile_artifact = verify_dataset_profile_artifact(
            benchmark_root.resolve(),
            semantic_claims_path.resolve(),
            dataset_profile_path.resolve(),
            expected_manifest_sha256=expected_manifest_sha256,
        )
    except (SemanticClaimsArtifactError, DatasetProfileArtifactError) as error:
        raise PresentationDecisionArtifactError(f"planner input is invalid: {error}") from error

    if (
        profile_artifact["input"]["semanticClaimsArtifactHash"]
        != claims_artifact["artifactHash"]
    ):
        raise PresentationDecisionArtifactError(
            "dataset profile is not linked to semantic claims"
        )
    if profile_artifact["benchmark"] != claims_artifact["benchmark"]:
        raise PresentationDecisionArtifactError(
            "planner inputs refer to different benchmark cases"
        )

    case_id = claims_artifact["benchmark"]["caseId"]
    try:
        summary, manifest_raw, case_path, case, case_raw = load_case(
            benchmark_root.resolve(), case_id, expected_manifest_sha256
        )
    except SemanticClaimsArtifactError as error:
        raise PresentationDecisionArtifactError(
            f"cannot load benchmark case: {error}"
        ) from error

    decision, evaluation, coverage = compute_presentation_decision(
        case,
        claims_artifact["claims"],
        profile_artifact["profile"],
    )
    oracle = case["expectedPresentation"]
    if decision != oracle:
        raise PresentationDecisionArtifactError(
            "trusted planner output does not exactly match the frozen expectedPresentation"
        )
    if coverage["complete"] is not True:
        raise PresentationDecisionArtifactError(
            "planner did not preserve mandatory fact coverage"
        )

    payload: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "stage": "deterministic-presentation-decision",
        "benchmark": {
            "benchmarkId": summary.benchmark_id,
            "manifestSha256": sha256_prefixed(manifest_raw),
            "caseId": case_id,
            "casePath": case_path,
            "caseSha256": sha256_prefixed(case_raw),
        },
        "input": {
            "semanticClaimsArtifactHash": claims_artifact["artifactHash"],
            "datasetProfileArtifactHash": profile_artifact["artifactHash"],
        },
        "planner": {
            "kind": "trusted-deterministic",
            "id": PLANNER_ID,
            "algorithmVersion": 1,
        },
        "evaluation": evaluation,
        "coverage": coverage,
        "decision": decision,
        "oracleComparison": {
            "oraclePresentationSha256": sha256_prefixed(
                canonical_json_bytes(oracle)
            ),
            "exactMatch": True,
        },
    }
    payload["artifactHash"] = artifact_hash(payload)
    return payload


def validate_artifact_shape(artifact: dict[str, Any]) -> None:
    exact_keys(
        artifact,
        {
            "schemaVersion",
            "stage",
            "benchmark",
            "input",
            "planner",
            "evaluation",
            "coverage",
            "decision",
            "oracleComparison",
            "artifactHash",
        },
        "artifact",
    )
    if artifact["schemaVersion"] != SCHEMA_VERSION:
        raise PresentationDecisionArtifactError(
            "unsupported presentation decision schema"
        )
    if artifact["stage"] != "deterministic-presentation-decision":
        raise PresentationDecisionArtifactError(
            "artifact stage must be deterministic-presentation-decision"
        )
    if artifact["planner"] != {
        "kind": "trusted-deterministic",
        "id": PLANNER_ID,
        "algorithmVersion": 1,
    }:
        raise PresentationDecisionArtifactError("unexpected planner identity")
    if artifact["oracleComparison"].get("exactMatch") is not True:
        raise PresentationDecisionArtifactError("oracle comparison must be exact")
    coverage = artifact["coverage"]
    if not isinstance(coverage, dict) or coverage.get("complete") is not True:
        raise PresentationDecisionArtifactError("coverage must be complete")
    decision = artifact["decision"]
    if not isinstance(decision, dict) or decision.get("mustExposeFallback") is not True:
        raise PresentationDecisionArtifactError(
            "decision must expose generic fallback"
        )


def verify_artifact(
    benchmark_root: Path,
    semantic_claims_path: Path,
    dataset_profile_path: Path,
    artifact_path: Path,
    *,
    expected_manifest_sha256: str | None = FROZEN_MANIFEST_SHA256,
) -> dict[str, Any]:
    artifact, raw = read_object(
        artifact_path.resolve(), "presentation decision artifact"
    )
    validate_artifact_shape(artifact)
    expected = build_artifact(
        benchmark_root.resolve(),
        semantic_claims_path.resolve(),
        dataset_profile_path.resolve(),
        expected_manifest_sha256=expected_manifest_sha256,
    )
    if artifact != expected:
        raise PresentationDecisionArtifactError(
            "artifact does not exactly reproduce the trusted planner output"
        )
    if raw != canonical_json_bytes(artifact):
        raise PresentationDecisionArtifactError(
            "artifact JSON is valid but not canonical bytes"
        )
    without_hash = deepcopy(artifact)
    recorded_hash = without_hash.pop("artifactHash")
    if artifact_hash(without_hash) != recorded_hash:
        raise PresentationDecisionArtifactError("artifactHash mismatch")
    return artifact


def create_command(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    if output.exists():
        raise PresentationDecisionArtifactError(f"output already exists: {output}")
    artifact = build_artifact(
        args.benchmark_root,
        args.semantic_claims,
        args.dataset_profile,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(artifact))
    print(f"Created presentation decision: {artifact['benchmark']['caseId']}")
    print(f"Outcome: {artifact['evaluation']['outcome']}")
    print(f"Artifact hash: {artifact['artifactHash']}")
    print(f"Output: {output}")
    return 0


def verify_command(args: argparse.Namespace) -> int:
    artifact = verify_artifact(
        args.benchmark_root,
        args.semantic_claims,
        args.dataset_profile,
        args.artifact,
    )
    print(f"Verified presentation decision: {artifact['benchmark']['caseId']}")
    print(f"Outcome: {artifact['evaluation']['outcome']}")
    print(f"Artifact hash: {artifact['artifactHash']}")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    for command in ("create", "verify"):
        item = sub.add_parser(command)
        item.add_argument(
            "--benchmark-root",
            type=Path,
            default=Path("experiments/presentation/semantic-planning-v0"),
        )
        item.add_argument("--semantic-claims", type=Path, required=True)
        item.add_argument("--dataset-profile", type=Path, required=True)
        if command == "create":
            item.add_argument("--output", type=Path, required=True)
            item.set_defaults(handler=create_command)
        else:
            item.add_argument("--artifact", type=Path, required=True)
            item.set_defaults(handler=verify_command)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.handler(args)
    except PresentationDecisionArtifactError as error:
        print(f"presentation decision artifact error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
