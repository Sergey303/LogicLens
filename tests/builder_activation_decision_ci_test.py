#!/usr/bin/env python3
"""Run the activation-decision fixture with production-equivalent semantics."""
from __future__ import annotations

import hashlib
import importlib.util
import json
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
    original_build_fixture = test.build_fixture

    def valid_hash(character: str) -> str:
        return "sha256:" + hashlib.sha256(
            character.encode("utf-8")
        ).hexdigest()

    def patched_build_fixture(root: Path):
        result = original_build_fixture(root)
        staged = result[1]
        runtime_path = staged / "rules" / "revision_runtime.pl"
        source = runtime_path.read_text(encoding="utf-8")

        old_call = "Response,\n            1\n        )"
        if source.count(old_call) != 2:
            raise RuntimeError(
                "synthetic runtime does not contain two error paths"
            )
        source = source.replace(
            old_call,
            "Response,\n            ExitCode\n        )",
        )

        tail = "        diagnostics: []\n    }.\n"
        position = source.rfind(tail)
        if position < 0:
            raise RuntimeError(
                "synthetic runtime error response tail was not found"
            )
        source = (
            source[:position]
            + "        diagnostics: []\n    },\n    ExitCode = 1.\n"
            + source[position + len(tail):]
        )
        runtime_path.write_text(
            source,
            encoding="utf-8",
            newline="\n",
        )

        manifest_path = staged / "manifest.json"
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        payload = test.tree_bytes(staged)
        payload.pop(test.PurePosixPath("manifest.json"), None)
        manifest["files"] = {
            str(path): test.sha256(content)
            for path, content in sorted(
                payload.items(),
                key=lambda item: str(item[0]),
            )
        }
        manifest["packageHash"] = test.aggregate_hash(
            b"LogicLensStagedRevision\0",
            1,
            payload.items(),
        )
        test.write_json(manifest_path, manifest)
        return result

    test.hash64 = valid_hash
    test.build_fixture = patched_build_fixture
    return test.main()


if __name__ == "__main__":
    raise SystemExit(main())
