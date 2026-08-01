#!/usr/bin/env python3
"""Create, verify, and score deterministic semantic-claim baseline artifacts."""
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
    sha256_prefixed,
)

CANDIDATE_SCHEMA = "semantic-claims-candidate-artifact-v0"
EVALUATION_SCHEMA = "semantic-claims-evaluation-artifact-v0"
CANDIDATE_DOMAIN = b"LogicLensSemanticClaimsCandidateArtifact\0"
EVALUATION_DOMAIN = b"LogicLensSemanticClaimsEvaluationArtifact\0"
HASH_VERSION = bytes((1,))
PRODUCER_ID = "ontology-label-datatype-heuristic-v0"
EVALUATOR_ID = "semantic-claims-exact-role-evaluator-v0"

LABEL_RULES: dict[str, tuple[str, str]] = {
    "редакция": ("display_role", "identifier"),
    "код": ("display_role", "identifier"),
    "название": ("display_role", "display_label"),
    "описание": ("display_role", "description"),
    "статус": ("value_role", "status"),
    "состояние": ("value_role", "status"),
    "материал": ("value_role", "category"),
    "температура": ("value_role", "measurement"),
    "цена": ("value_role", "monetary_amount"),
    "возраст": ("value_role", "age"),
    "действует с": ("value_role", "time_value"),
}
DATE_DATATYPES = {"xsd:date", "xsd:dateTime"}


class SemanticClaimsBaselineError(RuntimeError):
    pass


