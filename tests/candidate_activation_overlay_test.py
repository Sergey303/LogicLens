#!/usr/bin/env python3
"""Offline and SWI-Prolog verification for the reviewed activation overlay."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath


class VerificationError(AssertionError):
    pass


def load_module(name: str, path: Path):
    tools = path.parent
    sys.path.insert(0, str(tools))
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise VerificationError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(tools))


def write_json(module, path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(module.canonical_json_bytes(value))


def hash64(character: str) -> str:
    return "sha256:" + character * 64


def build_fixture(repository: Path, root: Path, overlay_module, readiness_module, plan_module):
    active = root / "active"
    candidate = root / "candidate"
    active.joinpath("rules").mkdir(parents=True)
    active_entry = (
        ":- use_module('rules/cli_runtime.pl').\n"
        ":- use_module(library(http/json)).\n\n"
        ":- initialization(main, main).\n\n"
        "main :-\n"
        "    json_read_dict(user_input, Request, [value_string_as(string)]),\n"
        "    cli_runtime:handle_request(Request, Response, ExitCode),\n"
        "    json_write_dict(current_output, Response, [width(0)]), nl,\n"
        "    halt(ExitCode).\n"
    ).encode("utf-8")
    cli_runtime = (
        ":- module(cli_runtime, [handle_request/3]).\n"
        "loaded_epoch(0).\n"
        "loaded_revision(0).\n"
        "handle_request(Request, Response, 0) :-\n"
        "    get_dict(requestId, Request, RequestId),\n"
        "    get_dict(command, Request, CommandText),\n"
        "    atom_string(Command, CommandText),\n"
        "    Response = response{\n"
        "        protocolVersion: \"0.1\",\n"
        "        requestId: RequestId,\n"
        "        command: Command,\n"
        "        status: ok,\n"
        "        epoch: 0,\n"
        "        revision: 0,\n"
        "        result: health_result{\n"
        "            kind: health,\n"
        "            availableCommands: [health],\n"
        "            baselineMarker: \"unchanged\"\n"
        "        },\n"
        "        diagnostics: []\n"
        "    }.\n"
    ).encode("utf-8")
    active.joinpath("entry.pl").write_bytes(active_entry)
    active.joinpath("rules", "cli_runtime.pl").write_bytes(cli_runtime)

    payload = {
        PurePosixPath("entry.pl"): active_entry,
        PurePosixPath("rules/cli_runtime.pl"): cli_runtime,
    }
    base_package_hash = overlay_module.aggregate_hash(
        b"LogicLensActiveEpoch\0",
        1,
        payload.items(),
    )
    active_manifest = {
        "schemaVersion": "0.1",
        "stage": "active",
        "epoch": 0,
        "baseRevision": 0,
        "uiContractVersion": "0.1",
        "cliProtocolVersion": "0.1",
        "packageHash": base_package_hash,
        "files": {
            str(path): overlay_module.sha256(content)
            for path, content in sorted(payload.items(), key=lambda item: str(item[0]))
        },
    }
    write_json(overlay_module, active / "manifest.json", active_manifest)
    shutil.copytree(active, candidate)

    candidate_rule = (
        ":- module(candidate_researcher_at_iis, [researcher_at_iis/2]).\n\n"
        "researcher_at_iis(\n"
        "    'urn:logiclens:person:alex',\n"
        "    ['f:participant', 'f:organization', 'f:role']\n"
        ").\n"
    ).encode("utf-8")
    candidate_test = (
        ":- begin_tests(candidate_researcher_at_iis).\n"
        ":- use_module('../rules/candidate_researcher_at_iis.pl').\n"
        "test(alex) :- researcher_at_iis('urn:logiclens:person:alex', _).\n"
        ":- end_tests(candidate_researcher_at_iis).\n"
    ).encode("utf-8")
    candidate_ui = overlay_module.canonical_json_bytes(
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
    additions = {
        PurePosixPath("rules/candidate_researcher_at_iis.pl"): ("rule", candidate_rule),
        PurePosixPath("tests/candidate_researcher_at_iis_tests.pl"): ("test", candidate_test),
        PurePosixPath("ui/researcher-at-iis.json"): ("ui", candidate_ui),
    }
    for path, (_, content) in additions.items():
        destination = candidate.joinpath(*path.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    candidate_hash = hash64("c")
    candidate_package_hash = hash64("d")
    candidate_manifest = {
        "schemaVersion": "0.1",
        "stage": "candidate",
        "candidateId": "fixture-candidate",
        "taskId": "fixture-task",
        "baseEpoch": 0,
        "baseRevision": 0,
        "basePackageHash": base_package_hash,
        "uiContractVersion": "0.1",
        "cliProtocolVersion": "0.1",
        "provider": {
            "kind": "fixture",
            "name": "fixture",
            "model": "deterministic",
            "runId": "fixture-run",
        },
        "metrics": {
            "cliCalls": 0,
            "manualFixes": 0,
            "elapsedMs": 0,
            "costUsd": 0,
        },
        "candidateHash": candidate_hash,
        "candidatePackageHash": candidate_package_hash,
        "files": {
            str(path): {
                "kind": kind,
                "sha256": overlay_module.sha256(content),
                "bytes": len(content),
            }
            for path, (kind, content) in sorted(additions.items(), key=lambda item: str(item[0]))
        },
    }
    candidate_manifest_path = candidate / "candidate-manifest.json"
    write_json(overlay_module, candidate_manifest_path, candidate_manifest)

    added_files = [
        {
            "path": str(path),
            "kind": kind,
            "sha256": overlay_module.sha256(content),
            "bytes": len(content),
        }
        for path, (kind, content) in sorted(additions.items(), key=lambda item: str(item[0]))
    ]
    plan = {
        "schemaVersion": "0.1",
        "stage": "candidate-promotion-plan",
        "planId": "fixture-plan",
        "review": {
            "reviewId": "fixture-review",
            "reviewHash": hash64("a"),
            "decision": "recommend",
        },
        "source": {
            "candidateId": "fixture-candidate",
            "taskId": "fixture-task",
            "baseEpoch": 0,
            "baseRevision": 0,
            "basePackageHash": base_package_hash,
            "candidateHash": candidate_hash,
            "candidatePackageHash": candidate_package_hash,
        },
        "target": {
            "epoch": 0,
            "revision": 1,
            "mode": "additive-revision",
            "plannedRevisionHash": hash64("e"),
        },
        "changes": {
            "addedFiles": added_files,
            "modifiedActiveFiles": [],
            "removedActiveFiles": [],
        },
        "rollback": {
            "epoch": 0,
            "revision": 0,
            "packageHash": base_package_hash,
        },
        "intent": {
            "manifest": "planned-only",
            "activePointerUpdate": "not-performed",
            "apply": "not-performed",
        },
        "evidence": {
            "reviewFileHash": hash64("f"),
            "candidateManifestFileHash": overlay_module.sha256(
                candidate_manifest_path.read_bytes()
            ),
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
    plan["promotionPlanHash"] = plan_module.compute_promotion_plan_hash(plan)
    plan_path = root / "promotion-plan.json"
    write_json(overlay_module, plan_path, plan)

    blockers = readiness_module.build_blockers(
        {
            "planVerified": True,
            "baselineVerified": True,
            "candidateFilesVerified": True,
            "targetRevisionRepresented": False,
            "candidateRuleLoaded": False,
            "candidatePredicateExposed": False,
        },
        0,
        1,
    )
    assessment = {
        "schemaVersion": "0.1",
        "stage": "candidate-activation-readiness",
        "assessmentId": "fixture-readiness",
        "status": "blocked",
        "source": {
            "planId": "fixture-plan",
            "promotionPlanHash": plan["promotionPlanHash"],
            "candidateHash": candidate_hash,
            "candidatePackageHash": candidate_package_hash,
            "basePackageHash": base_package_hash,
        },
        "target": {"epoch": 0, "revision": 1},
        "observedRuntime": {
            "loadedEpoch": 0,
            "loadedRevision": 0,
            "candidateModules": ["candidate_researcher_at_iis"],
            "candidateExports": ["researcher_at_iis/2"],
        },
        "checks": {
            "planVerified": True,
            "baselineVerified": True,
            "candidateFilesVerified": True,
            "targetRevisionRepresented": False,
            "candidateRuleLoaded": False,
            "candidatePredicateExposed": False,
        },
        "blockers": blockers,
        "intent": {
            "staging": "not-performed",
            "apply": "not-performed",
            "activePointerUpdate": "not-performed",
        },
    }
    assessment["assessmentHash"] = readiness_module.compute_assessment_hash(assessment)
    assessment_path = root / "readiness.json"
    write_json(overlay_module, assessment_path, assessment)
    return active, candidate, candidate_manifest_path, plan_path, assessment_path


def run_request(swipl: str, runtime: Path, request: dict) -> tuple[int, dict]:
    completed = subprocess.run(
        [swipl, "--quiet", "-s", str(runtime / "entry.pl"), "--"],
        cwd=runtime,
        input=json.dumps(request, ensure_ascii=False),
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise VerificationError(
            f"runtime returned {len(lines)} JSON lines: stdout={completed.stdout!r}; "
            f"stderr={completed.stderr!r}"
        )
    return completed.returncode, json.loads(lines[0])


def expect_error(module, action, expected: str) -> None:
    try:
        action()
    except module.ActivationOverlayError as exc:
        if expected not in str(exc):
            raise VerificationError(f"unexpected error: {exc}") from exc
    else:
        raise VerificationError(f"expected error containing {expected!r}")


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    tools = repository / "tools"
    overlay_module = load_module(
        "build_builder_candidate_activation_overlay",
        tools / "build_builder_candidate_activation_overlay.py",
    )
    readiness_module = load_module(
        "assess_builder_candidate_activation_readiness_overlay_test",
        tools / "assess_builder_candidate_activation_readiness.py",
    )
    plan_module = load_module(
        "plan_builder_candidate_promotion_overlay_test",
        tools / "plan_builder_candidate_promotion.py",
    )
    swipl = shutil.which("swipl")
    if swipl is None:
        raise VerificationError("swipl is required")

    with tempfile.TemporaryDirectory(prefix="logiclens-overlay-") as temporary:
        root = Path(temporary)
        active, candidate, candidate_manifest, plan_path, assessment_path = build_fixture(
            repository,
            root,
            overlay_module,
            readiness_module,
            plan_module,
        )
        readiness_schema = repository / "contracts" / "candidate-activation-readiness-v0.schema.json"
        plan_schema = repository / "contracts" / "candidate-promotion-plan-v0.schema.json"
        overlay_schema = repository / "contracts" / "candidate-activation-overlay-v0.schema.json"

        manifest, files = overlay_module.create_overlay(
            assessment_path=assessment_path,
            plan_path=plan_path,
            candidate_manifest_path=candidate_manifest,
            candidate_root=candidate,
            readiness_schema_path=readiness_schema,
            plan_schema_path=plan_schema,
            overlay_schema_path=overlay_schema,
            overlay_id="fixture-overlay",
        )
        second_manifest, second_files = overlay_module.create_overlay(
            assessment_path=assessment_path,
            plan_path=plan_path,
            candidate_manifest_path=candidate_manifest,
            candidate_root=candidate,
            readiness_schema_path=readiness_schema,
            plan_schema_path=plan_schema,
            overlay_schema_path=overlay_schema,
            overlay_id="fixture-overlay",
        )
        if manifest != second_manifest or files != second_files:
            raise VerificationError("overlay build is not deterministic")
        if manifest["intent"] != {
            "staging": "not-performed",
            "apply": "not-performed",
            "activePointerUpdate": "not-performed",
        }:
            raise VerificationError("overlay crossed the activation boundary")

        overlay_root = root / "overlay"
        overlay_module.write_overlay(overlay_root, manifest, files)
        verified = overlay_module.verify_overlay(
            overlay_root=overlay_root,
            assessment_path=assessment_path,
            plan_path=plan_path,
            candidate_manifest_path=candidate_manifest,
            candidate_root=candidate,
            readiness_schema_path=readiness_schema,
            plan_schema_path=plan_schema,
            overlay_schema_path=overlay_schema,
        )
        if verified != manifest:
            raise VerificationError("overlay verification changed the manifest")

        staged = root / "staged"
        shutil.copytree(candidate, staged)
        for relative, content in files.items():
            destination = staged.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)

        health_code, health = run_request(
            swipl,
            staged,
            {
                "protocolVersion": "0.1",
                "requestId": "health-1",
                "command": "health",
                "epoch": 0,
                "revision": 1,
                "options": {},
            },
        )
        if health_code != 0 or health.get("status") != "ok":
            raise VerificationError(f"overlay health failed: {health}")
        if health.get("revision") != 1:
            raise VerificationError("overlay health did not report revision 1")
        if health.get("result", {}).get("baselineMarker") != "unchanged":
            raise VerificationError("overlay changed the delegated baseline result")
        if "derived-query" not in health.get("result", {}).get("availableCommands", []):
            raise VerificationError("overlay health omitted derived-query")

        derived_code, derived = run_request(
            swipl,
            staged,
            {
                "protocolVersion": "0.1",
                "requestId": "derived-1",
                "command": "derived-query",
                "epoch": 0,
                "revision": 1,
                "options": {
                    "predicate": "urn:logiclens:derived:researcher-at-iis"
                },
            },
        )
        rows = derived.get("result", {}).get("rows", [])
        if derived_code != 0 or derived.get("status") != "ok" or len(rows) != 1:
            raise VerificationError(f"derived query failed: {derived}")
        if rows[0].get("entityId") != "urn:logiclens:person:alex":
            raise VerificationError("derived query returned the wrong entity")
        if rows[0].get("evidenceFactIds") != [
            "f:participant",
            "f:organization",
            "f:role",
        ]:
            raise VerificationError("derived query returned the wrong evidence")

        stale_code, stale = run_request(
            swipl,
            staged,
            {
                "protocolVersion": "0.1",
                "requestId": "stale-1",
                "command": "health",
                "epoch": 0,
                "revision": 0,
                "options": {},
            },
        )
        if stale_code != 1 or stale.get("error", {}).get("code") != "stale_state":
            raise VerificationError(f"stale state was not rejected: {stale}")

        unknown_code, unknown = run_request(
            swipl,
            staged,
            {
                "protocolVersion": "0.1",
                "requestId": "unknown-1",
                "command": "derived-query",
                "epoch": 0,
                "revision": 1,
                "options": {"predicate": "urn:logiclens:derived:unknown"},
            },
        )
        if unknown_code != 1 or unknown.get("error", {}).get("code") != "unknown_predicate":
            raise VerificationError(f"unknown predicate was not rejected: {unknown}")

        readiness = readiness_module.create_assessment(
            plan_path=plan_path,
            candidate_manifest_path=candidate_manifest,
            candidate_root=candidate,
            active_root=active,
            runtime_root=staged,
            plan_schema_path=plan_schema,
            readiness_schema_path=readiness_schema,
            assessment_id="fixture-ready",
        )
        if readiness["status"] != "ready" or readiness["blockers"] != []:
            raise VerificationError(f"overlay runtime did not become ready: {readiness}")
        if not all(readiness["checks"].values()):
            raise VerificationError("ready overlay contains a failed readiness check")

        tampered = overlay_root / "rules" / "revision_runtime.pl"
        tampered.write_text(tampered.read_text(encoding="utf-8") + "% tampered\n", encoding="utf-8")
        expect_error(
            overlay_module,
            lambda: overlay_module.verify_overlay(
                overlay_root=overlay_root,
                assessment_path=assessment_path,
                plan_path=plan_path,
                candidate_manifest_path=candidate_manifest,
                candidate_root=candidate,
                readiness_schema_path=readiness_schema,
                plan_schema_path=plan_schema,
                overlay_schema_path=overlay_schema,
            ),
            "differs from its manifest",
        )

        if overlay_module.tree_bytes(active) != overlay_module.tree_bytes(active):
            raise VerificationError("active fixture changed")

    source = (tools / "build_builder_candidate_activation_overlay.py").read_text(
        encoding="utf-8"
    )
    if "activate" in source.lower() or "activePointerUpdate\": \"performed" in source:
        raise VerificationError("overlay builder contains activation behavior")

    print("ok 1 - blocked readiness produces a deterministic reviewed overlay")
    print("ok 2 - overlay is limited to entry.pl and revision_runtime.pl")
    print("ok 3 - baseline health delegates unchanged while reporting revision 1")
    print("ok 4 - derived-query exposes the reviewed candidate predicate")
    print("ok 5 - stale state and unknown predicates are rejected")
    print("ok 6 - entry-selected readiness becomes ready in the isolated runtime")
    print("ok 7 - overlay tampering is detected and active files remain untouched")
    print("1..7")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        VerificationError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
