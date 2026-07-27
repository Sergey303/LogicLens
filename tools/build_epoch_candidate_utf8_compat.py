#!/usr/bin/env python3
"""Run the trusted candidate builder with locale-independent UTF-8 process I/O."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema.exceptions import ValidationError

import builder_candidate.cli as base
from builder_candidate.contract import CandidateError


UTF8 = "utf-8"


class CandidateInfrastructureError(RuntimeError):
    """Raised when the validator process environment fails before a model verdict."""


def run_process_utf8(
    command: list[str],
    cwd: Path,
    timeout_seconds: float,
    context: str,
    stdin_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    stdin_bytes = stdin_text.encode(UTF8) if stdin_text is not None else None
    try:
        completed = subprocess.run(
            command,
            input=stdin_bytes,
            capture_output=True,
            cwd=cwd,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise CandidateInfrastructureError(
            f"{context} exceeded the reviewed timeout"
        ) from exc
    except OSError as exc:
        raise CandidateInfrastructureError(f"{context} could not start: {exc}") from exc

    stdout_bytes = completed.stdout or b""
    stderr_bytes = completed.stderr or b""
    if not isinstance(stdout_bytes, bytes) or not isinstance(stderr_bytes, bytes):
        raise CandidateInfrastructureError(
            f"{context} returned non-binary process output"
        )
    if len(stdout_bytes) + len(stderr_bytes) > base.OUTPUT_LIMIT_BYTES:
        raise CandidateError(f"{context} exceeded the process output limit")

    try:
        stdout = stdout_bytes.decode(UTF8)
        stderr = stderr_bytes.decode(UTF8)
    except UnicodeDecodeError as exc:
        raise CandidateInfrastructureError(
            f"{context} returned output that is not valid UTF-8"
        ) from exc

    decoded = subprocess.CompletedProcess(
        completed.args,
        completed.returncode,
        stdout,
        stderr,
    )
    if decoded.returncode != 0:
        raise CandidateError(
            f"{context} failed with exit {decoded.returncode}: "
            f"stdout={decoded.stdout[-2000:]!r}, stderr={decoded.stderr[-2000:]!r}"
        )
    return decoded


def main() -> int:
    base.run_process = run_process_utf8
    try:
        return base.main()
    except (CandidateError, ValidationError, json.JSONDecodeError) as exc:
        print(f"Epoch candidate rejected: {exc}", file=sys.stderr)
        return 2
    except (
        CandidateInfrastructureError,
        OSError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"Epoch candidate infrastructure failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # fail closed on an unclassified validator crash
        print(f"Epoch candidate infrastructure failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
