#!/usr/bin/env python3
"""Contract checks for the Qwen-only Builder entry point."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


class VerificationError(AssertionError):
    pass


def load_runner(path: Path):
    spec = importlib.util.spec_from_file_location("run_builder_qwen_only", path)
    if spec is None or spec.loader is None:
        raise VerificationError(f"cannot load Qwen-only runner: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    runner_path = repository / "tools" / "run_builder_qwen_only.py"
    source = runner_path.read_text(encoding="utf-8")

    required = (
        "run_builder_ollama.py",
        "builder_experiment.py",
        "import-run",
        "qwen-only-summary.json",
        "--context-tokens",
        '"contextTokens": args.context_tokens',
        'adapter_status == "context-limited"',
        'return 1 if status == "infrastructure-failed" else 0',
        'return "rejected"',
        'return "passed"',
    )
    missing = [text for text in required if text not in source]
    if missing:
        raise VerificationError(f"Qwen-only runner is missing contracts: {missing}")

    forbidden = ("run_builder_codex.py", "codex-provider", "codex-run")
    present = [text for text in forbidden if text in source]
    if present:
        raise VerificationError(f"Qwen-only runner references Codex: {present}")

    if source.count("run_builder_ollama.py") != 1:
        raise VerificationError("Qwen-only runner must invoke one Ollama adapter path")

    runner = load_runner(runner_path)
    with tempfile.TemporaryDirectory(prefix="logiclens-qwen-status-") as temporary:
        provider = Path(temporary) / "provider"
        raw = provider / "raw"
        raw.mkdir(parents=True)
        (raw / "adapter-result.json").write_text(
            json.dumps(
                {
                    "schemaVersion": "0.1",
                    "status": "context-limited",
                    "contextTokens": 16_384,
                    "promptEvalCount": 16_000,
                }
            ),
            encoding="utf-8",
        )
        if runner.read_adapter_failure_status(provider) != "context-limited":
            raise VerificationError("context-limited adapter result was not recognized")

    print("ok 1 - Qwen-only runner has preparation and trusted import stages")
    print("ok 2 - reviewed context window is passed and recorded")
    print("ok 3 - context-limited responses are infrastructure failures")
    print("ok 4 - ordinary rejection remains a measured result")
    print("ok 5 - no Codex adapter or artifact path is present")
    print("1..5")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
