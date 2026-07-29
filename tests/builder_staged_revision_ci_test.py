#!/usr/bin/env python3
"""Run the staged revision test with one clean-overlay module instance."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_test(path: Path):
    spec = importlib.util.spec_from_file_location("builder_staged_revision_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    test = load_test(repository / "tests" / "builder_staged_revision_test.py")
    original_load_module = test.load_module

    def patched_load_module(name: str, path: Path):
        if path.name == "build_builder_candidate_activation_overlay_clean_compat.py":
            existing = sys.modules.get(
                "build_builder_candidate_activation_overlay_clean_compat"
            )
            if existing is None:
                raise RuntimeError("clean overlay module was not loaded by staged builder")
            return existing
        return original_load_module(name, path)

    test.load_module = patched_load_module
    return test.main()


if __name__ == "__main__":
    raise SystemExit(main())
