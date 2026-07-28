#!/usr/bin/env python3
"""Assess whether a reviewed Builder candidate can become a functional revision.

The assessor is read-only. It never stages files, applies a plan, changes an active
manifest, or updates an active pointer.
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

from active_epoch.hashing import canonical_json_bytes, sha256
from builder_candidate.cli import tree_bytes, verify_active_baseline
from plan_builder_candidate_promotion import (
    compute_promotion_plan_hash,
    verify_candidate_files,
)


UTF8 = "utf-8"
ASSESSMENT_DOMAIN = b"LogicLensCandidateActivationReadiness\0"
ASSESSMENT_VERSION = bytes((1,))
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
MODULE_RE = re.compile(
    r":-\s*module\s*\(\s*([a-z][A-Za-z0-9_]*)\s*,\s*\[(.*?)\]\s*\)\s*\.",
    re.DOTALL,
)
EXPORT_RE = re.compile(r"\b([a-z][A-Za-z0-9_]*)\s*/\s*([0-9]+)\b")
LOADED_EPOCH_RE = re.compile(r"\bloaded_epoch\s*\(\s*([0-9]+)\s*\)\s*\.")
LOADED_REVISION_RE = re.compile(r"\bloaded_revision\s*\(\s*([0-9]+)\s*\)\s*\.")


class ActivationReadinessError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    assess = subparsers.add_parser("assess")
    add_common_inputs(assess)
    assess.add_argument("--assessment-id", required=True)
    assess.add_argument("--output", required=True, type=Path)

    verify = subparsers.add_parser("verify")
    add_common_inputs(verify)
    verify.add_argument("--assessment", required=True, type=Path)
    return parser.parse_args()


def add_common_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--candidate-manifest", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--active-root", required=True, type=Path)
    parser.add_argument("--runtime-root", required=True, type=Path)
    parser.add_argument("--plan-schema", required=True, type=Path)
    parser.add_argument("--readiness-schema", required=True, type=Path)


def main() -> int:
    args = parse_args()
    if args.command == "assess":
        output = args.output.resolve()
        if output.exists():
            raise ActivationReadinessError(f"output already exists: {output}")
        record = create_assessment(
            plan_path=args.plan,
            candidate_manifest_path=args.candidate_manifest,
            candidate_root=args.candidate_root,
            active_root=args.active_root,
            runtime_root=args.runtime_root,
            plan_schema_path=args.plan_schema,
            readiness_schema_path=args.readiness_schema,
            assessment_id=args.assessment_id,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical_json_bytes(record))
        print(f"Activation readiness: {record['status']}")
        print(f"Assessment: {record['assessmentId']}")
        print(f"Blockers: {len(record['blockers'])}")
        print("Staging: not performed")
        print(f"Output: {output}")
        return 0

    verify_assessment(
        assessment_path=args.assessment,
        plan_path=args.plan,
        candidate_manifest_path=args.candidate_manifest,
        candidate_root=args.candidate_root,
        active_root=args.active_root,
        runtime_root=args.runtime_root,
        plan_schema_path=args.plan_schema,
        readiness_schema_path=args.readiness_schema,
    )
    print(f"Verified activation readiness: {args.assessment.resolve()}")
    print("Staging: not performed")
    return 0


def create_assessment(
    *,
    plan_path: Path,
    candidate_manifest_path: Path,
    candidate_root: Path,
    active_root: Path,
    runtime_root: Path,
    plan_schema_path: Path,
    readiness_schema_path: Path,
    assessment_id: str,
) -> dict[str, Any]:
    validate_identifier(assessment_id)
    plan, _ = read_json_object(plan_path, "promotion plan")
    candidate, candidate_bytes = read_json_object(
        candidate_manifest_path,
        "candidate manifest",
    )
    plan_schema, _ = read_json_object(plan_schema_path, "promotion plan schema")
    readiness_schema, _ = read_json_object(
        readiness_schema_path,
        "activation readiness schema",
    )
    validate_schema(plan, plan_schema, "promotion plan")
    if compute_promotion_plan_hash(plan) != plan.get("promotionPlanHash"):
        raise ActivationReadinessError("promotion plan hash does not match its payload")

    source = required_object(plan, "source")
    target = required_object(plan, "target")
    evidence = required_object(plan, "evidence")
    if evidence.get("candidateManifestFileHash") != sha256(candidate_bytes):
        raise ActivationReadinessError("candidate manifest differs from the promotion plan")
    for key in ("candidateHash", "candidatePackageHash", "basePackageHash"):
        if candidate.get(key) != source.get(key):
            raise ActivationReadinessError(
                f"candidate manifest field {key} differs from the promotion plan"
            )

    active = active_root.resolve()
    runtime = runtime_root.resolve()
    if not active.is_dir():
        raise ActivationReadinessError(f"active root does not exist: {active}")
    if not runtime.is_dir():
        raise ActivationReadinessError(f"runtime root does not exist: {runtime}")
    active_manifest = verify_active_baseline(tree_bytes(active))
    if active_manifest.get("packageHash") != source.get("basePackageHash"):
        raise ActivationReadinessError("active baseline hash differs from the plan")

    verified_files = verify_candidate_files(candidate, candidate_root)
    if verified_files != required_object(plan, "changes").get("addedFiles"):
        raise ActivationReadinessError("candidate files differ from the promotion plan")

    modules, exports, rule_paths = candidate_interfaces(candidate_root, verified_files)
    runtime_sources = read_runtime_sources(runtime, rule_paths)
    loaded_epoch = unique_integer(runtime_sources.values(), LOADED_EPOCH_RE)
    loaded_revision = unique_integer(runtime_sources.values(), LOADED_REVISION_RE)
    target_epoch = required_nonnegative_int(target, "epoch")
    target_revision = required_nonnegative_int(target, "revision")

    revision_ready = loaded_epoch == target_epoch and loaded_revision == target_revision
    rule_loaded = rules_have_load_path(runtime_sources, rule_paths)
    predicate_exposed = exports_have_invocation_path(runtime_sources, modules, exports)

    checks = {
        "planVerified": True,
        "baselineVerified": True,
        "candidateFilesVerified": True,
        "targetRevisionRepresented": revision_ready,
        "candidateRuleLoaded": rule_loaded,
        "candidatePredicateExposed": predicate_exposed,
    }
    blockers = build_blockers(checks, target_epoch, target_revision)
    status = "ready" if all(checks.values()) else "blocked"

    record: dict[str, Any] = {
        "schemaVersion": "0.1",
        "stage": "candidate-activation-readiness",
        "assessmentId": assessment_id,
        "status": status,
        "source": {
            "planId": required_string(plan, "planId"),
            "promotionPlanHash": required_string(plan, "promotionPlanHash"),
            "candidateHash": required_string(source, "candidateHash"),
            "candidatePackageHash": required_string(source, "candidatePackageHash"),
            "basePackageHash": required_string(source, "basePackageHash"),
        },
        "target": {
            "epoch": target_epoch,
            "revision": target_revision,
        },
        "observedRuntime": {
            "loadedEpoch": loaded_epoch,
            "loadedRevision": loaded_revision,
            "candidateModules": sorted(modules),
            "candidateExports": sorted(exports),
        },
        "checks": checks,
        "blockers": blockers,
        "intent": {
            "staging": "not-performed",
            "apply": "not-performed",
            "activePointerUpdate": "not-performed",
        },
    }
    record["assessmentHash"] = compute_assessment_hash(record)
    validate_schema(record, readiness_schema, "activation readiness")
    validate_status_consistency(record)
    return record


def verify_assessment(
    *,
    assessment_path: Path,
    plan_path: Path,
    candidate_manifest_path: Path,
    candidate_root: Path,
    active_root: Path,
    runtime_root: Path,
    plan_schema_path: Path,
    readiness_schema_path: Path,
) -> dict[str, Any]:
    record, _ = read_json_object(assessment_path, "activation readiness")
    readiness_schema, _ = read_json_object(
        readiness_schema_path,
        "activation readiness schema",
    )
    validate_schema(record, readiness_schema, "activation readiness")
    validate_status_consistency(record)
    if compute_assessment_hash(record) != record.get("assessmentHash"):
        raise ActivationReadinessError("assessment hash does not match its payload")
    expected = create_assessment(
        plan_path=plan_path,
        candidate_manifest_path=candidate_manifest_path,
        candidate_root=candidate_root,
        active_root=active_root,
        runtime_root=runtime_root,
        plan_schema_path=plan_schema_path,
        readiness_schema_path=readiness_schema_path,
        assessment_id=required_string(record, "assessmentId"),
    )
    if record != expected:
        raise ActivationReadinessError(
            "assessment does not match the supplied plan and runtime trees"
        )
    return record


def candidate_interfaces(
    candidate_root: Path,
    files: list[dict[str, Any]],
) -> tuple[set[str], set[str], set[PurePosixPath]]:
    modules: set[str] = set()
    exports: set[str] = set()
    paths: set[PurePosixPath] = set()
    root = candidate_root.resolve()
    for item in files:
        if item.get("kind") != "rule":
            continue
        relative = PurePosixPath(item["path"])
        paths.add(relative)
        text = root.joinpath(*relative.parts).read_text(encoding=UTF8)
        match = MODULE_RE.search(text)
        if match is None:
            raise ActivationReadinessError(f"candidate rule has no module declaration: {relative}")
        module = match.group(1)
        modules.add(module)
        for name, arity in EXPORT_RE.findall(match.group(2)):
            exports.add(f"{name}/{arity}")
    if not modules or not exports:
        raise ActivationReadinessError("candidate rule exports could not be determined")
    return modules, exports, paths


def read_runtime_sources(
    runtime_root: Path,
    candidate_rule_paths: set[PurePosixPath],
) -> dict[PurePosixPath, str]:
    result: dict[PurePosixPath, str] = {}
    root = runtime_root.resolve()
    for path in sorted(root.rglob("*.pl")):
        if path.is_symlink() or not path.is_file():
            raise ActivationReadinessError(f"runtime Prolog path is unsafe: {path}")
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if relative in candidate_rule_paths or relative.parts[0] == "tests":
            continue
        result[relative] = path.read_text(encoding=UTF8)
    if not result:
        raise ActivationReadinessError("runtime tree contains no trusted Prolog sources")
    return result


def unique_integer(values: Any, pattern: re.Pattern[str]) -> int | None:
    found = {int(item) for text in values for item in pattern.findall(text)}
    return next(iter(found)) if len(found) == 1 else None


def rules_have_load_path(
    runtime_sources: dict[PurePosixPath, str],
    rule_paths: set[PurePosixPath],
) -> bool:
    for rule_path in rule_paths:
        filename = re.escape(rule_path.name)
        pattern = re.compile(rf":-\s*use_module\s*\([^)]*{filename}[^)]*\)\s*\.")
        if not any(pattern.search(text) for text in runtime_sources.values()):
            return False
    return True


def exports_have_invocation_path(
    runtime_sources: dict[PurePosixPath, str],
    modules: set[str],
    exports: set[str],
) -> bool:
    combined = "\n".join(runtime_sources.values())
    for export in exports:
        name, _ = export.split("/", 1)
        qualified = any(
            re.search(rf"\b{re.escape(module)}\s*:\s*{re.escape(name)}\s*\(", combined)
            for module in modules
        )
        unqualified = re.search(rf"\b{re.escape(name)}\s*\(", combined) is not None
        if not (qualified or unqualified):
            return False
    return True


def build_blockers(
    checks: dict[str, bool],
    target_epoch: int,
    target_revision: int,
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    if not checks["targetRevisionRepresented"]:
        blockers.append(
            {
                "code": "runtime_revision_not_represented",
                "message": f"The proposed runtime does not declare epoch {target_epoch} revision {target_revision}.",
                "remediation": "Add a reviewed activation overlay that updates the runtime epoch/revision source and verify stale-state behavior before staging.",
            }
        )
    if not checks["candidateRuleLoaded"]:
        blockers.append(
            {
                "code": "candidate_rule_not_loaded",
                "message": "No trusted runtime module imports every candidate rule module.",
                "remediation": "Add a reviewed deterministic loader or registry entry outside the untrusted candidate files.",
            }
        )
    if not checks["candidatePredicateExposed"]:
        blockers.append(
            {
                "code": "candidate_predicate_not_exposed",
                "message": "The closed runtime has no invocation path for every exported candidate predicate.",
                "remediation": "Define and test a reviewed CLI or derived-predicate registry contract before staging the revision.",
            }
        )
    return blockers


def validate_status_consistency(record: dict[str, Any]) -> None:
    checks = required_object(record, "checks")
    blockers = record.get("blockers")
    ready = all(value is True for value in checks.values())
    if record.get("status") == "ready":
        if not ready or blockers != []:
            raise ActivationReadinessError("ready assessment contains failed checks or blockers")
    elif ready or not isinstance(blockers, list) or not blockers:
        raise ActivationReadinessError("blocked assessment must contain failed checks and blockers")


def compute_assessment_hash(record: dict[str, Any]) -> str:
    payload = deepcopy(record)
    payload.pop("assessmentHash", None)
    digest = hashlib.sha256()
    digest.update(ASSESSMENT_DOMAIN)
    digest.update(ASSESSMENT_VERSION)
    digest.update(canonical_json_bytes(payload))
    return "sha256:" + digest.hexdigest()


def read_json_object(path: Path, context: str) -> tuple[dict[str, Any], bytes]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ActivationReadinessError(f"{context} does not exist: {resolved}")
    try:
        content = resolved.read_bytes()
        value = json.loads(content.decode(UTF8))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ActivationReadinessError(f"cannot read {context}: {exc}") from exc
    if not isinstance(value, dict):
        raise ActivationReadinessError(f"{context} must be a JSON object")
    return value, content


def validate_schema(value: dict[str, Any], schema: dict[str, Any], context: str) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: list(item.path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors[:10]
        )
        raise ActivationReadinessError(f"{context} schema validation failed: {details}")


def required_object(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise ActivationReadinessError(f"required object {key!r} is missing")
    return result


def required_string(value: dict[str, Any], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise ActivationReadinessError(f"required string {key!r} is missing")
    return result


def required_nonnegative_int(value: dict[str, Any], key: str) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool) or result < 0:
        raise ActivationReadinessError(f"required integer {key!r} is invalid")
    return result


def validate_identifier(value: str) -> None:
    if not IDENTIFIER.fullmatch(value):
        raise ActivationReadinessError("assessment ID is not a safe identifier")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ActivationReadinessError, OSError, ValueError) as exc:
        print(f"Activation readiness failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
