#!/usr/bin/env python3
"""Create and verify a reviewed authorization for one staged LogicLens revision.

This command records authorization only. It never copies a staged package into an
active location, applies a revision, or updates an active pointer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from active_epoch.hashing import aggregate_hash, canonical_json_bytes, sha256
from builder_candidate.cli import tree_bytes, verify_active_baseline
from build_builder_staged_revision import (
    PACKAGE_DOMAIN as STAGED_PACKAGE_DOMAIN,
    PACKAGE_VERSION as STAGED_PACKAGE_VERSION,
    validate_staged_runtime,
)


UTF8 = "utf-8"
DECISION_DOMAIN = b"LogicLensActivationDecision\0"
DECISION_VERSION = bytes((1,))
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ActivationDecisionError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    add_common_inputs(create)
    create.add_argument("--decision-id", required=True)
    create.add_argument("--output", required=True, type=Path)

    verify = subparsers.add_parser("verify")
    add_common_inputs(verify)
    verify.add_argument("--decision", required=True, type=Path)

    return parser.parse_args()


def add_common_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--staged", required=True, type=Path)
    parser.add_argument("--active-root", required=True, type=Path)
    parser.add_argument("--candidate-manifest", required=True, type=Path)
    parser.add_argument("--overlay-manifest", required=True, type=Path)
    parser.add_argument("--staged-schema", required=True, type=Path)
    parser.add_argument("--decision-schema", required=True, type=Path)
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--timeout-ms", type=int, default=30_000)


def main() -> int:
    args = parse_args()
    if not 100 <= args.timeout_ms <= 60_000:
        raise ActivationDecisionError("timeout-ms must be between 100 and 60000")
    timeout_seconds = args.timeout_ms / 1000.0

    if args.command == "create":
        output = args.output.resolve()
        require_fresh_output(
            output,
            [
                args.staged.resolve(),
                args.active_root.resolve(),
                args.candidate_manifest.resolve(),
                args.overlay_manifest.resolve(),
            ],
        )
        record = create_activation_decision(
            decision_id=args.decision_id,
            staged_root=args.staged,
            active_root=args.active_root,
            candidate_manifest_path=args.candidate_manifest,
            overlay_manifest_path=args.overlay_manifest,
            staged_schema_path=args.staged_schema,
            decision_schema_path=args.decision_schema,
            swipl=args.swipl,
            timeout_seconds=timeout_seconds,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical_json_bytes(record))
        print(f"Created activation decision: {record['decisionId']}")
        print(f"Decision: {record['decision']}")
        print(f"Target revision: {record['target']['epoch']}.{record['target']['revision']}")
        print(f"Decision hash: {record['decisionHash']}")
        print("Apply: not performed")
        print("Active pointer update: not performed")
        print(f"Output: {output}")
        return 0

    record = verify_activation_decision(
        decision_path=args.decision,
        staged_root=args.staged,
        active_root=args.active_root,
        candidate_manifest_path=args.candidate_manifest,
        overlay_manifest_path=args.overlay_manifest,
        staged_schema_path=args.staged_schema,
        decision_schema_path=args.decision_schema,
        swipl=args.swipl,
        timeout_seconds=timeout_seconds,
    )
    print(f"Verified activation decision: {record['decisionId']}")
    print(f"Decision: {record['decision']}")
    print("Apply: not performed")
    print("Active pointer update: not performed")
    return 0


def create_activation_decision(
    *,
    decision_id: str,
    staged_root: Path,
    active_root: Path,
    candidate_manifest_path: Path,
    overlay_manifest_path: Path,
    staged_schema_path: Path,
    decision_schema_path: Path,
    swipl: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    validate_identifier(decision_id)
    staged = staged_root.resolve()
    active = active_root.resolve()
    if not staged.is_dir():
        raise ActivationDecisionError(f"staged package does not exist: {staged}")
    if not active.is_dir():
        raise ActivationDecisionError(f"active package does not exist: {active}")
    if paths_overlap(staged, active):
        raise ActivationDecisionError("staged and active packages must be separate")

    active_before = tree_bytes(active)
    active_manifest = verify_active_baseline(active_before)
    staged_manifest_path = staged / "manifest.json"
    staged_manifest_bytes = require_file(staged_manifest_path, "staged manifest").read_bytes()
    staged_manifest = decode_json_object(staged_manifest_bytes, "staged manifest")
    staged_schema = read_json_object(staged_schema_path, "staged schema")
    decision_schema = read_json_object(decision_schema_path, "activation decision schema")
    validate_schema(staged_manifest, staged_schema, "staged manifest")
    validate_staged_package(staged, staged_manifest)

    candidate_manifest_file = require_file(
        candidate_manifest_path.resolve(),
        "candidate manifest",
    )
    overlay_manifest_file = require_file(
        overlay_manifest_path.resolve(),
        "overlay manifest",
    )
    candidate_manifest_bytes = candidate_manifest_file.read_bytes()
    overlay_manifest_bytes = overlay_manifest_file.read_bytes()
    candidate_manifest = decode_json_object(candidate_manifest_bytes, "candidate manifest")
    overlay_manifest = decode_json_object(overlay_manifest_bytes, "overlay manifest")
    bind_source_manifests(staged_manifest, candidate_manifest, overlay_manifest)

    expected_current = {
        "epoch": required_nonnegative_int(active_manifest, "epoch", "active manifest"),
        "revision": required_nonnegative_int(
            active_manifest,
            "baseRevision",
            "active manifest",
        ),
        "packageHash": required_hash(active_manifest, "packageHash", "active manifest"),
    }
    target_source = required_object(staged_manifest, "target", "staged manifest")
    target = {
        "epoch": required_nonnegative_int(target_source, "epoch", "staged target"),
        "revision": required_positive_int(target_source, "revision", "staged target"),
        "packageHash": required_hash(staged_manifest, "packageHash", "staged manifest"),
    }
    rollback = deepcopy(required_object(staged_manifest, "rollback", "staged manifest"))
    validate_transition(expected_current, target, rollback)

    try:
        validate_staged_runtime(
            staged_root=staged,
            active_root=active,
            candidate_manifest=candidate_manifest,
            overlay_manifest=overlay_manifest,
            swipl=swipl,
            timeout_seconds=timeout_seconds,
        )
    except Exception as exc:
        raise ActivationDecisionError(
            f"staged runtime revalidation failed: {exc}"
        ) from exc

    if tree_bytes(active) != active_before:
        raise ActivationDecisionError("authorization validation modified the active package")

    source = required_object(staged_manifest, "source", "staged manifest")
    record: dict[str, Any] = {
        "schemaVersion": "0.1",
        "stage": "activation-decision",
        "decisionId": decision_id,
        "decision": "authorize",
        "source": {
            "stageId": required_string(staged_manifest, "stageId", "staged manifest"),
            "stagedPackageHash": target["packageHash"],
            "promotionPlanHash": required_hash(
                source,
                "promotionPlanHash",
                "staged source",
            ),
            "plannedRevisionHash": required_hash(
                source,
                "plannedRevisionHash",
                "staged source",
            ),
            "assessmentHash": required_hash(
                source,
                "assessmentHash",
                "staged source",
            ),
            "overlayHash": required_hash(source, "overlayHash", "staged source"),
            "candidateHash": required_hash(source, "candidateHash", "staged source"),
            "candidatePackageHash": required_hash(
                source,
                "candidatePackageHash",
                "staged source",
            ),
            "basePackageHash": required_hash(
                source,
                "basePackageHash",
                "staged source",
            ),
        },
        "expectedCurrent": expected_current,
        "target": target,
        "rollback": rollback,
        "evidence": {
            "stagedManifestFileHash": sha256(staged_manifest_bytes),
            "activeManifestFileHash": sha256((active / "manifest.json").read_bytes()),
            "candidateManifestFileHash": sha256(candidate_manifest_bytes),
            "overlayManifestFileHash": sha256(overlay_manifest_bytes),
        },
        "checks": {
            "stagedSchemaVerified": True,
            "stagedFilesVerified": True,
            "stagedPackageHashVerified": True,
            "sourceBindingsVerified": True,
            "activeBaselineVerified": True,
            "transitionIsNextRevision": True,
            "rollbackPinned": True,
            "runtimeRevalidated": True,
            "activePackageUntouched": True,
        },
        "intent": {
            "authorization": "recorded-only",
            "apply": "not-performed",
            "activePointerUpdate": "not-performed",
        },
    }
    record["decisionHash"] = compute_decision_hash(record)
    validate_schema(record, decision_schema, "activation decision")
    return record


def verify_activation_decision(
    *,
    decision_path: Path,
    staged_root: Path,
    active_root: Path,
    candidate_manifest_path: Path,
    overlay_manifest_path: Path,
    staged_schema_path: Path,
    decision_schema_path: Path,
    swipl: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    record = read_json_object(decision_path, "activation decision")
    schema = read_json_object(decision_schema_path, "activation decision schema")
    validate_schema(record, schema, "activation decision")
    if compute_decision_hash(record) != record.get("decisionHash"):
        raise ActivationDecisionError("activation decision hash does not match its payload")
    if record.get("decision") != "authorize":
        raise ActivationDecisionError("activation decision is not authorize")

    expected = create_activation_decision(
        decision_id=required_string(record, "decisionId", "activation decision"),
        staged_root=staged_root,
        active_root=active_root,
        candidate_manifest_path=candidate_manifest_path,
        overlay_manifest_path=overlay_manifest_path,
        staged_schema_path=staged_schema_path,
        decision_schema_path=decision_schema_path,
        swipl=swipl,
        timeout_seconds=timeout_seconds,
    )
    if record != expected:
        raise ActivationDecisionError(
            "activation decision differs from the reviewed staged and active packages"
        )
    return record


def validate_staged_package(root: Path, manifest: dict[str, Any]) -> None:
    actual = tree_bytes(root)
    actual.pop(PurePosixPath("manifest.json"), None)
    expected_files = {
        str(path): sha256(content)
        for path, content in sorted(actual.items(), key=lambda item: str(item[0]))
    }
    if manifest.get("files") != expected_files:
        raise ActivationDecisionError("staged per-file hashes do not match its contents")
    package_hash = aggregate_hash(
        STAGED_PACKAGE_DOMAIN,
        STAGED_PACKAGE_VERSION,
        actual.items(),
    )
    if manifest.get("packageHash") != package_hash:
        raise ActivationDecisionError("staged packageHash is invalid")
    checks = required_object(manifest, "checks", "staged manifest")
    if not checks or not all(value is True for value in checks.values()):
        raise ActivationDecisionError("staged manifest does not contain all passed checks")
    intent = required_object(manifest, "intent", "staged manifest")
    if (
        intent.get("staging") != "isolated-output-only"
        or intent.get("apply") != "not-performed"
        or intent.get("activePointerUpdate") != "not-performed"
    ):
        raise ActivationDecisionError("staged package crossed the activation boundary")


def bind_source_manifests(
    staged: dict[str, Any],
    candidate: dict[str, Any],
    overlay: dict[str, Any],
) -> None:
    source = required_object(staged, "source", "staged manifest")
    pairs = (
        (candidate, "candidateHash", "candidateHash"),
        (candidate, "candidatePackageHash", "candidatePackageHash"),
        (candidate, "basePackageHash", "basePackageHash"),
        (overlay, "overlayHash", "overlayHash"),
    )
    for document, document_key, source_key in pairs:
        if document.get(document_key) != source.get(source_key):
            raise ActivationDecisionError(
                f"{document_key} differs from the staged source binding"
            )
    overlay_source = required_object(overlay, "source", "overlay manifest")
    for key in (
        "candidateHash",
        "candidatePackageHash",
        "basePackageHash",
        "promotionPlanHash",
    ):
        if overlay_source.get(key) != source.get(key):
            raise ActivationDecisionError(
                f"overlay source {key} differs from the staged source binding"
            )
    overlay_target = required_object(overlay, "target", "overlay manifest")
    staged_target = required_object(staged, "target", "staged manifest")
    if (
        overlay_target.get("epoch") != staged_target.get("epoch")
        or overlay_target.get("revision") != staged_target.get("revision")
    ):
        raise ActivationDecisionError("overlay target differs from staged target")


def validate_transition(
    current: dict[str, Any],
    target: dict[str, Any],
    rollback: dict[str, Any],
) -> None:
    if (
        target["epoch"] != current["epoch"]
        or target["revision"] != current["revision"] + 1
    ):
        raise ActivationDecisionError(
            "target must be the next revision of the current active epoch"
        )
    if rollback != current:
        raise ActivationDecisionError("rollback does not match the current active package")


def compute_decision_hash(record: dict[str, Any]) -> str:
    payload = deepcopy(record)
    payload.pop("decisionHash", None)
    digest = hashlib.sha256()
    digest.update(DECISION_DOMAIN)
    digest.update(DECISION_VERSION)
    digest.update(canonical_json_bytes(payload))
    return "sha256:" + digest.hexdigest()


def require_fresh_output(output: Path, sources: list[Path]) -> None:
    if output.exists():
        raise ActivationDecisionError(f"output already exists: {output}")
    for source in sources:
        if paths_overlap(output, source):
            raise ActivationDecisionError(f"output overlaps a reviewed source: {source}")


def paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def validate_identifier(value: str) -> None:
    if not IDENTIFIER.fullmatch(value):
        raise ActivationDecisionError("decision ID is not a safe identifier")


def require_file(path: Path, context: str) -> Path:
    if not path.is_file():
        raise ActivationDecisionError(f"{context} does not exist: {path}")
    return path


def decode_json_object(content: bytes, context: str) -> dict[str, Any]:
    try:
        value = json.loads(content.decode(UTF8))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ActivationDecisionError(f"cannot decode {context}: {exc}") from exc
    if not isinstance(value, dict):
        raise ActivationDecisionError(f"{context} must be a JSON object")
    return value


def read_json_object(path: Path, context: str) -> dict[str, Any]:
    resolved = path.resolve()
    return decode_json_object(require_file(resolved, context).read_bytes(), context)


def validate_schema(value: dict[str, Any], schema: dict[str, Any], context: str) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: list(item.path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: "
            f"{error.message}"
            for error in errors[:10]
        )
        raise ActivationDecisionError(f"{context} schema validation failed: {details}")


def required_object(value: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise ActivationDecisionError(f"{context} object {key!r} is missing")
    return result


def required_string(value: dict[str, Any], key: str, context: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise ActivationDecisionError(f"{context} string {key!r} is missing")
    return result


def required_hash(value: dict[str, Any], key: str, context: str) -> str:
    result = required_string(value, key, context)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", result):
        raise ActivationDecisionError(f"{context} hash {key!r} is invalid")
    return result


def required_nonnegative_int(value: dict[str, Any], key: str, context: str) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool) or result < 0:
        raise ActivationDecisionError(f"{context} integer {key!r} is invalid")
    return result


def required_positive_int(value: dict[str, Any], key: str, context: str) -> int:
    result = required_nonnegative_int(value, key, context)
    if result < 1:
        raise ActivationDecisionError(f"{context} integer {key!r} must be positive")
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ActivationDecisionError, OSError, ValueError) as exc:
        print(f"Activation decision failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
