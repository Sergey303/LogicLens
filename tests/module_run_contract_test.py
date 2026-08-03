#!/usr/bin/env python3
"""Contract test for deterministic Markdown/JSON module runs."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from capsule_contract_test import build_fixture

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "module_run.py"
CONTRACTS = ROOT / "contracts"


def run(*args: str, success: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--contracts-root", str(CONTRACTS), *args],
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
    with tempfile.TemporaryDirectory(prefix="logiclens-module-run-") as temp_name:
        temp = Path(temp_name)
        world = build_fixture(temp)
        # The generic fixture scenario has no roleVariants; make it a valid issued module.
        scenario = world / "modules" / "fixture" / "scenario.json"
        scenario.write_text(
            '{"schemaVersion":"0.1","scenarioId":"fixture-scenario",'
            '"title":"Fixture scenario","sharedFacts":{"risk":"high"},'
            '"hiddenTensions":["hidden"],"roleVariants":{'
            '"fixture-track":{"task":"Decide","primaryOutcomes":["outcome.a"],'
            '"mustEscalate":["risk"]}}}\n',
            encoding="utf-8",
        )
        rubric = world / "modules" / "fixture" / "rubric.json"
        rubric.write_text(
            '{"schemaVersion":"0.1","rubricId":"fixture",'
            '"criteria":[],"pass":{"minimumScore":75}}\n',
            encoding="utf-8",
        )
        package_a = temp / "run-a"
        package_b = temp / "run-b"
        common = (
            "issue", "--world-root", str(world), "--module", "fixture.module",
            "--track", "fixture-track", "--run-id", "fixture-run",
        )
        run(*common, "--output", str(package_a))
        run(*common, "--output", str(package_b))
        for name in ("run.json", "briefing.md", "response-template.md", "evaluator-frame.json", "run-files.json"):
            if (package_a / name).read_bytes() != (package_b / name).read_bytes():
                raise AssertionError(f"non-deterministic module output: {name}")
        run("verify", "--run", str(package_a))
        briefing = package_a / "briefing.md"
        briefing.write_text(briefing.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
        run("verify", "--run", str(package_a), success=False)
    print("Module run contract verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
