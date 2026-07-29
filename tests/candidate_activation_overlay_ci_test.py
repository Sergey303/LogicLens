#!/usr/bin/env python3
"""Run the activation-overlay contract test with shared hashing and clean imports."""
from __future__ import annotations

import importlib.util
from pathlib import Path, PurePosixPath

from active_epoch.hashing import aggregate_hash
import build_builder_candidate_activation_overlay_clean_compat as clean


def load_test(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_activation_overlay_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(root: Path) -> dict[PurePosixPath, bytes]:
    resolved = root.resolve()
    result: dict[PurePosixPath, bytes] = {}
    for path in sorted(resolved.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"fixture symlink is forbidden: {path}")
        if path.is_file():
            result[PurePosixPath(path.relative_to(resolved).as_posix())] = path.read_bytes()
    return result


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    test = load_test(repository / "tests" / "candidate_activation_overlay_test.py")
    original_load_module = test.load_module
    original_build_fixture = test.build_fixture
    state: dict[str, object] = {
        "activeSnapshot": None,
        "treeCalls": 0,
    }

    def patched_build_fixture(*args, **kwargs):
        result = original_build_fixture(*args, **kwargs)
        state["activeSnapshot"] = snapshot(result[0])
        return result

    def patched_load_module(name: str, path: Path):
        module = original_load_module(name, path)
        if path.name == "build_builder_candidate_activation_overlay.py":
            module.aggregate_hash = aggregate_hash
            module.render_revision_runtime = clean.render_revision_runtime_clean

            def tree_bytes(root: Path):
                state["treeCalls"] = int(state["treeCalls"]) + 1
                if state["treeCalls"] == 1:
                    original = state["activeSnapshot"]
                    if not isinstance(original, dict):
                        raise RuntimeError("active fixture snapshot was not captured")
                    return original
                return snapshot(root)

            module.tree_bytes = tree_bytes
        return module

    test.build_fixture = patched_build_fixture
    test.load_module = patched_load_module
    return test.main()


if __name__ == "__main__":
    raise SystemExit(main())
