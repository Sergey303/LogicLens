#!/usr/bin/env python3
"""Execute a frozen Semantic Claims LLM pilot without retrying attempted run IDs."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any

from active_epoch.hashing import append_field, canonical_json_bytes
from semantic_claims_llm_contract import (
    DEFAULT_ENDPOINT,
    SemanticClaimsLlmError,
    validate_endpoint,
)
from semantic_claims_llm_experiment import (
    SemanticClaimsExperimentError,
    aggregate_report,
    verify_plan,
    write_new,
)

EXECUTION_SCHEMA = "semantic-claims-llm-execution-record-v0"
EXECUTION_DOMAIN = b"LogicLensSemanticClaimsLlmExecutionRecord\0"
HASH_VERSION = bytes((1,))
MAX_CAPTURE_CHARS = 1_000_000


class SemanticClaimsPilotRunnerError(RuntimeError):
    pass


def domain_hash(value: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(EXECUTION_DOMAIN)
    digest.update(HASH_VERSION)
    append_field(digest, canonical_json_bytes(value))
    return "sha256:" + digest.hexdigest()


def bounded_text(value: str) -> tuple[str, bool]:
    if len(value) <= MAX_CAPTURE_CHARS:
        return value, False
    return value[:MAX_CAPTURE_CHARS], True


def build_command(
    tool_path: Path,
    item: dict[str, Any],
    plan: dict[str, Any],
    endpoint: str,
    timeout_seconds: float,
    output: Path,
) -> list[str]:
    producer = plan["producer"]
    return [
        sys.executable,
        str(tool_path),
        "run",
        "--case-id",
        item["caseId"],
        "--model",
        producer["model"],
        "--seed",
        str(item["seed"]),
        "--context-tokens",
        str(producer["numCtx"]),
        "--output-tokens",
        str(producer["numPredict"]),
        "--endpoint",
        endpoint,
        "--timeout-seconds",
        str(timeout_seconds),
        "--output",
        str(output),
    ]


def execution_record(
    *,
    item: dict[str, Any],
    command: list[str],
    endpoint: str,
    timeout_seconds: float,
    outcome: str,
    return_code: int | None,
    stdout: str,
    stderr: str,
) -> dict[str, Any]:
    stdout_value, stdout_truncated = bounded_text(stdout)
    stderr_value, stderr_truncated = bounded_text(stderr)
    payload: dict[str, Any] = {
        "schemaVersion": EXECUTION_SCHEMA,
        "stage": "local-ollama-pilot-execution",
        "runId": item["runId"],
        "caseId": item["caseId"],
        "seed": item["seed"],
        "endpoint": endpoint,
        "timeoutSeconds": timeout_seconds,
        "command": command,
        "outcome": outcome,
        "returnCode": return_code,
        "stdout": stdout_value,
        "stderr": stderr_value,
        "stdoutTruncated": stdout_truncated,
        "stderrTruncated": stderr_truncated,
    }
    payload["artifactHash"] = domain_hash(payload)
    return payload


def write_execution(directory: Path, record: dict[str, Any]) -> None:
    path = directory / "execution.json"
    if path.exists():
        raise SemanticClaimsPilotRunnerError(f"execution record already exists: {path}")
    path.write_bytes(canonical_json_bytes(record))


def finalize_interrupted(
    staging: Path,
    final: Path,
    item: dict[str, Any],
    endpoint: str,
    timeout_seconds: float,
) -> None:
    record = execution_record(
        item=item,
        command=[],
        endpoint=endpoint,
        timeout_seconds=timeout_seconds,
        outcome="interrupted-before-finalization",
        return_code=None,
        stdout="",
        stderr="staging directory existed before this invocation; run was not retried",
    )
    if not (staging / "execution.json").exists():
        write_execution(staging, record)
    staging.rename(final)


def execute_plan(
    benchmark_root: Path,
    plan_path: Path,
    runs_root: Path,
    report_path: Path,
    *,
    endpoint: str = DEFAULT_ENDPOINT,
    timeout_seconds: float = 600.0,
    tool_path: Path | None = None,
) -> dict[str, Any]:
    try:
        validate_endpoint(endpoint)
    except SemanticClaimsLlmError as error:
        raise SemanticClaimsPilotRunnerError(str(error)) from error
    if timeout_seconds <= 0:
        raise SemanticClaimsPilotRunnerError("timeout must be positive")
    if report_path.resolve().exists():
        raise SemanticClaimsPilotRunnerError(f"report output already exists: {report_path.resolve()}")
    plan = verify_plan(benchmark_root.resolve(), plan_path.resolve())
    runs_root = runs_root.resolve()
    try:
        runs_root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise SemanticClaimsPilotRunnerError(
            f"cannot create runs root {runs_root}: {error}"
        ) from error
    tool = (tool_path or Path(__file__).with_name("semantic_claims_llm.py")).resolve()
    if not tool.is_file():
        raise SemanticClaimsPilotRunnerError(f"bounded LLM runner not found: {tool}")

    for item in plan["matrix"]:
        final = runs_root / item["runId"]
        staging = runs_root / f".{item['runId']}.in-progress"
        if final.exists():
            print(f"Skip attempted run: {item['runId']}")
            continue
        if staging.exists():
            print(f"Finalize interrupted run without retry: {item['runId']}")
            finalize_interrupted(staging, final, item, endpoint, timeout_seconds)
            continue

        command = build_command(tool, item, plan, endpoint, timeout_seconds, staging)
        print(f"Execute run: {item['runId']}")
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            return_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
            outcome = "completed" if return_code == 0 else "runner-failed"
        except OSError as error:
            return_code = None
            stdout = ""
            stderr = str(error)
            outcome = "runner-start-failed"

        staging.mkdir(parents=True, exist_ok=True)
        write_execution(
            staging,
            execution_record(
                item=item,
                command=command,
                endpoint=endpoint,
                timeout_seconds=timeout_seconds,
                outcome=outcome,
                return_code=return_code,
                stdout=stdout,
                stderr=stderr,
            ),
        )
        staging.rename(final)

    report = aggregate_report(benchmark_root.resolve(), plan, runs_root)
    write_new(report_path, report, "experiment report")
    return report


def execute_command(args: argparse.Namespace) -> int:
    try:
        report = execute_plan(
            args.benchmark_root,
            args.plan,
            args.runs_root,
            args.report,
            endpoint=args.endpoint,
            timeout_seconds=args.timeout_seconds,
        )
    except SemanticClaimsExperimentError as error:
        raise SemanticClaimsPilotRunnerError(str(error)) from error
    summary = report["summary"]
    print(f"Pilot execution accounted: {summary['validRuns']}/{summary['plannedRuns']} valid")
    print(f"Report: {args.report.resolve()}")
    return 0 if summary["complete"] else 2


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--benchmark-root",
        type=Path,
        default=Path("experiments/presentation/semantic-planning-v0"),
    )
    result.add_argument("--plan", type=Path, required=True)
    result.add_argument("--runs-root", type=Path, required=True)
    result.add_argument("--report", type=Path, required=True)
    result.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    result.add_argument("--timeout-seconds", type=float, default=600.0)
    result.set_defaults(handler=execute_command)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.handler(args)
    except SemanticClaimsPilotRunnerError as error:
        print(f"semantic claims pilot runner error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())