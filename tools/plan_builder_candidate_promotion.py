#!/usr/bin/env python3
"""Create and verify additive Builder candidate promotion plans.

This tool plans a future revision. It never copies files into an active epoch,
changes a manifest, or updates an active pointer.
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

from active_epoch.hashing import append_field, canonical_json_bytes
from review_builder_candidate import compute_review_hash


UTF8 = "utf-8"
PLAN_HASH_DOMAIN = b"LogicLensCandidatePromotionPlan\0"
PLAN_HASH_VERSION = bytes((1,))
REVISION_HASH_DOMAIN = b"LogicLensPlannedRevision\0"
REVISION_HASH_VERSION = bytes((1,))
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
EXPECTED_REVIEW_CHECKS = {
    "identityConsistent",
    "baselineConsistent",
    "candidateValidationPassed",
    "oracleValidationPassed",
    "comparisonValidationsPassed",
    "runtimeOutputsEqual",
    "activeFilesUnchanged",
}
KIND_ROOTS = {
    "rule": "rules",
    "test": "tests",
    "ui": "ui",
}
KIND_SUFFIXES = {
    "rule": ".pl",
    "test": ".pl",
    "ui": ".json",
}


class PromotionPlanError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    add_common_inputs(create)
    create.add_argument("--plan-id", required=True)
    create.add_argument("--output", required=True, type=Path)

    verify = subparsers.add_parser("verify")
    add_common_inputs(verify)
    verify.add_argument("--plan", required=True, type=Path)

    return parser.parse_args()


def add_common_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--candidate-manifest", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--review-schema", required=True, type=Path)
    parser.add_argument("--plan-schema", required=True, type=Path)


def main() -> int:
    args = parse_args()
    if args.command == "create":
        output = args.output.resolve()
        candidate_root = args.candidate_root.resolve()
        if output.exists():
            raise PromotionPlanError(f"output already exists: {output}")
        if output == candidate_root or candidate_root in output.parents:
            raise PromotionPlanError("output must not overlap the candidate package")
        record = create_promotion_plan(
            review_path=args.review,
            candidate_manifest_path=args.candidate_manifest,
            candidate_root=args.candidate_root,
            review_schema_path=args.review_schema,
            plan_schema_path=args.plan_schema,
            plan_id=args.plan_id,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical_json_bytes(record))
        print(f"Created promotion plan: {record['planId']}")
        print(
            "Target revision: "
            f"{record['target']['epoch']}.{record['target']['revision']}"
        )
        print(f"Added files: {len(record['changes']['addedFiles'])}")
        print(f"Planned revision hash: {record['target']['plannedRevisionHash']}")
        print("Apply: not performed")
        print(f"Output: {output}")
        return 0

    verify_promotion_plan(
        plan_path=args.plan,
        review_path=args.review,
        candidate_manifest_path=args.candidate_manifest,
        candidate_root=args.candidate_root,
        review_schema_path=args.review_schema,
        plan_schema_path=args.plan_schema,
    )
    print(f"Verified promotion plan: {args.plan.resolve()}")
    print("Apply: not performed")
    return 0


def create_promotion_plan(
    *,
    review_path: Path,
    candidate_manifest_path: Path,
    candidate_root: Path,
    review_schema_path: Path,
    plan_schema_path: Path,
    plan_id: str,
) -> dict[str, Any]:
    validate_identifier(plan_id, "plan ID")
    review, review_bytes = read_json_object(review_path, "candidate review")
    candidate, candidate_bytes = read_json_object(
        candidate_manifest_path,
        "candidate manifest",
    )
    review_schema, _ = read_json_object(review_schema_path, "candidate review schema")
    plan_schema, _ = read_json_object(plan_schema_path, "promotion plan schema")
    validate_schema(review, review_schema, "candidate review")

    review_hash = required_hash(review, "reviewHash", "candidate review")
    if compute_review_hash(review) != review_hash:
        raise PromotionPlanError("candidate review hash does not match its payload")
    if review.get("decision") != "recommend":
        raise PromotionPlanError("candidate review decision is not recommend")
    if required_object(review, "activation").get("status") != "not-performed":
        raise PromotionPlanError("candidate review already crossed the activation boundary")
    review_checks = required_object(review, "checks")
    if set(review_checks) != EXPECTED_REVIEW_CHECKS or not all(
        review_checks.get(name) is True for name in EXPECTED_REVIEW_CHECKS
    ):
        raise PromotionPlanError("candidate review does not contain all passed checks")

    subject = required_object(review, "subject")
    evidence = required_object(review, "evidence")
    candidate_manifest_file_hash = sha256(candidate_bytes)
    if evidence.get("candidateManifestFileHash") != candidate_manifest_file_hash:
        raise PromotionPlanError("candidate manifest file hash differs from the review")

    validate_candidate_identity(candidate, subject)
    added_files = verify_candidate_files(candidate, candidate_root)

    base_epoch = required_nonnegative_int(candidate, "baseEpoch", "candidate manifest")
    base_revision = required_nonnegative_int(
        candidate,
        "baseRevision",
        "candidate manifest",
    )
    base_package_hash = required_hash(
        candidate,
        "basePackageHash",
        "candidate manifest",
    )
    candidate_hash = required_hash(candidate, "candidateHash", "candidate manifest")
    target_epoch = base_epoch
    target_revision = base_revision + 1
    planned_revision_hash = compute_planned_revision_hash(
        review_hash=review_hash,
        base_package_hash=base_package_hash,
        candidate_hash=candidate_hash,
        target_epoch=target_epoch,
        target_revision=target_revision,
        added_files=added_files,
    )

    plan: dict[str, Any] = {
        "schemaVersion": "0.1",
        "stage": "candidate-promotion-plan",
        "planId": plan_id,
        "review": {
            "reviewId": required_string(review, "reviewId", "candidate review"),
            "reviewHash": review_hash,
            "decision": "recommend",
        },
        "source": {
            "candidateId": required_string(
                candidate,
                "candidateId",
                "candidate manifest",
            ),
            "taskId": required_string(candidate, "taskId", "candidate manifest"),
            "baseEpoch": base_epoch,
            "baseRevision": base_revision,
            "basePackageHash": base_package_hash,
            "candidateHash": candidate_hash,
            "candidatePackageHash": required_hash(
                candidate,
                "candidatePackageHash",
                "candidate manifest",
            ),
        },
        "target": {
            "epoch": target_epoch,
            "revision": target_revision,
            "mode": "additive-revision",
            "plannedRevisionHash": planned_revision_hash,
        },
        "changes": {
            "addedFiles": added_files,
            "modifiedActiveFiles": [],
            "removedActiveFiles": [],
        },
        "rollback": {
            "epoch": base_epoch,
            "revision": base_revision,
            "packageHash": base_package_hash,
        },
        "intent": {
            "manifest": "planned-only",
            "activePointerUpdate": "not-performed",
            "apply": "not-performed",
        },
        "evidence": {
            "reviewFileHash": sha256(review_bytes),
            "candidateManifestFileHash": candidate_manifest_file_hash,
        },
        "checks": {
            "reviewRecommended": True,
            "reviewHashVerified": True,
            "candidateIdentityConsistent": True,
            "candidateFilesVerified": True,
            "additiveOnly": True,
            "rollbackPinned": True,
        },
    }
    plan["promotionPlanHash"] = compute_promotion_plan_hash(plan)
    validate_schema(plan, plan_schema, "candidate promotion plan")
    return plan


def verify_promotion_plan(
    *,
    plan_path: Path,
    review_path: Path,
    candidate_manifest_path: Path,
    candidate_root: Path,
    review_schema_path: Path,
    plan_schema_path: Path,
) -> dict[str, Any]:
    plan, _ = read_json_object(plan_path, "candidate promotion plan")
    plan_schema, _ = read_json_object(plan_schema_path, "promotion plan schema")
    validate_schema(plan, plan_schema, "candidate promotion plan")
    if compute_promotion_plan_hash(plan) != plan.get("promotionPlanHash"):
        raise PromotionPlanError("promotion plan hash does not match its payload")

    expected = create_promotion_plan(
        review_path=review_path,
        candidate_manifest_path=candidate_manifest_path,
        candidate_root=candidate_root,
        review_schema_path=review_schema_path,
        plan_schema_path=plan_schema_path,
        plan_id=required_string(plan, "planId", "promotion plan"),
    )
    if plan != expected:
        raise PromotionPlanError(
            "promotion plan does not match the supplied review and candidate package"
        )
    return plan


def validate_candidate_identity(
    candidate: dict[str, Any],
    subject: dict[str, Any],
) -> None:
    if candidate.get("schemaVersion") != "0.1" or candidate.get("stage") != "candidate":
        raise PromotionPlanError("candidate manifest stage or version is invalid")
    pairs = (
        ("taskId", "taskId"),
        ("basePackageHash", "basePackageHash"),
        ("candidateHash", "candidateHash"),
        ("candidatePackageHash", "candidatePackageHash"),
    )
    mismatches = [
        candidate_key
        for candidate_key, subject_key in pairs
        if candidate.get(candidate_key) != subject.get(subject_key)
    ]
    if mismatches:
        raise PromotionPlanError(
            "candidate identity differs from the reviewed subject: "
            + ", ".join(mismatches)
        )


def verify_candidate_files(
    candidate: dict[str, Any],
    candidate_root: Path,
) -> list[dict[str, Any]]:
    root = candidate_root.resolve()
    if not root.is_dir():
        raise PromotionPlanError(f"candidate root does not exist: {root}")
    files = candidate.get("files")
    if not isinstance(files, dict) or not 1 <= len(files) <= 64:
        raise PromotionPlanError("candidate manifest files must contain 1..64 entries")

    result: list[dict[str, Any]] = []
    for raw_path, metadata in sorted(files.items()):
        if not isinstance(raw_path, str) or not isinstance(metadata, dict):
            raise PromotionPlanError("candidate file declaration is invalid")
        relative_path = validate_candidate_path(raw_path, metadata.get("kind"))
        expected_hash = required_hash(metadata, "sha256", f"candidate file {raw_path}")
        expected_bytes = required_positive_int(
            metadata,
            "bytes",
            f"candidate file {raw_path}",
        )
        destination = root.joinpath(*relative_path.parts)
        if destination.is_symlink():
            raise PromotionPlanError(f"candidate file is a symlink: {raw_path}")
        try:
            resolved = destination.resolve(strict=True)
        except OSError as exc:
            raise PromotionPlanError(f"candidate file is missing: {raw_path}") from exc
        if root not in resolved.parents or not resolved.is_file():
            raise PromotionPlanError(f"candidate file escaped its package: {raw_path}")
        content = resolved.read_bytes()
        if len(content) != expected_bytes:
            raise PromotionPlanError(f"candidate file size differs: {raw_path}")
        if sha256(content) != expected_hash:
            raise PromotionPlanError(f"candidate file hash differs: {raw_path}")
        result.append(
            {
                "path": raw_path,
                "kind": metadata["kind"],
                "sha256": expected_hash,
                "bytes": expected_bytes,
            }
        )
    return result


def validate_candidate_path(raw_path: str, kind: Any) -> PurePosixPath:
    if kind not in KIND_ROOTS:
        raise PromotionPlanError(f"unknown candidate file kind: {kind!r}")
    if "\\" in raw_path:
        raise PromotionPlanError(f"candidate path contains a backslash: {raw_path}")
    path = PurePosixPath(raw_path)
    if (
        path.is_absolute()
        or ".." in path.parts
        or len(path.parts) != 2
        or path.parts[0] != KIND_ROOTS[kind]
        or not path.name.endswith(KIND_SUFFIXES[kind])
        or not path.name
    ):
        raise PromotionPlanError(f"candidate path is outside the additive allowlist: {raw_path}")
    safe_name = path.name[: -len(KIND_SUFFIXES[kind])]
    if not safe_name or not re.fullmatch(r"[A-Za-z0-9._-]+", safe_name):
        raise PromotionPlanError(f"candidate filename is unsafe: {raw_path}")
    return path


def compute_planned_revision_hash(
    *,
    review_hash: str,
    base_package_hash: str,
    candidate_hash: str,
    target_epoch: int,
    target_revision: int,
    added_files: list[dict[str, Any]],
) -> str:
    digest = hashlib.sha256()
    digest.update(REVISION_HASH_DOMAIN)
    digest.update(REVISION_HASH_VERSION)
    for value in (
        review_hash,
        base_package_hash,
        candidate_hash,
        str(target_epoch),
        str(target_revision),
    ):
        append_field(digest, value.encode(UTF8))
    for item in added_files:
        append_field(digest, canonical_json_bytes(item))
    return "sha256:" + digest.hexdigest()


def compute_promotion_plan_hash(plan: dict[str, Any]) -> str:
    payload = deepcopy(plan)
    payload.pop("promotionPlanHash", None)
    digest = hashlib.sha256()
    digest.update(PLAN_HASH_DOMAIN)
    digest.update(PLAN_HASH_VERSION)
    digest.update(canonical_json_bytes(payload))
    return "sha256:" + digest.hexdigest()


def read_json_object(path: Path, context: str) -> tuple[dict[str, Any], bytes]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise PromotionPlanError(f"{context} does not exist: {resolved}")
    try:
        content = resolved.read_bytes()
        value = json.loads(content.decode(UTF8))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PromotionPlanError(f"cannot read {context}: {exc}") from exc
    if not isinstance(value, dict):
        raise PromotionPlanError(f"{context} must be a JSON object")
    return value, content


def validate_schema(value: dict[str, Any], schema: dict[str, Any], context: str) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors[:10]
        )
        raise PromotionPlanError(f"{context} schema validation failed: {details}")


def required_object(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise PromotionPlanError(f"required object {key!r} is missing")
    return result


def required_string(value: dict[str, Any], key: str, context: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise PromotionPlanError(f"{context} field {key!r} is missing")
    return result


def required_hash(value: dict[str, Any], key: str, context: str) -> str:
    result = required_string(value, key, context)
    if not SHA256_PATTERN.fullmatch(result):
        raise PromotionPlanError(f"{context} field {key!r} is not SHA-256")
    return result


def required_nonnegative_int(value: dict[str, Any], key: str, context: str) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool) or result < 0:
        raise PromotionPlanError(f"{context} field {key!r} is not non-negative")
    return result


def required_positive_int(value: dict[str, Any], key: str, context: str) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool) or result <= 0:
        raise PromotionPlanError(f"{context} field {key!r} is not positive")
    return result


def validate_identifier(value: str, context: str) -> None:
    if not IDENTIFIER.fullmatch(value):
        raise PromotionPlanError(f"{context} is not a safe identifier")


def sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PromotionPlanError, OSError, ValueError) as exc:
        print(f"Promotion planning failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
