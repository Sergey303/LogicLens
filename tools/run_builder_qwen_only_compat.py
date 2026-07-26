#!/usr/bin/env python3
"""Run Qwen-only Builder with the ENG-61 diagnostic Ollama transport."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import run_builder_qwen_only as base

_ORIGINAL_RUN_OPTIONAL = base.run_optional


def run_optional_with_compat(command: list[str], cwd: Path) -> int:
    updated = list(command)
    for index, argument in enumerate(updated):
        if Path(argument).name == "run_builder_ollama.py":
            updated[index] = str(cwd / "tools" / "run_builder_ollama_compat.py")
    return _ORIGINAL_RUN_OPTIONAL(updated, cwd)


def main() -> int:
    base.run_optional = run_optional_with_compat
    return base.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        base.QwenOnlyRunError,
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as exc:
        print(f"Qwen-only compatibility run failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
