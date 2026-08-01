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

import semantic_claims_llm as llm
from active_epoch.hashing import canonical_json_bytes


def literal(value: str, datatype: str | None = None) -> dict:
    return {
        "kind": "literal",
        "lexical": value,
        "literalKind": "datatype" if datatype else "plain",
        "language": None,
        "datatype": datatype,
    }


def fact(fid: str, subject: str, predicate: str, value: str, datatype: str | None = None) -> dict:
    return {
        "factId": fid,
        "subject": subject,
        "predicate": predicate,
        "object": literal(value, datatype),
        "origins": ["origin:test"],
    }


def case_value() -> dict:
    return {
        "task": {
            "language": "ru",
            "goal": "compare_revisions",
            "text": "Сравни R1 и R2 по состоянию и материалу.",
            "questions": [{"questionId": "q1", "text": "Какое состояние у R2?"}],
            "answerKey": [{"questionId": "q1", "answer": "checked"}],
        },
        "canonicalFacts": [
            fact("f:r1:id", "r1", "p:id", "R1"),
            fact("f:r1:state", "r1", "p:state", "open"),
            fact("f:r2:id", "r2", "p:id", "R2"),
            fact("f:r2:state", "r2", "p:state", "checked"),
        ],
        "ontologyEvidence": [
            {
                "element": {"kind": "predicate", "id": "p:id"},
                "labels": [{"language": "ru", "text": "Редакция"}],
                "definitions": [],
            }
        ],
        "oracleSemanticClaims": [{"secret": True}],
        "oracleDatasetProfile": {"secret": True},
        "expectedPresentation": {"secret": True},
    }


def valid_response() -> dict:
    return {
        "claims": [
            {
                "dataElement": {"kind": "predicate", "id": "p:id"},
                "facet": "display_role",
                "role": "identifier",
                "status": "supported",
                "evidence": [{"kind": "fact_ids", "factIds": ["f:r1:id", "f:r2:id"]}],
                "alternativeIndices": [],
            },
            {
                "dataElement": {"kind": "predicate", "id": "p:state"},
                "facet": "value_role",
                "role": "status",
                "status": "supported",
                "evidence": [
                    {"kind": "fact_ids", "factIds": ["f:r1:state", "f:r2:state"]},
                    {"kind": "task_text", "value": "состоянию"},
                    {"kind": "neighboring_predicates", "predicateIds": ["p:id"]},
                ],
                "alternativeIndices": [],
            },
        ],
        "unclassifiedPredicateIds": [],
    }


def ambiguous_response() -> dict:
    return {
        "claims": [
            {
                "dataElement": {"kind": "predicate", "id": "p:state"},
                "facet": "value_role",
                "role": "status",
                "status": "possible",
                "evidence": [{"kind": "task_text", "value": "состоянию"}],
                "alternativeIndices": [1],
            },
            {
                "dataElement": {"kind": "predicate", "id": "p:state"},
                "facet": "value_role",
                "role": "category",
                "status": "possible",
                "evidence": [{"kind": "fact_ids", "factIds": ["f:r1:state", "f:r2:state"]}],
                "alternativeIndices": [0],
            },
        ],
        "unclassifiedPredicateIds": ["p:id"],
    }


