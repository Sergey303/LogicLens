#!/usr/bin/env python3
"""Run one real Qwen Builder attempt against a frozen LogicLens workspace."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_CONTEXT_TOKENS = 16_384
MIN_CONTEXT_TOKENS = 4_096
MAX_CONTEXT_TOKENS = 32_768
DEFAULT_OUTPUT_TOKENS = 2_048
MIN_OUTPUT_TOKENS = 256
MAX_OUTPUT_TOKENS = 8_192


class QwenOnlyRunError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--qwen-model", default="qwen2.5-coder:7b")
    parser.add_argument("--qwen-timeout-seconds", type=float, default=300.0)
    parser.add_argument(
        "--context-tokens",
        type=int,
        default=DEFAULT_CONTEXT_TOKENS,
        help="Ollama context window passed to the Qwen Builder adapter",
    )
    parser.add_argument(
        "--output-tokens",
        type=int,
        default=DEFAULT_OUTPUT_TOKENS,
        help="Ollama structured-response budget passed to the Qwen Builder adapter",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.qwen_model or len(args.qwen_model) > 256:
        raise QwenOnlyRunError(
            "qwen-model must be a non-empty string up to 256 characters"
        )
    if args.qwen_timeout_seconds <= 0 or args.qwen_timeout_seconds > 1800:
        raise QwenOnlyRunError(
            "qwen-timeout-seconds must be between 0 and 1800"
        )
    validate_context_tokens(args.context_tokens)
    validate_output_tokens(args.output_tokens)

    repository = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    task = repository / "experiments" / "builder" / "eng-26-researcher-at-iis"
    baseline = output / "active-epoch"
    workspace = output / "workspace"
    provider = output / "qwen-provider"
    run_output = output / "qwen-run-001"
    summary_path = output / "qwen-only-summary.json"

    if repository == output or output in repository.parents:
        raise QwenOnlyRunError("output must not contain the repository")

    require_clean_output(output)
    commit = capture(["git", "rev-parse", "HEAD"], repository).strip()
    run_required(
        [
            sys.executable,
            str(repository / "tools" / "build_active_epoch.py"),
            "--repository-root",
            str(repository),
            "--output",
            str(baseline),
            "--engine-commit",
            commit,
        ],
        repository,
    )
    run_required(
        [
            sys.executable,
            str(repository / "tools" / "builder_experiment.py"),
            "prepare",
            "--baseline",
            str(baseline),
            "--task",
            str(task),
            "--task-schema",
            str(repository / "contracts" / "builder-task-v0.schema.json"),
            "--candidate-schema",
            str(repository / "contracts" / "epoch-candidate-v0.schema.json"),
            "--output",
            str(workspace),
        ],
        repository,
    )

    status = run_qwen(
        repository=repository,
        baseline=baseline,
        task=task,
        workspace=workspace,
        provider=provider,
        run_output=run_output,
        model=args.qwen_model,
        timeout_seconds=args.qwen_timeout_seconds,
        context_tokens=args.context_tokens,
        output_tokens=args.output_tokens,
    )
    summary = {
        "schemaVersion": "0.1",
        "result": status,
        "provider": {
            "runId": "qwen-run-001",
            "kind": "ollama",
            "model": args.qwen_model,
            "contextTokens": args.context_tokens,
            "outputTokens": args.output_tokens,
            "status": status,
        },
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"Qwen-only Builder result: {status}")
    print(f"Context tokens: {args.context_tokens}")
    print(f"Output tokens: {args.output_tokens}")
    print(f"Summary: {summary_path}")
    return 1 if status == "infrastructure-failed" else 0


def run_qwen(
    repository: Path,
    baseline: Path,
    task: Path,
    workspace: Path,
    provider: Path,
    run_output: Path,
    model: str,
    timeout_seconds: float,
    context_tokens: int,
    output_tokens: int,
) -> str:
    adapter_exit = run_optional(
        [
            sys.executable,
            str(repository / "tools" / "run_builder_ollama.py"),
            "--workspace",
            str(workspace),
            "--output",
            str(provider),
            "--run-id",
            "qwen-run-001",
            "--model",
            model,
            "--timeout-seconds",
            str(timeout_seconds),
            "--context-tokens",
            str(context_tokens),
            "--output-tokens",
            str(output_tokens),
        ],
        repository,
    )
    raw_output = provider / "raw" / "provider-output.json"
    if adapter_exit != 0:
        adapter_status = read_adapter_failure_status(provider)
        if adapter_status in {"context-limited", "output-limited"}:
            print(
                "qwen-run-001: provider response was preserved but the request "
                f"was classified as {adapter_status}"
            )
            return "infrastructure-failed"
        if raw_output.is_file():
            print("qwen-run-001: provider response was preserved and rejected")
            return "rejected"
        print("qwen-run-001: provider stage failed before a response was preserved")
        return "infrastructure-failed"

    import_exit = run_optional(
        [
            sys.executable,
            str(repository / "tools" / "builder_experiment.py"),
            "import-run",
            "--baseline",
            str(baseline),
            "--task",
            str(task),
            "--task-schema",
            str(repository / "contracts" / "builder-task-v0.schema.json"),
            "--candidate-schema",
            str(repository / "contracts" / "epoch-candidate-v0.schema.json"),
            "--run-schema",
            str(repository / "contracts" / "builder-run-v0.schema.json"),
            "--workspace",
            str(workspace),
            "--proposal",
            str(provider / "proposal"),
            "--raw-output",
            str(raw_output),
            "--output",
            str(run_output),
            "--run-id",
            "qwen-run-001",
        ],
        repository,
    )
    if import_exit == 0:
        return "passed"
    if raw_output.is_file():
        print("qwen-run-001: candidate was rejected by trusted validation or oracle")
        return "rejected"
    return "infrastructure-failed"


def read_adapter_failure_status(provider: Path) -> str | None:
    path = provider / "raw" / "adapter-result.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QwenOnlyRunError(f"cannot read adapter result {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise QwenOnlyRunError(f"adapter result must be a JSON object: {path}")
    status = value.get("status")
    if not isinstance(status, str) or not status:
        raise QwenOnlyRunError(f"adapter result has no status: {path}")
    return status


def validate_context_tokens(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise QwenOnlyRunError("context-tokens must be an integer")
    if value < MIN_CONTEXT_TOKENS or value > MAX_CONTEXT_TOKENS:
        raise QwenOnlyRunError(
            f"context-tokens must be between {MIN_CONTEXT_TOKENS} and "
            f"{MAX_CONTEXT_TOKENS}"
        )


def validate_output_tokens(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise QwenOnlyRunError("output-tokens must be an integer")
    if value < MIN_OUTPUT_TOKENS or value > MAX_OUTPUT_TOKENS:
        raise QwenOnlyRunError(
            f"output-tokens must be between {MIN_OUTPUT_TOKENS} and "
            f"{MAX_OUTPUT_TOKENS}"
        )


def require_clean_output(path: Path) -> None:
    if path.exists():
        if not path.is_dir() or any(path.iterdir()):
            raise QwenOnlyRunError(f"output directory must be empty: {path}")
    else:
        path.mkdir(parents=True)


def run_required(command: list[str], cwd: Path) -> None:
    if run_optional(command, cwd) != 0:
        raise QwenOnlyRunError(
            "required stage failed; existing artifacts were preserved"
        )


def run_optional(command: list[str], cwd: Path) -> int:
    print("+ " + " ".join(command))
    completed = subprocess.run(command, cwd=cwd, check=False)
    return completed.returncode


def capture(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise QwenOnlyRunError(
            f"command failed with exit {completed.returncode}: {completed.stderr[-1000:]}"
        )
    return completed.stdout


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (QwenOnlyRunError, OSError, subprocess.SubprocessError) as exc:
        print(f"Qwen-only Builder failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
