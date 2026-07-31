#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

spec = importlib.util.spec_from_file_location("semantic_claims_artifact", TOOLS / "semantic_claims_artifact.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def case_value(role: str = "fixture_specific_role") -> dict:
    return {
        "schemaVersion": "semantic-planning-benchmark-case-v0",
        "caseId": "artifact-fixture",
        "caseKind": "negative",
        "researchTargets": ["semantic_interpretation"],
        "task": {
            "language": "ru",
            "text": "Покажи статус документа.",
            "goal": "inspect_entity",
            "questions": [{"questionId": "q1", "text": "Каков статус?"}],
            "answerKey": [{"questionId": "q1", "answer": "active", "supportFactIds": ["fixture:status"]}],
        },
        "canonicalFacts": [
            {
                "factId": "fixture:title",
                "subject": "doc:1",
                "predicate": "dc:title",
                "object": {"kind": "literal", "lexical": "Doc", "literalKind": "plain", "language": None, "datatype": None},
                "origins": ["origin:test"],
            },
            {
                "factId": "fixture:status",
                "subject": "doc:1",
                "predicate": "ex:status",
                "object": {"kind": "literal", "lexical": "active", "literalKind": "plain", "language": None, "datatype": None},
                "origins": ["origin:test"],
            },
        ],
        "ontologyEvidence": [
            {"element": {"kind": "predicate", "id": "dc:title"}, "labels": [{"language": "ru", "text": "Название"}], "definitions": []},
            {"element": {"kind": "predicate", "id": "ex:status"}, "labels": [{"language": "ru", "text": "Статус"}], "definitions": []},
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
                "role": role,
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
            "acceptableDecisions": [{"kind": "fallback", "component": "generic_property_sections", "reason": "repeated_records_required"}],
            "requiredRejectedCandidates": [{"component": "comparison_table", "reason": "repeated_records_required"}],
            "requiredCoveredFactIds": ["fixture:title", "fixture:status"],
            "mustExposeFallback": True,
        },
    }


def make_benchmark(base: Path, role: str = "fixture_specific_role") -> Path:
    root = base / "benchmark"
    (root / "cases").mkdir(parents=True)
    (root / "README.md").write_text("# Test benchmark\n", encoding="utf-8")
    case_path = root / "cases/01-artifact-fixture.json"
    write_json(case_path, case_value(role))
    files = []
    for relative in ["README.md", "cases/01-artifact-fixture.json"]:
        data = (root / relative).read_bytes()
        files.append({"path": relative, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    write_json(
        root / "manifest.json",
        {
            "schemaVersion": "semantic-planning-benchmark-manifest-v0",
            "benchmarkId": "artifact-test-v0",
            "status": "frozen",
            "researchSpecification": "docs/research/semantic-presentation-planning-v1.md",
            "caseCount": 1,
            "caseIds": ["artifact-fixture"],
            "mutationPolicy": "append-new-version-only",
            "files": files,
        },
    )
    return root


class SemanticClaimsArtifactTest(unittest.TestCase):
    def test_build_preserves_fixture_local_role(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory), "publication_time")
            artifact = module.build_artifact(root, "artifact-fixture", expected_manifest_sha256=None)
            self.assertEqual("publication_time", artifact["claims"][1]["role"])

    def test_build_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            first = module.build_artifact(root, "artifact-fixture", expected_manifest_sha256=None)
            second = module.build_artifact(root, "artifact-fixture", expected_manifest_sha256=None)
            self.assertEqual(first, second)
            self.assertEqual(module.canonical_json_bytes(first), module.canonical_json_bytes(second))

    def test_canonical_roundtrip_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            artifact = module.build_artifact(root, "artifact-fixture", expected_manifest_sha256=None)
            path = Path(directory) / "artifact.json"
            path.write_bytes(module.canonical_json_bytes(artifact))
            verified = module.verify_artifact(root, path, expected_manifest_sha256=None)
            self.assertEqual(artifact["artifactHash"], verified["artifactHash"])

    def test_altered_claim_is_rejected_even_with_recomputed_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            artifact = module.build_artifact(root, "artifact-fixture", expected_manifest_sha256=None)
            artifact["claims"][1]["role"] = "normalized_status"
            without_hash = deepcopy(artifact)
            without_hash.pop("artifactHash")
            artifact["artifactHash"] = module.artifact_hash(without_hash)
            path = Path(directory) / "artifact.json"
            path.write_bytes(module.canonical_json_bytes(artifact))
            with self.assertRaises(module.SemanticClaimsArtifactError) as context:
                module.verify_artifact(root, path, expected_manifest_sha256=None)
            self.assertIn("altered, or normalized", str(context.exception))

    def test_noncanonical_bytes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            artifact = module.build_artifact(root, "artifact-fixture", expected_manifest_sha256=None)
            path = Path(directory) / "artifact.json"
            path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(module.SemanticClaimsArtifactError) as context:
                module.verify_artifact(root, path, expected_manifest_sha256=None)
            self.assertIn("not in canonical byte representation", str(context.exception))

    def test_stale_artifact_is_rejected_after_case_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = make_benchmark(base)
            artifact = module.build_artifact(root, "artifact-fixture", expected_manifest_sha256=None)
            path = base / "artifact.json"
            path.write_bytes(module.canonical_json_bytes(artifact))
            root = make_benchmark(base / "changed", "changed_role")
            with self.assertRaises(module.SemanticClaimsArtifactError):
                module.verify_artifact(root, path, expected_manifest_sha256=None)

    def test_unknown_producer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = make_benchmark(Path(directory))
            artifact = module.build_artifact(root, "artifact-fixture", expected_manifest_sha256=None)
            artifact["producer"]["kind"] = "llm"
            without_hash = deepcopy(artifact)
            without_hash.pop("artifactHash")
            artifact["artifactHash"] = module.artifact_hash(without_hash)
            path = Path(directory) / "artifact.json"
            path.write_bytes(module.canonical_json_bytes(artifact))
            with self.assertRaises(module.SemanticClaimsArtifactError) as context:
                module.verify_artifact(root, path, expected_manifest_sha256=None)
            self.assertIn("only exact oracle-fixture", str(context.exception))


if __name__ == "__main__":
    unittest.main()