class SemanticClaimsLlmTests(unittest.TestCase):
    def test_committed_schema_matches_runtime_schema(self):
        schema_path = REPO_ROOT / "contracts" / "semantic-claims-llm-response-v0.schema.json"
        committed = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(committed, llm.response_schema())

    def test_response_schema_is_closed_but_role_is_not_an_enum(self):
        schema = llm.response_schema()
        self.assertFalse(schema["additionalProperties"])
        claim = schema["properties"]["claims"]["items"]
        self.assertFalse(claim["additionalProperties"])
        role = claim["properties"]["role"]
        self.assertIn("pattern", role)
        self.assertNotIn("enum", role)

    def test_prompt_excludes_all_oracle_and_answer_fields(self):
        prompt = llm.build_prompt(case_value())
        for key in llm.FORBIDDEN_PROMPT_KEYS:
            self.assertNotIn(f'"{key}"', prompt)
        self.assertIn("p:state", prompt)
        self.assertIn("Сравни R1 и R2", prompt)

    def test_request_must_exactly_reproduce_frozen_public_case(self):
        case = case_value()
        request = llm.build_request(case, "qwen:test", 0, 8192, 2048)
        llm.validate_request(case, request)
        request["messages"][0]["content"] += "\nORACLE: hidden"
        with self.assertRaisesRegex(llm.SemanticClaimsLlmError, "exactly reproduce"):
            llm.validate_request(case, request)

    def test_valid_response_covers_every_predicate(self):
        llm.validate_response(case_value(), valid_response())

    def test_unknown_predicate_is_rejected(self):
        response = valid_response()
        response["claims"][0]["dataElement"]["id"] = "p:invented"
        with self.assertRaisesRegex(llm.SemanticClaimsLlmError, "unknown predicate"):
            llm.validate_response(case_value(), response)

    def test_invalid_fact_reference_is_rejected(self):
        response = valid_response()
        response["claims"][1]["evidence"][0]["factIds"] = ["f:invented"]
        with self.assertRaisesRegex(llm.SemanticClaimsLlmError, "unknown FactId"):
            llm.validate_response(case_value(), response)

    def test_non_substring_task_evidence_is_rejected(self):
        response = valid_response()
        response["claims"][1]["evidence"][1]["value"] = "hidden answer"
        with self.assertRaisesRegex(llm.SemanticClaimsLlmError, "task.text substring"):
            llm.validate_response(case_value(), response)

    def test_supported_claim_requires_evidence(self):
        response = valid_response()
        response["claims"][0]["evidence"] = []
        with self.assertRaisesRegex(llm.SemanticClaimsLlmError, "requires evidence"):
            llm.validate_response(case_value(), response)

    def test_coverage_cannot_silently_omit_predicates(self):
        response = valid_response()
        response["claims"] = response["claims"][:1]
        with self.assertRaisesRegex(llm.SemanticClaimsLlmError, "omitted visible predicates"):
            llm.validate_response(case_value(), response)

    def test_alternatives_are_symmetric_and_get_deterministic_ids(self):
        response = ambiguous_response()
        llm.validate_response(case_value(), response)
        claims = llm.convert_claims("case", response)
        self.assertEqual("llm:case:001", claims[0]["claimId"])
        self.assertEqual(["llm:case:002"], claims[0]["alternatives"])
        response["claims"][1]["alternativeIndices"] = []
        with self.assertRaisesRegex(llm.SemanticClaimsLlmError, "symmetric"):
            llm.validate_response(case_value(), response)

    def test_invalid_json_is_not_repaired(self):
        raw = {
            "done": True,
            "done_reason": "stop",
            "eval_count": 100,
            "message": {"content": '{"claims":['},
        }
        with self.assertRaisesRegex(llm.SemanticClaimsLlmError, "not repaired"):
            llm.extract_content(raw, 2048)

    def test_output_limited_response_is_rejected(self):
        raw = {
            "done": True,
            "done_reason": "length",
            "eval_count": 2048,
            "message": {"content": "{}"},
        }
        with self.assertRaisesRegex(llm.SemanticClaimsLlmError, "output limit"):
            llm.extract_content(raw, 2048)

    def test_only_loopback_ollama_endpoint_is_allowed(self):
        llm.validate_endpoint("http://127.0.0.1:11434/api/chat")
        llm.validate_endpoint("http://localhost:11434/api/chat")
        for value in (
            "https://127.0.0.1:11434/api/chat",
            "http://example.com/api/chat",
            "http://127.0.0.1:11434/api/generate",
        ):
            with self.assertRaises(llm.SemanticClaimsLlmError):
                llm.validate_endpoint(value)

    def test_candidate_is_bound_to_request_response_and_scorer(self):
        case = case_value()
        response = valid_response()
        request = llm.build_request(case, "qwen:test", 7, 8192, 2048)
        summary = SimpleNamespace(benchmark_id="b")
        fake_load = (summary, b"manifest", "cases/01.json", case, b"case")
        transport = {"doneReason": "stop", "promptEvalCount": 100, "evalCount": 80, "totalDuration": 1}
        with patch.object(llm, "load_case", return_value=fake_load):
            candidate = llm.build_candidate(
                Path("."), "case", response, model="qwen:test", seed=7,
                request=request, transport=transport, expected_manifest_sha256=None,
            )
            self.assertEqual("qwen:test", candidate["producer"]["model"])
            self.assertFalse(candidate["inputPolicy"]["oracleClaimsUsed"])
            with patch.object(llm.baseline, "evaluate_claims", return_value={"exactRole": {"tp": 2}}) as scorer:
                evaluation = llm.build_evaluation(Path("."), candidate, expected_manifest_sha256=None)
                scorer.assert_called_once()
                self.assertEqual({"exactRole": {"tp": 2}}, evaluation["metrics"])

    def test_candidate_roundtrip_rejects_tampering(self):
        case = case_value()
        response = valid_response()
        request = llm.build_request(case, "qwen:test", 0, 8192, 2048)
        summary = SimpleNamespace(benchmark_id="b")
        fake_load = (summary, b"manifest", "cases/01.json", case, b"case")
        raw_response = {
            "model": "qwen:test",
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 100,
            "eval_count": 80,
            "total_duration": 1,
            "message": {"content": json.dumps(response, ensure_ascii=False)},
        }
        raw_bytes = canonical_json_bytes(raw_response)
        _, transport = llm.extract_content(raw_response, 2048)
        transport["rawResponseSha256"] = llm.sha256_prefixed(raw_bytes)
        with patch.object(llm, "load_case", return_value=fake_load):
            candidate = llm.build_candidate(
                Path("."), "case", response, model="qwen:test", seed=0,
                request=request, transport=transport, expected_manifest_sha256=None,
            )
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                request_path = root / "request.json"
                raw_path = root / "raw.json"
                response_path = root / "response.json"
                candidate_path = root / "candidate.json"
                request_path.write_bytes(canonical_json_bytes(request))
                raw_path.write_bytes(raw_bytes)
                response_path.write_bytes(canonical_json_bytes(response))
                candidate_path.write_bytes(canonical_json_bytes(candidate))
                verified = llm.verify_candidate(
                    Path("."), request_path, raw_path, response_path, candidate_path,
                    expected_manifest_sha256=None,
                )
                self.assertEqual(candidate, verified)
                candidate["claims"][0]["role"] = "changed"
                candidate_path.write_bytes(canonical_json_bytes(candidate))
                with self.assertRaises(llm.SemanticClaimsLlmError):
                    llm.verify_candidate(
                        Path("."), request_path, raw_path, response_path, candidate_path,
                        expected_manifest_sha256=None,
                    )


if __name__ == "__main__":
    unittest.main()
