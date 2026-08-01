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

import presentation_decision_artifact as planner


def fact(fact_id: str, subject: str, predicate: str) -> dict:
    return {
        "factId": fact_id,
        "subject": subject,
        "predicate": predicate,
        "object": {
            "kind": "literal",
            "lexical": fact_id,
            "literalKind": "plain",
            "language": None,
            "datatype": None,
        },
        "origins": ["origin:test"],
    }


def claim(
    claim_id: str,
    predicate: str,
    role: str,
    status: str = "supported",
) -> dict:
    return {
        "claimId": claim_id,
        "dataElement": {"kind": "predicate", "id": predicate},
        "facet": "value_role",
        "role": role,
        "status": status,
        "evidence": [],
        "alternatives": [],
    }


def positive_inputs():
    case = {
        "task": {"goal": "compare_records"},
        "canonicalFacts": [
            fact("f:a:id", "a", "p:id"),
            fact("f:a:status", "a", "p:status"),
            fact("f:b:id", "b", "p:id"),
            fact("f:b:status", "b", "p:status"),
        ],
        "expectedPresentation": {},
    }
    claims = [
        {**claim("c:id", "p:id", "identifier"), "facet": "display_role"},
        claim("c:status", "p:status", "status"),
    ]
    profile = {
        "profileVersion": "dataset-profile-v0",
        "entityIds": ["a", "b"],
        "entityCount": 2,
        "factCount": 4,
        "repeatedRecordShape": True,
        "commonPredicates": ["p:id", "p:status"],
        "candidateRowLabelPredicate": "p:id",
        "candidateDimensions": [
            {
                "predicate": "p:status",
                "semanticClaimIds": ["c:status"],
                "present": 2,
                "total": 2,
                "eligible": True,
            }
        ],
        "technicalPredicates": [],
        "mandatoryFactIds": [
            "f:a:id",
            "f:a:status",
            "f:b:id",
            "f:b:status",
        ],
    }
    return case, claims, profile


