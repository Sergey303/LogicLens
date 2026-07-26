#!/usr/bin/env python3
"""Static contract checks for the Qwen-only Builder entry point."""

from __future__ import annotations

import sys
from pathlib import Path


class VerificationError(AssertionError):
    pass


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    runner = repository / "tools" / "run_builder_qwen_only.py"
    source = runner.read_text(encoding="utf-8")

    required = (
        "run_builder_ollama.py",
        "builder_experiment.py",
        "import-run",
        "qwen-only-summary.json",
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

    print("ok 1 - Qwen-only runner has preparation and trusted import stages")
    print("ok 2 - rejection remains a measured non-infrastructure result")
    print("ok 3 - no Codex adapter or artifact path is present")
    print("1..3")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
