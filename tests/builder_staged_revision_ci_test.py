#!/usr/bin/env python3
"""Run the staged revision test with one clean-overlay module instance."""
from __future__ import annotations

import importlib.util
import json
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
    original_add_smoke_and_rebind = test.add_smoke_and_rebind

    def patched_load_module(name: str, path: Path):
        if path.name == "build_builder_candidate_activation_overlay_clean_compat.py":
            existing = sys.modules.get(
                "build_builder_candidate_activation_overlay_clean_compat"
            )
            if existing is None:
                raise RuntimeError("clean overlay module was not loaded by staged builder")
            return existing
        return original_load_module(name, path)

    def patched_add_smoke_and_rebind(*args, **kwargs) -> None:
        original_add_smoke_and_rebind(*args, **kwargs)

        candidate_manifest_path = kwargs["candidate_manifest_path"]
        plan_path = kwargs["plan_path"]
        blocked_path = kwargs["blocked_path"]
        hashing_module = kwargs["hashing_module"]
        readiness_module = kwargs["readiness_module"]
        plan_module = kwargs["plan_module"]

        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["evidence"]["candidateManifestFileHash"] = hashing_module.sha256(
            candidate_manifest_path.read_bytes()
        )
        plan["promotionPlanHash"] = plan_module.compute_promotion_plan_hash(plan)
        test.write_json(hashing_module, plan_path, plan)

        blocked = json.loads(blocked_path.read_text(encoding="utf-8"))
        blocked["source"]["promotionPlanHash"] = plan["promotionPlanHash"]
        blocked["assessmentHash"] = readiness_module.compute_assessment_hash(blocked)
        test.write_json(hashing_module, blocked_path, blocked)

    test.load_module = patched_load_module
    test.add_smoke_and_rebind = patched_add_smoke_and_rebind
    return test.main()


if __name__ == "__main__":
    raise SystemExit(main())
