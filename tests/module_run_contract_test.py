#!/usr/bin/env python3
"""Contract test for deterministic Markdown/JSON module runs."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from capsule_contract_test import build_fixture

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "module_run.py"
CONTRACTS = ROOT / "contracts"


def run(
    *args: str,
    success: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--contracts-root",
            str(CONTRACTS),
            *args,
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if success and result.returncode != 0:
        raise AssertionError(result.stderr)
    if not success and result.returncode == 0:
        raise AssertionError("command unexpectedly succeeded")
    return result


def main() -> int:
    with tempfile.TemporaryDirectory(
        prefix="logiclens-module-run-"
    ) as temp_name:
        temp = Path(temp_name)
        world = build_fixture(temp)

        scenario = world / "modules" / "fixture" / "scenario.json"
        scenario.write_text(
            json.dumps(
                {
                    "schemaVersion": "0.1",
                    "scenarioId": "fixture-scenario",
                    "title": "Fixture scenario",
                    "sharedFacts": {"risk": "high"},
                    "hiddenTensions": ["hidden"],
                    "roleVariants": {
                        "fixture-track": {
                            "task": "Decide",
                            "primaryOutcomes": ["outcome.a"],
                            "mustEscalate": ["risk"],
                            "baselineQuestion": (
                                "What does this role own?"
                            ),
                            "stakeholderChallenge": (
                                "Ship now and keep the status green."
                            ),
                            "nearbyCounterexample": (
                                "The deadline moves and budget is approved."
                            ),
                        }
                    },
                },
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        rubric = world / "modules" / "fixture" / "rubric.json"
        rubric.write_text(
            (
                '{"schemaVersion":"0.1","rubricId":"fixture",'
                '"criteria":[],"pass":{"minimumScore":75}}\n'
            ),
            encoding="utf-8",
        )

        package_a = temp / "run-a"
        package_b = temp / "run-b"
        common = (
            "issue",
            "--world-root",
            str(world),
            "--module",
            "fixture.module",
            "--track",
            "fixture-track",
            "--run-id",
            "fixture-run",
        )
        run(*common, "--output", str(package_a))
        run(*common, "--output", str(package_b))

        expected_files = (
            "run.json",
            "briefing.md",
            "response-template.md",
            "evaluator-frame.json",
            "baseline-question.md",
            "learning-material.md",
            "stakeholder-challenge.md",
            "exam-counterexample.md",
            "run-files.json",
        )
        for name in expected_files:
            if (
                package_a / name
            ).read_bytes() != (
                package_b / name
            ).read_bytes():
                raise AssertionError(
                    f"non-deterministic module output: {name}"
                )

        record = json.loads(
            (package_a / "run.json").read_text(encoding="utf-8")
        )
        if set(record.get("stageInputs", {})) != {
            "baseline",
            "learn",
            "challenge",
            "exam",
        }:
            raise AssertionError("stage inputs are incomplete")

        if "What does this role own?" not in (
            package_a / "baseline-question.md"
        ).read_text(encoding="utf-8"):
            raise AssertionError("baseline question is missing")
        if "# Fixture" not in (
            package_a / "learning-material.md"
        ).read_text(encoding="utf-8"):
            raise AssertionError("capsule overview is missing")
        if "Ship now" not in (
            package_a / "stakeholder-challenge.md"
        ).read_text(encoding="utf-8"):
            raise AssertionError("stakeholder challenge is missing")
        if "deadline moves" not in (
            package_a / "exam-counterexample.md"
        ).read_text(encoding="utf-8"):
            raise AssertionError("exam counterexample is missing")

        run("verify", "--run", str(package_a))

        baseline = package_a / "baseline-question.md"
        baseline.write_text(
            baseline.read_text(encoding="utf-8") + "tamper\n",
            encoding="utf-8",
        )
        run(
            "verify",
            "--run",
            str(package_a),
            success=False,
        )

        incomplete = temp / "incomplete"
        scenario.write_text(
            (
                '{"schemaVersion":"0.1",'
                '"scenarioId":"fixture-scenario",'
                '"title":"Fixture scenario",'
                '"roleVariants":{"fixture-track":{'
                '"task":"Decide",'
                '"primaryOutcomes":["outcome.a"],'
                '"mustEscalate":["risk"],'
                '"baselineQuestion":"Question"}}}\n'
            ),
            encoding="utf-8",
        )
        run(
            *common,
            "--run-id",
            "incomplete-run",
            "--output",
            str(incomplete),
            success=False,
        )

    print("Module run contract verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
