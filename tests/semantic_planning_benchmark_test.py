#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tools" / "verify_semantic_planning_benchmark.py"
spec = importlib.util.spec_from_file_location("semantic_benchmark_verifier", MODULE_PATH)
assert spec and spec.loader
verifier = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = verifier
spec.loader.exec_module(verifier)


def frozen_case() -> dict:
    return {
        "schemaVersion": "semantic-planning-benchmark-case-v0",
        "caseId": "single-fixture",
        "caseKind": "negative",
        "researchTargets": ["dataset_profile", "false_rich_view_rejection"],
        "task": {
            "language": "ru",
            "text": "Покажи документ и его статус.",
            "goal": "inspect_entity",
            "questions": [{"questionId": "q1", "text": "Каков статус?"}],
            "answerKey": [
                {
                    "questionId": "q1",
                    "answer": "active",
                    "supportFactIds": ["fixture:status"],
                }
            ],
        },
        "canonicalFacts": [
            {
                "factId": "fixture:title",
                "subject": "doc:1",
                "predicate": "dc:title",
                "object": {
                    "kind": "literal",
                    "lexical": "Document",
                    "literalKind": "language",
                    "language": "en",
                    "datatype": None,
                },
                "origins": ["origin:test"],
            },
            {
                "factId": "fixture:status",
                "subject": "doc:1",
                "predicate": "ex:status",
                "object": {
                    "kind": "literal",
                    "lexical": "active",
                    "literalKind": "plain",
                    "language": None,
                    "datatype": None,
                },
                "origins": ["origin:test"],
            },
        ],
        "ontologyEvidence": [
            {
                "element": {"kind": "predicate", "id": "dc:title"},
                "labels": [{"language": "ru", "text": "Название"}],
                "definitions": [],
            },
            {
                "element": {"kind": "predicate", "id": "ex:status"},
                "labels": [{"language": "ru", "text": "Статус"}],
                "definitions": [],
            },
        ],
        "oracleSemanticClaims": [
            {
                "claimId": "claim:title",
                "dataElement": {"kind": "predicate", "id": "dc:title"},
                "facet": "display_role",
                "role": "display_label",
                "status": "supported",
                "evidence": [{"kind": "ontology_label", "value": "Название"}],
                "alternatives": [],
            },
            {
                "claimId": "claim:status",
                "dataElement": {"kind": "predicate", "id": "ex:status"},
                "facet": "value_role",
                "role": "status",
                "status": "supported",
                "evidence": [{"kind": "ontology_label", "value": "Статус"}],
                "alternatives": [],
            },
        ],
        "oracleDatasetProfile": {
            "profileVersion": "dataset-profile-v0",
            "entityIds": ["doc:1"],
            "entityCount": 1,
            "factCount": 2,
            "repeatedRecordShape": False,
            "commonPredicates": ["dc:title", "ex:status"],
            "candidateRowLabelPredicate": "dc:title",
            "candidateDimensions": [],
            "technicalPredicates": [],
            "mandatoryFactIds": ["fixture:title", "fixture:status"],
        },
        "expectedPresentation": {
            "acceptableDecisions": [
                {
                    "kind": "fallback",
                    "component": "generic_property_sections",
                    "reason": "repeated_records_required",
                }
            ],
            "requiredRejectedCandidates": [
                {
                    "component": "comparison_table",
                    "reason": "repeated_records_required",
                }
            ],
            "requiredCoveredFactIds": ["fixture:title", "fixture:status"],
            "mustExposeFallback": True,
        },
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rebuild_manifest(root: Path) -> None:
    files = []
    for relative in ["README.md", "cases/01-single-fixture.json"]:
        data = (root / relative).read_bytes()
        files.append(
            {"path": relative, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        )
    manifest = {
        "schemaVersion": "semantic-planning-benchmark-manifest-v0",
        "benchmarkId": "test-semantic-planning-v0",
        "status": "frozen",
        "researchSpecification": "docs/research/semantic-presentation-planning-v1.md",
        "caseCount": 1,
        "caseIds": ["single-fixture"],
        "mutationPolicy": "append-new-version-only",
        "files": files,
    }
    write_json(root / "manifest.json", manifest)


def make_benchmark(base: Path, case: dict | None = None) -> Path:
    root = base / "benchmark"
    (root / "cases").mkdir(parents=True)
    (root / "README.md").write_text("# Frozen test benchmark\n", encoding="utf-8")
    write_json(root / "cases/01-single-fixture.json", case or frozen_case())
    rebuild_manifest(root)
    return root


class SemanticPlanningBenchmarkTest(unittest.TestCase):
    def assert_invalid(self, root: Path, contains: str) -> None:
        with self.assertRaises(verifier.ValidationError) as context:
            verifier.validate_benchmark(root, expected_manifest_sha256=None)
        self.assertIn(contains, str(context.exception))

    def test_valid_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            summary = verifier.validate_benchmark(make_benchmark(Path(directory)), expected_manifest_sha256=None)
            self.assertEqual(1, summary.case_count)
            self.assertEqual(2, summary.file_count)

    def test_fixture_local_role_is_not_normalized_or_allowlisted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            case_path = root / "cases/01-single-fixture.json"
            case = json.loads(case_path.read_text(encoding="utf-8"))
            case["oracleSemanticClaims"][1]["role"] = "fixture_specific_status_semantics"
            write_json(case_path, case)
            rebuild_manifest(root)
            verifier.validate_benchmark(root, expected_manifest_sha256=None)

    def test_manifest_hash_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            readme = root / "README.md"
            data = readme.read_bytes()
            readme.write_bytes(b"!" + data[1:])
            self.assert_invalid(root, "sha256")

    def test_unlisted_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            (root / "unlisted.txt").write_text("hidden\n", encoding="utf-8")
            self.assert_invalid(root, "unlisted files")

    def test_duplicate_fact_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            case_path = root / "cases/01-single-fixture.json"
            case = json.loads(case_path.read_text(encoding="utf-8"))
            duplicate = copy.deepcopy(case["canonicalFacts"][0])
            case["canonicalFacts"].append(duplicate)
            case["oracleDatasetProfile"]["factCount"] = 3
            write_json(case_path, case)
            rebuild_manifest(root)
            self.assert_invalid(root, "duplicate factId")

    def test_unknown_answer_fact_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            case_path = root / "cases/01-single-fixture.json"
            case = json.loads(case_path.read_text(encoding="utf-8"))
            case["task"]["answerKey"][0]["supportFactIds"] = ["fixture:missing"]
            write_json(case_path, case)
            rebuild_manifest(root)
            self.assert_invalid(root, "unknown FactIds")

    def test_profile_count_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            case_path = root / "cases/01-single-fixture.json"
            case = json.loads(case_path.read_text(encoding="utf-8"))
            case["oracleDatasetProfile"]["factCount"] = 3
            write_json(case_path, case)
            rebuild_manifest(root)
            self.assert_invalid(root, "does not match canonicalFacts length")

    def test_mandatory_fact_set_must_be_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            case_path = root / "cases/01-single-fixture.json"
            case = json.loads(case_path.read_text(encoding="utf-8"))
            case["oracleDatasetProfile"]["mandatoryFactIds"] = ["fixture:status"]
            write_json(case_path, case)
            rebuild_manifest(root)
            self.assert_invalid(root, "must equal all canonical FactIds exactly")

    def test_presentation_coverage_gap_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            case_path = root / "cases/01-single-fixture.json"
            case = json.loads(case_path.read_text(encoding="utf-8"))
            case["expectedPresentation"]["requiredCoveredFactIds"] = ["fixture:status"]
            write_json(case_path, case)
            rebuild_manifest(root)
            self.assert_invalid(root, "coverage plus fallback-only coverage")

    def test_frozen_manifest_trust_anchor_rejects_coordinated_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            original_anchor = hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest()
            case_path = root / "cases/01-single-fixture.json"
            case = json.loads(case_path.read_text(encoding="utf-8"))
            case["oracleSemanticClaims"][1]["role"] = "coordinated_change"
            write_json(case_path, case)
            rebuild_manifest(root)
            with self.assertRaises(verifier.ValidationError) as context:
                verifier.validate_benchmark(root, expected_manifest_sha256=original_anchor)
            self.assertIn("frozen trust anchor mismatch", str(context.exception))

    def test_literal_shape_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            case_path = root / "cases/01-single-fixture.json"
            case = json.loads(case_path.read_text(encoding="utf-8"))
            case["canonicalFacts"][1]["object"]["literalKind"] = "plain"
            case["canonicalFacts"][1]["object"]["datatype"] = "xsd:string"
            write_json(case_path, case)
            rebuild_manifest(root)
            self.assert_invalid(root, "plain literal requires null language and datatype")


if __name__ == "__main__":
    unittest.main()
