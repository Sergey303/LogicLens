#!/usr/bin/env python3
"""Contract and SWI-Prolog checks for activation-decision-v0."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath

from active_epoch.hashing import aggregate_hash, canonical_json_bytes, sha256
from builder_candidate.cli import tree_bytes


class VerificationError(AssertionError):
    pass


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("activation_decision_tested", path)
    if spec is None or spec.loader is None:
        raise VerificationError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def hash64(character: str) -> str:
    return "sha256:" + character * 64


def build_fixture(root: Path) -> tuple[Path, Path, Path, Path]:
    active = root / "active"
    staged = root / "staged"
    active.joinpath("rules").mkdir(parents=True)
    active.joinpath("smoke").mkdir(parents=True)

    entry = """\
:- use_module('rules/cli_runtime.pl').
:- use_module(library(http/json)).
:- initialization(main, main).

main :-
    json_read_dict(user_input, Request, [value_string_as(string)]),
    cli_runtime:handle_request(Request, Response, ExitCode),
    json_write_dict(current_output, Response, [width(0)]),
    nl,
    halt(ExitCode).
""".encode("utf-8")

    cli_runtime = """\
:- module(cli_runtime, [handle_request/3]).

handle_request(Request, Response, 0) :-
    get_dict(requestId, Request, RequestId),
    get_dict(command, Request, "health"),
    get_dict(epoch, Request, 0),
    get_dict(revision, Request, 0),
    Response = response{
        protocolVersion: "0.1",
        requestId: RequestId,
        command: health,
        status: ok,
        epoch: 0,
        revision: 0,
        result: health_result{
            kind: health,
            availableCommands: [health],
            baselineMarker: "unchanged"
        },
        diagnostics: []
    }.
""".encode("utf-8")

    smoke_request = canonical_json_bytes(
        {
            "protocolVersion": "0.1",
            "requestId": "fixture-health",
            "command": "health",
            "epoch": 0,
            "revision": 0,
            "options": {},
        }
    )
    active_files = {
        PurePosixPath("entry.pl"): entry,
        PurePosixPath("rules/cli_runtime.pl"): cli_runtime,
        PurePosixPath("smoke/health.request.json"): smoke_request,
    }
    for relative, content in active_files.items():
        destination = active.joinpath(*relative.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    active_hash = aggregate_hash(
        b"LogicLensActiveEpoch\0",
        1,
        active_files.items(),
    )
    active_manifest = {
        "schemaVersion": "0.1",
        "stage": "active",
        "epoch": 0,
        "baseRevision": 0,
        "packageHash": active_hash,
        "files": {
            str(path): sha256(content)
            for path, content in sorted(active_files.items(), key=lambda item: str(item[0]))
        },
    }
    write_json(active / "manifest.json", active_manifest)

    shutil.copytree(active, staged)
    (staged / "manifest.json").unlink()

    candidate_rule = """\
:- module(candidate_researcher_at_iis, [researcher_at_iis/2]).

researcher_at_iis(
    'urn:logiclens:person:alex',
    ['f:organization', 'f:participant', 'f:role']
).
""".encode("utf-8")
    candidate_test = """\
:- begin_tests(candidate_researcher_at_iis).
:- use_module('../rules/candidate_researcher_at_iis.pl').

test(alex) :-
    researcher_at_iis(
        'urn:logiclens:person:alex',
        ['f:organization', 'f:participant', 'f:role']
    ).

:- end_tests(candidate_researcher_at_iis).
""".encode("utf-8")
    candidate_ui = canonical_json_bytes(
        {
            "schemaVersion": "0.1",
            "bindings": [
                {
                    "predicate": "urn:logiclens:derived:researcher-at-iis",
                    "component": "Property",
                }
            ],
        }
    )
    revision_runtime = """\
:- module(revision_runtime, [handle_request/3]).
:- use_module('cli_runtime.pl', []).
:- use_module('candidate_researcher_at_iis.pl').

handle_request(Request, Response, ExitCode) :-
    get_dict(epoch, Request, RequestedEpoch),
    get_dict(revision, Request, RequestedRevision),
    (   RequestedEpoch =:= 0,
        RequestedRevision =:= 1
    ->  dispatch(Request, Response, ExitCode)
    ;   error_response(
            Request,
            "stale_state",
            "The requested state is stale.",
            Response,
            1
        )
    ).

dispatch(Request, Response, ExitCode) :-
    (   get_dict(command, Request, "derived-query")
    ->  derived(Request, Response, ExitCode)
    ;   put_dict(_{epoch: 0, revision: 0}, Request, BaselineRequest),
        cli_runtime:handle_request(BaselineRequest, BaselineResponse, ExitCode),
        put_dict(_{epoch: 0, revision: 1}, BaselineResponse, RevisionResponse),
        get_dict(result, RevisionResponse, Result0),
        get_dict(availableCommands, Result0, Commands0),
        append(Commands0, ['derived-query'], Commands),
        put_dict(availableCommands, Result0, Commands, Result),
        put_dict(result, RevisionResponse, Result, Response)
    ).

