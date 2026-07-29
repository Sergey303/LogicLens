#!/usr/bin/env python3
"""Build and verify an isolated LogicLens staged revision.

The tool may write only to a fresh output directory. It never changes an active
package, applies a revision, or updates an active pointer.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from active_epoch.hashing import aggregate_hash, canonical_json_bytes, sha256
from assess_builder_candidate_activation_readiness import compute_assessment_hash
from build_builder_candidate_activation_overlay_clean_compat import (
    compute_overlay_hash,
    read_declared_overlay_files,
)
from builder_candidate.cli import (
    CandidateError,
    run_candidate_tests,
    run_prolog_load,
    tree_bytes,
    verify_active_baseline,
)
from plan_builder_candidate_promotion import (
    compute_promotion_plan_hash,
    verify_candidate_files,
)


UTF8 = "utf-8"
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PACKAGE_DOMAIN = b"LogicLensStagedRevision\0"
PACKAGE_VERSION = 1
WEAK_IMPORT_WARNING = "overrides weak import from cli_runtime"
EXPECTED_OVERLAY_PATHS = {
    PurePosixPath("entry.pl"): "replace",
    PurePosixPath("rules/revision_runtime.pl"): "add",
}


class StagedRevisionError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    add_common_inputs(create)
    create.add_argument("--stage-id", required=True)
    create.add_argument("--output", required=True, type=Path)

    verify = subparsers.add_parser("verify")
    add_common_inputs(verify)
    verify.add_argument("--staged", required=True, type=Path)

    return parser.parse_args()


def add_common_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--blocked-assessment", required=True, type=Path)
    parser.add_argument("--ready-assessment", required=True, type=Path)
    parser.add_argument("--candidate-manifest", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--active-root", required=True, type=Path)
    parser.add_argument("--plan-schema", required=True, type=Path)
    parser.add_argument("--readiness-schema", required=True, type=Path)
    parser.add_argument("--overlay-schema", required=True, type=Path)
    parser.add_argument("--staged-schema", required=True, type=Path)
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--timeout-ms", type=int, default=10_000)


def main() -> int:
    args = parse_args()
    if args.timeout_ms < 100 or args.timeout_ms > 60_000:
        raise StagedRevisionError("timeout-ms must be between 100 and 60000")

    common = dict(
        plan_path=args.plan,
        blocked_assessment_path=args.blocked_assessment,
        ready_assessment_path=args.ready_assessment,
        candidate_manifest_path=args.candidate_manifest,
        candidate_root=args.candidate_root,
        overlay_root=args.overlay,
        active_root=args.active_root,
        plan_schema_path=args.plan_schema,
        readiness_schema_path=args.readiness_schema,
        overlay_schema_path=args.overlay_schema,
        staged_schema_path=args.staged_schema,
        swipl=args.swipl,
        timeout_seconds=args.timeout_ms / 1000.0,
    )

    if args.command == "create":
        output = args.output.resolve()
        validate_identifier(args.stage_id)
        require_fresh_separate_output(
            output,
            [
                args.candidate_root.resolve(),
                args.overlay.resolve(),
                args.active_root.resolve(),
            ],
        )
        manifest, payload = create_staged_revision(
            stage_id=args.stage_id,
            output=output,
            **common,
        )
        write_payload(output, payload)
        validate_staged_runtime(
            staged_root=output,
            active_root=args.active_root.resolve(),
            candidate_manifest=read_json_object(
                args.candidate_manifest,
                "candidate manifest",
            ),
            overlay_manifest=read_json_object(
                args.overlay / "overlay-manifest.json",
                "overlay manifest",
            ),
            swipl=args.swipl,
            timeout_seconds=args.timeout_ms / 1000.0,
        )
        (output / "manifest.json").write_bytes(canonical_json_bytes(manifest))
        print(f"Created staged revision: {manifest['stageId']}")
        print(
            "Target revision: "
            f"{manifest['target']['epoch']}.{manifest['target']['revision']}"
        )
        print(f"Package hash: {manifest['packageHash']}")
        print("Apply: not performed")
        print("Active pointer update: not performed")
        print(f"Output: {output}")
        return 0

    verify_staged_revision(staged_root=args.staged, **common)
    print(f"Verified staged revision: {args.staged.resolve()}")
    print("Apply: not performed")
    print("Active pointer update: not performed")
    return 0


def create_staged_revision(
    *,
    stage_id: str,
    output: Path,
    plan_path: Path,
    blocked_assessment_path: Path,
    ready_assessment_path: Path,
    candidate_manifest_path: Path,
    candidate_root: Path,
    overlay_root: Path,
    active_root: Path,
    plan_schema_path: Path,
    readiness_schema_path: Path,
    overlay_schema_path: Path,
    staged_schema_path: Path,
    swipl: str,
    timeout_seconds: float,
) -> tuple[dict[str, Any], dict[PurePosixPath, bytes]]:
    del output, swipl, timeout_seconds
    validate_identifier(stage_id)

    plan = read_json_object(plan_path, "promotion plan")
    blocked = read_json_object(
        blocked_assessment_path,
        "blocked readiness assessment",
    )
    ready = read_json_object(
        ready_assessment_path,
        "ready readiness assessment",
    )
    candidate = read_json_object(candidate_manifest_path, "candidate manifest")
    overlay_manifest = read_json_object(
        overlay_root.resolve() / "overlay-manifest.json",
        "overlay manifest",
    )

    validate_schema(
        plan,
        read_json_object(plan_schema_path, "promotion plan schema"),
        "promotion plan",
    )
    readiness_schema = read_json_object(readiness_schema_path, "readiness schema")
    validate_schema(blocked, readiness_schema, "blocked readiness assessment")
    validate_schema(ready, readiness_schema, "ready readiness assessment")
    validate_schema(
        overlay_manifest,
        read_json_object(overlay_schema_path, "overlay schema"),
        "overlay manifest",
    )

    if compute_promotion_plan_hash(plan) != plan.get("promotionPlanHash"):
        raise StagedRevisionError("promotion plan hash does not match its payload")
    if compute_assessment_hash(blocked) != blocked.get("assessmentHash"):
        raise StagedRevisionError("blocked readiness hash does not match its payload")
    if compute_assessment_hash(ready) != ready.get("assessmentHash"):
        raise StagedRevisionError("ready readiness hash does not match its payload")
    if blocked.get("status") != "blocked":
        raise StagedRevisionError("overlay source readiness must be blocked")
    if ready.get("status") != "ready" or ready.get("blockers") != []:
        raise StagedRevisionError("staging requires a blocker-free ready assessment")
    if not all(value is True for value in required_object(ready, "checks").values()):
        raise StagedRevisionError("ready assessment contains a failed check")

    overlay_files = read_declared_overlay_files(
        overlay_root.resolve(),
        overlay_manifest,
    )
    if (
        compute_overlay_hash(overlay_manifest, overlay_files)
        != overlay_manifest.get("overlayHash")
    ):
        raise StagedRevisionError("overlay hash does not match its contents")
    validate_overlay_paths(overlay_manifest, overlay_files)

    plan_source = required_object(plan, "source")
    plan_target = required_object(plan, "target")
    ready_source = required_object(ready, "source")
    ready_target = required_object(ready, "target")
    overlay_source = required_object(overlay_manifest, "source")
    overlay_target = required_object(overlay_manifest, "target")

    identity_pairs = (
        (ready_source.get("promotionPlanHash"), plan.get("promotionPlanHash")),
        (ready_source.get("candidateHash"), plan_source.get("candidateHash")),
        (
            ready_source.get("candidatePackageHash"),
            plan_source.get("candidatePackageHash"),
        ),
        (ready_source.get("basePackageHash"), plan_source.get("basePackageHash")),
        (overlay_source.get("promotionPlanHash"), plan.get("promotionPlanHash")),
        (overlay_source.get("candidateHash"), plan_source.get("candidateHash")),
        (
            overlay_source.get("candidatePackageHash"),
            plan_source.get("candidatePackageHash"),
        ),
        (overlay_source.get("basePackageHash"), plan_source.get("basePackageHash")),
        (overlay_source.get("assessmentHash"), blocked.get("assessmentHash")),
        (candidate.get("candidateHash"), plan_source.get("candidateHash")),
        (
            candidate.get("candidatePackageHash"),
            plan_source.get("candidatePackageHash"),
        ),
        (candidate.get("basePackageHash"), plan_source.get("basePackageHash")),
        (ready_target.get("epoch"), plan_target.get("epoch")),
        (ready_target.get("revision"), plan_target.get("revision")),
        (overlay_target.get("epoch"), plan_target.get("epoch")),
        (overlay_target.get("revision"), plan_target.get("revision")),
    )
    if any(left != right for left, right in identity_pairs):
        raise StagedRevisionError(
            "plan, readiness, overlay, and candidate identities differ"
        )

    active_before = tree_bytes(active_root.resolve())
    active_manifest = verify_active_baseline(active_before)
    if active_manifest.get("packageHash") != plan_source.get("basePackageHash"):
        raise StagedRevisionError(
            "active baseline package differs from the promotion plan"
        )
    if active_manifest.get("epoch") != plan_source.get("baseEpoch"):
        raise StagedRevisionError("active baseline epoch differs from the promotion plan")
    if active_manifest.get("baseRevision") != plan_source.get("baseRevision"):
        raise StagedRevisionError(
            "active baseline revision differs from the promotion plan"
        )

    added_rows = verify_candidate_files(candidate, candidate_root)
    if added_rows != required_object(plan, "changes").get("addedFiles"):
        raise StagedRevisionError("candidate files differ from the promotion plan")

    candidate_files: dict[PurePosixPath, bytes] = {}
    candidate_kinds: dict[PurePosixPath, str] = {}
    for row in added_rows:
        path = PurePosixPath(row["path"])
        candidate_files[path] = candidate_root.resolve().joinpath(*path.parts).read_bytes()
        candidate_kinds[path] = row["kind"]
    validate_staged_candidate_files(candidate_files, candidate_kinds)

    payload = {
        path: content
        for path, content in active_before.items()
        if path != PurePosixPath("manifest.json")
    }
    for path, content in candidate_files.items():
        if path in payload:
            raise StagedRevisionError(
                f"candidate file would overwrite baseline content: {path}"
            )
        payload[path] = content
    for path, content in overlay_files.items():
        operation = EXPECTED_OVERLAY_PATHS[path]
        if operation == "replace" and path not in payload:
            raise StagedRevisionError(f"overlay replacement target is missing: {path}")
        if operation == "add" and path in payload:
            raise StagedRevisionError(f"overlay addition already exists: {path}")
        payload[path] = content

    if tree_bytes(active_root.resolve()) != active_before:
        raise StagedRevisionError("staging preparation modified the active baseline")

    package_hash = aggregate_hash(PACKAGE_DOMAIN, PACKAGE_VERSION, payload.items())
    manifest: dict[str, Any] = {
        "schemaVersion": "0.1",
        "stage": "staged-revision",
        "stageId": stage_id,
        "source": {
            "planId": required_string(plan, "planId", "promotion plan"),
            "promotionPlanHash": required_string(
                plan,
                "promotionPlanHash",
                "promotion plan",
            ),
            "plannedRevisionHash": required_string(
                plan_target,
                "plannedRevisionHash",
                "promotion target",
            ),
            "assessmentId": required_string(
                ready,
                "assessmentId",
                "ready assessment",
            ),
            "assessmentHash": required_string(
                ready,
                "assessmentHash",
                "ready assessment",
            ),
            "overlayId": required_string(
                overlay_manifest,
                "overlayId",
                "overlay manifest",
            ),
            "overlayHash": required_string(
                overlay_manifest,
                "overlayHash",
                "overlay manifest",
            ),
            "candidateHash": required_string(
                plan_source,
                "candidateHash",
                "plan source",
            ),
            "candidatePackageHash": required_string(
                plan_source,
                "candidatePackageHash",
                "plan source",
            ),
            "basePackageHash": required_string(
                plan_source,
                "basePackageHash",
                "plan source",
            ),
        },
        "target": {
            "epoch": required_nonnegative_int(
                plan_target,
                "epoch",
                "promotion target",
            ),
            "revision": required_positive_int(
                plan_target,
                "revision",
                "promotion target",
            ),
            "mode": "additive-revision",
        },
        "rollback": deepcopy(required_object(plan, "rollback")),
        "changes": {
            "candidateAddedFiles": sorted(str(path) for path in candidate_files),
            "overlayAddedFiles": sorted(
                str(path)
                for path, operation in EXPECTED_OVERLAY_PATHS.items()
                if operation == "add"
            ),
            "overlayReplacedFiles": sorted(
                str(path)
                for path, operation in EXPECTED_OVERLAY_PATHS.items()
                if operation == "replace"
            ),
        },
        "checks": {
            "planVerified": True,
            "readyAssessmentVerified": True,
            "overlayVerified": True,
            "baselineVerified": True,
            "candidateFilesVerified": True,
            "overlayFilesVerified": True,
            "staticValidationPassed": True,
            "prologLoadPassed": True,
            "plunitPassed": True,
            "runtimePreviewPassed": True,
            "baselineBehaviorPreserved": True,
            "activePackageUntouched": True,
        },
        "intent": {
            "staging": "isolated-output-only",
            "apply": "not-performed",
            "activePointerUpdate": "not-performed",
        },
        "files": {
            str(path): sha256(content)
            for path, content in sorted(payload.items(), key=lambda item: str(item[0]))
        },
        "packageHash": package_hash,
    }
    validate_schema(
        manifest,
        read_json_object(staged_schema_path, "staged revision schema"),
        "staged revision manifest",
    )
    return manifest, dict(sorted(payload.items(), key=lambda item: str(item[0])))


def verify_staged_revision(
    *,
    staged_root: Path,
    plan_path: Path,
    blocked_assessment_path: Path,
    ready_assessment_path: Path,
    candidate_manifest_path: Path,
    candidate_root: Path,
    overlay_root: Path,
    active_root: Path,
    plan_schema_path: Path,
    readiness_schema_path: Path,
    overlay_schema_path: Path,
    staged_schema_path: Path,
    swipl: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    root = staged_root.resolve()
    if not root.is_dir():
        raise StagedRevisionError(f"staged revision does not exist: {root}")
    manifest = read_json_object(root / "manifest.json", "staged revision manifest")
    validate_schema(
        manifest,
        read_json_object(staged_schema_path, "staged revision schema"),
        "staged revision manifest",
    )
    actual = tree_bytes(root)
    actual.pop(PurePosixPath("manifest.json"), None)
    expected_file_hashes = {
        str(path): sha256(content)
        for path, content in actual.items()
    }
    if manifest.get("files") != expected_file_hashes:
        raise StagedRevisionError("staged per-file hashes do not match its contents")
    if (
        aggregate_hash(PACKAGE_DOMAIN, PACKAGE_VERSION, actual.items())
        != manifest.get("packageHash")
    ):
        raise StagedRevisionError("staged packageHash is invalid")

    expected_manifest, expected_payload = create_staged_revision(
        stage_id=required_string(manifest, "stageId", "staged manifest"),
        output=root,
        plan_path=plan_path,
        blocked_assessment_path=blocked_assessment_path,
        ready_assessment_path=ready_assessment_path,
        candidate_manifest_path=candidate_manifest_path,
        candidate_root=candidate_root,
        overlay_root=overlay_root,
        active_root=active_root,
        plan_schema_path=plan_schema_path,
        readiness_schema_path=readiness_schema_path,
        overlay_schema_path=overlay_schema_path,
        staged_schema_path=staged_schema_path,
        swipl=swipl,
        timeout_seconds=timeout_seconds,
    )
    if manifest != expected_manifest or actual != expected_payload:
        raise StagedRevisionError("staged revision differs from its reviewed inputs")

    validate_staged_runtime(
        staged_root=root,
        active_root=active_root.resolve(),
        candidate_manifest=read_json_object(
            candidate_manifest_path,
            "candidate manifest",
        ),
        overlay_manifest=read_json_object(
            overlay_root / "overlay-manifest.json",
            "overlay manifest",
        ),
        swipl=swipl,
        timeout_seconds=timeout_seconds,
    )
    return manifest


def validate_staged_candidate_files(
    files: dict[PurePosixPath, bytes],
    kinds: dict[PurePosixPath, str],
) -> None:
    if set(files) != set(kinds):
        raise StagedRevisionError("candidate file kinds differ from candidate bytes")
    for path, content in files.items():
        if b"\x00" in content:
            raise StagedRevisionError(f"candidate file contains NUL: {path}")
        try:
            text = content.decode(UTF8)
        except UnicodeDecodeError as exc:
            raise StagedRevisionError(f"candidate file is not UTF-8: {path}") from exc
        kind = kinds[path]
        if kind in {"rule", "test"}:
            forbidden = re.search(
                r"\b(?:shell|process_create|consult|load_files|open|tell|told|see|seen|"
                r"working_directory|delete_file|rename_file|copy_file|make_directory|"
                r"http_open|http_get|tcp_connect|tcp_socket|udp_socket|socket|"
                r"asserta|assertz|retract|retractall|abolish|nb_setval|setenv|"
                r"call|call_cleanup|setup_call_cleanup|phrase_from_file)\s*\(",
                text,
                re.IGNORECASE,
            )
            if forbidden:
                raise StagedRevisionError(
                    f"candidate Prolog uses forbidden call {forbidden.group(0)!r}: {path}"
                )
            if kind == "rule" and ":- module(" not in text:
                raise StagedRevisionError(
                    f"candidate rule has no module declaration: {path}"
                )
            if kind == "test" and (
                ":- begin_tests(" not in text or ":- end_tests(" not in text
            ):
                raise StagedRevisionError(
                    f"candidate test has no PlUnit boundary: {path}"
                )
        elif kind == "ui":
            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                raise StagedRevisionError(f"candidate UI JSON is invalid: {path}") from exc
            if (
                not isinstance(value, dict)
                or value.get("schemaVersion") != "0.1"
                or set(value) != {"schemaVersion", "bindings"}
                or not isinstance(value.get("bindings"), list)
                or not value["bindings"]
            ):
                raise StagedRevisionError(f"candidate UI contract is invalid: {path}")
            for binding in value["bindings"]:
                if (
                    not isinstance(binding, dict)
                    or set(binding) != {"predicate", "component"}
                    or not isinstance(binding.get("predicate"), str)
                    or not binding["predicate"]
                    or binding.get("component") != "Property"
                ):
                    raise StagedRevisionError(
                        f"candidate UI binding is not trusted: {path}"
                    )
        else:
            raise StagedRevisionError(f"unsupported candidate file kind: {kind}")


def validate_staged_runtime(
    *,
    staged_root: Path,
    active_root: Path,
    candidate_manifest: dict[str, Any],
    overlay_manifest: dict[str, Any],
    swipl: str,
    timeout_seconds: float,
) -> None:
    files = required_object(candidate_manifest, "files")
    rule_paths = [
        staged_root.joinpath(*PurePosixPath(path).parts)
        for path, metadata in files.items()
        if isinstance(metadata, dict) and metadata.get("kind") == "rule"
    ]
    test_paths = [
        staged_root.joinpath(*PurePosixPath(path).parts)
        for path, metadata in files.items()
        if isinstance(metadata, dict) and metadata.get("kind") == "test"
    ]
    try:
        run_prolog_load(swipl, staged_root, rule_paths, timeout_seconds)
        run_candidate_tests(swipl, staged_root, test_paths, timeout_seconds)
    except CandidateError as exc:
        raise StagedRevisionError(f"staged Prolog validation failed: {exc}") from exc

    target = required_object(overlay_manifest, "target")
    target_epoch = required_nonnegative_int(target, "epoch", "overlay target")
    target_revision = required_positive_int(
        target,
        "revision",
        "overlay target",
    )
    predicate_iri = required_string(
        required_object(overlay_manifest, "derivedBinding"),
        "predicateIri",
        "overlay derived binding",
    )

    compare_smoke(
        swipl=swipl,
        active_root=active_root,
        staged_root=staged_root,
        target_epoch=target_epoch,
        target_revision=target_revision,
        timeout_seconds=timeout_seconds,
    )

    health = {
        "protocolVersion": "0.1",
        "requestId": "staged-health",
        "command": "health",
        "epoch": target_epoch,
        "revision": target_revision,
        "options": {},
    }
    code, response, stderr = run_request(
        swipl,
        staged_root,
        health,
        timeout_seconds,
    )
    require_no_overlay_warning(stderr)
    if code != 0 or response.get("status") != "ok":
        raise StagedRevisionError(f"staged health failed: {response}")
    commands = list(required_object(response, "result").get("availableCommands") or [])
    if commands.count("derived-query") != 1:
        raise StagedRevisionError(
            "staged health does not expose exactly one derived-query"
        )

    derived = {
        "protocolVersion": "0.1",
        "requestId": "staged-derived",
        "command": "derived-query",
        "epoch": target_epoch,
        "revision": target_revision,
        "options": {"predicate": predicate_iri},
    }
    code, response, stderr = run_request(
        swipl,
        staged_root,
        derived,
        timeout_seconds,
    )
    require_no_overlay_warning(stderr)
    rows = (
        list(required_object(response, "result").get("rows") or [])
        if response.get("status") == "ok"
        else []
    )
    if code != 0 or len(rows) != 1:
        raise StagedRevisionError(f"staged derived-query failed: {response}")
    evidence = rows[0].get("evidenceFactIds")
    if (
        rows[0].get("entityId") != "urn:logiclens:person:alex"
        or not isinstance(evidence, list)
        or len(evidence) != 3
        or evidence != sorted(evidence)
        or len(set(evidence)) != 3
    ):
        raise StagedRevisionError(
            f"staged derived-query returned unexpected rows: {rows}"
        )

    stale = deepcopy(health)
    stale["requestId"] = "staged-stale"
    stale["revision"] = target_revision - 1
    code, response, stderr = run_request(
        swipl,
        staged_root,
        stale,
        timeout_seconds,
    )
    require_no_overlay_warning(stderr)
    if code != 1 or required_object(response, "error").get("code") != "stale_state":
        raise StagedRevisionError(f"staged runtime accepted stale state: {response}")

    unknown = deepcopy(derived)
    unknown["requestId"] = "staged-unknown"
    unknown["options"] = {"predicate": "urn:logiclens:derived:unknown"}
    code, response, stderr = run_request(
        swipl,
        staged_root,
        unknown,
        timeout_seconds,
    )
    require_no_overlay_warning(stderr)
    if (
        code != 1
        or required_object(response, "error").get("code")
        != "unknown_predicate"
    ):
        raise StagedRevisionError(
            f"staged runtime accepted an unknown predicate: {response}"
        )


def compare_smoke(
    *,
    swipl: str,
    active_root: Path,
    staged_root: Path,
    target_epoch: int,
    target_revision: int,
    timeout_seconds: float,
) -> None:
    requests = sorted((active_root / "smoke").glob("*.request.json"))
    if not requests:
        raise StagedRevisionError("active baseline has no smoke requests")
    for path in requests:
        request = read_json_object(path, f"smoke request {path.name}")
        baseline_code, baseline, _ = run_request(
            swipl,
            active_root,
            request,
            timeout_seconds,
        )
        if baseline_code != 0 or baseline.get("status") != "ok":
            raise StagedRevisionError(f"baseline smoke failed: {path.name}")
        staged_request = deepcopy(request)
        staged_request["epoch"] = target_epoch
        staged_request["revision"] = target_revision
        staged_code, staged, staged_stderr = run_request(
            swipl,
            staged_root,
            staged_request,
            timeout_seconds,
        )
        require_no_overlay_warning(staged_stderr)
        if staged_code != 0 or staged.get("status") != "ok":
            raise StagedRevisionError(f"staged smoke failed: {path.name}")
        if normalize_response(baseline) != normalize_response(staged):
            raise StagedRevisionError(
                f"staged smoke changed baseline behavior: {path.name}"
            )


def normalize_response(response: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(response)
    result.pop("epoch", None)
    result.pop("revision", None)
    if result.get("command") == "health":
        health = required_object(result, "result")
        commands = list(health.get("availableCommands") or [])
        health["availableCommands"] = [
            command for command in commands if command != "derived-query"
        ]
    return result


def run_request(
    swipl: str,
    package: Path,
    request: dict[str, Any],
    timeout_seconds: float,
) -> tuple[int, dict[str, Any], str]:
    entry = (package.resolve() / "entry.pl").resolve()
    if not entry.is_file():
        raise StagedRevisionError(f"runtime entry is missing: {entry}")
    try:
        completed = subprocess.run(
            [swipl, "--quiet", "-s", str(entry), "--"],
            cwd=str(package.resolve()),
            input=json.dumps(request, ensure_ascii=False),
            text=True,
            encoding=UTF8,
            errors="strict",
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise StagedRevisionError(
            "staged runtime exceeded the reviewed timeout"
        ) from exc
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise StagedRevisionError(
            "staged runtime must return exactly one JSON line: "
            f"stdout={completed.stdout!r}; stderr={completed.stderr!r}"
        )
    try:
        value = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise StagedRevisionError("staged runtime returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise StagedRevisionError(
            "staged runtime response is not a JSON object"
        )
    return completed.returncode, value, completed.stderr


def require_no_overlay_warning(stderr: str) -> None:
    if WEAK_IMPORT_WARNING in stderr:
        raise StagedRevisionError(
            "staged runtime emitted the forbidden weak-import warning"
        )


def validate_overlay_paths(
    manifest: dict[str, Any],
    files: dict[PurePosixPath, bytes],
) -> None:
    rows = manifest.get("files")
    if not isinstance(rows, list):
        raise StagedRevisionError("overlay file declarations are invalid")
    declared = {
        PurePosixPath(row.get("path", "")): row.get("operation")
        for row in rows
        if isinstance(row, dict)
    }
    if declared != EXPECTED_OVERLAY_PATHS or set(files) != set(
        EXPECTED_OVERLAY_PATHS
    ):
        raise StagedRevisionError(
            "overlay files differ from the staged-revision allowlist"
        )


def write_payload(
    output: Path,
    payload: dict[PurePosixPath, bytes],
) -> None:
    output.mkdir(parents=True)
    for path, content in payload.items():
        destination = output.joinpath(*path.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)


def require_fresh_separate_output(
    output: Path,
    sources: list[Path],
) -> None:
    if output.exists():
        raise StagedRevisionError(f"output already exists: {output}")
    for source in sources:
        if output == source or output in source.parents or source in output.parents:
            raise StagedRevisionError(
                f"output overlaps a reviewed source: {source}"
            )


def read_json_object(path: Path, context: str) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise StagedRevisionError(f"{context} does not exist: {resolved}")
    try:
        value = json.loads(resolved.read_text(encoding=UTF8))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StagedRevisionError(f"cannot read {context}: {exc}") from exc
    if not isinstance(value, dict):
        raise StagedRevisionError(f"{context} must be a JSON object")
    return value


def validate_schema(
    value: dict[str, Any],
    schema: dict[str, Any],
    context: str,
) -> None:
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
        raise StagedRevisionError(
            f"{context} schema validation failed: {details}"
        )


def required_object(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise StagedRevisionError(f"required object {key!r} is missing")
    return result


def required_string(
    value: dict[str, Any],
    key: str,
    context: str,
) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise StagedRevisionError(f"{context} field {key!r} is missing")
    return result


def required_nonnegative_int(
    value: dict[str, Any],
    key: str,
    context: str,
) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool) or result < 0:
        raise StagedRevisionError(f"{context} field {key!r} is invalid")
    return result


def required_positive_int(
    value: dict[str, Any],
    key: str,
    context: str,
) -> int:
    result = required_nonnegative_int(value, key, context)
    if result < 1:
        raise StagedRevisionError(
            f"{context} field {key!r} must be positive"
        )
    return result


def validate_identifier(value: str) -> None:
    if not IDENTIFIER.fullmatch(value):
        raise StagedRevisionError("stage ID is not a safe identifier")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (StagedRevisionError, CandidateError, OSError, ValueError) as exc:
        print(f"Staged revision failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
