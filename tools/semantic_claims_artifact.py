#!/usr/bin/env python3
"""Create and verify replayable oracle Semantic Claims artifacts for benchmark v0."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from active_epoch.hashing import append_field, canonical_json_bytes
from verify_semantic_planning_benchmark import (
    FROZEN_MANIFEST_SHA256,
    ValidationError,
    validate_benchmark,
)

SCHEMA_VERSION = "semantic-claims-artifact-v0"
HASH_DOMAIN = b"LogicLensSemanticClaimsArtifact\0"
HASH_VERSION = bytes((1,))


class SemanticClaimsArtifactError(RuntimeError):
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
        raise SemanticClaimsArtifactError(f"cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise SemanticClaimsArtifactError(f"{label} must be a JSON object: {path}")
    return value, raw


def exact_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = required - set(value)
    extra = set(value) - required
    if missing:
        raise SemanticClaimsArtifactError(f"{label} missing keys: {sorted(missing)}")
    if extra:
        raise SemanticClaimsArtifactError(f"{label} has unknown keys: {sorted(extra)}")


def load_case(benchmark_root: Path, case_id: str, expected_manifest_sha256: str | None):
    try:
        summary = validate_benchmark(benchmark_root, expected_manifest_sha256)
    except ValidationError as error:
        raise SemanticClaimsArtifactError(f"benchmark validation failed: {error}") from error
    manifest, manifest_raw = read_object(benchmark_root / "manifest.json", "benchmark manifest")
    for entry in manifest["files"]:
        relative = entry["path"]
        if not relative.startswith("cases/") or not relative.endswith(".json"):
            continue
        case_path = benchmark_root / relative
        case, case_raw = read_object(case_path, "benchmark case")
        if case.get("caseId") == case_id:
            return summary, manifest_raw, relative, case, case_raw
    raise SemanticClaimsArtifactError(f"unknown benchmark caseId: {case_id}")


def build_artifact(
    benchmark_root: Path,
    case_id: str,
    *,
    expected_manifest_sha256: str | None = FROZEN_MANIFEST_SHA256,
) -> dict[str, Any]:
    summary, manifest_raw, case_path, case, case_raw = load_case(
        benchmark_root.resolve(), case_id, expected_manifest_sha256
    )
    task = case["task"]
    payload: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "stage": "oracle-semantic-claims",
        "benchmark": {
            "benchmarkId": summary.benchmark_id,
            "manifestSha256": sha256_prefixed(manifest_raw),
            "caseId": case_id,
            "casePath": case_path,
            "caseSha256": sha256_prefixed(case_raw),
        },
        "producer": {
            "kind": "oracle-fixture",
            "sourceField": "oracleSemanticClaims",
        },
        "task": {
            "language": task["language"],
            "goal": task["goal"],
            "textSha256": sha256_prefixed(task["text"].encode("utf-8")),
        },
        "claims": deepcopy(case["oracleSemanticClaims"]),
    }
    payload["artifactHash"] = artifact_hash(payload)
    return payload


def validate_artifact_shape(artifact: dict[str, Any]) -> None:
    exact_keys(
        artifact,
        {"schemaVersion", "stage", "benchmark", "producer", "task", "claims", "artifactHash"},
        "artifact",
    )
    if artifact["schemaVersion"] != SCHEMA_VERSION:
        raise SemanticClaimsArtifactError("unsupported semantic claims artifact schema")
    if artifact["stage"] != "oracle-semantic-claims":
        raise SemanticClaimsArtifactError("artifact stage must be oracle-semantic-claims")
    benchmark = artifact["benchmark"]
    producer = artifact["producer"]
    task = artifact["task"]
    if not isinstance(benchmark, dict) or not isinstance(producer, dict) or not isinstance(task, dict):
        raise SemanticClaimsArtifactError("benchmark, producer, and task must be objects")
    exact_keys(
        benchmark,
        {"benchmarkId", "manifestSha256", "caseId", "casePath", "caseSha256"},
        "artifact.benchmark",
    )
    exact_keys(producer, {"kind", "sourceField"}, "artifact.producer")
    exact_keys(task, {"language", "goal", "textSha256"}, "artifact.task")
    if producer != {"kind": "oracle-fixture", "sourceField": "oracleSemanticClaims"}:
        raise SemanticClaimsArtifactError("unsupported producer: only exact oracle-fixture is allowed in v0")
    if not isinstance(artifact["claims"], list) or not artifact["claims"]:
        raise SemanticClaimsArtifactError("claims must be a non-empty array")
    for field in ("manifestSha256", "caseSha256"):
        value = benchmark[field]
        if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
            raise SemanticClaimsArtifactError(f"artifact.benchmark.{field} is not a SHA-256 value")
    if not isinstance(task["textSha256"], str) or not task["textSha256"].startswith("sha256:"):
        raise SemanticClaimsArtifactError("artifact.task.textSha256 is not a SHA-256 value")
    if not isinstance(artifact["artifactHash"], str) or not artifact["artifactHash"].startswith("sha256:"):
        raise SemanticClaimsArtifactError("artifactHash is not a SHA-256 value")


def verify_artifact(
    benchmark_root: Path,
    artifact_path: Path,
    *,
    expected_manifest_sha256: str | None = FROZEN_MANIFEST_SHA256,
) -> dict[str, Any]:
    artifact, raw = read_object(artifact_path.resolve(), "semantic claims artifact")
    validate_artifact_shape(artifact)
    expected = build_artifact(
        benchmark_root.resolve(),
        artifact["benchmark"]["caseId"],
        expected_manifest_sha256=expected_manifest_sha256,
    )
    if artifact != expected:
        raise SemanticClaimsArtifactError(
            "artifact does not exactly reproduce the benchmark case; claims may be stale, altered, or normalized"
        )
    canonical = canonical_json_bytes(artifact)
    if raw != canonical:
        raise SemanticClaimsArtifactError("artifact JSON is valid but not in canonical byte representation")
    without_hash = deepcopy(artifact)
    recorded_hash = without_hash.pop("artifactHash")
    if artifact_hash(without_hash) != recorded_hash:
        raise SemanticClaimsArtifactError("artifactHash mismatch")
    return artifact


def create_command(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    if output.exists():
        raise SemanticClaimsArtifactError(f"output already exists: {output}")
    artifact = build_artifact(args.benchmark_root, args.case_id)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(artifact))
    print(f"Created oracle semantic claims artifact: {artifact['benchmark']['caseId']}")
    print(f"Artifact hash: {artifact['artifactHash']}")
    print(f"Output: {output}")
    return 0


def verify_command(args: argparse.Namespace) -> int:
    artifact = verify_artifact(args.benchmark_root, args.artifact)
    print(f"Verified oracle semantic claims artifact: {artifact['benchmark']['caseId']}")
    print(f"Artifact hash: {artifact['artifactHash']}")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--benchmark-root", type=Path, default=Path("experiments/presentation/semantic-planning-v0"))
    create.add_argument("--case-id", required=True)
    create.add_argument("--output", type=Path, required=True)
    create.set_defaults(handler=create_command)
    verify = sub.add_parser("verify")
    verify.add_argument("--benchmark-root", type=Path, default=Path("experiments/presentation/semantic-planning-v0"))
    verify.add_argument("--artifact", type=Path, required=True)
    verify.set_defaults(handler=verify_command)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.handler(args)
    except SemanticClaimsArtifactError as error:
        print(f"semantic claims artifact error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
