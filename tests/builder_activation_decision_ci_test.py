#!/usr/bin/env python3
"""Run the activation-decision fixture with schema-valid synthetic hashes."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


def load_test(path: Path):
    spec = importlib.util.spec_from_file_location(
        "builder_activation_decision_test",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    test = load_test(
        repository / "tests" / "builder_activation_decision_test.py"
    )

    def valid_hash(character: str) -> str:
        return "sha256:" + hashlib.sha256(
            character.encode("utf-8")
        ).hexdigest()

    test.hash64 = valid_hash
    return test.main()


if __name__ == "__main__":
    raise SystemExit(main())