class PresentationDecisionTests(unittest.TestCase):
    def test_selects_comparison_table_with_complete_coverage(self):
        case, claims, profile = positive_inputs()
        decision, evaluation, coverage = planner.compute_presentation_decision(
            case, claims, profile
        )
        self.assertEqual("selected", evaluation["outcome"])
        self.assertEqual(
            "comparison_table",
            decision["acceptableDecisions"][0]["component"],
        )
        self.assertEqual(
            ["p:status"],
            decision["acceptableDecisions"][0]["dimensionPredicates"],
        )
        self.assertTrue(decision["mustExposeFallback"])
        self.assertTrue(coverage["complete"])
        self.assertEqual([], coverage["fallbackOnlyFactIds"])

    def test_ambiguous_time_is_excluded_and_timeline_rejected(self):
        case, claims, profile = positive_inputs()
        case["canonicalFacts"].insert(1, fact("f:a:date", "a", "p:date"))
        case["canonicalFacts"].insert(4, fact("f:b:date", "b", "p:date"))
        profile["mandatoryFactIds"] = [
            item["factId"] for item in case["canonicalFacts"]
        ]
        claims.extend(
            [
                claim("c:date:event", "p:date", "time_value", "possible"),
                claim(
                    "c:date:publication",
                    "p:date",
                    "publication_time",
                    "possible",
                ),
            ]
        )
        profile["candidateDimensions"].insert(
            0,
            {
                "predicate": "p:date",
                "semanticClaimIds": [
                    "c:date:event",
                    "c:date:publication",
                ],
                "present": 2,
                "total": 2,
                "eligible": False,
                "ineligibilityReason": "required_semantic_claim_not_supported",
            },
        )
        decision, evaluation, coverage = planner.compute_presentation_decision(
            case, claims, profile
        )
        selected = decision["acceptableDecisions"][0]
        self.assertEqual(
            [{"predicate": "p:date", "reason": "ambiguous_time_semantics"}],
            selected["excludedPredicates"],
        )
        self.assertEqual(
            [{"component": "timeline", "reason": "ambiguous_time_semantics"}],
            decision["requiredRejectedCandidates"],
        )
        self.assertEqual(
            ["f:a:date", "f:b:date"],
            decision["factsRequiredOnlyInFallback"],
        )
        self.assertEqual("selected", evaluation["outcome"])
        self.assertTrue(coverage["complete"])

    def test_lookalike_records_fall_back_without_shared_dimensions(self):
        case, claims, profile = positive_inputs()
        profile["candidateRowLabelPredicate"] = None
        profile["candidateDimensions"] = []
        decision, evaluation, coverage = planner.compute_presentation_decision(
            case, claims, profile
        )
        self.assertEqual("rejected", evaluation["outcome"])
        self.assertEqual(
            "insufficient_shared_semantic_dimensions",
            evaluation["reason"],
        )
        self.assertEqual(
            "generic_property_sections",
            decision["acceptableDecisions"][0]["component"],
        )
        self.assertEqual(
            profile["mandatoryFactIds"], coverage["primaryFactIds"]
        )

    def test_single_entity_falls_back_before_other_constraints(self):
        case, claims, profile = positive_inputs()
        profile["entityIds"] = ["a"]
        profile["entityCount"] = 1
        profile["repeatedRecordShape"] = False
        decision, evaluation, _ = planner.compute_presentation_decision(
            case, claims, profile
        )
        self.assertEqual("repeated_records_required", evaluation["reason"])
        self.assertEqual(
            "repeated_records_required",
            decision["requiredRejectedCandidates"][0]["reason"],
        )

    def test_non_comparison_task_is_rejected_fail_closed(self):
        case, claims, profile = positive_inputs()
        case["task"]["goal"] = "inspect_collection"
        decision, evaluation, _ = planner.compute_presentation_decision(
            case, claims, profile
        )
        self.assertEqual("comparison_task_required", evaluation["reason"])
        self.assertEqual(
            "comparison_task_required",
            decision["requiredRejectedCandidates"][0]["reason"],
        )

    def test_compute_does_not_read_frozen_expected_presentation(self):
        case, claims, profile = positive_inputs()
        first = planner.compute_presentation_decision(case, claims, profile)
        case["expectedPresentation"] = {"malicious": "oracle leakage"}
        second = planner.compute_presentation_decision(case, claims, profile)
        self.assertEqual(first, second)

    def test_non_time_unsupported_dimension_is_excluded_without_timeline(self):
        case, claims, profile = positive_inputs()
        claims.append(claim("c:maybe", "p:maybe", "category", "possible"))
        profile["candidateDimensions"].append(
            {
                "predicate": "p:maybe",
                "semanticClaimIds": ["c:maybe"],
                "present": 2,
                "total": 2,
                "eligible": False,
                "ineligibilityReason": "required_semantic_claim_not_supported",
            }
        )
        decision, _, _ = planner.compute_presentation_decision(
            case, claims, profile
        )
        selected = decision["acceptableDecisions"][0]
        self.assertEqual(
            "required_semantic_claim_not_supported",
            selected["excludedPredicates"][0]["reason"],
        )
        self.assertEqual([], decision["requiredRejectedCandidates"])

    def artifact_context(self):
        case, claims, profile = positive_inputs()
        decision, _, _ = planner.compute_presentation_decision(
            case, claims, profile
        )
        case["expectedPresentation"] = decision
        benchmark = {
            "benchmarkId": "b0",
            "manifestSha256": "sha256:" + "1" * 64,
            "caseId": "case-1",
            "casePath": "cases/1.json",
            "caseSha256": "sha256:" + "2" * 64,
        }
        claims_artifact = {
            "benchmark": benchmark,
            "claims": claims,
            "artifactHash": "sha256:" + "3" * 64,
        }
        profile_artifact = {
            "benchmark": benchmark,
            "input": {
                "semanticClaimsArtifactHash": claims_artifact["artifactHash"]
            },
            "profile": profile,
            "artifactHash": "sha256:" + "4" * 64,
        }
        load_result = (
            SimpleNamespace(benchmark_id="b0"),
            b"manifest",
            "cases/1.json",
            case,
            b"case",
        )
        return case, claims_artifact, profile_artifact, load_result

    def test_build_binds_inputs_and_exact_oracle(self):
        _, claims_artifact, profile_artifact, load_result = self.artifact_context()
        with patch.object(
            planner,
            "verify_semantic_claims_artifact",
            return_value=claims_artifact,
        ), patch.object(
            planner,
            "verify_dataset_profile_artifact",
            return_value=profile_artifact,
        ), patch.object(planner, "load_case", return_value=load_result):
            artifact = planner.build_artifact(
                Path("benchmark"), Path("claims"), Path("profile")
            )
        self.assertEqual(
            claims_artifact["artifactHash"],
            artifact["input"]["semanticClaimsArtifactHash"],
        )
        self.assertEqual(
            profile_artifact["artifactHash"],
            artifact["input"]["datasetProfileArtifactHash"],
        )
        self.assertTrue(artifact["oracleComparison"]["exactMatch"])
        self.assertTrue(artifact["artifactHash"].startswith("sha256:"))

    def test_build_rejects_oracle_mismatch(self):
        case, claims_artifact, profile_artifact, load_result = self.artifact_context()
        case["expectedPresentation"] = {"not": "the computed decision"}
        with patch.object(
            planner,
            "verify_semantic_claims_artifact",
            return_value=claims_artifact,
        ), patch.object(
            planner,
            "verify_dataset_profile_artifact",
            return_value=profile_artifact,
        ), patch.object(planner, "load_case", return_value=load_result):
            with self.assertRaisesRegex(
                planner.PresentationDecisionArtifactError,
                "does not exactly match",
            ):
                planner.build_artifact(
                    Path("benchmark"), Path("claims"), Path("profile")
                )

    def test_verify_rejects_noncanonical_bytes(self):
        _, claims_artifact, profile_artifact, load_result = self.artifact_context()
        with patch.object(
            planner,
            "verify_semantic_claims_artifact",
            return_value=claims_artifact,
        ), patch.object(
            planner,
            "verify_dataset_profile_artifact",
            return_value=profile_artifact,
        ), patch.object(planner, "load_case", return_value=load_result):
            artifact = planner.build_artifact(
                Path("benchmark"), Path("claims"), Path("profile")
            )
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "artifact.json"
                path.write_text(
                    json.dumps(artifact, ensure_ascii=False),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(
                    planner.PresentationDecisionArtifactError,
                    "not canonical",
                ):
                    planner.verify_artifact(
                        Path("benchmark"),
                        Path("claims"),
                        Path("profile"),
                        path,
                    )


if __name__ == "__main__":
    unittest.main()
