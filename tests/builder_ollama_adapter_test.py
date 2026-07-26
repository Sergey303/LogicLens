#!/usr/bin/env python3
"""Offline verification for the loopback-only Ollama Builder adapter."""

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


def failure(completed: subprocess.CompletedProcess[str], text: str) -> None:
    if completed.returncode == 0:
        raise VerificationError("command unexpectedly succeeded")
    combined = completed.stdout + completed.stderr
    if text not in combined:
        raise VerificationError(f"failure did not contain {text!r}: {combined!r}")


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

    with tempfile.TemporaryDirectory(prefix="logiclens-ollama-adapter-") as temporary:
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

        adapter_output = temporary_root / "ollama"
        success(
            run(
                [
                    str(root() / "tools" / "run_builder_ollama.py"),
                    "--workspace",
                    str(workspace),
                    "--output",
                    str(adapter_output),
                    "--run-id",
                    "offline-qwen",
                    "--model",
                    "qwen2.5-coder:7b",
                    "--response-file",
                    str(args.response),
                    "--elapsed-ms",
                    "1234.5",
                ]
            )
        )
        proposal = read_json(adapter_output / "proposal" / "proposal.json")
        if proposal["provider"] != {
            "kind": "ollama",
            "name": "ollama",
            "model": "qwen2.5-coder:7b",
            "runId": "offline-qwen",
        }:
            raise VerificationError("adapter proposal provider metadata is incorrect")
        if proposal["metrics"] != {
            "cliCalls": 0,
            "manualFixes": 0,
            "elapsedMs": 1234.5,
            "costUsd": 0,
        }:
            raise VerificationError("adapter proposal metrics are incorrect")
        request_text = (adapter_output / "raw" / "request.json").read_text(
            encoding="utf-8"
        )
        if "oracle" in request_text.lower():
            raise VerificationError("trusted oracle leaked into Ollama request")
        if "127.0.0.1" in request_text or "localhost" in request_text:
            raise VerificationError("machine endpoint leaked into retained request")

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
                    "offline-qwen",
                ]
            )
        )
        envelope = read_json(run_output / "run.json")
        if envelope["provider"]["kind"] != "ollama":
            raise VerificationError("trusted import lost Ollama provider kind")
        if envelope["validation"] != {"candidate": "passed", "oracle": "passed"}:
            raise VerificationError("offline Ollama run did not pass both validations")

        invalid_response = read_json(args.response)
        invalid_message = invalid_response.get("message")
        if not isinstance(invalid_message, dict):
            raise VerificationError("fixture response is missing message")
        invalid_content = json.loads(invalid_message.get("content", ""))
        if not isinstance(invalid_content, dict):
            raise VerificationError("fixture message content must be a JSON object")
        invalid_content["files"] = {"unexpected.txt": "invalid candidate"}
        invalid_message["content"] = json.dumps(invalid_content, ensure_ascii=False)
        invalid_response_path = temporary_root / "invalid-response.json"
        invalid_response_path.write_text(
            json.dumps(invalid_response, ensure_ascii=False),
            encoding="utf-8",
        )
        invalid_output = temporary_root / "invalid-output"
        invalid_run = run(
            [
                str(root() / "tools" / "run_builder_ollama.py"),
                "--workspace",
                str(workspace),
                "--output",
                str(invalid_output),
                "--run-id",
                "invalid-files",
                "--response-file",
                str(invalid_response_path),
            ]
        )
        failure(invalid_run, "expected=")
        failure(invalid_run, "actual=")
        retained_output = invalid_output / "raw" / "provider-output.json"
        if retained_output.read_bytes() != invalid_response_path.read_bytes():
            raise VerificationError("invalid provider response was not retained verbatim")

        bad_endpoint = run(
            [
                str(root() / "tools" / "run_builder_ollama.py"),
                "--workspace",
                str(workspace),
                "--output",
                str(temporary_root / "bad-endpoint"),
                "--run-id",
                "bad-endpoint",
                "--endpoint",
                "https://example.com/api/chat",
            ]
        )
        failure(bad_endpoint, "loopback")

    print("ok 1 - offline Ollama response to trusted run")
    print("ok 2 - oracle excluded from provider request")
    print("ok 3 - invalid response retained with path diagnostics")
    print("ok 4 - non-loopback endpoint rejected")
    print("1..4")
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
