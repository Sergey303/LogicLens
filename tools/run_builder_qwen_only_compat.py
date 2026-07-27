#!/usr/bin/env python3
"""Run Qwen-only Builder with diagnostic Ollama and UTF-8 validator transport."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import run_builder_qwen_only as base


_ORIGINAL_RUN_OPTIONAL = base.run_optional
REJECTED_EXIT = 2


def run_optional_with_compat(command: list[str], cwd: Path) -> int:
    updated = list(command)
    replacements = {
        "run_builder_ollama.py": "run_builder_ollama_compat.py",
        "builder_experiment.py": "builder_experiment_utf8_compat.py",
    }
    for index, argument in enumerate(updated):
        replacement = replacements.get(Path(argument).name)
        if replacement is not None:
            updated[index] = str(cwd / "tools" / replacement)
    return _ORIGINAL_RUN_OPTIONAL(updated, cwd)


def classify_import_exit(returncode: int) -> str:
    if returncode == 0:
        return "passed"
    if returncode == REJECTED_EXIT:
        return "rejected"
    return "infrastructure-failed"


def run_qwen_with_compat(
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
    adapter_exit = run_optional_with_compat(
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
        adapter_status = base.read_adapter_failure_status(provider)
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

    import_exit = run_optional_with_compat(
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
    status = classify_import_exit(import_exit)
    if status == "passed":
        return status
    if status == "rejected":
        print("qwen-run-001: candidate was rejected by trusted validation or oracle")
        return status
    print("qwen-run-001: trusted import failed before a model verdict")
    return status


def main() -> int:
    base.run_optional = run_optional_with_compat
    base.run_qwen = run_qwen_with_compat
    return base.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        base.QwenOnlyRunError,
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as exc:
        print(f"Qwen-only compatibility run failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