def domain_hash(domain: bytes, value: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(HASH_VERSION)
    append_field(digest, canonical_json_bytes(value))
    return "sha256:" + digest.hexdigest()


def read_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SemanticClaimsBaselineError(f"cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise SemanticClaimsBaselineError(f"{label} must be a JSON object: {path}")
    return value, raw


def exact_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = required - set(value)
    extra = set(value) - required
    if missing:
        raise SemanticClaimsBaselineError(f"{label} missing keys: {sorted(missing)}")
    if extra:
        raise SemanticClaimsBaselineError(f"{label} has unknown keys: {sorted(extra)}")


def normalize_label(value: str) -> str:
    return " ".join(value.strip().lower().split())


def claim_id(element_id: str, facet: str, role: str) -> str:
    material = f"{element_id}\0{facet}\0{role}".encode("utf-8")
    return "heuristic:" + hashlib.sha256(material).hexdigest()[:20]


def predicate_datatypes(case: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for fact in case["canonicalFacts"]:
        obj = fact["object"]
        datatype = obj.get("datatype") if obj["kind"] == "literal" else None
        if datatype and datatype not in result.setdefault(fact["predicate"], []):
            result[fact["predicate"]].append(datatype)
    return result


def generate_claims(case: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Generate claims using ontology labels and datatypes, never oracle claims."""
    datatypes = predicate_datatypes(case)
    claims: list[dict[str, Any]] = []
    classified: set[str] = set()
    evidence_by_predicate = {
        item["element"]["id"]: item for item in case["ontologyEvidence"]
    }
    predicate_order: list[str] = []
    for fact in case["canonicalFacts"]:
        if fact["predicate"] not in predicate_order:
            predicate_order.append(fact["predicate"])

    for predicate in predicate_order:
        ontology = evidence_by_predicate.get(predicate)
        if not ontology:
            continue
        labels = ontology.get("labels", [])
        selected: tuple[str, str, str, str] | None = None
        for label in labels:
            normalized = normalize_label(label["text"])
            if normalized in LABEL_RULES:
                facet, role = LABEL_RULES[normalized]
                selected = (facet, role, "supported", label["text"])
                break
            if normalized == "дата" and any(
                datatype in DATE_DATATYPES
                for datatype in datatypes.get(predicate, [])
            ):
                selected = (
                    "value_role",
                    "time_value",
                    "possible",
                    label["text"],
                )
                break
        if selected is None:
            continue
        facet, role, status, label_text = selected
        evidence: list[dict[str, Any]] = [
            {"kind": "ontology_label", "value": label_text}
        ]
        if role == "time_value" and datatypes.get(predicate):
            evidence.append(
                {"kind": "datatype", "value": datatypes[predicate][0]}
            )
        claims.append(
            {
                "claimId": claim_id(predicate, facet, role),
                "dataElement": {"kind": "predicate", "id": predicate},
                "facet": facet,
                "role": role,
                "status": status,
                "evidence": evidence,
                "alternatives": [],
            }
        )
        classified.add(predicate)

    return claims, [
        predicate for predicate in predicate_order if predicate not in classified
    ]


def benchmark_record(
    summary: Any,
    manifest_raw: bytes,
    case_path: str,
    case_id: str,
    case_raw: bytes,
) -> dict[str, Any]:
    return {
        "benchmarkId": summary.benchmark_id,
        "manifestSha256": sha256_prefixed(manifest_raw),
        "caseId": case_id,
        "casePath": case_path,
        "caseSha256": sha256_prefixed(case_raw),
    }


def build_candidate(
    benchmark_root: Path,
    case_id: str,
    *,
    expected_manifest_sha256: str | None = FROZEN_MANIFEST_SHA256,
) -> dict[str, Any]:
    try:
        summary, manifest_raw, case_path, case, case_raw = load_case(
            benchmark_root.resolve(), case_id, expected_manifest_sha256
        )
    except SemanticClaimsArtifactError as error:
        raise SemanticClaimsBaselineError(
            f"cannot load benchmark case: {error}"
        ) from error
    claims, unclassified = generate_claims(case)
    payload: dict[str, Any] = {
        "schemaVersion": CANDIDATE_SCHEMA,
        "stage": "deterministic-semantic-claims",
        "benchmark": benchmark_record(
            summary, manifest_raw, case_path, case_id, case_raw
        ),
        "producer": {
            "kind": "trusted-deterministic",
            "id": PRODUCER_ID,
            "algorithmVersion": 1,
            "inputs": ["ontology_labels", "literal_datatypes"],
        },
        "task": {
            "language": case["task"]["language"],
            "goal": case["task"]["goal"],
            "textUsed": False,
        },
        "claims": claims,
        "unclassifiedPredicateIds": unclassified,
    }
    payload["artifactHash"] = domain_hash(CANDIDATE_DOMAIN, payload)
    return payload


def validate_candidate_shape(artifact: dict[str, Any]) -> None:
    exact_keys(
        artifact,
        {
            "schemaVersion",
            "stage",
            "benchmark",
            "producer",
            "task",
            "claims",
            "unclassifiedPredicateIds",
            "artifactHash",
        },
        "candidate artifact",
    )
    if artifact["schemaVersion"] != CANDIDATE_SCHEMA:
        raise SemanticClaimsBaselineError("unsupported candidate artifact schema")
    if artifact["stage"] != "deterministic-semantic-claims":
        raise SemanticClaimsBaselineError("candidate stage mismatch")
    if artifact["producer"] != {
        "kind": "trusted-deterministic",
        "id": PRODUCER_ID,
        "algorithmVersion": 1,
        "inputs": ["ontology_labels", "literal_datatypes"],
    }:
        raise SemanticClaimsBaselineError("unexpected candidate producer")
    if artifact["task"].get("textUsed") is not False:
        raise SemanticClaimsBaselineError("baseline must not use task text")


def verify_candidate(
    benchmark_root: Path,
    artifact_path: Path,
    *,
    expected_manifest_sha256: str | None = FROZEN_MANIFEST_SHA256,
) -> dict[str, Any]:
    artifact, raw = read_object(
        artifact_path.resolve(), "semantic claims candidate"
    )
    validate_candidate_shape(artifact)
    expected = build_candidate(
        benchmark_root.resolve(),
        artifact["benchmark"]["caseId"],
        expected_manifest_sha256=expected_manifest_sha256,
    )
    if artifact != expected:
        raise SemanticClaimsBaselineError(
            "candidate does not reproduce the deterministic baseline"
        )
    if raw != canonical_json_bytes(artifact):
        raise SemanticClaimsBaselineError("candidate JSON is not canonical bytes")
    without_hash = deepcopy(artifact)
    recorded = without_hash.pop("artifactHash")
    if domain_hash(CANDIDATE_DOMAIN, without_hash) != recorded:
        raise SemanticClaimsBaselineError("candidate artifactHash mismatch")
    return artifact


def role_key(claim: dict[str, Any]) -> tuple[str, str, str, str]:
    element = claim["dataElement"]
    return (
        element["kind"],
        element["id"],
        claim["facet"],
        claim["role"],
    )


def safe_ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def prf(tp: int, fp: int, fn: int) -> dict[str, Any]:
    precision = safe_ratio(tp, tp + fp)
    recall = safe_ratio(tp, tp + fn)
    f1 = (
        round(2 * precision * recall / (precision + recall), 6)
        if precision + recall
        else 0.0
    )
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def ambiguity_elements(
    claims: list[dict[str, Any]],
) -> set[tuple[str, str, str]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for claim in claims:
        element = claim["dataElement"]
        key = (element["kind"], element["id"], claim["facet"])
        groups.setdefault(key, []).append(claim)
    return {
        key
        for key, values in groups.items()
        if any(value["status"] == "possible" for value in values)
    }


def evidence_is_valid(
    case: dict[str, Any],
    claim: dict[str, Any],
    evidence: dict[str, Any],
) -> bool:
    predicate = claim["dataElement"]["id"]
    if evidence["kind"] == "ontology_label":
        return any(
            item["element"]["id"] == predicate
            and any(
                label["text"] == evidence["value"]
                for label in item["labels"]
            )
            for item in case["ontologyEvidence"]
        )
    if evidence["kind"] == "datatype":
        return any(
            fact["predicate"] == predicate
            and fact["object"].get("datatype") == evidence["value"]
            for fact in case["canonicalFacts"]
        )
    return False


def evaluate_claims(
    case: dict[str, Any],
    candidate_claims: list[dict[str, Any]],
) -> dict[str, Any]:
    oracle_claims = case["oracleSemanticClaims"]
    oracle = {role_key(claim): claim for claim in oracle_claims}
    candidate = {role_key(claim): claim for claim in candidate_claims}
    oracle_keys = set(oracle)
    candidate_keys = set(candidate)
    exact = prf(
        len(oracle_keys & candidate_keys),
        len(candidate_keys - oracle_keys),
        len(oracle_keys - candidate_keys),
    )

    classes = sorted(
        {(key[2], key[3]) for key in oracle_keys | candidate_keys}
    )
    by_role: list[dict[str, Any]] = []
    for facet, role in classes:
        expected = {
            key for key in oracle_keys if key[2:] == (facet, role)
        }
        actual = {
            key for key in candidate_keys if key[2:] == (facet, role)
        }
        by_role.append(
            {
                "facet": facet,
                "role": role,
                **prf(
                    len(expected & actual),
                    len(actual - expected),
                    len(expected - actual),
                ),
            }
        )
    macro_f1 = (
        round(sum(item["f1"] for item in by_role) / len(by_role), 6)
        if by_role
        else 0.0
    )

    oracle_ambiguity = ambiguity_elements(oracle_claims)
    candidate_ambiguity = ambiguity_elements(candidate_claims)
    ambiguity = prf(
        len(oracle_ambiguity & candidate_ambiguity),
        len(candidate_ambiguity - oracle_ambiguity),
        len(oracle_ambiguity - candidate_ambiguity),
    )

    false_supported = sum(
        1
        for key, claim in candidate.items()
        if claim["status"] == "supported"
        and (key not in oracle or oracle[key]["status"] != "supported")
    )
    evidence_items = [
        (claim, evidence)
        for claim in candidate_claims
        for evidence in claim["evidence"]
    ]
    valid_evidence = sum(
        evidence_is_valid(case, claim, evidence)
        for claim, evidence in evidence_items
    )
    return {
        "exactRole": exact,
        "macroF1ByRole": macro_f1,
        "byRole": by_role,
        "ambiguityDetection": ambiguity,
        "falseSupportedCount": false_supported,
        "evidenceValidity": {
            "valid": valid_evidence,
            "total": len(evidence_items),
            "rate": safe_ratio(valid_evidence, len(evidence_items)),
        },
        "oracleClaimCount": len(oracle_claims),
        "candidateClaimCount": len(candidate_claims),
    }


def build_evaluation(
    benchmark_root: Path,
    candidate_path: Path,
    *,
    expected_manifest_sha256: str | None = FROZEN_MANIFEST_SHA256,
) -> dict[str, Any]:
    candidate = verify_candidate(
        benchmark_root.resolve(),
        candidate_path.resolve(),
        expected_manifest_sha256=expected_manifest_sha256,
    )
    case_id = candidate["benchmark"]["caseId"]
    try:
        summary, manifest_raw, case_path, case, case_raw = load_case(
            benchmark_root.resolve(), case_id, expected_manifest_sha256
        )
    except SemanticClaimsArtifactError as error:
        raise SemanticClaimsBaselineError(
            f"cannot load benchmark case: {error}"
        ) from error
    payload: dict[str, Any] = {
        "schemaVersion": EVALUATION_SCHEMA,
        "stage": "semantic-claims-evaluation",
        "benchmark": benchmark_record(
            summary, manifest_raw, case_path, case_id, case_raw
        ),
        "input": {"candidateArtifactHash": candidate["artifactHash"]},
        "evaluator": {
            "kind": "trusted-deterministic",
            "id": EVALUATOR_ID,
            "algorithmVersion": 1,
        },
        "metrics": evaluate_claims(case, candidate["claims"]),
    }
    payload["artifactHash"] = domain_hash(EVALUATION_DOMAIN, payload)
    return payload


def verify_evaluation(
    benchmark_root: Path,
    candidate_path: Path,
    evaluation_path: Path,
    *,
    expected_manifest_sha256: str | None = FROZEN_MANIFEST_SHA256,
) -> dict[str, Any]:
    artifact, raw = read_object(
        evaluation_path.resolve(), "semantic claims evaluation"
    )
    expected = build_evaluation(
        benchmark_root.resolve(),
        candidate_path.resolve(),
        expected_manifest_sha256=expected_manifest_sha256,
    )
    if artifact != expected:
        raise SemanticClaimsBaselineError(
            "evaluation does not reproduce exact scoring"
        )
    if raw != canonical_json_bytes(artifact):
        raise SemanticClaimsBaselineError(
            "evaluation JSON is not canonical bytes"
        )
    return artifact


def write_new(path: Path, value: dict[str, Any]) -> None:
    output = path.resolve()
    if output.exists():
        raise SemanticClaimsBaselineError(f"output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(value))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument(
        "--benchmark-root",
        type=Path,
        default=Path("experiments/presentation/semantic-planning-v0"),
    )
    create.add_argument("--case-id", required=True)
    create.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument(
        "--benchmark-root",
        type=Path,
        default=Path("experiments/presentation/semantic-planning-v0"),
    )
    verify.add_argument("--artifact", type=Path, required=True)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument(
        "--benchmark-root",
        type=Path,
        default=Path("experiments/presentation/semantic-planning-v0"),
    )
    evaluate.add_argument("--candidate", type=Path, required=True)
    evaluate.add_argument("--output", type=Path, required=True)
    verify_eval = sub.add_parser("verify-evaluation")
    verify_eval.add_argument(
        "--benchmark-root",
        type=Path,
        default=Path("experiments/presentation/semantic-planning-v0"),
    )
    verify_eval.add_argument("--candidate", type=Path, required=True)
    verify_eval.add_argument("--artifact", type=Path, required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "create":
            artifact = build_candidate(args.benchmark_root, args.case_id)
            write_new(args.output, artifact)
            print(f"Created semantic baseline: {args.case_id}")
        elif args.command == "verify":
            artifact = verify_candidate(args.benchmark_root, args.artifact)
            print(
                f"Verified semantic baseline: {artifact['benchmark']['caseId']}"
            )
        elif args.command == "evaluate":
            artifact = build_evaluation(
                args.benchmark_root, args.candidate
            )
            write_new(args.output, artifact)
            print(
                f"Evaluated semantic baseline: {artifact['benchmark']['caseId']}"
            )
            print(
                json.dumps(
                    artifact["metrics"],
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
        else:
            artifact = verify_evaluation(
                args.benchmark_root,
                args.candidate,
                args.artifact,
            )
            print(
                f"Verified semantic evaluation: {artifact['benchmark']['caseId']}"
            )
        return 0
    except SemanticClaimsBaselineError as error:
        print(f"semantic claims baseline error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
