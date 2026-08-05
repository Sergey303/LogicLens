#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
MIGRATION = REPO / "EpistemicCompilerLab" / "research-execution" / "scripts" / "apply_round3_canonical_generator_fix.py"
SELF = Path(__file__).resolve()


def main() -> int:
    spec = importlib.util.spec_from_file_location("round3_migration", MIGRATION)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load round-3 migration module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    original = module.GENERATOR.read_text(encoding="utf-8")
    patched = module.replace_function(original, "acceptance_yaml", "wrapper_source", module.ACCEPTANCE_FUNCTION)
    patched = module.replace_function(patched, "build_handoff", "main", module.HANDOFF_FUNCTION)
    if patched == original:
        raise RuntimeError("generator patch produced no change")
    module.GENERATOR.write_text(patched, encoding="utf-8")

    MIGRATION.unlink()
    SELF.unlink()
    print(json.dumps({
        "status": "PASS",
        "modified": str(module.GENERATOR.relative_to(REPO)),
        "deleted": [
            str(MIGRATION.relative_to(REPO)),
            str(SELF.relative_to(REPO)),
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
