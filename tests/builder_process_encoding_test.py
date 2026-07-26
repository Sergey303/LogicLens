#!/usr/bin/env python3
"""Regression tests for locale-independent UTF-8 process capture."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from builder_experiment.cli import ExperimentError, run_process  # noqa: E402
from run_builder_codex import CodexAdapterError, call_codex  # noqa: E402


class VerificationError(AssertionError):
    pass


def test_builder_process_round_trips_utf8() -> None:
    value = "исследователь ✅"
    completed = run_process(
        [
            sys.executable,
            "-c",
            (
                "import sys;"
                "data=sys.stdin.buffer.read();"
                "sys.stdout.buffer.write(data);"
                "sys.stderr.buffer.write('диагностика'.encode('utf-8'))"
            ),
        ],
        ROOT,
        30.0,
        "UTF-8 round trip",
        value,
    )
    if completed.stdout != value or completed.stderr != "диагностика":
        raise VerificationError("Builder process capture changed UTF-8 text")


def test_builder_rejects_invalid_utf8_without_masking() -> None:
    try:
        run_process(
            [
                sys.executable,
                "-c",
                "import sys;sys.stdout.buffer.write(bytes([0x98]))",
            ],
            ROOT,
            30.0,
            "invalid UTF-8 fixture",
        )
    except ExperimentError as exc:
        message = str(exc)
        if "not valid UTF-8" not in message or "NoneType" in message:
            raise VerificationError(
                f"invalid UTF-8 produced the wrong diagnostic: {message}"
            ) from exc
    else:
        raise VerificationError("invalid UTF-8 process output was accepted")


def test_codex_process_uses_binary_utf8_capture() -> None:
    with tempfile.TemporaryDirectory(prefix="logiclens-codex-utf8-") as temporary:
        root = Path(temporary)
        schema = root / "schema.json"
        final = root / "final.json"
        schema.write_text("{}\n", encoding="utf-8")
        final.write_text('{"files":{}}\n', encoding="utf-8")
        completed = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"type":"turn.completed","message":"готово ✅"}\n'.encode("utf-8"),
            stderr="диагностика".encode("utf-8"),
        )
        with (
            patch("run_builder_codex.shutil.which", return_value=sys.executable),
            patch("run_builder_codex.subprocess.run", return_value=completed) as runner,
        ):
            response, events, calls = call_codex(
                "codex",
                "gpt-test",
                root,
                schema,
                final,
                "задача ✅",
                30.0,
            )
        invoked = runner.call_args.kwargs
        if invoked.get("input") != "задача ✅".encode("utf-8"):
            raise VerificationError("Codex prompt was not passed as UTF-8 bytes")
        if invoked.get("text") is not None or "encoding" in invoked:
            raise VerificationError("Codex capture still depends on the host locale")
        if response != final.read_bytes() or events != completed.stdout or calls != 0:
            raise VerificationError("Codex binary capture changed the provider result")


def test_codex_rejects_invalid_utf8() -> None:
    with tempfile.TemporaryDirectory(prefix="logiclens-codex-invalid-") as temporary:
        root = Path(temporary)
        schema = root / "schema.json"
        final = root / "final.json"
        schema.write_text("{}\n", encoding="utf-8")
        final.write_text("{}\n", encoding="utf-8")
        completed = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout=b"\x98",
            stderr=b"",
        )
        with (
            patch("run_builder_codex.shutil.which", return_value=sys.executable),
            patch("run_builder_codex.subprocess.run", return_value=completed),
        ):
            try:
                call_codex(
                    "codex",
                    "gpt-test",
                    root,
                    schema,
                    final,
                    "prompt",
                    30.0,
                )
            except CodexAdapterError as exc:
                if "not valid UTF-8" not in str(exc):
                    raise VerificationError(
                        f"Codex invalid UTF-8 produced the wrong diagnostic: {exc}"
                    ) from exc
            else:
                raise VerificationError("invalid Codex UTF-8 output was accepted")


def main() -> int:
    tests = [
        ("Builder UTF-8 round trip", test_builder_process_round_trips_utf8),
        (
            "Builder invalid UTF-8 diagnostic",
            test_builder_rejects_invalid_utf8_without_masking,
        ),
        ("Codex binary UTF-8 capture", test_codex_process_uses_binary_utf8_capture),
        ("Codex invalid UTF-8 diagnostic", test_codex_rejects_invalid_utf8),
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
        subprocess.SubprocessError,
    ) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
