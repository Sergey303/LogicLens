#!/usr/bin/env python3
"""Run Builder import with UTF-8 candidate transport and classified exits."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import builder_experiment.cli as base


UTF8 = "utf-8"
REJECTED_EXIT = 2


class ExperimentRejected(RuntimeError):
    """Raised when the preserved model proposal fails trusted validation."""


class ExperimentInfrastructureError(RuntimeError):
    """Raised when validation cannot produce a model verdict."""


def classify_candidate_exit(returncode: int) -> str:
    if returncode == 0:
        return "passed"
    if returncode == REJECTED_EXIT:
        return "rejected"
    return "infrastructure-failed"


def run_candidate_builder_utf8(
    baseline: Path,
    proposal: Path,
    candidate_schema: Path,
    candidate_output: Path,
    comparison_path: Path,
    swipl: str,
    timeout_ms: int,
) -> None:
    script = Path(__file__).resolve().parent / "build_epoch_candidate_utf8_compat.py"
    command = [
        sys.executable,
        str(script),
        "--baseline",
        str(baseline),
        "--proposal",
        str(proposal),
        "--schema",
        str(candidate_schema),
        "--output",
        str(candidate_output),
        "--report",
        str(comparison_path),
        "--swipl",
        swipl,
        "--timeout-ms",
        str(timeout_ms),
    ]
    timeout_seconds = max(90.0, timeout_ms / 1000.0 * 10)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            cwd=Path(__file__).resolve().parents[1],
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExperimentInfrastructureError(
            "trusted candidate validator exceeded the reviewed timeout"
        ) from exc
    except OSError as exc:
        raise ExperimentInfrastructureError(
            f"trusted candidate validator could not start: {exc}"
        ) from exc

    stdout_bytes = completed.stdout or b""
    stderr_bytes = completed.stderr or b""
    if not isinstance(stdout_bytes, bytes) or not isinstance(stderr_bytes, bytes):
        raise ExperimentInfrastructureError(
            "trusted candidate validator returned non-binary process output"
        )
    if len(stdout_bytes) + len(stderr_bytes) > base.MAX_PROCESS_OUTPUT_BYTES:
        raise ExperimentInfrastructureError(
            "trusted candidate validator exceeded the process output limit"
        )
    try:
        stdout = stdout_bytes.decode(UTF8)
        stderr = stderr_bytes.decode(UTF8)
    except UnicodeDecodeError as exc:
        raise ExperimentInfrastructureError(
            "trusted candidate validator returned output that is not valid UTF-8"
        ) from exc

    status = classify_candidate_exit(completed.returncode)
    detail = (
        f"stdout={stdout[-2000:]!r}, stderr={stderr[-2000:]!r}"
    )
    if status == "rejected":
        raise ExperimentRejected(f"trusted candidate validator rejected: {detail}")
    if status == "infrastructure-failed":
        raise ExperimentInfrastructureError(
            f"trusted candidate validator failed with exit {completed.returncode}: {detail}"
        )
    if "Candidate accepted:" not in stdout:
        raise ExperimentInfrastructureError(
            "candidate validator exited successfully without acceptance confirmation"
        )


def main() -> int:
    base.run_candidate_builder = run_candidate_builder_utf8
    try:
        return base.main()
    except ExperimentRejected as exc:
        print(f"Builder experiment rejected: {exc}", file=sys.stderr)
        return REJECTED_EXIT
    except (
        ExperimentInfrastructureError,
        base.ExperimentError,
        OSError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"Builder experiment infrastructure failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # fail closed on an unclassified import crash
        print(f"Builder experiment infrastructure failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
