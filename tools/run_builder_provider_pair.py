#!/usr/bin/env python3
"""Run the real Qwen/Codex Builder pair against one frozen workspace."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class PairRunError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--codex-model", required=True)
    parser.add_argument("--qwen-model", default="qwen2.5-coder:7b")
    parser.add_argument("--codex-timeout-seconds", type=float, default=900.0)
    parser.add_argument("--qwen-timeout-seconds", type=float, default=300.0)
    parser.add_argument(
        "--resume-after-qwen-rejection",
        action="store_true",
        help=(
            "reuse an existing baseline/workspace and preserved rejected Qwen "
            "response, then run Codex without invoking Qwen again"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repository = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    task = repository / "experiments" / "builder" / "eng-26-researcher-at-iis"
    baseline = output / "active-epoch"
    workspace = output / "workspace"
    qwen_provider = output / "qwen-provider"
    codex_provider = output / "codex-provider"
    qwen_run = output / "qwen-run-001"
    codex_run = output / "codex-run-001"
    comparison = output / "provider-comparison.json"
    summary_path = output / "provider-pair-summary.json"

    if repository == output or output in repository.parents:
        raise PairRunError("output must not contain the repository")

    if args.resume_after_qwen_rejection:
        validate_resume_state(
            output,
            baseline,
            workspace,
            qwen_provider,
            codex_provider,
            qwen_run,
            codex_run,
            comparison,
            summary_path,
        )
        qwen_status = "rejected"
    else:
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
        qwen_status = run_provider(
            repository,
            baseline,
            task,
            workspace,
            qwen_provider,
            qwen_run,
            "qwen-run-001",
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
        )

    codex_status = run_provider(
        repository,
        baseline,
        task,
        workspace,
        codex_provider,
        codex_run,
        "codex-run-001",
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
    )

    comparison_status = "not-written"
    if qwen_status == "passed" and codex_status == "passed":
        run_required(
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
        comparison_status = "written"

    result = pair_result(qwen_status, codex_status)
    summary = {
        "schemaVersion": "0.1",
        "result": result,
        "providers": [
            {
                "runId": "qwen-run-001",
                "kind": "ollama",
                "model": args.qwen_model,
                "status": qwen_status,
            },
            {
                "runId": "codex-run-001",
                "kind": "codex",
                "model": args.codex_model,
                "status": codex_status,
            },
        ],
        "comparison": comparison_status,
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"Builder provider pair result: {result}")
    print(f"Qwen: {qwen_status}")
    print(f"Codex: {codex_status}")
    print(f"Comparison: {comparison_status}")
    print(f"Summary: {summary_path}")
    return 1 if result == "infrastructure-failed" else 0


def run_provider(
    repository: Path,
    baseline: Path,
    task: Path,
    workspace: Path,
    provider: Path,
    output: Path,
    run_id: str,
    adapter_command: list[str],
) -> str:
    adapter_exit = run_optional(adapter_command, repository)
    raw_output = provider / "raw" / "provider-output.json"
    if adapter_exit != 0:
        if raw_output.is_file():
            print(f"{run_id}: provider response was preserved and rejected")
            return "rejected"
        print(f"{run_id}: provider stage failed before a response was preserved")
        return "infrastructure-failed"

    import_exit = run_optional(
        import_command(
            repository,
            baseline,
            task,
            workspace,
            provider,
            output,
            run_id,
        ),
        repository,
    )
    if import_exit == 0:
        return "passed"
    if raw_output.is_file():
        print(f"{run_id}: candidate was rejected by trusted validation or oracle")
        return "rejected"
    return "infrastructure-failed"


def import_command(
    repository: Path,
    baseline: Path,
    task: Path,
    workspace: Path,
    provider: Path,
    output: Path,
    run_id: str,
) -> list[str]:
    return [
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
    ]


def validate_resume_state(
    output: Path,
    baseline: Path,
    workspace: Path,
    qwen_provider: Path,
    codex_provider: Path,
    qwen_run: Path,
    codex_run: Path,
    comparison: Path,
    summary: Path,
) -> None:
    if not output.is_dir():
        raise PairRunError(f"resume output directory does not exist: {output}")
    for path, context in (
        (baseline, "active baseline"),
        (workspace, "frozen workspace"),
    ):
        if not path.is_dir():
            raise PairRunError(f"resume {context} does not exist: {path}")
    raw_qwen = qwen_provider / "raw" / "provider-output.json"
    if not raw_qwen.is_file():
        raise PairRunError(
            f"resume requires a preserved rejected Qwen response: {raw_qwen}"
        )
    if (qwen_provider / "proposal").exists() or qwen_run.exists():
        raise PairRunError(
            "resume-after-qwen-rejection requires Qwen to have no proposal or run"
        )
    for path in (codex_provider, codex_run, comparison, summary):
        if path.exists():
            raise PairRunError(f"resume target already exists: {path}")


def pair_result(qwen_status: str, codex_status: str) -> str:
    statuses = {qwen_status, codex_status}
    if "infrastructure-failed" in statuses:
        return "infrastructure-failed"
    if statuses == {"passed"}:
        return "passed"
    return "completed-with-rejection"


def require_clean_output(path: Path) -> None:
    if path.exists():
        if not path.is_dir() or any(path.iterdir()):
            raise PairRunError(f"output directory must be empty: {path}")
    else:
        path.mkdir(parents=True)


def run_required(command: list[str], cwd: Path) -> None:
    if run_optional(command, cwd) != 0:
        raise PairRunError(
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