derived(Request, Response, ExitCode) :-
    get_dict(options, Request, Options),
    get_dict(predicate, Options, Predicate),
    (   Predicate == "urn:logiclens:derived:researcher-at-iis"
    ->  candidate_researcher_at_iis:researcher_at_iis(Person, Evidence),
        get_dict(requestId, Request, RequestId),
        Response = response{
            protocolVersion: "0.1",
            requestId: RequestId,
            command: 'derived-query',
            status: ok,
            epoch: 0,
            revision: 1,
            result: derived_result{
                kind: 'derived-query',
                predicate: Predicate,
                rows: [row{entityId: Person, evidenceFactIds: Evidence}]
            },
            diagnostics: []
        },
        ExitCode = 0
    ;   error_response(
            Request,
            "unknown_predicate",
            "The predicate is unknown.",
            Response,
            1
        )
    ).

error_response(Request, Code, Message, Response, ExitCode) :-
    get_dict(requestId, Request, RequestId),
    get_dict(command, Request, Command),
    Response = response{
        protocolVersion: "0.1",
        requestId: RequestId,
        command: Command,
        status: error,
        epoch: 0,
        revision: 1,
        error: error{code: Code, message: Message, details: _{}},
        diagnostics: []
    }.
""".encode("utf-8")
    staged_entry = entry.replace(
        b"rules/cli_runtime.pl",
        b"rules/revision_runtime.pl",
    ).replace(
        b"cli_runtime:handle_request",
        b"revision_runtime:handle_request",
    )

    additions = {
        PurePosixPath("entry.pl"): staged_entry,
        PurePosixPath("rules/candidate_researcher_at_iis.pl"): candidate_rule,
        PurePosixPath("rules/revision_runtime.pl"): revision_runtime,
        PurePosixPath("tests/candidate_researcher_at_iis_tests.pl"): candidate_test,
        PurePosixPath("ui/researcher-at-iis.json"): candidate_ui,
    }
    for relative, content in additions.items():
        destination = staged.joinpath(*relative.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    candidate_hash = hash64("c")
    candidate_package_hash = hash64("d")
    promotion_plan_hash = hash64("p")
    planned_revision_hash = hash64("r")
    assessment_hash = hash64("a")
    overlay_hash = hash64("o")

    candidate_files = {
        "rules/candidate_researcher_at_iis.pl": {
            "kind": "rule",
            "sha256": sha256(candidate_rule),
            "bytes": len(candidate_rule),
        },
        "tests/candidate_researcher_at_iis_tests.pl": {
            "kind": "test",
            "sha256": sha256(candidate_test),
            "bytes": len(candidate_test),
        },
        "ui/researcher-at-iis.json": {
            "kind": "ui",
            "sha256": sha256(candidate_ui),
            "bytes": len(candidate_ui),
        },
    }
    candidate_manifest = {
        "schemaVersion": "0.1",
        "stage": "candidate",
        "candidateId": "fixture-candidate",
        "taskId": "fixture-task",
        "baseEpoch": 0,
        "baseRevision": 0,
        "basePackageHash": active_hash,
        "candidateHash": candidate_hash,
        "candidatePackageHash": candidate_package_hash,
        "files": candidate_files,
    }
    candidate_manifest_path = root / "candidate-manifest.json"
    write_json(candidate_manifest_path, candidate_manifest)

    overlay_manifest = {
        "schemaVersion": "0.1",
        "stage": "candidate-activation-overlay",
        "overlayId": "fixture-overlay",
        "status": "prepared",
        "source": {
            "assessmentId": "fixture-blocked",
            "assessmentHash": hash64("b"),
            "promotionPlanHash": promotion_plan_hash,
            "candidateHash": candidate_hash,
            "candidatePackageHash": candidate_package_hash,
            "basePackageHash": active_hash,
        },
        "target": {"epoch": 0, "revision": 1},
        "derivedBinding": {
            "command": "derived-query",
            "predicateIri": "urn:logiclens:derived:researcher-at-iis",
            "module": "candidate_researcher_at_iis",
            "predicate": "researcher_at_iis",
            "arity": 2,
        },
        "overlayHash": overlay_hash,
    }
    overlay_manifest_path = root / "overlay-manifest.json"
    write_json(overlay_manifest_path, overlay_manifest)

    payload = tree_bytes(staged)
    package_hash = aggregate_hash(
        b"LogicLensStagedRevision\0",
        1,
        payload.items(),
    )
    staged_manifest = {
        "schemaVersion": "0.1",
        "stage": "staged-revision",
        "stageId": "fixture-stage",
        "source": {
            "planId": "fixture-plan",
            "promotionPlanHash": promotion_plan_hash,
            "plannedRevisionHash": planned_revision_hash,
            "assessmentId": "fixture-ready",
            "assessmentHash": assessment_hash,
            "overlayId": "fixture-overlay",
            "overlayHash": overlay_hash,
            "candidateHash": candidate_hash,
            "candidatePackageHash": candidate_package_hash,
            "basePackageHash": active_hash,
        },
        "target": {"epoch": 0, "revision": 1, "mode": "additive-revision"},
        "rollback": {"epoch": 0, "revision": 0, "packageHash": active_hash},
        "changes": {
            "candidateAddedFiles": sorted(candidate_files),
            "overlayAddedFiles": ["rules/revision_runtime.pl"],
            "overlayReplacedFiles": ["entry.pl"],
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
    write_json(staged / "manifest.json", staged_manifest)
    return active, staged, candidate_manifest_path, overlay_manifest_path


def expect_error(module, action, fragment: str) -> None:
    try:
        action()
    except module.ActivationDecisionError as exc:
        if fragment not in str(exc):
            raise VerificationError(f"unexpected error: {exc}") from exc
    else:
        raise VerificationError(f"expected failure containing {fragment!r}")


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    module = load_module(repository / "tools" / "build_builder_activation_decision.py")
    swipl = shutil.which("swipl")
    if swipl is None:
        raise VerificationError("swipl is required")

    staged_schema = repository / "contracts" / "staged-revision-v0.schema.json"
    decision_schema = repository / "contracts" / "activation-decision-v0.schema.json"

    with tempfile.TemporaryDirectory(prefix="logiclens-activation-decision-") as temporary:
        root = Path(temporary)
        active, staged, candidate_manifest, overlay_manifest = build_fixture(root)
        active_before = tree_bytes(active)

        record = module.create_activation_decision(
            decision_id="fixture-decision",
            staged_root=staged,
            active_root=active,
            candidate_manifest_path=candidate_manifest,
            overlay_manifest_path=overlay_manifest,
            staged_schema_path=staged_schema,
            decision_schema_path=decision_schema,
            swipl=swipl,
            timeout_seconds=20.0,
        )
        if record["decision"] != "authorize":
            raise VerificationError("fixture was not authorized")
        if record["expectedCurrent"]["revision"] != 0:
            raise VerificationError("expected current revision differs")
        if record["target"]["revision"] != 1:
            raise VerificationError("target revision differs")
        if record["rollback"] != record["expectedCurrent"]:
            raise VerificationError("rollback is not pinned to current")
        if record["intent"] != {
            "authorization": "recorded-only",
            "apply": "not-performed",
            "activePointerUpdate": "not-performed",
        }:
            raise VerificationError("decision crossed the activation boundary")
        if tree_bytes(active) != active_before:
            raise VerificationError("decision creation changed active package")

        decision_path = root / "decision.json"
        write_json(decision_path, record)
        verified = module.verify_activation_decision(
            decision_path=decision_path,
            staged_root=staged,
            active_root=active,
            candidate_manifest_path=candidate_manifest,
            overlay_manifest_path=overlay_manifest,
            staged_schema_path=staged_schema,
            decision_schema_path=decision_schema,
            swipl=swipl,
            timeout_seconds=20.0,
        )
        if verified != record:
            raise VerificationError("verification changed decision")

        repeated = module.create_activation_decision(
            decision_id="fixture-decision",
            staged_root=staged,
            active_root=active,
            candidate_manifest_path=candidate_manifest,
            overlay_manifest_path=overlay_manifest,
            staged_schema_path=staged_schema,
            decision_schema_path=decision_schema,
            swipl=swipl,
            timeout_seconds=20.0,
        )
        if repeated != record:
            raise VerificationError("activation decision is not deterministic")

        tampered = staged / "rules" / "candidate_researcher_at_iis.pl"
        original = tampered.read_bytes()
        tampered.write_bytes(original + b"% tampered\n")
        expect_error(
            module,
            lambda: module.create_activation_decision(
                decision_id="tampered-stage",
                staged_root=staged,
                active_root=active,
                candidate_manifest_path=candidate_manifest,
                overlay_manifest_path=overlay_manifest,
                staged_schema_path=staged_schema,
                decision_schema_path=decision_schema,
                swipl=swipl,
                timeout_seconds=20.0,
            ),
            "per-file hashes",
        )
        tampered.write_bytes(original)

        modified = dict(record)
        modified["decisionHash"] = hash64("0")
        write_json(decision_path, modified)
        expect_error(
            module,
            lambda: module.verify_activation_decision(
                decision_path=decision_path,
                staged_root=staged,
                active_root=active,
                candidate_manifest_path=candidate_manifest,
                overlay_manifest_path=overlay_manifest,
                staged_schema_path=staged_schema,
                decision_schema_path=decision_schema,
                swipl=swipl,
                timeout_seconds=20.0,
            ),
            "decision hash",
        )

    source = (
        repository / "tools" / "build_builder_activation_decision.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "def activate",
        "def apply",
        "def switch_active",
        "def update_pointer",
        "os.replace(",
        "shutil.move(",
    ):
        if forbidden in source:
            raise VerificationError(
                f"authorization tool exposes forbidden operation: {forbidden}"
            )

    print("ok 1 - exact staged and active packages are rebound")
    print("ok 2 - runtime is revalidated before authorization")
    print("ok 3 - decision hash is deterministic and tamper-evident")
    print("ok 4 - staged tampering is rejected")
    print("ok 5 - active package remains byte-identical")
    print("ok 6 - authorization tool has no apply or pointer operation")
    print("1..6")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
