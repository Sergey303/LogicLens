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

    qwen = load_module(
        "run_builder_qwen_only_compat_tested",
        tools / "run_builder_qwen_only_compat.py",
    )
    for exit_code, expected in expected_candidate.items():
        actual = qwen.classify_import_exit(exit_code)
        if actual != expected:
            raise VerificationError(
                f"import exit {exit_code} classified as {actual}, expected {expected}"
            )

    captured: list[list[str]] = []

    def fake_run(command: list[str], cwd: Path) -> int:
        captured.append(command)
        return 0

    qwen._ORIGINAL_RUN_OPTIONAL = fake_run
    qwen.run_optional_with_compat(
        [sys.executable, str(tools / "run_builder_ollama.py")], repository
    )
    qwen.run_optional_with_compat(
        [sys.executable, str(tools / "builder_experiment.py"), "import-run"],
        repository,
    )
    names = [Path(command[1]).name for command in captured]
    if names != [
        "run_builder_ollama_compat.py",
        "builder_experiment_utf8_compat.py",
    ]:
        raise VerificationError(f"compatibility substitutions are wrong: {names}")

    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            tools / "build_epoch_candidate_utf8_compat.py",
            tools / "builder_experiment_utf8_compat.py",
            tools / "run_builder_qwen_only_compat.py",
        )
    )
    if "codex" in sources.lower():
        raise VerificationError("UTF-8 compatibility path references Codex")

    print("ok 1 - validator process output is decoded as strict UTF-8")
    print("ok 2 - invalid process encoding is infrastructure failure")
    print("ok 3 - candidate rejection uses dedicated exit code 2")
    print("ok 4 - Qwen import distinguishes rejection from infrastructure failure")
    print("ok 5 - compatibility wrappers select diagnostic transport entries")
    print("ok 6 - no Codex path is present")
    print("1..6")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
