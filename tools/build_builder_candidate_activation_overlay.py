#!/usr/bin/env python3
"""Create and verify a reviewed Builder activation overlay.

The overlay is an isolated artifact. This tool never stages it, copies it into an
active package, applies it, or updates an active pointer.
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
from assess_builder_candidate_activation_readiness import compute_assessment_hash
from plan_builder_candidate_promotion import (
    compute_promotion_plan_hash,
    verify_candidate_files,
)


UTF8 = "utf-8"
OVERLAY_DOMAIN = b"LogicLensCandidateActivationOverlay\0"
OVERLAY_VERSION = bytes((1,))
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
MODULE_RE = re.compile(
    r":-\s*module\s*\(\s*([a-z][A-Za-z0-9_]*)\s*,\s*\[(.*?)\]\s*\)\s*\.",
    re.DOTALL,
)
EXPORT_RE = re.compile(r"\b([a-z][A-Za-z0-9_]*)\s*/\s*([0-9]+)\b")
EXPECTED_BLOCKERS = {
    "runtime_revision_not_represented",
    "candidate_rule_not_loaded",
    "candidate_predicate_not_exposed",
}
EXPECTED_PASSED_CHECKS = {
    "planVerified",
    "baselineVerified",
    "candidateFilesVerified",
}
EXPECTED_FAILED_CHECKS = {
    "targetRevisionRepresented",
    "candidateRuleLoaded",
    "candidatePredicateExposed",
}
OVERLAY_PATHS = {
    PurePosixPath("entry.pl"): "replace",
    PurePosixPath("rules/revision_runtime.pl"): "add",
}


class ActivationOverlayError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    add_common_inputs(create)
    create.add_argument("--overlay-id", required=True)
    create.add_argument("--output", required=True, type=Path)

    verify = subparsers.add_parser("verify")
    add_common_inputs(verify)
    verify.add_argument("--overlay", required=True, type=Path)
    return parser.parse_args()


def add_common_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--assessment", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--candidate-manifest", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--readiness-schema", required=True, type=Path)
    parser.add_argument("--plan-schema", required=True, type=Path)
    parser.add_argument("--overlay-schema", required=True, type=Path)


def main() -> int:
    args = parse_args()
    if args.command == "create":
        output = args.output.resolve()
        candidate_root = args.candidate_root.resolve()
        if output.exists():
            raise ActivationOverlayError(f"output already exists: {output}")
        if output == candidate_root or candidate_root in output.parents:
            raise ActivationOverlayError("output must not overlap the candidate package")
        manifest, files = create_overlay(
            assessment_path=args.assessment,
            plan_path=args.plan,
            candidate_manifest_path=args.candidate_manifest,
            candidate_root=args.candidate_root,
            readiness_schema_path=args.readiness_schema,
            plan_schema_path=args.plan_schema,
            overlay_schema_path=args.overlay_schema,
            overlay_id=args.overlay_id,
        )
        write_overlay(output, manifest, files)
        print(f"Created activation overlay: {manifest['overlayId']}")
        print(
            "Target revision: "
            f"{manifest['target']['epoch']}.{manifest['target']['revision']}"
        )
        print(f"Derived predicate: {manifest['derivedBinding']['predicateIri']}")
        print("Staging: not performed")
        print(f"Output: {output}")
        return 0

    verify_overlay(
        overlay_root=args.overlay,
        assessment_path=args.assessment,
        plan_path=args.plan,
        candidate_manifest_path=args.candidate_manifest,
        candidate_root=args.candidate_root,
        readiness_schema_path=args.readiness_schema,
        plan_schema_path=args.plan_schema,
        overlay_schema_path=args.overlay_schema,
    )
    print(f"Verified activation overlay: {args.overlay.resolve()}")
    print("Staging: not performed")
    return 0


def create_overlay(
    *,
    assessment_path: Path,
    plan_path: Path,
    candidate_manifest_path: Path,
    candidate_root: Path,
    readiness_schema_path: Path,
    plan_schema_path: Path,
    overlay_schema_path: Path,
    overlay_id: str,
) -> tuple[dict[str, Any], dict[PurePosixPath, bytes]]:
    validate_identifier(overlay_id)
    assessment, _ = read_json_object(assessment_path, "activation readiness")
    plan, _ = read_json_object(plan_path, "promotion plan")
    candidate, _ = read_json_object(candidate_manifest_path, "candidate manifest")
    readiness_schema, _ = read_json_object(
        readiness_schema_path,
        "activation readiness schema",
    )
    plan_schema, _ = read_json_object(plan_schema_path, "promotion plan schema")
    overlay_schema, _ = read_json_object(overlay_schema_path, "activation overlay schema")

    validate_schema(assessment, readiness_schema, "activation readiness")
    validate_schema(plan, plan_schema, "promotion plan")
    if compute_assessment_hash(assessment) != assessment.get("assessmentHash"):
        raise ActivationOverlayError("activation readiness hash does not match its payload")
    if compute_promotion_plan_hash(plan) != plan.get("promotionPlanHash"):
        raise ActivationOverlayError("promotion plan hash does not match its payload")
    validate_blocked_assessment(assessment)
    validate_identity(assessment, plan, candidate)

    verified_files = verify_candidate_files(candidate, candidate_root)
    if verified_files != required_object(plan, "changes").get("addedFiles"):
        raise ActivationOverlayError("candidate files differ from the promotion plan")

    module, predicate, arity, rule_path = reviewed_rule_interface(
        candidate,
        candidate_root,
    )
    predicate_iri = reviewed_ui_predicate(candidate, candidate_root)
    target = required_object(plan, "target")
    target_epoch = required_nonnegative_int(target, "epoch", "promotion target")
    target_revision = required_positive_int(target, "revision", "promotion target")

    files = {
        PurePosixPath("entry.pl"): render_entry(),
        PurePosixPath("rules/revision_runtime.pl"): render_revision_runtime(
            target_epoch=target_epoch,
            target_revision=target_revision,
            rule_filename=rule_path.name,
            module=module,
            predicate=predicate,
            predicate_iri=predicate_iri,
        ),
    }
    file_rows = [
        {
            "path": str(path),
            "operation": OVERLAY_PATHS[path],
            "sha256": sha256(content),
            "bytes": len(content),
        }
        for path, content in sorted(files.items(), key=lambda item: str(item[0]))
    ]

    assessment_source = required_object(assessment, "source")
    manifest: dict[str, Any] = {
        "schemaVersion": "0.1",
        "stage": "candidate-activation-overlay",
        "overlayId": overlay_id,
        "status": "prepared",
        "source": {
            "assessmentId": required_string(assessment, "assessmentId", "assessment"),
            "assessmentHash": required_string(
                assessment,
                "assessmentHash",
                "assessment",
            ),
            "promotionPlanHash": required_string(
                assessment_source,
                "promotionPlanHash",
                "assessment source",
            ),
            "candidateHash": required_string(
                assessment_source,
                "candidateHash",
                "assessment source",
            ),
            "candidatePackageHash": required_string(
                assessment_source,
                "candidatePackageHash",
                "assessment source",
            ),
            "basePackageHash": required_string(
                assessment_source,
                "basePackageHash",
                "assessment source",
            ),
        },
        "target": {
            "epoch": target_epoch,
            "revision": target_revision,
        },
        "derivedBinding": {
            "command": "derived-query",
            "predicateIri": predicate_iri,
            "module": module,
            "predicate": predicate,
            "arity": arity,
        },
        "changes": {
            "replacedFiles": ["entry.pl"],
            "addedFiles": ["rules/revision_runtime.pl"],
            "modifiedActiveFiles": [],
            "removedActiveFiles": [],
        },
        "files": file_rows,
        "checks": {
            "assessmentVerified": True,
            "knownBlockersMatched": True,
            "candidateIdentityConsistent": True,
            "candidateInterfaceReviewed": True,
            "overlayAllowlistEnforced": True,
            "activePackageUntouched": True,
        },
        "intent": {
            "staging": "not-performed",
            "apply": "not-performed",
            "activePointerUpdate": "not-performed",
        },
    }
    manifest["overlayHash"] = compute_overlay_hash(manifest, files)
    validate_schema(manifest, overlay_schema, "activation overlay")
    return manifest, files


def verify_overlay(
    *,
    overlay_root: Path,
    assessment_path: Path,
    plan_path: Path,
    candidate_manifest_path: Path,
    candidate_root: Path,
    readiness_schema_path: Path,
    plan_schema_path: Path,
    overlay_schema_path: Path,
) -> dict[str, Any]:
    root = overlay_root.resolve()
    if not root.is_dir():
        raise ActivationOverlayError(f"overlay root does not exist: {root}")
    manifest, _ = read_json_object(root / "overlay-manifest.json", "overlay manifest")
    overlay_schema, _ = read_json_object(overlay_schema_path, "activation overlay schema")
    validate_schema(manifest, overlay_schema, "activation overlay")
    files = read_declared_overlay_files(root, manifest)
    if compute_overlay_hash(manifest, files) != manifest.get("overlayHash"):
        raise ActivationOverlayError("activation overlay hash does not match its contents")

    expected_manifest, expected_files = create_overlay(
        assessment_path=assessment_path,
        plan_path=plan_path,
        candidate_manifest_path=candidate_manifest_path,
        candidate_root=candidate_root,
        readiness_schema_path=readiness_schema_path,
        plan_schema_path=plan_schema_path,
        overlay_schema_path=overlay_schema_path,
        overlay_id=required_string(manifest, "overlayId", "overlay manifest"),
    )
    if manifest != expected_manifest or files != expected_files:
        raise ActivationOverlayError(
            "activation overlay differs from the supplied assessment and candidate"
        )
    return manifest


def validate_blocked_assessment(assessment: dict[str, Any]) -> None:
    if assessment.get("status") != "blocked":
        raise ActivationOverlayError("activation overlay requires a blocked assessment")
    intent = required_object(assessment, "intent")
    if any(
        intent.get(key) != "not-performed"
        for key in ("staging", "apply", "activePointerUpdate")
    ):
        raise ActivationOverlayError("assessment already crossed the activation boundary")
    blockers = assessment.get("blockers")
    if not isinstance(blockers, list) or not all(isinstance(row, dict) for row in blockers):
        raise ActivationOverlayError("assessment blockers are invalid")
    blocker_codes = {row.get("code") for row in blockers}
    if blocker_codes != EXPECTED_BLOCKERS or len(blockers) != len(EXPECTED_BLOCKERS):
        raise ActivationOverlayError("assessment contains an unknown blocker set")
    checks = required_object(assessment, "checks")
    if any(checks.get(name) is not True for name in EXPECTED_PASSED_CHECKS):
        raise ActivationOverlayError("assessment prerequisite checks did not pass")
    if any(checks.get(name) is not False for name in EXPECTED_FAILED_CHECKS):
        raise ActivationOverlayError("assessment no longer matches the overlay remediation")


def validate_identity(
    assessment: dict[str, Any],
    plan: dict[str, Any],
    candidate: dict[str, Any],
) -> None:
    assessment_source = required_object(assessment, "source")
    plan_source = required_object(plan, "source")
    plan_target = required_object(plan, "target")
    assessment_target = required_object(assessment, "target")
    pairs = (
        (assessment_source.get("promotionPlanHash"), plan.get("promotionPlanHash")),
        (assessment_source.get("candidateHash"), plan_source.get("candidateHash")),
        (assessment_source.get("candidatePackageHash"), plan_source.get("candidatePackageHash")),
        (assessment_source.get("basePackageHash"), plan_source.get("basePackageHash")),
        (candidate.get("candidateHash"), plan_source.get("candidateHash")),
        (candidate.get("candidatePackageHash"), plan_source.get("candidatePackageHash")),
        (candidate.get("basePackageHash"), plan_source.get("basePackageHash")),
        (assessment_target.get("epoch"), plan_target.get("epoch")),
        (assessment_target.get("revision"), plan_target.get("revision")),
    )
    if any(left != right for left, right in pairs):
        raise ActivationOverlayError("assessment, plan, and candidate identities differ")


def reviewed_rule_interface(
    candidate: dict[str, Any],
    candidate_root: Path,
) -> tuple[str, str, int, PurePosixPath]:
    rule_paths = [
        PurePosixPath(path)
        for path, metadata in required_object(candidate, "files").items()
        if isinstance(metadata, dict) and metadata.get("kind") == "rule"
    ]
    if len(rule_paths) != 1:
        raise ActivationOverlayError("overlay v0 requires exactly one candidate rule")
    rule_path = rule_paths[0]
    text = candidate_root.resolve().joinpath(*rule_path.parts).read_text(encoding=UTF8)
    match = MODULE_RE.search(text)
    if match is None:
        raise ActivationOverlayError("candidate rule module declaration is missing")
    exports = EXPORT_RE.findall(match.group(2))
    if len(exports) != 1:
        raise ActivationOverlayError("overlay v0 requires exactly one exported predicate")
    predicate, arity_text = exports[0]
    arity = int(arity_text)
    if arity != 2:
        raise ActivationOverlayError("overlay v0 requires a predicate with arity 2")
    return match.group(1), predicate, arity, rule_path


def reviewed_ui_predicate(candidate: dict[str, Any], candidate_root: Path) -> str:
    ui_paths = [
        PurePosixPath(path)
        for path, metadata in required_object(candidate, "files").items()
        if isinstance(metadata, dict) and metadata.get("kind") == "ui"
    ]
    if len(ui_paths) != 1:
        raise ActivationOverlayError("overlay v0 requires exactly one UI binding file")
    path = candidate_root.resolve().joinpath(*ui_paths[0].parts)
    value, _ = read_json_object(path, "candidate UI binding")
    bindings = value.get("bindings")
    if not isinstance(bindings, list) or len(bindings) != 1 or not isinstance(bindings[0], dict):
        raise ActivationOverlayError("overlay v0 requires exactly one UI binding")
    predicate = bindings[0].get("predicate")
    if not isinstance(predicate, str) or not predicate or len(predicate) > 1024:
        raise ActivationOverlayError("candidate UI predicate is invalid")
    return predicate


def render_entry() -> bytes:
    return (
        ":- use_module('rules/revision_runtime.pl').\n"
        ":- use_module(library(http/json)).\n\n"
        ":- initialization(main, main).\n\n\n"
        "main :-\n"
        "    set_prolog_flag(encoding, utf8),\n"
        "    catch(\n"
        "        json_read_dict(user_input, Request, [value_string_as(string)]),\n"
        "        Error,\n"
        "        bootstrap_failure(Error)\n"
        "    ),\n"
        "    revision_runtime:handle_request(Request, Response, ExitCode),\n"
        "    json_write_dict(current_output, Response, [width(0)]),\n"
        "    nl,\n"
        "    flush_output(current_output),\n"
        "    halt(ExitCode).\n\n\n"
        "bootstrap_failure(Error) :-\n"
        "    print_message(error, Error),\n"
        "    halt(2).\n"
    ).encode(UTF8)


def render_revision_runtime(
    *,
    target_epoch: int,
    target_revision: int,
    rule_filename: str,
    module: str,
    predicate: str,
    predicate_iri: str,
) -> bytes:
    iri_literal = json.dumps(predicate_iri, ensure_ascii=False)
    return f''':- module(revision_runtime, [handle_request/3]).
:- use_module('cli_runtime.pl').
:- use_module('{rule_filename}').

protocol_version("0.1").
loaded_epoch({target_epoch}).
loaded_revision({target_revision}).
derived_predicate({iri_literal}).

handle_request(Request, Response, ExitCode) :-
    reported_context(Request, RequestId, Command),
    catch(
        handle_checked(Request, Response0, ExitCode0),
        Error,
        overlay_error_response(Error, RequestId, Command, Response0, ExitCode0)
    ),
    Response = Response0,
    ExitCode = ExitCode0.

handle_checked(Request, Response, ExitCode) :-
    (   request_state(Request, RequestedEpoch, RequestedRevision)
    ->  loaded_epoch(LoadedEpoch),
        loaded_revision(LoadedRevision),
        (   RequestedEpoch =:= LoadedEpoch,
            RequestedRevision =:= LoadedRevision
        ->  dispatch_current(Request, Response, ExitCode)
        ;   stale_state_response(
                Request,
                RequestedEpoch,
                RequestedRevision,
                Response,
                ExitCode
            )
        )
    ;   delegate_unvalidated(Request, Response, ExitCode)
    ).

request_state(Request, Epoch, Revision) :-
    is_dict(Request),
    get_dict(epoch, Request, Epoch),
    integer(Epoch),
    Epoch >= 0,
    get_dict(revision, Request, Revision),
    integer(Revision),
    Revision >= 0.

dispatch_current(Request, Response, ExitCode) :-
    (   get_dict(command, Request, "derived-query")
    ->  run_derived_request(Request, Response, ExitCode)
    ;   delegate_current(Request, Response, ExitCode)
    ).

delegate_current(Request, Response, ExitCode) :-
    put_dict(_{{epoch: 0, revision: 0}}, Request, BaselineRequest),
    cli_runtime:handle_request(BaselineRequest, BaselineResponse, ExitCode),
    patch_baseline_response(BaselineResponse, Response).

delegate_unvalidated(Request, Response, ExitCode) :-
    cli_runtime:handle_request(Request, BaselineResponse, ExitCode),
    patch_baseline_response(BaselineResponse, Response).

patch_baseline_response(BaselineResponse, Response) :-
    loaded_epoch(Epoch),
    loaded_revision(Revision),
    put_dict(_{{epoch: Epoch, revision: Revision}}, BaselineResponse, RevisionResponse),
    patch_health_commands(RevisionResponse, Response).

patch_health_commands(Response0, Response) :-
    (   get_dict(status, Response0, ok),
        get_dict(command, Response0, health),
        get_dict(result, Response0, Result0),
        get_dict(availableCommands, Result0, Commands0)
    ->  append(Commands0, ['derived-query'], Commands),
        put_dict(availableCommands, Result0, Commands, Result),
        put_dict(result, Response0, Result, Response)
    ;   Response = Response0
    ).

run_derived_request(Request, Response, ExitCode) :-
    validate_derived_request(Request, RequestId, PredicateIri),
    findall(
        row{{entityId: Person, evidenceFactIds: EvidenceFactIds}},
        {module}:{predicate}(Person, EvidenceFactIds),
        Rows0
    ),
    sort(Rows0, Rows),
    length(Rows, RowCount),
    (   RowCount =< 1000
    ->  true
    ;   throw(overlay_error(
            "result_limit_exceeded",
            "The reviewed derived result exceeds 1000 rows.",
            _{{rowCount: RowCount, maxRows: 1000}}
        ))
    ),
    protocol_version(Version),
    loaded_epoch(Epoch),
    loaded_revision(Revision),
    Response = response{{
        protocolVersion: Version,
        requestId: RequestId,
        command: 'derived-query',
        status: ok,
        epoch: Epoch,
        revision: Revision,
        result: derived_result{{
            kind: 'derived-query',
            predicate: PredicateIri,
            rows: Rows
        }},
        diagnostics: []
    }},
    ExitCode = 0.

validate_derived_request(Request, RequestId, PredicateIri) :-
    require_exact_keys(
        Request,
        [protocolVersion, requestId, command, epoch, revision, options]
    ),
    get_dict(protocolVersion, Request, Version),
    protocol_version(ExpectedVersion),
    (   Version == ExpectedVersion
    ->  true
    ;   throw(overlay_error(
            "unsupported_protocol",
            "The requested protocol version is not supported.",
            _{{requested: Version, supported: ExpectedVersion}}
        ))
    ),
    get_dict(requestId, Request, RequestId),
    require_string(RequestId, requestId),
    get_dict(options, Request, Options),
    require_exact_keys(Options, [predicate]),
    get_dict(predicate, Options, PredicateIri),
    require_string(PredicateIri, predicate),
    derived_predicate(ExpectedPredicate),
    (   PredicateIri == ExpectedPredicate
    ->  true
    ;   throw(overlay_error(
            "unknown_predicate",
            "The predicate is not part of the reviewed derived registry.",
            _{{predicate: PredicateIri}}
        ))
    ).

require_exact_keys(Dict, ExpectedKeys) :-
    (   is_dict(Dict)
    ->  dict_keys(Dict, Keys0),
        sort(Keys0, Keys),
        sort(ExpectedKeys, Expected),
        (   Keys == Expected
        ->  true
        ;   throw(overlay_error(
                "invalid_request",
                "The request contains missing or unknown fields.",
                _{{}}
            ))
        )
    ;   throw(overlay_error(
            "invalid_request",
            "The request must be a JSON object.",
            _{{}}
        ))
    ).

require_string(Value, Field) :-
    (   string(Value),
        string_length(Value, Length),
        between(1, 1024, Length)
    ->  true
    ;   throw(overlay_error(
            "invalid_request",
            "A reviewed string field is invalid.",
            _{{field: Field}}
        ))
    ).

stale_state_response(Request, RequestedEpoch, RequestedRevision, Response, 1) :-
    reported_context(Request, RequestId, Command),
    loaded_epoch(Epoch),
    loaded_revision(Revision),
    protocol_version(Version),
    Response = response{{
        protocolVersion: Version,
        requestId: RequestId,
        command: Command,
        status: error,
        epoch: Epoch,
        revision: Revision,
        error: error{{
            code: "stale_state",
            message: "The requested epoch or revision does not match the loaded state.",
            details: _{{
                requestedEpoch: RequestedEpoch,
                requestedRevision: RequestedRevision,
                loadedEpoch: Epoch,
                loadedRevision: Revision
            }}
        }},
        diagnostics: []
    }}.

reported_context(Request, RequestId, Command) :-
    (   is_dict(Request),
        get_dict(requestId, Request, CandidateRequestId),
        string(CandidateRequestId)
    ->  RequestId = CandidateRequestId
    ;   RequestId = null
    ),
    (   is_dict(Request),
        get_dict(command, Request, CandidateCommand),
        string(CandidateCommand)
    ->  Command = CandidateCommand
    ;   Command = null
    ).

overlay_error_response(
    overlay_error(Code, Message, Details),
    RequestId,
    Command,
    Response,
    1
) :-
    !,
    error_response(Code, Message, Details, RequestId, Command, Response).
overlay_error_response(_, RequestId, Command, Response, 1) :-
    error_response(
        "internal_error",
        "The reviewed derived command failed before producing a result.",
        _{{}},
        RequestId,
        Command,
        Response
    ).

error_response(Code, Message, Details, RequestId, Command, Response) :-
    protocol_version(Version),
    loaded_epoch(Epoch),
    loaded_revision(Revision),
    Response = response{{
        protocolVersion: Version,
        requestId: RequestId,
        command: Command,
        status: error,
        epoch: Epoch,
        revision: Revision,
        error: error{{code: Code, message: Message, details: Details}},
        diagnostics: []
    }}.
'''.encode(UTF8)


def write_overlay(
    output: Path,
    manifest: dict[str, Any],
    files: dict[PurePosixPath, bytes],
) -> None:
    output.mkdir(parents=True)
    for relative_path, content in files.items():
        destination = output.joinpath(*relative_path.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    (output / "overlay-manifest.json").write_bytes(canonical_json_bytes(manifest))


def read_declared_overlay_files(
    root: Path,
    manifest: dict[str, Any],
) -> dict[PurePosixPath, bytes]:
    rows = manifest.get("files")
    if not isinstance(rows, list):
        raise ActivationOverlayError("overlay manifest files are invalid")
    declared: dict[PurePosixPath, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ActivationOverlayError("overlay file declaration is invalid")
        path = PurePosixPath(row.get("path", ""))
        if path not in OVERLAY_PATHS or row.get("operation") != OVERLAY_PATHS[path]:
            raise ActivationOverlayError("overlay file is outside the reviewed allowlist")
        if path in declared:
            raise ActivationOverlayError("overlay file is declared twice")
        declared[path] = row

    actual_paths: set[PurePosixPath] = set()
    files: dict[PurePosixPath, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ActivationOverlayError(f"overlay symlink is forbidden: {path}")
        if not path.is_file():
            continue
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if relative == PurePosixPath("overlay-manifest.json"):
            continue
        actual_paths.add(relative)
        if relative not in declared:
            raise ActivationOverlayError(f"overlay contains an undeclared file: {relative}")
        content = path.read_bytes()
        row = declared[relative]
        if len(content) != row.get("bytes") or sha256(content) != row.get("sha256"):
            raise ActivationOverlayError(f"overlay file differs from its manifest: {relative}")
        files[relative] = content
    if actual_paths != set(declared) or set(declared) != set(OVERLAY_PATHS):
        raise ActivationOverlayError("overlay file set is incomplete")
    return dict(sorted(files.items(), key=lambda item: str(item[0])))


def compute_overlay_hash(
    manifest: dict[str, Any],
    files: dict[PurePosixPath, bytes],
) -> str:
    payload = deepcopy(manifest)
    payload.pop("overlayHash", None)
    digest = hashlib.sha256()
    digest.update(OVERLAY_DOMAIN)
    digest.update(OVERLAY_VERSION)
    digest.update(canonical_json_bytes(payload))
    for path, content in sorted(files.items(), key=lambda item: str(item[0])):
        append_field(digest, str(path).encode(UTF8))
        append_field(digest, content)
    return "sha256:" + digest.hexdigest()


def append_field(digest: Any, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big", signed=False))
    digest.update(value)


def read_json_object(path: Path, context: str) -> tuple[dict[str, Any], bytes]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ActivationOverlayError(f"{context} does not exist: {resolved}")
    try:
        content = resolved.read_bytes()
        value = json.loads(content.decode(UTF8))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ActivationOverlayError(f"cannot read {context}: {exc}") from exc
    if not isinstance(value, dict):
        raise ActivationOverlayError(f"{context} must be a JSON object")
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
        raise ActivationOverlayError(f"{context} schema validation failed: {details}")


def required_object(value: dict[str, Any], key: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise ActivationOverlayError(f"required object {key!r} is missing")
    return result


def required_string(value: dict[str, Any], key: str, context: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise ActivationOverlayError(f"{context} field {key!r} is missing")
    return result


def required_nonnegative_int(value: dict[str, Any], key: str, context: str) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool) or result < 0:
        raise ActivationOverlayError(f"{context} field {key!r} is invalid")
    return result


def required_positive_int(value: dict[str, Any], key: str, context: str) -> int:
    result = required_nonnegative_int(value, key, context)
    if result < 1:
        raise ActivationOverlayError(f"{context} field {key!r} must be positive")
    return result


def validate_identifier(value: str) -> None:
    if not IDENTIFIER.fullmatch(value):
        raise ActivationOverlayError("overlay ID is not a safe identifier")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ActivationOverlayError, OSError, ValueError) as exc:
        print(f"Activation overlay failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
