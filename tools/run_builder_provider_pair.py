#!/usr/bin/env python3
"""Run the real Qwen/Codex Builder pair against one frozen workspace."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


class PairRunError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--codex-model", required=True)
    parser.add_argument("--qwen-model", default="qwen2.5-coder:7b")
    parser.add_argument("--codex-timeout-seconds", type=float, default=900.0)
    parser.add_argument("--qwen-timeout-seconds", type=float, default=300.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repository = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            raise PairRunError(f"output directory must be empty: {output}")
    else:
        output.mkdir(parents=True)
    if repository == output or output in repository.parents:
        raise PairRunError("output must not contain the repository")

    task = repository / "experiments" / "builder" / "eng-26-researcher-at-iis"
    baseline = output / "active-epoch"
    workspace = output / "workspace"
    qwen_provider = output / "qwen-provider"
    codex_provider = output / "codex-provider"
    qwen_run = output / "qwen-run-001"
    codex_run = output / "codex-run-001"
    comparison = output / "provider-comparison.json"

    commit = capture(["git", "rev-parse", "HEAD"], repository).strip()
    run(
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
    run(
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
    run(
        [
            sys.executable,
            str(repository / "tools" / "run_builder_ollama.py"),
            "--workspace",
            str(workspace),
            "--output",
            str(qwen_provider),
            "--run-id",
            "qwen-run-001",
            "--model",
            args.qwen_model,
            "--timeout-seconds",
            str(args.qwen_timeout_seconds),
        ],
        repository,
    )
    run(
        [
            sys.executable,
            str(repository / "tools" / "run_builder_codex.py"),
            "--workspace",
            str(workspace),
            "--output",
            str(codex_provider),
            "--run-id",
            "codex-run-001",
            "--model",
            args.codex_model,
            "--timeout-seconds",
            str(args.codex_timeout_seconds),
        ],
        repository,
    )
    import_run(repository, baseline, task, workspace, qwen_provider, qwen_run, "qwen-run-001")
    import_run(
        repository,
        baseline,
        task,
        workspace,
        codex_provider,
        codex_run,
        "codex-run-001",
    )
    run(
        [
            sys.executable,
            str(repository / "tools" / "builder_experiment.py"),
            "compare",
            "--run-schema",
            str(repository / "contracts" / "builder-run-v0.schema.json"),
            "--run",
            str(qwen_run),
            "--run",
            str(codex_run),
            "--output",
            str(comparison),
        ],
        repository,
    )
    print(f"Builder provider pair completed: {output}")
    print(f"Comparison: {comparison}")
    return 0


def import_run(
    repository: Path,
    baseline: Path,
    task: Path,
    workspace: Path,
    provider: Path,
    output: Path,
    run_id: str,
) -> None:
    run(
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
            str(provider / "raw" / "provider-output.json"),
            "--output",
            str(output),
            "--run-id",
            run_id,
        ],
        repository,
    )


def run(command: list[str], cwd: Path) -> None:
    print("+ " + " ".join(command))
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise PairRunError(
            f"stage failed with exit {completed.returncode}; existing artifacts were preserved"
        )


def capture(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise PairRunError(
            f"command failed with exit {completed.returncode}: {completed.stderr[-1000:]}"
        )
    return completed.stdout


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PairRunError, OSError, subprocess.SubprocessError) as exc:
        print(f"Builder provider pair failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
