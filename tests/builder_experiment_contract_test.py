#!/usr/bin/env python3
"""End-to-end contract tests for reproducible Qwen/Codex Builder runs."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Callable


class VerificationError(AssertionError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--task-schema", required=True, type=Path)
    parser.add_argument("--candidate-schema", required=True, type=Path)
    parser.add_argument("--run-schema", required=True, type=Path)
    parser.add_argument("--qwen-fixture", required=True, type=Path)
    parser.add_argument("--codex-fixture", required=True, type=Path)
    return parser.parse_args()


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def tree(root: Path) -> dict[PurePosixPath, bytes]:
    result: dict[PurePosixPath, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            result[PurePosixPath(path.relative_to(root).as_posix())] = path.read_bytes()
    return result


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, separators=(",", ": "))
        + "\n",
        encoding="utf-8",
    )


def run_tool(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(repository_root() / "tools" / "builder_experiment.py"),
            *arguments,
        ],
        cwd=repository_root(),
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )


def require_success(completed: subprocess.CompletedProcess[str]) -> None:
    if completed.returncode != 0:
        raise VerificationError(
            f"command failed: stdout={completed.stdout!r}, stderr={completed.stderr!r}"
        )


def require_failure(
    completed: subprocess.CompletedProcess[str],
    expected_text: str,
) -> None:
    if completed.returncode == 0:
        raise VerificationError(
            f"command unexpectedly succeeded: {completed.stdout!r}"
        )
    combined = completed.stdout + completed.stderr
    if expected_text not in combined:
        raise VerificationError(
            f"failure did not contain {expected_text!r}: {combined!r}"
        )


def prepare(
    args: argparse.Namespace,
    output: Path,
    task: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return run_tool(
        [
            "prepare",
            "--baseline",
            str(args.baseline),
            "--task",
            str(task or args.task),
            "--task-schema",
            str(args.task_schema),
            "--candidate-schema",
            str(args.candidate_schema),
            "--output",
            str(output),
        ]
    )


def import_run(
    args: argparse.Namespace,
    workspace: Path,
    proposal: Path,
    output: Path,
    run_id: str,
    task: Path | None = None,
    raw_output: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        "import-run",
        "--baseline",
        str(args.baseline),
        "--task",
        str(task or args.task),
        "--task-schema",
        str(args.task_schema),
        "--candidate-schema",
        str(args.candidate_schema),
        "--run-schema",
        str(args.run_schema),
        "--workspace",
        str(workspace),
        "--proposal",
        str(proposal),
        "--output",
        str(output),
        "--run-id",
        run_id,
    ]
    if raw_output is not None:
        command.extend(("--raw-output", str(raw_output)))
    return run_tool(command)


def compare(
    args: argparse.Namespace,
    runs: list[Path],
    output: Path,
) -> subprocess.CompletedProcess[str]:
    command = ["compare", "--run-schema", str(args.run_schema), "--output", str(output)]
    for run in runs:
        command.extend(("--run", str(run)))
    return run_tool(command)


def test_deterministic_workspace_and_runs(args: argparse.Namespace) -> None:
    baseline_before = tree(args.baseline)
    with tempfile.TemporaryDirectory(prefix="logiclens-builder-experiment-") as temporary:
        root = Path(temporary)
        workspace_a = root / "workspace-a"
        workspace_b = root / "workspace-b"
        require_success(prepare(args, workspace_a))
        require_success(prepare(args, workspace_b))
        if tree(workspace_a) != tree(workspace_b):
            raise VerificationError("frozen workspaces are not byte-identical")
        if (workspace_a / "oracle.json").exists():
            raise VerificationError("trusted oracle leaked into provider workspace")
        evidence_files = sorted((workspace_a / "evidence").glob("*.json"))
        if len(evidence_files) != 3:
            raise VerificationError("workspace does not contain all frozen evidence")

        raw = root / "qwen-raw.txt"
        raw.write_text('{"fixture":"qwen"}\n', encoding="utf-8")
        qwen_a = root / "qwen-a"
        qwen_b = root / "qwen-b"
        codex = root / "codex"
        require_success(
            import_run(
                args,
                workspace_a,
                args.qwen_fixture,
                qwen_a,
                "fixture-qwen",
                raw_output=raw,
            )
        )
        require_success(
            import_run(
                args,
                workspace_b,
                args.qwen_fixture,
                qwen_b,
                "fixture-qwen",
                raw_output=raw,
            )
        )
        require_success(
            import_run(
                args,
                workspace_a,
                args.codex_fixture,
                codex,
                "fixture-codex",
            )
        )
        if tree(qwen_a) != tree(qwen_b):
            raise VerificationError("identical provider runs are not byte-identical")

        qwen_run = read_json(qwen_a / "run.json")
        codex_run = read_json(codex / "run.json")
        for run in (qwen_run, codex_run):
            if run["validation"] != {"candidate": "passed", "oracle": "passed"}:
                raise VerificationError("accepted run did not record both validations")
            if not run["taskHash"].startswith("sha256:"):
                raise VerificationError("run did not pin task hash")
            if not run["oracleHash"].startswith("sha256:"):
                raise VerificationError("run did not pin oracle hash")
            if not run["basePackageHash"].startswith("sha256:"):
                raise VerificationError("run did not pin active package hash")
        if qwen_run["rawOutput"] is None:
            raise VerificationError("raw provider output was not retained")
        if codex_run["rawOutput"] is not None:
            raise VerificationError("missing raw output should remain explicit null")

        comparison_a = root / "comparison-a.json"
        comparison_b = root / "comparison-b.json"
        require_success(compare(args, [qwen_a, codex], comparison_a))
        require_success(compare(args, [codex, qwen_a], comparison_b))
        if comparison_a.read_bytes() != comparison_b.read_bytes():
            raise VerificationError("run comparison depends on argument order")
        report = read_json(comparison_a)
        if report["recommendedRunId"] is not None:
            raise VerificationError("fixture runs must not produce a recommendation")
        if "fixture runs" not in report["recommendationReason"]:
            raise VerificationError("fixture comparison reason is missing")
        if [item["runId"] for item in report["runs"]] != [
            "fixture-codex",
            "fixture-qwen",
        ]:
            raise VerificationError("comparison run order is not deterministic")

    if tree(args.baseline) != baseline_before:
        raise VerificationError("experiment pipeline modified the active baseline")


def test_hidden_oracle_rejects_consistent_falsehood(args: argparse.Namespace) -> None:
    baseline_before = tree(args.baseline)
    with tempfile.TemporaryDirectory(prefix="logiclens-builder-falsehood-") as temporary:
        root = Path(temporary)
        workspace = root / "workspace"
        require_success(prepare(args, workspace))
        proposal = root / "proposal"
        shutil.copytree(args.qwen_fixture, proposal)
        (proposal / "files" / "rules" / "candidate_researcher_at_iis.pl").write_text(
            ":- module(candidate_researcher_at_iis, [researcher_at_iis/2]).\n"
            "researcher_at_iis('urn:logiclens:person:false', []).\n",
            encoding="utf-8",
        )
        (proposal / "files" / "tests" / "candidate_researcher_at_iis_tests.pl").write_text(
            ":- begin_tests(candidate_researcher_at_iis).\n"
            ":- use_module('../rules/candidate_researcher_at_iis.pl').\n"
            "test(self_authored_falsehood_passes) :-\n"
            "    candidate_researcher_at_iis:researcher_at_iis(\n"
            "        'urn:logiclens:person:false', []).\n"
            ":- end_tests(candidate_researcher_at_iis).\n",
            encoding="utf-8",
        )
        completed = import_run(
            args,
            workspace,
            proposal,
            root / "run",
            "fixture-qwen",
        )
        require_failure(completed, "trusted hidden oracle")
    if tree(args.baseline) != baseline_before:
        raise VerificationError("oracle rejection modified the active baseline")


def test_workspace_tampering_is_rejected(args: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory(prefix="logiclens-builder-tamper-") as temporary:
        root = Path(temporary)
        workspace = root / "workspace"
        require_success(prepare(args, workspace))
        evidence = sorted((workspace / "evidence").glob("*.json"))[0]
        evidence.write_bytes(evidence.read_bytes() + b" ")
        completed = import_run(
            args,
            workspace,
            args.qwen_fixture,
            root / "run",
            "fixture-qwen",
        )
        require_failure(completed, "workspace file hashes")


def test_task_change_after_prepare_is_rejected(args: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory(prefix="logiclens-builder-task-change-") as temporary:
        root = Path(temporary)
        workspace = root / "workspace"
        require_success(prepare(args, workspace))
        changed_task = root / "task"
        shutil.copytree(args.task, changed_task)
        prompt = changed_task / "prompt.md"
        prompt.write_text(prompt.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
        completed = import_run(
            args,
            workspace,
            args.qwen_fixture,
            root / "run",
            "fixture-qwen",
            task=changed_task,
        )
        require_failure(completed, "workspace task hash mismatch")


def test_extra_task_file_is_rejected(args: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory(prefix="logiclens-builder-extra-file-") as temporary:
        root = Path(temporary)
        workspace = root / "workspace"
        require_success(prepare(args, workspace))
        proposal = root / "proposal"
        shutil.copytree(args.qwen_fixture, proposal)
        value = read_json(proposal / "proposal.json")
        value["files"].append(
            {"path": "rules/candidate_extra.pl", "kind": "rule"}
        )
        write_json(proposal / "proposal.json", value)
        (proposal / "files" / "rules" / "candidate_extra.pl").write_text(
            ":- module(candidate_extra, [candidate_extra/1]).\n"
            "candidate_extra(ok).\n",
            encoding="utf-8",
        )
        completed = import_run(
            args,
            workspace,
            proposal,
            root / "run",
            "fixture-qwen",
        )
        require_failure(completed, "exactly the three task-declared files")


def test_incompatible_runs_cannot_compare(args: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory(prefix="logiclens-builder-incompatible-") as temporary:
        root = Path(temporary)
        workspace = root / "workspace"
        require_success(prepare(args, workspace))
        qwen = root / "qwen"
        codex = root / "codex"
        require_success(
            import_run(args, workspace, args.qwen_fixture, qwen, "fixture-qwen")
        )
        require_success(
            import_run(args, workspace, args.codex_fixture, codex, "fixture-codex")
        )
        changed = read_json(codex / "run.json")
        changed["taskHash"] = "sha256:" + "0" * 64
        write_json(codex / "run.json", changed)
        completed = compare(args, [qwen, codex], root / "comparison.json")
        require_failure(completed, "runs differ in taskHash")


def main() -> int:
    args = parse_args()
    for name in (
        "baseline",
        "task",
        "task_schema",
        "candidate_schema",
        "run_schema",
        "qwen_fixture",
        "codex_fixture",
    ):
        setattr(args, name, getattr(args, name).resolve())

    tests: list[tuple[str, Callable[[], None]]] = [
        (
            "deterministic workspace runs and comparison",
            lambda: test_deterministic_workspace_and_runs(args),
        ),
        (
            "hidden oracle rejects consistent falsehood",
            lambda: test_hidden_oracle_rejects_consistent_falsehood(args),
        ),
        (
            "workspace tampering",
            lambda: test_workspace_tampering_is_rejected(args),
        ),
        (
            "task changed after preparation",
            lambda: test_task_change_after_prepare_is_rejected(args),
        ),
        (
            "extra task file",
            lambda: test_extra_task_file_is_rejected(args),
        ),
        (
            "incompatible run comparison",
            lambda: test_incompatible_runs_cannot_compare(args),
        ),
    ]
    for index, (name, test) in enumerate(tests, start=1):
        test()
        print(f"ok {index} - {name}")
    print(f"1..{len(tests)}")
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
