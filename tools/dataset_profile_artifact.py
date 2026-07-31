#!/usr/bin/env python3
"""Create and verify deterministic Dataset Profile artifacts for benchmark v0."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from active_epoch.hashing import append_field, canonical_json_bytes
from semantic_claims_artifact import (
    FROZEN_MANIFEST_SHA256,
    SemanticClaimsArtifactError,
    load_case,
    verify_artifact as verify_semantic_claims_artifact,
)

SCHEMA_VERSION = "dataset-profile-artifact-v0"
HASH_DOMAIN = b"LogicLensDatasetProfileArtifact\0"
HASH_VERSION = bytes((1,))
ANALYZER_ID = "dataset-profile-v0"


class DatasetProfileArtifactError(RuntimeError):
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
        raise DatasetProfileArtifactError(f"cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise DatasetProfileArtifactError(f"{label} must be a JSON object: {path}")
    return value, raw


def exact_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = required - set(value)
    extra = set(value) - required
    if missing:
        raise DatasetProfileArtifactError(f"{label} missing keys: {sorted(missing)}")
    if extra:
        raise DatasetProfileArtifactError(f"{label} has unknown keys: {sorted(extra)}")


def object_shape(value: dict[str, Any]) -> tuple[str, ...]:
    kind = value["kind"]
    if kind == "iri":
        return ("iri",)
    return ("literal", value["literalKind"])


def ordered_unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def compute_dataset_profile(case: dict[str, Any], claims: list[dict[str, Any]]) -> dict[str, Any]:
    facts = case["canonicalFacts"]
    entity_ids = ordered_unique([fact["subject"] for fact in facts])
    facts_by_entity: dict[str, list[dict[str, Any]]] = {entity_id: [] for entity_id in entity_ids}
    for fact in facts:
        facts_by_entity[fact["subject"]].append(fact)

    signatures = [
        sorted(object_shape(fact["object"]) for fact in facts_by_entity[entity_id])
        for entity_id in entity_ids
    ]
    repeated_record_shape = len(entity_ids) >= 2 and all(
        signature == signatures[0] for signature in signatures[1:]
    )

    first_predicates = ordered_unique(
        [fact["predicate"] for fact in facts_by_entity[entity_ids[0]]]
    )
    common_predicates = [
        predicate
        for predicate in first_predicates
        if all(
            any(fact["predicate"] == predicate for fact in facts_by_entity[entity_id])
            for entity_id in entity_ids
        )
    ]

    claims_by_predicate: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        predicate = claim["dataElement"]["id"]
        claims_by_predicate.setdefault(predicate, []).append(claim)

    row_candidates: list[str] = []
    for predicate in common_predicates:
        predicate_claims = claims_by_predicate.get(predicate, [])
        if any(
            claim["facet"] == "display_role"
            and claim["role"] in {"identifier", "display_label"}
            and claim["status"] == "supported"
            for claim in predicate_claims
        ):
            row_candidates.append(predicate)
    if len(row_candidates) > 1:
        raise DatasetProfileArtifactError(
            f"dataset profile has ambiguous row label predicates: {row_candidates}"
        )
    row_label = row_candidates[0] if row_candidates else None

    candidate_dimensions: list[dict[str, Any]] = []
    if repeated_record_shape:
        for predicate in common_predicates:
            if predicate == row_label:
                continue
            predicate_claims = claims_by_predicate.get(predicate, [])
            if not predicate_claims:
                continue
            claim_ids = [claim["claimId"] for claim in predicate_claims]
            present = sum(
                any(fact["predicate"] == predicate for fact in facts_by_entity[entity_id])
                for entity_id in entity_ids
            )
            eligible = all(claim["status"] == "supported" for claim in predicate_claims)
            dimension: dict[str, Any] = {
                "predicate": predicate,
                "semanticClaimIds": claim_ids,
                "present": present,
                "total": len(entity_ids),
                "eligible": eligible,
            }
            if not eligible:
                dimension["ineligibilityReason"] = "required_semantic_claim_not_supported"
            candidate_dimensions.append(dimension)

    predicate_order = ordered_unique([fact["predicate"] for fact in facts])
    technical_predicates = [
        predicate
        for predicate in predicate_order
        if any(
            claim["facet"] == "policy_role"
            and claim["role"] == "technical_metadata"
            and claim["status"] == "supported"
            for claim in claims_by_predicate.get(predicate, [])
        )
    ]

    return {
        "profileVersion": ANALYZER_ID,
        "entityIds": entity_ids,
        "entityCount": len(entity_ids),
        "factCount": len(facts),
        "repeatedRecordShape": repeated_record_shape,
        "commonPredicates": common_predicates,
        "candidateRowLabelPredicate": row_label,
        "candidateDimensions": candidate_dimensions,
        "technicalPredicates": technical_predicates,
        "mandatoryFactIds": [fact["factId"] for fact in facts],
    }


def build_artifact(
    benchmark_root: Path,
    semantic_claims_path: Path,
    *,
    expected_manifest_sha256: str | None = FROZEN_MANIFEST_SHA256,
) -> dict[str, Any]:
    try:
        claims_artifact = verify_semantic_claims_artifact(
            benchmark_root.resolve(),
            semantic_claims_path.resolve(),
            expected_manifest_sha256=expected_manifest_sha256,
        )
    except SemanticClaimsArtifactError as error:
        raise DatasetProfileArtifactError(f"semantic claims input is invalid: {error}") from error

    case_id = claims_artifact["benchmark"]["caseId"]
    try:
        summary, manifest_raw, case_path, case, case_raw = load_case(
            benchmark_root.resolve(), case_id, expected_manifest_sha256
        )
    except SemanticClaimsArtifactError as error:
        raise DatasetProfileArtifactError(f"cannot load benchmark case: {error}") from error

    profile = compute_dataset_profile(case, claims_artifact["claims"])
    oracle_profile = case["oracleDatasetProfile"]
    if profile != oracle_profile:
        raise DatasetProfileArtifactError(
            "trusted analyzer output does not exactly match the frozen oracleDatasetProfile"
        )

    payload: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "stage": "deterministic-dataset-profile",
        "benchmark": {
            "benchmarkId": summary.benchmark_id,
            "manifestSha256": sha256_prefixed(manifest_raw),
            "caseId": case_id,
            "casePath": case_path,
            "caseSha256": sha256_prefixed(case_raw),
        },
        "input": {
            "semanticClaimsArtifactHash": claims_artifact["artifactHash"],
        },
        "analyzer": {
            "kind": "trusted-deterministic",
            "id": ANALYZER_ID,
            "algorithmVersion": 1,
        },
        "profile": profile,
        "oracleComparison": {
            "oracleProfileSha256": sha256_prefixed(canonical_json_bytes(oracle_profile)),
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
            "analyzer",
            "profile",
            "oracleComparison",
            "artifactHash",
        },
        "artifact",
    )
    if artifact["schemaVersion"] != SCHEMA_VERSION:
        raise DatasetProfileArtifactError("unsupported dataset profile artifact schema")
    if artifact["stage"] != "deterministic-dataset-profile":
        raise DatasetProfileArtifactError("artifact stage must be deterministic-dataset-profile")
    if artifact["analyzer"] != {
        "kind": "trusted-deterministic",
        "id": ANALYZER_ID,
        "algorithmVersion": 1,
    }:
        raise DatasetProfileArtifactError("unexpected analyzer identity")
    if artifact["oracleComparison"].get("exactMatch") is not True:
        raise DatasetProfileArtifactError("oracle comparison must be exact")


def verify_artifact(
    benchmark_root: Path,
    semantic_claims_path: Path,
    artifact_path: Path,
    *,
    expected_manifest_sha256: str | None = FROZEN_MANIFEST_SHA256,
) -> dict[str, Any]:
    artifact, raw = read_object(artifact_path.resolve(), "dataset profile artifact")
    validate_artifact_shape(artifact)
    expected = build_artifact(
        benchmark_root.resolve(),
        semantic_claims_path.resolve(),
        expected_manifest_sha256=expected_manifest_sha256,
    )
    if artifact != expected:
        raise DatasetProfileArtifactError(
            "artifact does not exactly reproduce the trusted analyzer output"
        )
    if raw != canonical_json_bytes(artifact):
        raise DatasetProfileArtifactError("artifact JSON is valid but not canonical bytes")
    without_hash = deepcopy(artifact)
    recorded_hash = without_hash.pop("artifactHash")
    if artifact_hash(without_hash) != recorded_hash:
        raise DatasetProfileArtifactError("artifactHash mismatch")
    return artifact


def create_command(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    if output.exists():
        raise DatasetProfileArtifactError(f"output already exists: {output}")
    artifact = build_artifact(args.benchmark_root, args.semantic_claims)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(artifact))
    print(f"Created deterministic dataset profile: {artifact['benchmark']['caseId']}")
    print(f"Artifact hash: {artifact['artifactHash']}")
    print(f"Output: {output}")
    return 0


def verify_command(args: argparse.Namespace) -> int:
    artifact = verify_artifact(args.benchmark_root, args.semantic_claims, args.artifact)
    print(f"Verified deterministic dataset profile: {artifact['benchmark']['caseId']}")
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
    except DatasetProfileArtifactError as error:
        print(f"dataset profile artifact error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
