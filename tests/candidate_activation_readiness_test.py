#!/usr/bin/env python3
"""Focused offline checks for candidate activation readiness."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath

from active_epoch.hashing import aggregate_hash, canonical_json_bytes, sha256


class VerificationError(AssertionError):
    pass


def load_module(path: Path, name: str):
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


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def build_active(root: Path) -> dict:
    (root / "rules").mkdir(parents=True)
    (root / "entry.pl").write_text(
        ":- use_module('rules/cli_runtime.pl').\n",
        encoding="utf-8",
        newline="\n",
    )
    (root / "rules" / "cli_runtime.pl").write_text(
        ":- module(cli_runtime, []).\nloaded_epoch(0).\nloaded_revision(0).\n",
        encoding="utf-8",
        newline="\n",
    )
    payload = {
        PurePosixPath(path.relative_to(root).as_posix()): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    manifest = {
        "epoch": 0,
        "parentEpoch": None,
        "baseRevision": 0,
        "stage": "active",
        "engineCommit": "a" * 40,
        "uiContractVersion": "0.1",
        "cliProtocolVersion": "0.1",
        "factContractVersion": "1",
        "factIdEncodingVersion": 1,
        "prologDataContractVersion": "1",
        "ontologyLabelContractVersion": "1",
        "occurrenceIdEncodingVersion": 1,
        "dataCompilerCommit": "a" * 40,
        "ontologyCompilerCommit": "a" * 40,
        "dataHash": "sha256:" + "1" * 64,
        "ontologyHash": "sha256:" + "2" * 64,
        "rulesHash": "sha256:" + "3" * 64,
        "packageHash": aggregate_hash(
            b"LogicLensActiveEpoch\0",
            1,
            payload.items(),
        ),
        "files": {str(path): sha256(content) for path, content in payload.items()},
    }
    write_json(root / "manifest.json", manifest)
    return manifest


def build_inputs(root: Path, plan_module):
    active_root = root / "active"
    active_manifest = build_active(active_root)
    candidate_root = root / "candidate"
    shutil.copytree(active_root, candidate_root)

    files = {
        "rules/candidate_researcher.pl": (
            "rule",
            ":- module(candidate_researcher, [researcher_at_iis/2]).\n"
            "researcher_at_iis(person, [fact]).\n",
        ),
        "tests/candidate_researcher_tests.pl": (
            "test",
            ":- begin_tests(candidate_researcher).\n"
            ":- use_module('../rules/candidate_researcher.pl').\n"
            "test(works) :- researcher_at_iis(person, [fact]).\n"
            ":- end_tests(candidate_researcher).\n",
        ),
        "ui/researcher.json": (
            "ui",
            '{"schemaVersion":"0.1","bindings":[{"predicate":"urn:test:researcher","component":"Property"}]}\n',
        ),
    }
    declarations = {}
    for relative, (kind, text) in files.items():
        destination = candidate_root / Path(*PurePosixPath(relative).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8", newline="\n")
        content = destination.read_bytes()
        declarations[relative] = {
            "kind": kind,
            "sha256": sha256(content),
            "bytes": len(content),
        }

    candidate = {
        "schemaVersion": "0.1",
        "stage": "candidate",
        "candidateId": "fixture-candidate",
        "taskId": "fixture-task",
        "baseEpoch": 0,
        "baseRevision": 0,
        "basePackageHash": active_manifest["packageHash"],
        "uiContractVersion": "0.1",
        "cliProtocolVersion": "0.1",
        "provider": {
            "kind": "fixture",
            "name": "fixture",
            "model": "fixture",
            "runId": "fixture-run",
        },
        "metrics": {"cliCalls": 0, "manualFixes": 0, "elapsedMs": 0, "costUsd": 0},
        "candidateHash": "sha256:" + "4" * 64,
        "candidatePackageHash": "sha256:" + "5" * 64,
        "files": declarations,
    }
    candidate_path = candidate_root / "candidate-manifest.json"
    write_json(candidate_path, candidate)

    added = [
        {
            "path": path,
            "kind": metadata["kind"],
            "sha256": metadata["sha256"],
            "bytes": metadata["bytes"],
        }
        for path, metadata in sorted(declarations.items())
    ]
    plan = {
        "schemaVersion": "0.1",
        "stage": "candidate-promotion-plan",
        "planId": "fixture-plan",
        "review": {
            "reviewId": "fixture-review",
            "reviewHash": "sha256:" + "6" * 64,
            "decision": "recommend",
        },
        "source": {
            "candidateId": "fixture-candidate",
            "taskId": "fixture-task",
            "baseEpoch": 0,
            "baseRevision": 0,
            "basePackageHash": active_manifest["packageHash"],
            "candidateHash": candidate["candidateHash"],
            "candidatePackageHash": candidate["candidatePackageHash"],
        },
        "target": {
            "epoch": 0,
            "revision": 1,
            "mode": "additive-revision",
            "plannedRevisionHash": "sha256:" + "7" * 64,
        },
        "changes": {
            "addedFiles": added,
            "modifiedActiveFiles": [],
            "removedActiveFiles": [],
        },
        "rollback": {
            "epoch": 0,
            "revision": 0,
            "packageHash": active_manifest["packageHash"],
        },
        "intent": {
            "manifest": "planned-only",
            "activePointerUpdate": "not-performed",
            "apply": "not-performed",
        },
        "evidence": {
            "reviewFileHash": "sha256:" + "8" * 64,
            "candidateManifestFileHash": sha256(candidate_path.read_bytes()),
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
    write_json(plan_path, plan)
    return active_root, candidate_root, candidate_path, plan_path


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    tools = repository / "tools"
    assessor = load_module(
        tools / "assess_builder_candidate_activation_readiness.py",
        "activation_readiness_tested",
    )
    plan_module = load_module(
        tools / "plan_builder_candidate_promotion.py",
        "promotion_plan_tested",
    )
    plan_schema = repository / "contracts" / "candidate-promotion-plan-v0.schema.json"
    readiness_schema = repository / "contracts" / "candidate-activation-readiness-v0.schema.json"

    with tempfile.TemporaryDirectory(prefix="logiclens-readiness-") as temporary:
        root = Path(temporary)
        active_root, candidate_root, candidate_path, plan_path = build_inputs(
            root,
            plan_module,
        )
        blocked = assessor.create_assessment(
            plan_path=plan_path,
            candidate_manifest_path=candidate_path,
            candidate_root=candidate_root,
            active_root=active_root,
            runtime_root=candidate_root,
            plan_schema_path=plan_schema,
            readiness_schema_path=readiness_schema,
            assessment_id="blocked-assessment",
        )
        codes = {item["code"] for item in blocked["blockers"]}
        expected = {
            "runtime_revision_not_represented",
            "candidate_rule_not_loaded",
            "candidate_predicate_not_exposed",
        }
        if blocked["status"] != "blocked" or codes != expected:
            raise VerificationError(f"dormant candidate verdict is wrong: {blocked}")

        ready_root = root / "ready-runtime"
        shutil.copytree(candidate_root, ready_root)
        (ready_root / "entry.pl").write_text(
            ":- use_module('rules/cli_runtime.pl').\n"
            ":- use_module('rules/candidate_researcher.pl').\n"
            "exposed(P,E) :- candidate_researcher:researcher_at_iis(P,E).\n",
            encoding="utf-8",
            newline="\n",
        )
        (ready_root / "rules" / "cli_runtime.pl").write_text(
            ":- module(cli_runtime, []).\nloaded_epoch(0).\nloaded_revision(1).\n",
            encoding="utf-8",
            newline="\n",
        )
        ready = assessor.create_assessment(
            plan_path=plan_path,
            candidate_manifest_path=candidate_path,
            candidate_root=candidate_root,
            active_root=active_root,
            runtime_root=ready_root,
            plan_schema_path=plan_schema,
            readiness_schema_path=readiness_schema,
            assessment_id="ready-assessment",
        )
        if ready["status"] != "ready" or ready["blockers"]:
            raise VerificationError(f"integrated runtime verdict is wrong: {ready}")

        assessment_path = root / "assessment.json"
        write_json(assessment_path, blocked)
        assessor.verify_assessment(
            assessment_path=assessment_path,
            plan_path=plan_path,
            candidate_manifest_path=candidate_path,
            candidate_root=candidate_root,
            active_root=active_root,
            runtime_root=candidate_root,
            plan_schema_path=plan_schema,
            readiness_schema_path=readiness_schema,
        )
        tampered = json.loads(assessment_path.read_text(encoding="utf-8"))
        tampered["blockers"][0]["message"] = "tampered"
        write_json(assessment_path, tampered)
        try:
            assessor.verify_assessment(
                assessment_path=assessment_path,
                plan_path=plan_path,
                candidate_manifest_path=candidate_path,
                candidate_root=candidate_root,
                active_root=active_root,
                runtime_root=candidate_root,
                plan_schema_path=plan_schema,
                readiness_schema_path=readiness_schema,
            )
        except assessor.ActivationReadinessError as exc:
            if "hash does not match" not in str(exc):
                raise VerificationError(f"unexpected tamper error: {exc}") from exc
        else:
            raise VerificationError("tampered assessment was accepted")

    source = (tools / "assess_builder_candidate_activation_readiness.py").read_text(
        encoding="utf-8"
    ).lower()
    if "run_builder_ollama" in source or "run_builder_codex" in source:
        raise VerificationError("assessor invokes a provider")
    if "copytree" in source or "update_ref" in source:
        raise VerificationError("assessor contains staging or pointer mutation")

    print("ok 1 - dormant files are blocked with exact remediation")
    print("ok 2 - integrated target revision is marked ready")
    print("ok 3 - plan, baseline and candidate bytes are verified")
    print("ok 4 - assessment tampering is rejected")
    print("ok 5 - assessor cannot invoke providers, stage or switch pointers")
    print("1..5")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
