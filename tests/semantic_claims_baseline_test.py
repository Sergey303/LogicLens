#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import semantic_claims_baseline as baseline
from active_epoch.hashing import canonical_json_bytes


def obj(lexical: str, datatype: str | None = None) -> dict:
    return {
        "kind": "literal",
        "lexical": lexical,
        "literalKind": "datatype" if datatype else "plain",
        "language": None,
        "datatype": datatype,
    }


def fact(
    fact_id: str,
    subject: str,
    predicate: str,
    lexical: str,
    datatype: str | None = None,
) -> dict:
    return {
        "factId": fact_id,
        "subject": subject,
        "predicate": predicate,
        "object": obj(lexical, datatype),
        "origins": ["origin:test"],
    }


def ontology(predicate: str, label: str) -> dict:
    return {
        "element": {"kind": "predicate", "id": predicate},
        "labels": [{"language": "ru", "text": label}],
        "definitions": [],
    }


def oracle(
    claim_id: str,
    predicate: str,
    facet: str,
    role: str,
    status: str = "supported",
) -> dict:
    return {
        "claimId": claim_id,
        "dataElement": {"kind": "predicate", "id": predicate},
        "facet": facet,
        "role": role,
        "status": status,
        "evidence": [],
        "alternatives": [],
    }


def case_value() -> dict:
    return {
        "task": {
            "language": "ru",
            "goal": "compare_revisions",
            "text": "ignored by baseline",
        },
        "canonicalFacts": [
            fact("f1", "a", "p:id", "A"),
            fact("f2", "a", "p:status", "draft"),
            fact("f3", "b", "p:id", "B"),
            fact("f4", "b", "p:status", "approved"),
        ],
        "ontologyEvidence": [
            ontology("p:id", "Редакция"),
            ontology("p:status", "Статус"),
        ],
        "oracleSemanticClaims": [
            oracle("o1", "p:id", "display_role", "identifier"),
            oracle("o2", "p:status", "value_role", "status"),
        ],
        "expectedPresentation": {},
    }


class SemanticClaimsBaselineTests(unittest.TestCase):
    def test_known_labels_generate_supported_claims(self):
        claims, unknown = baseline.generate_claims(case_value())
        self.assertEqual([], unknown)
        self.assertEqual(
            [
                ("display_role", "identifier", "supported"),
                ("value_role", "status", "supported"),
            ],
            [
                (claim["facet"], claim["role"], claim["status"])
                for claim in claims
            ],
        )

    def test_opaque_predicates_remain_unclassified(self):
        case = case_value()
        case["ontologyEvidence"] = []
        claims, unknown = baseline.generate_claims(case)
        self.assertEqual([], claims)
        self.assertEqual(["p:id", "p:status"], unknown)

    def test_generic_date_is_possible_not_supported(self):
        case = case_value()
        case["canonicalFacts"] = [
            fact(
                "f",
                "a",
                "p:date",
                "2026-01-01T00:00:00Z",
                "xsd:dateTime",
            )
        ]
        case["ontologyEvidence"] = [ontology("p:date", "Дата")]
        claims, _ = baseline.generate_claims(case)
        self.assertEqual("time_value", claims[0]["role"])
        self.assertEqual("possible", claims[0]["status"])
        self.assertEqual("xsd:dateTime", claims[0]["evidence"][1]["value"])

    def test_generation_does_not_read_oracle_or_task_text(self):
        case = case_value()
        first = baseline.generate_claims(case)
        case["oracleSemanticClaims"] = [{"malicious": True}]
        case["task"]["text"] = "different"
        self.assertEqual(first, baseline.generate_claims(case))

    def test_exact_role_metrics(self):
        case = case_value()
        claims, _ = baseline.generate_claims(case)
        metrics = baseline.evaluate_claims(case, claims)
        self.assertEqual(
            {
                "tp": 2,
                "fp": 0,
                "fn": 0,
                "precision": 1.0,
                "recall": 1.0,
                "f1": 1.0,
            },
            metrics["exactRole"],
        )
        self.assertEqual(1.0, metrics["macroF1ByRole"])
        self.assertEqual(0, metrics["falseSupportedCount"])
        self.assertEqual(1.0, metrics["evidenceValidity"]["rate"])

    def test_ambiguity_detection_uses_possible_status(self):
        case = case_value()
        case["canonicalFacts"] = [
            fact("f", "a", "p:date", "2026-01-01", "xsd:date")
        ]
        case["ontologyEvidence"] = [ontology("p:date", "Дата")]
        case["oracleSemanticClaims"] = [
            oracle(
                "o1",
                "p:date",
                "value_role",
                "time_value",
                "possible",
            ),
            oracle(
                "o2",
                "p:date",
                "value_role",
                "publication_time",
                "possible",
            ),
        ]
        claims, _ = baseline.generate_claims(case)
        metrics = baseline.evaluate_claims(case, claims)
        self.assertEqual(1, metrics["ambiguityDetection"]["tp"])
        self.assertEqual(1, metrics["exactRole"]["tp"])
        self.assertEqual(1, metrics["exactRole"]["fn"])

    def context(self):
        case = case_value()
        loaded = (
            SimpleNamespace(benchmark_id="b"),
            b"manifest",
            "cases/1.json",
            case,
            b"case",
        )
        return case, loaded

    def test_candidate_roundtrip_and_hash(self):
        _, loaded = self.context()
        with patch.object(baseline, "load_case", return_value=loaded):
            artifact = baseline.build_candidate(
                Path("benchmark"),
                "case",
                expected_manifest_sha256=None,
            )
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "candidate.json"
                path.write_bytes(canonical_json_bytes(artifact))
                self.assertEqual(
                    artifact,
                    baseline.verify_candidate(
                        Path("benchmark"),
                        path,
                        expected_manifest_sha256=None,
                    ),
                )

    def test_evaluation_roundtrip_rejects_noncanonical(self):
        _, loaded = self.context()
        with patch.object(baseline, "load_case", return_value=loaded):
            artifact = baseline.build_candidate(
                Path("benchmark"),
                "case",
                expected_manifest_sha256=None,
            )
            with tempfile.TemporaryDirectory() as temp:
                candidate = Path(temp) / "candidate.json"
                candidate.write_bytes(canonical_json_bytes(artifact))
                evaluation = baseline.build_evaluation(
                    Path("benchmark"),
                    candidate,
                    expected_manifest_sha256=None,
                )
                output = Path(temp) / "evaluation.json"
                output.write_text(json.dumps(evaluation), encoding="utf-8")
                with self.assertRaisesRegex(
                    baseline.SemanticClaimsBaselineError,
                    "not canonical",
                ):
                    baseline.verify_evaluation(
                        Path("benchmark"),
                        candidate,
                        output,
                        expected_manifest_sha256=None,
                    )


if __name__ == "__main__":
    unittest.main()
