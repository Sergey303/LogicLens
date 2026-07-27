#!/usr/bin/env python3
"""Fail when generated Python bytecode is tracked by Git."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class VerificationError(AssertionError):
    pass


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repository,
        check=True,
        stdout=subprocess.PIPE,
    )
    tracked = [
        item.decode("utf-8", errors="strict").replace("\\", "/")
        for item in completed.stdout.split(b"\0")
        if item
    ]
    generated = sorted(
        path
        for path in tracked
        if "/__pycache__/" in f"/{path}"
        or path.endswith((".pyc", ".pyo"))
    )
    if generated:
        joined = "\n".join(f"- {path}" for path in generated)
        raise VerificationError(f"generated Python bytecode is tracked:\n{joined}")

    print("ok 1 - no Python bytecode or __pycache__ entries are tracked")
    print("1..1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError, VerificationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
