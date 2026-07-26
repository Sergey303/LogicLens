#!/usr/bin/env python3
"""Offline verification for the Codex CLI Builder adapter."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


class VerificationError(AssertionError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--task-schema", required=True, type=Path)
    parser.add_argument("--candidate-schema", required=True, type=Path)
    parser.add_argument("--run-schema", required=True, type=Path)
    parser.add_argument("--response", required=True, type=Path)
    return parser.parse_args()


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *command],
        cwd=root(),
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )


def success(completed: subprocess.CompletedProcess[str]) -> None:
    if completed.returncode != 0:
        raise VerificationError(
            f"command failed: stdout={completed.stdout!r}, stderr={completed.stderr!r}"
        )


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"expected JSON object: {path}")
    return value


def main() -> int:
    args = parse_args()
    for name in (
        "baseline",
        "task",
        "task_schema",
        "candidate_schema",
        "run_schema",
        "response",
    ):
        setattr(args, name, getattr(args, name).resolve())

    with tempfile.TemporaryDirectory(prefix="logiclens-codex-adapter-") as temporary:
        temporary_root = Path(temporary)
        workspace = temporary_root / "workspace"
        success(
            run(
                [
                    str(root() / "tools" / "builder_experiment.py"),
                    "prepare",
                    "--baseline",
                    str(args.baseline),
                    "--task",
                    str(args.task),
                    "--task-schema",
                    str(args.task_schema),
                    "--candidate-schema",
                    str(args.candidate_schema),
                    "--output",
                    str(workspace),
                ]
            )
        )
        workspace_before = {
            path.relative_to(workspace).as_posix(): path.read_bytes()
            for path in workspace.rglob("*")
            if path.is_file()
        }

        adapter_output = temporary_root / "codex"
        success(
            run(
                [
                    str(root() / "tools" / "run_builder_codex.py"),
                    "--workspace",
                    str(workspace),
                    "--output",
                    str(adapter_output),
                    "--run-id",
                    "offline-codex",
                    "--model",
                    "gpt-test-codex",
                    "--response-file",
                    str(args.response),
                    "--elapsed-ms",
                    "987.6",
                ]
            )
        )
        proposal = read_json(adapter_output / "proposal" / "proposal.json")
        if proposal["provider"] != {
            "kind": "codex",
            "name": "codex-cli",
            "model": "gpt-test-codex",
            "runId": "offline-codex",
        }:
            raise VerificationError("adapter proposal provider metadata is incorrect")
        if proposal["metrics"] != {
            "cliCalls": 0,
            "manualFixes": 0,
            "elapsedMs": 987.6,
        }:
            raise VerificationError("adapter proposal metrics are incorrect")
        request_text = (adapter_output / "raw" / "request.json").read_text(
            encoding="utf-8"
        )
        if "oracle.json" in request_text:
            raise VerificationError("trusted oracle leaked into Codex request")
        workspace_after = {
            path.relative_to(workspace).as_posix(): path.read_bytes()
            for path in workspace.rglob("*")
            if path.is_file()
        }
        if workspace_after != workspace_before:
            raise VerificationError("Codex adapter changed the frozen workspace")

        run_output = temporary_root / "run"
        success(
            run(
                [
                    str(root() / "tools" / "builder_experiment.py"),
                    "import-run",
                    "--baseline",
                    str(args.baseline),
                    "--task",
                    str(args.task),
                    "--task-schema",
                    str(args.task_schema),
                    "--candidate-schema",
                    str(args.candidate_schema),
                    "--run-schema",
                    str(args.run_schema),
                    "--workspace",
                    str(workspace),
                    "--proposal",
                    str(adapter_output / "proposal"),
                    "--raw-output",
                    str(adapter_output / "raw" / "provider-output.json"),
                    "--output",
                    str(run_output),
                    "--run-id",
                    "offline-codex",
                ]
            )
        )
        envelope = read_json(run_output / "run.json")
        if envelope["provider"]["kind"] != "codex":
            raise VerificationError("trusted import lost Codex provider kind")
        if envelope["metrics"]["costUsd"] is not None:
            raise VerificationError("unknown Codex cost was not retained as null")
        if envelope["validation"] != {"candidate": "passed", "oracle": "passed"}:
            raise VerificationError("offline Codex run did not pass both validations")

    print("ok 1 - offline Codex response to trusted run")
    print("ok 2 - oracle excluded and frozen workspace unchanged")
    print("ok 3 - unknown Codex cost retained as null")
    print("1..3")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        VerificationError,
        OSError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
