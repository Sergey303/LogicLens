#!/usr/bin/env python3
"""Offline and SWI-Prolog checks for staged-revision-v0."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath

from active_epoch.hashing import aggregate_hash
from builder_candidate.cli import tree_bytes


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


def expect_error(module, action, expected: str) -> None:
    try:
        action()
    except module.StagedRevisionError as exc:
        if expected not in str(exc):
            raise VerificationError(f"unexpected error: {exc}") from exc
    else:
        raise VerificationError(f"expected error containing {expected!r}")


def add_smoke_and_rebind(
    *,
    active: Path,
    candidate: Path,
    candidate_manifest_path: Path,
    plan_path: Path,
    blocked_path: Path,
    hashing_module,
    readiness_module,
    plan_module,
) -> None:
    request = {
        "protocolVersion": "0.1",
        "requestId": "fixture-health",
        "command": "health",
        "epoch": 0,
        "revision": 0,
        "options": {},
    }
    request_bytes = hashing_module.canonical_json_bytes(request)
    for root in (active, candidate):
        smoke = root / "smoke" / "health.request.json"
        smoke.parent.mkdir(parents=True, exist_ok=True)
        smoke.write_bytes(request_bytes)

    payload = tree_bytes(active)
    payload.pop(PurePosixPath("manifest.json"), None)
    active_manifest = json.loads((active / "manifest.json").read_text(encoding="utf-8"))
    active_manifest["files"] = {
        str(path): hashing_module.sha256(content)
        for path, content in sorted(payload.items(), key=lambda item: str(item[0]))
    }
    active_manifest["packageHash"] = aggregate_hash(
        b"LogicLensActiveEpoch\0",
        1,
        payload.items(),
    )
    write_json(hashing_module, active / "manifest.json", active_manifest)
    write_json(hashing_module, candidate / "manifest.json", active_manifest)

    candidate_manifest = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
    candidate_manifest["basePackageHash"] = active_manifest["packageHash"]
    write_json(hashing_module, candidate_manifest_path, candidate_manifest)

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["source"]["basePackageHash"] = active_manifest["packageHash"]
    plan["rollback"]["packageHash"] = active_manifest["packageHash"]
    plan["promotionPlanHash"] = plan_module.compute_promotion_plan_hash(plan)
    write_json(hashing_module, plan_path, plan)

    blocked = json.loads(blocked_path.read_text(encoding="utf-8"))
    blocked["source"]["promotionPlanHash"] = plan["promotionPlanHash"]
    blocked["source"]["basePackageHash"] = active_manifest["packageHash"]
    blocked["assessmentHash"] = readiness_module.compute_assessment_hash(blocked)
    write_json(hashing_module, blocked_path, blocked)


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    tools = repository / "tools"
    tests = repository / "tests"

    staged = load_module(
        "build_builder_staged_revision_tested",
        tools / "build_builder_staged_revision.py",
    )
    overlay_base = load_module(
        "build_builder_candidate_activation_overlay_tested",
        tools / "build_builder_candidate_activation_overlay.py",
    )
    overlay_clean = load_module(
        "build_builder_candidate_activation_overlay_clean_tested",
        tools / "build_builder_candidate_activation_overlay_clean_compat.py",
    )
    readiness = load_module(
        "assess_builder_candidate_activation_readiness_staged_tested",
        tools / "assess_builder_candidate_activation_readiness.py",
    )
    plan_module = load_module(
        "plan_builder_candidate_promotion_staged_tested",
        tools / "plan_builder_candidate_promotion.py",
    )
    fixture = load_module(
        "candidate_activation_overlay_fixture",
        tests / "candidate_activation_overlay_test.py",
    )

    overlay_base.aggregate_hash = aggregate_hash
    overlay_base.tree_bytes = tree_bytes

    swipl = shutil.which("swipl")
    if swipl is None:
        raise VerificationError("swipl is required")

    plan_schema = repository / "contracts" / "candidate-promotion-plan-v0.schema.json"
    readiness_schema = repository / "contracts" / "candidate-activation-readiness-v0.schema.json"
    overlay_schema = repository / "contracts" / "candidate-activation-overlay-v0.schema.json"
    staged_schema = repository / "contracts" / "staged-revision-v0.schema.json"

    with tempfile.TemporaryDirectory(prefix="logiclens-staged-") as temporary:
        root = Path(temporary)
        active, candidate, candidate_manifest, plan_path, blocked_path = fixture.build_fixture(
            repository,
            root,
            overlay_base,
            readiness,
            plan_module,
        )
        add_smoke_and_rebind(
            active=active,
            candidate=candidate,
            candidate_manifest_path=candidate_manifest,
            plan_path=plan_path,
            blocked_path=blocked_path,
            hashing_module=overlay_base,
            readiness_module=readiness,
            plan_module=plan_module,
        )

        overlay_manifest, overlay_files = overlay_clean.create_overlay(
            assessment_path=blocked_path,
            plan_path=plan_path,
            candidate_manifest_path=candidate_manifest,
            candidate_root=candidate,
            readiness_schema_path=readiness_schema,
            plan_schema_path=plan_schema,
            overlay_schema_path=overlay_schema,
            overlay_id="fixture-clean-overlay",
        )
        overlay_root = root / "overlay"
        overlay_clean.write_overlay(overlay_root, overlay_manifest, overlay_files)

        preview = root / "preview"
        shutil.copytree(candidate, preview)
        for relative, content in overlay_files.items():
            destination = preview.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)

        ready = readiness.create_assessment(
            plan_path=plan_path,
            candidate_manifest_path=candidate_manifest,
            candidate_root=candidate,
            active_root=active,
            runtime_root=preview,
            plan_schema_path=plan_schema,
            readiness_schema_path=readiness_schema,
            assessment_id="fixture-ready",
        )
        if ready["status"] != "ready" or ready["blockers"] != []:
            raise VerificationError(f"fixture did not become ready: {ready}")
        ready_path = root / "ready.json"
        write_json(overlay_base, ready_path, ready)

        active_before = tree_bytes(active)
        output = root / "staged"
        manifest, payload = staged.create_staged_revision(
            stage_id="fixture-stage",
            output=output,
            plan_path=plan_path,
            blocked_assessment_path=blocked_path,
            ready_assessment_path=ready_path,
            candidate_manifest_path=candidate_manifest,
            candidate_root=candidate,
            overlay_root=overlay_root,
            active_root=active,
            plan_schema_path=plan_schema,
            readiness_schema_path=readiness_schema,
            overlay_schema_path=overlay_schema,
            staged_schema_path=staged_schema,
            swipl=swipl,
            timeout_seconds=20.0,
        )
        staged.write_payload(output, payload)
        staged.validate_staged_runtime(
            staged_root=output,
            active_root=active,
            candidate_manifest=json.loads(candidate_manifest.read_text(encoding="utf-8")),
            overlay_manifest=overlay_manifest,
            swipl=swipl,
            timeout_seconds=20.0,
        )
        write_json(overlay_base, output / "manifest.json", manifest)

        verified = staged.verify_staged_revision(
            staged_root=output,
            plan_path=plan_path,
            blocked_assessment_path=blocked_path,
            ready_assessment_path=ready_path,
            candidate_manifest_path=candidate_manifest,
            candidate_root=candidate,
            overlay_root=overlay_root,
            active_root=active,
            plan_schema_path=plan_schema,
            readiness_schema_path=readiness_schema,
            overlay_schema_path=overlay_schema,
            staged_schema_path=staged_schema,
            swipl=swipl,
            timeout_seconds=20.0,
        )
        if verified != manifest:
            raise VerificationError("staged verification changed the manifest")
        if manifest["target"] != {
            "epoch": 0,
            "revision": 1,
            "mode": "additive-revision",
        }:
            raise VerificationError("staged target is not revision 0.1")
        if manifest["intent"] != {
            "staging": "isolated-output-only",
            "apply": "not-performed",
            "activePointerUpdate": "not-performed",
        }:
            raise VerificationError("staged package crossed the activation boundary")
        if tree_bytes(active) != active_before:
            raise VerificationError("staging changed the active fixture")

        second_manifest, second_payload = staged.create_staged_revision(
            stage_id="fixture-stage",
            output=root / "unused",
            plan_path=plan_path,
            blocked_assessment_path=blocked_path,
            ready_assessment_path=ready_path,
            candidate_manifest_path=candidate_manifest,
            candidate_root=candidate,
            overlay_root=overlay_root,
            active_root=active,
            plan_schema_path=plan_schema,
            readiness_schema_path=readiness_schema,
            overlay_schema_path=overlay_schema,
            staged_schema_path=staged_schema,
            swipl=swipl,
            timeout_seconds=20.0,
        )
        if second_manifest != manifest or second_payload != payload:
            raise VerificationError("staged package is not deterministic")

        tampered = output / "rules" / "candidate_researcher_at_iis.pl"
        tampered.write_text(tampered.read_text(encoding="utf-8") + "% tampered\n", encoding="utf-8")
        expect_error(
            staged,
            lambda: staged.verify_staged_revision(
                staged_root=output,
                plan_path=plan_path,
                blocked_assessment_path=blocked_path,
                ready_assessment_path=ready_path,
                candidate_manifest_path=candidate_manifest,
                candidate_root=candidate,
                overlay_root=overlay_root,
                active_root=active,
                plan_schema_path=plan_schema,
                readiness_schema_path=readiness_schema,
                overlay_schema_path=overlay_schema,
                staged_schema_path=staged_schema,
                swipl=swipl,
                timeout_seconds=20.0,
            ),
            "per-file hashes",
        )

    source = (tools / "build_builder_staged_revision.py").read_text(encoding="utf-8")
    for forbidden in ("activate", "switch_active", "update_pointer"):
        if f"def {forbidden}" in source:
            raise VerificationError(f"staged tool exposes forbidden operation: {forbidden}")

    print("ok 1 - exact baseline, candidate, plan, ready assessment and overlay are rebound")
    print("ok 2 - staged revision 0.1 is deterministic and schema-valid")
    print("ok 3 - Prolog load, PlUnit, smoke and derived runtime checks pass")
    print("ok 4 - package tampering is rejected")
    print("ok 5 - active package remains byte-identical")
    print("ok 6 - staged tool has no activation or pointer-update operation")
    print("1..6")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
