#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

TEST_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = TEST_ROOT / "tools" / "semantic_claims_llm_experiment.py"


def canonical_json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, separators=(",", ": ")) + "\n").encode("utf-8")


def append_field(digest, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big", signed=False))
    digest.update(value)


def install_stubs() -> None:
    active_epoch = types.ModuleType("active_epoch")
    hashing = types.ModuleType("active_epoch.hashing")
    hashing.append_field = append_field
    hashing.canonical_json_bytes = canonical_json_bytes
    active_epoch.hashing = hashing
    sys.modules["active_epoch"] = active_epoch
    sys.modules["active_epoch.hashing"] = hashing

    claims = types.ModuleType("semantic_claims_artifact")
    claims.FROZEN_MANIFEST_SHA256 = "frozen"
    claims.SemanticClaimsArtifactError = type("SemanticClaimsArtifactError", (RuntimeError,), {})
    claims.load_case = lambda *_args, **_kwargs: None
    sys.modules["semantic_claims_artifact"] = claims

    llm = types.ModuleType("semantic_claims_llm")
    llm.SemanticClaimsLlmError = type("SemanticClaimsLlmError", (RuntimeError,), {})
    llm.build_request = lambda case, model, seed, context, output: {
        "case": case["caseId"],
        "model": model,
        "seed": seed,
        "context": context,
        "output": output,
    }
    llm.sha256_prefixed = lambda data: "sha256:" + hashlib.sha256(data).hexdigest()
    llm.verify_candidate = lambda *_args, **_kwargs: None
    llm.verify_evaluation = lambda *_args, **_kwargs: None
    sys.modules["semantic_claims_llm"] = llm

    contract = types.ModuleType("semantic_claims_llm_contract")
    contract.DEFAULT_CONTEXT_TOKENS = 2048
    contract.DEFAULT_MODEL = "qwen:test"
    contract.DEFAULT_OUTPUT_TOKENS = 1024
    sys.modules["semantic_claims_llm_contract"] = contract


install_stubs()
spec = importlib.util.spec_from_file_location("semantic_claims_llm_experiment", MODULE_PATH)
assert spec and spec.loader
experiment = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = experiment
spec.loader.exec_module(experiment)


def fake_load_case(_root: Path, case_id: str):
    summary = SimpleNamespace(benchmark_id="benchmark-v0")
    case = {"caseId": case_id}
    return summary, b"manifest", f"cases/{case_id}.json", case, case_id.encode("utf-8")


def valid_record(item: dict, signature_suffix: str = "same"):
    record = {
        "runId": item["runId"],
        "caseId": item["caseId"],
        "seed": item["seed"],
        "status": "valid",
        "candidateArtifactHash": f"candidate:{item['runId']}",
        "evaluationArtifactHash": f"evaluation:{item['runId']}",
        "exactRole": {"tp": 1, "fp": 0, "fn": 0, "f1": 1.0},
        "macroF1ByRole": 1.0,
        "falseSupportedCount": 0,
        "ambiguityDetection": {"tp": 0, "fp": 0, "fn": 0, "f1": 0.0},
        "contractEvidenceValidity": {"valid": 1, "total": 1, "rate": 1.0},
        "unclassifiedPredicateIds": [],
    }
    detail = {"candidate": {}, "signature": [(item["caseId"], signature_suffix)]}
    return record, detail


class SemanticClaimsLlmExperimentTests(unittest.TestCase):
    def plan(self):
        with patch.object(experiment, "load_frozen_case", side_effect=fake_load_case):
            return experiment.build_plan(Path("."))

    def test_fixed_plan_has_fifteen_unique_runs(self):
        plan = self.plan()
        self.assertEqual(15, len(plan["matrix"]))
        self.assertEqual(15, len({item["runId"] for item in plan["matrix"]}))
        self.assertEqual(set(experiment.PILOT_CASES), {item["caseId"] for item in plan["matrix"]})
        self.assertEqual(set(experiment.PILOT_SEEDS), {item["seed"] for item in plan["matrix"]})
        self.assertFalse(plan["policy"]["automaticPromotion"])
        self.assertTrue(plan["policy"]["allRunsMustBeAccountedFor"])

    def test_plan_roundtrip_is_canonical_and_tamper_evident(self):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_bytes(canonical_json_bytes(plan))
            with patch.object(experiment, "build_plan", return_value=plan):
                self.assertEqual(plan, experiment.verify_plan(Path("."), path))
            tampered = deepcopy(plan)
            tampered["matrix"][0]["seed"] = 99
            path.write_bytes(canonical_json_bytes(tampered))
            with patch.object(experiment, "build_plan", return_value=plan):
                with self.assertRaises(experiment.SemanticClaimsExperimentError):
                    experiment.verify_plan(Path("."), path)

    def test_empty_runs_are_all_reported_missing(self):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as directory:
            report = experiment.aggregate_report(Path("."), plan, Path(directory))
        summary = report["summary"]
        self.assertEqual(15, summary["plannedRuns"])
        self.assertEqual(0, summary["validRuns"])
        self.assertEqual(15, summary["missingRuns"])
        self.assertFalse(summary["complete"])
        self.assertFalse(report["pilotSignals"]["opaqueBeatsDeterministicBaseline"])
        self.assertFalse(report["pilotSignals"]["allSafetyChecksPass"])
        self.assertFalse(report["pilotSignals"]["resultsStableAcrossDeclaredSeeds"])
        self.assertFalse(report["pilotSignals"]["automaticPromotionAllowed"])

    def test_complete_stable_valid_runs_enable_only_research_signals(self):
        plan = self.plan()
        with patch.object(experiment, "inspect_run", side_effect=lambda _b, _r, item, _p: valid_record(item)):
            report = experiment.aggregate_report(Path("."), plan, Path("runs"))
        summary = report["summary"]
        self.assertTrue(summary["complete"])
        self.assertEqual(15, summary["validRuns"])
        self.assertTrue(summary["contractEvidenceSafe"])
        self.assertTrue(summary["falseSupportedSafe"])
        self.assertTrue(summary["stableAcrossSeeds"])
        self.assertTrue(report["pilotSignals"]["opaqueBeatsDeterministicBaseline"])
        self.assertTrue(report["pilotSignals"]["allSafetyChecksPass"])
        self.assertTrue(report["pilotSignals"]["resultsStableAcrossDeclaredSeeds"])
        self.assertFalse(report["pilotSignals"]["automaticPromotionAllowed"])

    def test_invalid_run_is_never_silently_excluded(self):
        plan = self.plan()
        first = plan["matrix"][0]["runId"]

        def inspect(_b, _r, item, _p):
            if item["runId"] == first:
                return ({"runId": item["runId"], "caseId": item["caseId"], "seed": item["seed"], "status": "invalid", "reason": "bad artifact"}, None)
            return valid_record(item)

        with patch.object(experiment, "inspect_run", side_effect=inspect):
            report = experiment.aggregate_report(Path("."), plan, Path("runs"))
        self.assertEqual(1, report["summary"]["invalidRuns"])
        self.assertEqual(14, report["summary"]["validRuns"])
        self.assertFalse(report["summary"]["complete"])
        self.assertFalse(report["pilotSignals"]["opaqueBeatsDeterministicBaseline"])
        self.assertIn("bad artifact", json.dumps(report["records"]))

    def test_seed_instability_blocks_stability_signal(self):
        plan = self.plan()

        def inspect(_b, _r, item, _p):
            suffix = "different" if item["caseId"] == experiment.PILOT_CASES[0] and item["seed"] == 2 else "same"
            return valid_record(item, suffix)

        with patch.object(experiment, "inspect_run", side_effect=inspect):
            report = experiment.aggregate_report(Path("."), plan, Path("runs"))
        first_case = report["summary"]["byCase"][0]
        self.assertFalse(first_case["stableAcrossSeeds"])
        self.assertFalse(report["summary"]["stableAcrossSeeds"])
        self.assertFalse(report["pilotSignals"]["resultsStableAcrossDeclaredSeeds"])

    def test_safety_failure_blocks_all_safety_signal(self):
        plan = self.plan()
        first = plan["matrix"][0]["runId"]

        def inspect(_b, _r, item, _p):
            record, detail = valid_record(item)
            if item["runId"] == first:
                record["falseSupportedCount"] = 1
            return record, detail

        with patch.object(experiment, "inspect_run", side_effect=inspect):
            report = experiment.aggregate_report(Path("."), plan, Path("runs"))
        self.assertTrue(report["summary"]["complete"])
        self.assertFalse(report["summary"]["falseSupportedSafe"])
        self.assertFalse(report["pilotSignals"]["allSafetyChecksPass"])
        self.assertFalse(report["pilotSignals"]["automaticPromotionAllowed"])


if __name__ == "__main__":
    unittest.main()
