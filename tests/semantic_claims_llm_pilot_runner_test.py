#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

TEST_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = TEST_ROOT / "tools" / "run_semantic_claims_llm_pilot.py"


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

    contract = types.ModuleType("semantic_claims_llm_contract")
    contract.DEFAULT_ENDPOINT = "http://127.0.0.1:11434/api/chat"
    contract.SemanticClaimsLlmError = type("SemanticClaimsLlmError", (RuntimeError,), {})
    contract.validate_endpoint = lambda value: None
    sys.modules["semantic_claims_llm_contract"] = contract

    experiment = types.ModuleType("semantic_claims_llm_experiment")
    experiment.SemanticClaimsExperimentError = type("SemanticClaimsExperimentError", (RuntimeError,), {})
    experiment.verify_plan = lambda *_args, **_kwargs: None
    experiment.aggregate_report = lambda *_args, **_kwargs: None

    def write_new(path, value, _label):
        path = Path(path)
        if path.exists():
            raise experiment.SemanticClaimsExperimentError("exists")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_json_bytes(value))

    experiment.write_new = write_new
    sys.modules["semantic_claims_llm_experiment"] = experiment


install_stubs()
spec = importlib.util.spec_from_file_location("run_semantic_claims_llm_pilot", MODULE_PATH)
assert spec and spec.loader
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


def plan_value():
    return {
        "producer": {
            "model": "qwen:test",
            "numCtx": 2048,
            "numPredict": 1024,
        },
        "matrix": [
            {"runId": "case--seed-0", "caseId": "case", "seed": 0},
            {"runId": "case--seed-1", "caseId": "case", "seed": 1},
        ],
    }


def report_for(root: Path, plan: dict):
    records = []
    valid = 0
    for item in plan["matrix"]:
        directory = root / item["runId"]
        status = "valid" if (directory / "candidate.json").exists() else "incomplete"
        valid += status == "valid"
        records.append({"runId": item["runId"], "status": status})
    return {
        "summary": {
            "plannedRuns": len(plan["matrix"]),
            "validRuns": valid,
            "complete": valid == len(plan["matrix"]),
        },
        "records": records,
    }


class PilotRunnerTests(unittest.TestCase):
    def test_command_is_shell_free_and_plan_bound(self):
        item = plan_value()["matrix"][0]
        command = runner.build_command(
            Path("tool.py"), item, plan_value(),
            "http://127.0.0.1:11434/api/chat", 600.0, Path("out")
        )
        self.assertEqual(sys.executable, command[0])
        self.assertIn("--case-id", command)
        self.assertIn("case", command)
        self.assertIn("--seed", command)
        self.assertIn("0", command)
        self.assertNotIn("shell=True", command)

    def test_failed_attempt_becomes_final_incomplete_and_is_not_retried(self):
        plan = plan_value()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tool = root / "semantic_claims_llm.py"
            tool.write_text("# stub\n", encoding="utf-8")
            runs = root / "runs"
            report = root / "report.json"
            completed = subprocess.CompletedProcess(["python"], 1, "stdout", "stderr")
            with patch.object(runner, "verify_plan", return_value=plan), \
                 patch.object(runner, "aggregate_report", side_effect=lambda _b, p, r: report_for(r, p)), \
                 patch.object(runner.subprocess, "run", return_value=completed) as call:
                value = runner.execute_plan(Path("."), root / "plan.json", runs, report, tool_path=tool)
                self.assertEqual(2, call.call_count)
                self.assertFalse(value["summary"]["complete"])
                for item in plan["matrix"]:
                    final = runs / item["runId"]
                    self.assertTrue(final.is_dir())
                    record = json.loads((final / "execution.json").read_text(encoding="utf-8"))
                    self.assertEqual("runner-failed", record["outcome"])
                    self.assertEqual(1, record["returnCode"])

            second_report = root / "report-2.json"
            with patch.object(runner, "verify_plan", return_value=plan), \
                 patch.object(runner, "aggregate_report", side_effect=lambda _b, p, r: report_for(r, p)), \
                 patch.object(runner.subprocess, "run") as call:
                runner.execute_plan(Path("."), root / "plan.json", runs, second_report, tool_path=tool)
                call.assert_not_called()

    def test_interrupted_staging_is_finalized_without_retry(self):
        plan = plan_value()
        plan["matrix"] = plan["matrix"][:1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tool = root / "semantic_claims_llm.py"
            tool.write_text("# stub\n", encoding="utf-8")
            runs = root / "runs"
            staging = runs / ".case--seed-0.in-progress"
            staging.mkdir(parents=True)
            (staging / "request.json").write_text("{}\n", encoding="utf-8")
            report = root / "report.json"
            with patch.object(runner, "verify_plan", return_value=plan), \
                 patch.object(runner, "aggregate_report", side_effect=lambda _b, p, r: report_for(r, p)), \
                 patch.object(runner.subprocess, "run") as call:
                runner.execute_plan(Path("."), root / "plan.json", runs, report, tool_path=tool)
                call.assert_not_called()
            final = runs / "case--seed-0"
            self.assertTrue(final.is_dir())
            record = json.loads((final / "execution.json").read_text(encoding="utf-8"))
            self.assertEqual("interrupted-before-finalization", record["outcome"])

    def test_existing_report_blocks_execution_before_any_run(self):
        plan = plan_value()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tool = root / "semantic_claims_llm.py"
            tool.write_text("# stub\n", encoding="utf-8")
            report = root / "report.json"
            report.write_text("{}\n", encoding="utf-8")
            with patch.object(runner, "verify_plan", return_value=plan), \
                 patch.object(runner.subprocess, "run") as call:
                with self.assertRaises(runner.SemanticClaimsPilotRunnerError):
                    runner.execute_plan(Path("."), root / "plan.json", root / "runs", report, tool_path=tool)
                call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
