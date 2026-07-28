#!/usr/bin/env python3
"""Run the activation-overlay contract test with the shared aggregate hasher."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from active_epoch.hashing import aggregate_hash


def load_test(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_activation_overlay_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    test = load_test(repository / "tests" / "candidate_activation_overlay_test.py")
    original_load_module = test.load_module

    def patched_load_module(name: str, path: Path):
        module = original_load_module(name, path)
        if path.name == "build_builder_candidate_activation_overlay.py":
            module.aggregate_hash = aggregate_hash
        return module

    test.load_module = patched_load_module
    return test.main()


if __name__ == "__main__":
    raise SystemExit(main())
