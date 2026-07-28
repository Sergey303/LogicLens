#!/usr/bin/env python3
"""Focused checks for locale-independent validator transport and exit classes."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


class VerificationError(AssertionError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise VerificationError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    tools = repository / "tools"
    sys.path.insert(0, str(tools))

    candidate = load_module(
        "build_epoch_candidate_utf8_compat_tested",
        tools / "build_epoch_candidate_utf8_compat.py",
    )
    completed = candidate.run_process_utf8(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.stdout.buffer.write('исследователь\\n'.encode('utf-8'))"
            ),
        ],
        repository,
        10.0,
        "UTF-8 probe",
    )
    if completed.stdout != "исследователь\n":
        raise VerificationError(f"UTF-8 output changed: {completed.stdout!r}")

    try:
        candidate.run_process_utf8(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(bytes([0x98]))",
            ],
            repository,
            10.0,
            "invalid UTF-8 probe",
        )
    except candidate.CandidateInfrastructureError as exc:
        if "not valid UTF-8" not in str(exc):
            raise VerificationError(f"unexpected invalid UTF-8 error: {exc}") from exc
    else:
        raise VerificationError("invalid process encoding was accepted")

    experiment = load_module(
        "builder_experiment_utf8_compat_tested",
        tools / "builder_experiment_utf8_compat.py",
    )
    expected_candidate = {
        0: "passed",
        2: "rejected",
        1: "infrastructure-failed",
        7: "infrastructure-failed",
    }
    for exit_code, expected in expected_candidate.items():
        actual = experiment.classify_candidate_exit(exit_code)
        if actual != expected:
            raise VerificationError(
                f"candidate exit {exit_code} classified as {actual}, expected {expected}"
            )

    def oracle_mismatch(*_args, **_kwargs) -> None:
        raise experiment.base.ExperimentError(
            "trusted hidden oracle failed with exit 1: stdout='', stderr=''"
        )

    experiment._ORIGINAL_RUN_ORACLE = oracle_mismatch
    try:
        experiment.run_oracle_classified()
    except experiment.ExperimentRejected as exc:
        if "hidden oracle rejected" not in str(exc):
            raise VerificationError(f"unexpected oracle rejection message: {exc}") from exc
    else:
        raise VerificationError("hidden-oracle mismatch was not classified as rejection")

    def oracle_transport_failure(*_args, **_kwargs) -> None:
        raise experiment.base.ExperimentError(
            "trusted hidden oracle returned output that is not valid UTF-8"
        )

    experiment._ORIGINAL_RUN_ORACLE = oracle_transport_failure
    try:
        experiment.run_oracle_classified()
    except experiment.ExperimentInfrastructureError as exc:
        if "could not produce a verdict" not in str(exc):
            raise VerificationError(
                f"unexpected oracle infrastructure message: {exc}"
            ) from exc
    else:
        raise VerificationError("oracle transport failure was not infrastructure failure")

    print("ok 1 - validator process output is decoded as strict UTF-8")
    print("ok 2 - invalid process encoding is infrastructure failure")
    print("ok 3 - candidate rejection uses dedicated exit code 2")
    print("ok 4 - hidden-oracle mismatch is measured rejection")
    print("ok 5 - hidden-oracle transport failure remains infrastructure failure")
    print("1..5")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
