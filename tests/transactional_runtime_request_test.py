#!/usr/bin/env python3
"""SWI-Prolog process check for the transactional runtime request launcher."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class VerificationError(AssertionError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise VerificationError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def invoke(
    repository: Path,
    deployment: Path,
    swipl: str,
    command: str,
    options: dict,
) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repository / "tools")
    completed = subprocess.run(
        [
            sys.executable,
            str(repository / "tools" / "run_transactional_runtime.py"),
            "--repository-root",
            str(repository),
            "--deployment-root",
            str(deployment),
            "--swipl",
            swipl,
            "request",
            "--command",
            command,
            "--request-id",
            f"eng-111-{command}",
            "--options-json",
            json.dumps(options, ensure_ascii=False),
        ],
        cwd=repository,
        env=env,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise VerificationError(
            f"launcher failed: stdout={completed.stdout!r}; stderr={completed.stderr!r}"
        )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise VerificationError("launcher output is not one JSON object")
    return value


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    swipl = shutil.which("swipl")
    if swipl is None:
        raise VerificationError("SWI-Prolog is required")
    support = load_module(
        "transactional_runtime_selection_support",
        repository / "tests" / "transactional_runtime_selection_test.py",
    )

    with tempfile.TemporaryDirectory(prefix="logiclens-selected-request-") as tmp:
        deployment, _, target = support.create_committed_deployment(
            repository,
            Path(tmp),
        )
        health = invoke(repository, deployment, swipl, "health", {})
        selection = health.get("selection") or {}
        response = health.get("response") or {}
        if (
            selection.get("generation") != 1
            or selection.get("revision") != 1
            or selection.get("packageHash") != target.get("packageHash")
        ):
            raise VerificationError("health did not use the selected revision 0.1")
        if (
            response.get("status") != "ok"
            or response.get("epoch") != 0
            or response.get("revision") != 1
        ):
            raise VerificationError(f"selected health response differs: {response}")

        derived = invoke(
            repository,
            deployment,
            swipl,
            "derived-query",
            {"predicate": "urn:logiclens:derived:researcher-at-iis"},
        )
        rows = list(((derived.get("response") or {}).get("result") or {}).get("rows") or [])
        if len(rows) != 1 or rows[0].get("entityId") != "urn:logiclens:person:alex":
            raise VerificationError(f"selected derived query differs: {rows}")
        evidence = list(rows[0].get("evidenceFactIds") or [])
        if evidence != ["f:organization", "f:participant", "f:role"]:
            raise VerificationError(f"selected evidence differs: {evidence}")

    print("Transactional runtime request tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
