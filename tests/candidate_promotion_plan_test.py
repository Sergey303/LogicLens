#!/usr/bin/env python3
"""Offline verification for additive Builder candidate promotion plans."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


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


def build_fixture(repository: Path, root: Path):
    review_module = load_module(
        "review_builder_candidate_fixture",
        repository / "tools" / "review_builder_candidate.py",
    )
    plan_module = load_module(
        "plan_builder_candidate_promotion_fixture",
        repository / "tools" / "plan_builder_candidate_promotion.py",
    )

    candidate_root = root / "candidate"
    contents = {
        "rules/candidate_researcher_at_iis.pl": (
            ":- module(candidate_researcher_at_iis, [researcher_at_iis/2]).\n"
        ).encode("utf-8"),
        "tests/candidate_researcher_at_iis_tests.pl": (
            ":- begin_tests(candidate_researcher_at_iis).\n"
            "test(candidate_exists) :- assertion(true).\n"
            ":- end_tests(candidate_researcher_at_iis).\n"
        ).encode("utf-8"),
        "ui/researcher-at-iis.json": (
            '{"schemaVersion":"0.1","bindings":[]}\n'
        ).encode("utf-8"),
    }
    file_records = {}
    kinds = {
        "rules/candidate_researcher_at_iis.pl": "rule",
        "tests/candidate_researcher_at_iis_tests.pl": "test",
        "ui/researcher-at-iis.json": "ui",
    }
    for relative_path, content in contents.items():
        destination = candidate_root / Path(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        file_records[relative_path] = {
            "kind": kinds[relative_path],
            "sha256": plan_module.sha256(content),
            "bytes": len(content),
        }

    candidate_hash = "sha256:" + "c" * 64
    candidate_package_hash = "sha256:" + "d" * 64
    base_hash = "sha256:" + "b" * 64
    provider = {
        "kind": "ollama",
        "name": "ollama",
        "model": "qwen2.5-coder:7b",
    }
    metrics = {
        "cliCalls": 0,
        "manualFixes": 0,
        "elapsedMs": 12985.073,
        "costUsd": 0,
    }
    candidate = {
        "schemaVersion": "0.1",
        "stage": "candidate",
        "candidateId": "qwen-run-001-candidate",
        "taskId": "eng-26-researcher-at-iis-v0",
        "baseEpoch": 0,
        "baseRevision": 0,
        "basePackageHash": base_hash,
        "uiContractVersion": "0.1",
        "cliProtocolVersion": "0.1",
        "provider": {**provider, "runId": "qwen-run-001"},
        "metrics": metrics,
        "candidateHash": candidate_hash,
        "candidatePackageHash": candidate_package_hash,
        "files": file_records,
    }
    candidate_path = candidate_root / "candidate-manifest.json"
    write_json(plan_module, candidate_path, candidate)

    comparison = {
        "schemaVersion": "0.1",
        "candidateId": candidate["candidateId"],
        "taskId": candidate["taskId"],
        "provider": {**provider, "runId": "qwen-run-001"},
        "metrics": metrics,
        "baseline": {"epoch": 0, "revision": 0, "packageHash": base_hash},
        "candidate": {
            "candidateHash": candidate_hash,
            "candidatePackageHash": candidate_package_hash,
            "fileCount": 3,
            "ruleFiles": 1,
            "testFiles": 1,
            "uiFiles": 1,
        },
        "validation": [
            {"name": name, "status": "passed"}
            for name in (
                "baselineIntegrity",
                "proposalSchema",
                "pathAndSizePolicy",
                "staticSafety",
                "uiVocabulary",
                "prologLoad",
                "candidateTests",
                "portableSmoke",
                "activePackageUnchanged",
            )
        ],
        "comparison": {
            "runtimeOutputsEqual": True,
            "addedFiles": sorted(contents),
            "modifiedActiveFiles": [],
            "removedActiveFiles": [],
        },
    }
    comparison_path = root / "comparison.json"
    write_json(plan_module, comparison_path, comparison)

    run = {
        "schemaVersion": "0.1",
        "runId": "qwen-run-001",
        "taskId": candidate["taskId"],
        "taskHash": "sha256:" + "1" * 64,
        "oracleHash": "sha256:" + "2" * 64,
        "basePackageHash": base_hash,
        "provider": provider,
        "metrics": metrics,
        "rawOutput": None,
        "proposalHash": "sha256:" + "3" * 64,
        "candidateHash": candidate_hash,
        "candidatePackageHash": candidate_package_hash,
        "comparisonReportHash": review_module.sha256(comparison_path.read_bytes()),
        "validation": {"candidate": "passed", "oracle": "passed"},
    }
    run_path = root / "run.json"
    write_json(plan_module, run_path, run)

    review_schema = repository / "contracts" / "candidate-review-v0.schema.json"
    run_schema = repository / "contracts" / "builder-run-v0.schema.json"
    review = review_module.create_review_record(
        run_path=run_path,
        comparison_path=comparison_path,
        candidate_manifest_path=candidate_path,
        run_schema_path=run_schema,
        review_schema_path=review_schema,
        review_id="eng-86-review-001",
        reviewer="Sergey303",
        decision="recommend",
        reason="Passed all technical checks and selected for promotion planning.",
    )
    review_path = root / "review.json"
    write_json(plan_module, review_path, review)
    return plan_module, review_module, candidate_root, candidate_path, review_path


def expect_error(module, action, expected: str) -> None:
    try:
        action()
    except module.PromotionPlanError as exc:
        if expected not in str(exc):
            raise VerificationError(f"unexpected error: {exc}") from exc
    else:
        raise VerificationError(f"expected error containing {expected!r}")


def create_plan(module, repository, candidate_root, candidate_path, review_path):
    return module.create_promotion_plan(
        review_path=review_path,
        candidate_manifest_path=candidate_path,
        candidate_root=candidate_root,
        review_schema_path=repository / "contracts" / "candidate-review-v0.schema.json",
        plan_schema_path=(
            repository / "contracts" / "candidate-promotion-plan-v0.schema.json"
        ),
        plan_id="eng-87-plan-001",
    )


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="logiclens-promotion-plan-") as temporary:
        root = Path(temporary)
        module, review_module, candidate_root, candidate_path, review_path = (
            build_fixture(repository, root)
        )
        plan = create_plan(
            module,
            repository,
            candidate_root,
            candidate_path,
            review_path,
        )
        if plan["target"]["epoch"] != 0 or plan["target"]["revision"] != 1:
            raise VerificationError("target revision is not the next additive revision")
        if plan["rollback"] != {
            "epoch": 0,
            "revision": 0,
            "packageHash": "sha256:" + "b" * 64,
        }:
            raise VerificationError("rollback target was not pinned to the baseline")
        if plan["intent"] != {
            "manifest": "planned-only",
            "activePointerUpdate": "not-performed",
            "apply": "not-performed",
        }:
            raise VerificationError("promotion plan crossed the apply boundary")
        if [item["path"] for item in plan["changes"]["addedFiles"]] != sorted(
            item["path"] for item in plan["changes"]["addedFiles"]
        ):
            raise VerificationError("added files are not sorted deterministically")
        if not all(plan["checks"].values()):
            raise VerificationError("promotion plan contains a failed check")

        plan_path = root / "promotion-plan.json"
        write_json(module, plan_path, plan)
        verified = module.verify_promotion_plan(
            plan_path=plan_path,
            review_path=review_path,
            candidate_manifest_path=candidate_path,
            candidate_root=candidate_root,
            review_schema_path=repository / "contracts" / "candidate-review-v0.schema.json",
            plan_schema_path=(
                repository / "contracts" / "candidate-promotion-plan-v0.schema.json"
            ),
        )
        if verified != plan:
            raise VerificationError("verified promotion plan changed")

        rule_path = candidate_root / "rules" / "candidate_researcher_at_iis.pl"
        original_rule = rule_path.read_bytes()
        rule_path.write_bytes(original_rule + b"% tamper\n")
        expect_error(
            module,
            lambda: create_plan(
                module,
                repository,
                candidate_root,
                candidate_path,
                review_path,
            ),
            "size differs",
        )
        rule_path.write_bytes(original_rule)

        review = json.loads(review_path.read_text(encoding="utf-8"))
        review["decision"] = "reject"
        review["reviewHash"] = review_module.compute_review_hash(review)
        write_json(module, review_path, review)
        expect_error(
            module,
            lambda: create_plan(
                module,
                repository,
                candidate_root,
                candidate_path,
                review_path,
            ),
            "decision is not recommend",
        )

        module, review_module, candidate_root, candidate_path, review_path = (
            build_fixture(repository, root / "fresh")
        )
        plan = create_plan(
            module,
            repository,
            candidate_root,
            candidate_path,
            review_path,
        )
        plan["target"]["revision"] = 2
        plan_path = root / "tampered-plan.json"
        write_json(module, plan_path, plan)
        expect_error(
            module,
            lambda: module.verify_promotion_plan(
                plan_path=plan_path,
                review_path=review_path,
                candidate_manifest_path=candidate_path,
                candidate_root=candidate_root,
                review_schema_path=(
                    repository / "contracts" / "candidate-review-v0.schema.json"
                ),
                plan_schema_path=(
                    repository
                    / "contracts"
                    / "candidate-promotion-plan-v0.schema.json"
                ),
            ),
            "hash does not match",
        )

        expect_error(
            module,
            lambda: module.validate_candidate_path("../entry.pl", "rule"),
            "outside the additive allowlist",
        )

    source = (
        repository / "tools" / "plan_builder_candidate_promotion.py"
    ).read_text(encoding="utf-8")
    if "run_builder_ollama" in source or "run_builder_codex" in source:
        raise VerificationError("promotion planner invokes a provider")
    if "shutil.copy" in source or "replace(" in source:
        raise VerificationError("promotion planner contains an apply-like file operation")

    print("ok 1 - reviewed recommendation creates deterministic revision 0.1 plan")
    print("ok 2 - exact added file hashes and rollback baseline are pinned")
    print("ok 3 - candidate file tampering is rejected")
    print("ok 4 - rejected human review cannot produce a promotion plan")
    print("ok 5 - plan tampering and path traversal are rejected")
    print("ok 6 - planner never invokes providers or applies a revision")
    print("1..6")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
