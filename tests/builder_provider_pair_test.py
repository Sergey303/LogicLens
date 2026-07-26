#!/usr/bin/env python3
"""Offline orchestration checks for the real Builder provider pair runner."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


class VerificationError(AssertionError):
    pass


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("builder_provider_pair", path)
    if spec is None or spec.loader is None:
        raise VerificationError(f"cannot load pair runner: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rejected_qwen_does_not_block_codex(module) -> None:
    with tempfile.TemporaryDirectory(prefix="logiclens-pair-test-") as temporary:
        root = Path(temporary)
        output = root / "pair"
        output.mkdir()
        (output / "active-epoch").mkdir()
        (output / "workspace").mkdir()
        raw = output / "qwen-provider" / "raw"
        raw.mkdir(parents=True)
        (raw / "provider-output.json").write_text("{}\n", encoding="utf-8")

        commands: list[list[str]] = []

        def fake_optional(command: list[str], cwd: Path) -> int:
            commands.append(command)
            if "run_builder_codex.py" in " ".join(command):
                codex_raw = output / "codex-provider" / "raw"
                codex_raw.mkdir(parents=True)
                (codex_raw / "provider-output.json").write_text(
                    "{}\n", encoding="utf-8"
                )
                (output / "codex-provider" / "proposal").mkdir()
                return 0
            if "import-run" in command:
                (output / "codex-run-001").mkdir()
                return 0
            raise VerificationError(f"unexpected command: {command}")

        old_argv = sys.argv
        old_optional = module.run_optional
        try:
            module.run_optional = fake_optional
            sys.argv = [
                str(Path(module.__file__)),
                "--output",
                str(output),
                "--codex-model",
                "codex-test",
                "--resume-after-qwen-rejection",
            ]
            result = module.main()
        finally:
            sys.argv = old_argv
            module.run_optional = old_optional

        if result != 0:
            raise VerificationError(f"recorded Qwen rejection returned {result}")
        rendered = [" ".join(command) for command in commands]
        if not any("run_builder_codex.py" in command for command in rendered):
            raise VerificationError("Codex adapter was not run")
        if not any("import-run" in command for command in rendered):
            raise VerificationError("successful Codex proposal was not imported")
        if any("run_builder_ollama.py" in command for command in rendered):
            raise VerificationError("resume unexpectedly invoked Ollama")
        summary = json.loads(
            (output / "provider-pair-summary.json").read_text(encoding="utf-8")
        )
        if summary["result"] != "completed-with-rejection":
            raise VerificationError(f"unexpected summary: {summary}")
        statuses = {
            provider["kind"]: provider["status"]
            for provider in summary["providers"]
        }
        if statuses != {"ollama": "rejected", "codex": "passed"}:
            raise VerificationError(f"unexpected provider statuses: {statuses}")
        if (output / "provider-comparison.json").exists():
            raise VerificationError("comparison was written for a rejected run")


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    module = load_module(repository / "tools" / "run_builder_provider_pair.py")
    test_rejected_qwen_does_not_block_codex(module)
    print("ok 1 - rejected Qwen does not block Codex")
    print("1..1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
