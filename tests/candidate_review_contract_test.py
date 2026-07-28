#!/usr/bin/env python3
"""Offline verification for reviewed Builder candidate recommendations."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


class VerificationError(AssertionError):
    pass


def load_module(path: Path):
    tools = path.parent
    sys.path.insert(0, str(tools))
    try:
        spec = importlib.util.spec_from_file_location("review_builder_candidate", path)
        if spec is None or spec.loader is None:
            raise VerificationError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(tools))


def write_json(module, path: Path, value: dict) -> None:
    path.write_bytes(module.canonical_json_bytes(value))


def fixture(module, root: Path) -> tuple[Path, Path, Path]:
    candidate_hash = "sha256:" + "c" * 64
    candidate_package_hash = "sha256:" + "d" * 64
    base_hash = "sha256:" + "b" * 64
    metrics = {
        "cliCalls": 0,
        "manualFixes": 0,
        "elapsedMs": 12985.073,
        "costUsd": 0,
    }
    provider = {
        "kind": "ollama",
        "name": "ollama",
        "model": "qwen2.5-coder:7b",
    }
    comparison = {
        "schemaVersion": "0.1",
        "candidateId": "qwen-run-001-candidate",
        "taskId": "eng-26-researcher-at-iis-v0",
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
            "addedFiles": [
                "rules/candidate_researcher_at_iis.pl",
                "tests/candidate_researcher_at_iis_tests.pl",
                "ui/researcher-at-iis.json",
            ],
            "modifiedActiveFiles": [],
            "removedActiveFiles": [],
        },
    }
    comparison_path = root / "comparison.json"
    write_json(module, comparison_path, comparison)

    run = {
        "schemaVersion": "0.1",
        "runId": "qwen-run-001",
        "taskId": "eng-26-researcher-at-iis-v0",
        "taskHash": "sha256:" + "1" * 64,
        "oracleHash": "sha256:" + "2" * 64,
        "basePackageHash": base_hash,
        "provider": provider,
        "metrics": metrics,
        "rawOutput": None,
        "proposalHash": "sha256:" + "3" * 64,
        "candidateHash": candidate_hash,
        "candidatePackageHash": candidate_package_hash,
        "comparisonReportHash": module.sha256(comparison_path.read_bytes()),
        "validation": {"candidate": "passed", "oracle": "passed"},
    }
    run_path = root / "run.json"
    write_json(module, run_path, run)

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
        "files": {},
    }
    candidate_path = root / "candidate-manifest.json"
    write_json(module, candidate_path, candidate)
    return run_path, comparison_path, candidate_path


def expect_error(module, action, expected: str) -> None:
    try:
        action()
    except module.CandidateReviewError as exc:
        if expected not in str(exc):
            raise VerificationError(f"unexpected error: {exc}") from exc
    else:
        raise VerificationError(f"expected error containing {expected!r}")


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    module = load_module(repository / "tools" / "review_builder_candidate.py")
    run_schema = repository / "contracts" / "builder-run-v0.schema.json"
    review_schema = repository / "contracts" / "candidate-review-v0.schema.json"

    with tempfile.TemporaryDirectory(prefix="logiclens-review-") as temporary:
        root = Path(temporary)
        run_path, comparison_path, candidate_path = fixture(module, root)
        record = module.create_review_record(
            run_path=run_path,
            comparison_path=comparison_path,
            candidate_manifest_path=candidate_path,
            run_schema_path=run_schema,
            review_schema_path=review_schema,
            review_id="eng-86-review-001",
            reviewer="Sergey303",
            decision="recommend",
            reason="Reviewed after candidate validation and hidden-oracle success.",
        )
        if record["decision"] != "recommend":
            raise VerificationError("recommend decision was not retained")
        if record["activation"] != {"status": "not-performed"}:
            raise VerificationError("review record crossed the activation boundary")
        if not all(record["checks"].values()):
            raise VerificationError("review record contains a failed technical check")

        review_path = root / "review.json"
        review_path.write_bytes(module.canonical_json_bytes(record))
        verified = module.verify_review_record(
            review_path=review_path,
            run_path=run_path,
            comparison_path=comparison_path,
            candidate_manifest_path=candidate_path,
            run_schema_path=run_schema,
            review_schema_path=review_schema,
        )
        if verified != record:
            raise VerificationError("verified record changed")

        rejected = module.create_review_record(
            run_path=run_path,
            comparison_path=comparison_path,
            candidate_manifest_path=candidate_path,
            run_schema_path=run_schema,
            review_schema_path=review_schema,
            review_id="eng-86-review-reject",
            reviewer="Sergey303",
            decision="reject",
            reason="Technically valid, but not selected for the reviewed release.",
        )
        if rejected["decision"] != "reject":
            raise VerificationError("human reject decision was not retained")

        broken_comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
        broken_comparison["comparison"]["modifiedActiveFiles"] = ["entry.pl"]
        write_json(module, comparison_path, broken_comparison)
        run = json.loads(run_path.read_text(encoding="utf-8"))
        run["comparisonReportHash"] = module.sha256(comparison_path.read_bytes())
        write_json(module, run_path, run)
        expect_error(
            module,
            lambda: module.create_review_record(
                run_path=run_path,
                comparison_path=comparison_path,
                candidate_manifest_path=candidate_path,
                run_schema_path=run_schema,
                review_schema_path=review_schema,
                review_id="eng-86-invalid-active",
                reviewer="Sergey303",
                decision="recommend",
                reason="This candidate must not be eligible for recommendation.",
            ),
            "activeFilesUnchanged",
        )

        run_path, comparison_path, candidate_path = fixture(module, root)
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate["candidateHash"] = "sha256:" + "e" * 64
        write_json(module, candidate_path, candidate)
        expect_error(
            module,
            lambda: module.create_review_record(
                run_path=run_path,
                comparison_path=comparison_path,
                candidate_manifest_path=candidate_path,
                run_schema_path=run_schema,
                review_schema_path=review_schema,
                review_id="eng-86-invalid-identity",
                reviewer="Sergey303",
                decision="recommend",
                reason="This candidate must not be eligible for recommendation.",
            ),
            "identityConsistent",
        )

        run_path, comparison_path, candidate_path = fixture(module, root)
        record = module.create_review_record(
            run_path=run_path,
            comparison_path=comparison_path,
            candidate_manifest_path=candidate_path,
            run_schema_path=run_schema,
            review_schema_path=review_schema,
            review_id="eng-86-review-tamper",
            reviewer="Sergey303",
            decision="recommend",
            reason="Reviewed after candidate validation and hidden-oracle success.",
        )
        record["reason"] = "Tampered after review creation."
        review_path.write_bytes(module.canonical_json_bytes(record))
        expect_error(
            module,
            lambda: module.verify_review_record(
                review_path=review_path,
                run_path=run_path,
                comparison_path=comparison_path,
                candidate_manifest_path=candidate_path,
                run_schema_path=run_schema,
                review_schema_path=review_schema,
            ),
            "hash does not match",
        )

    source = (repository / "tools" / "review_builder_candidate.py").read_text(
        encoding="utf-8"
    )
    if "run_builder_ollama" in source or "run_builder_codex" in source:
        raise VerificationError("review tool invokes a provider")

    print("ok 1 - a passed Builder run creates a canonical human review record")
    print("ok 2 - recommendation pins run, candidate and evidence hashes")
    print("ok 3 - reject remains an explicit human decision over a valid candidate")
    print("ok 4 - active-file changes and identity mismatches are rejected")
    print("ok 5 - review tampering is detected")
    print("ok 6 - review never invokes providers or activates an epoch")
    print("1..6")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
