#!/usr/bin/env python3
"""Build a temporary DSL-B management world without modifying the source world."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from capsule import canonical_json, validate_world  # noqa: E402

UTF8 = "utf-8"
OVERLAY_VERSION = "0.2.0"
RULE_RELATIVE = "rules/logical-rules-dsl-b-v0.jsonl"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-world", required=True, type=Path)
    parser.add_argument("--output-world", required=True, type=Path)
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path(__file__).with_name("dsl-b-logical-rules-v0.jsonl"),
    )
    parser.add_argument(
        "--contracts-root",
        type=Path,
        default=ROOT / "contracts",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding=UTF8))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object expected: {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_json(value))


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = arguments()
    source = args.source_world.resolve()
    output = args.output_world.resolve()
    rules = args.rules.resolve()
    if not source.is_dir():
        raise RuntimeError(f"source world does not exist: {source}")
    if not rules.is_file():
        raise RuntimeError(f"logical rules do not exist: {rules}")
    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            raise RuntimeError(f"output world must be absent or empty: {output}")
        output.rmdir()

    source_capsule_path = source / "capsules" / "role-boundaries" / "capsule.json"
    source_module_path = source / "modules" / "00-role-boundaries" / "module.json"
    source_capsule = read_json(source_capsule_path)
    source_module = read_json(source_module_path)
    source_capsule_version = source_capsule.get("version")
    source_module_version = source_module.get("version")

    shutil.copytree(source, output)
    capsule_path = output / "capsules" / "role-boundaries" / "capsule.json"
    module_path = output / "modules" / "00-role-boundaries" / "module.json"
    capsule = read_json(capsule_path)
    module = read_json(module_path)

    rule_files = capsule.get("ruleFiles")
    if not isinstance(rule_files, list):
        raise RuntimeError("capsule ruleFiles must be an array")
    if any(
        isinstance(item, dict) and item.get("path") == RULE_RELATIVE
        for item in rule_files
    ):
        raise RuntimeError("DSL-B rule overlay is already declared")
    rule_files.append(
        {
            "path": RULE_RELATIVE,
            "kind": "rules",
            "description": "Experimental ground logical DSL-B rules for the frozen management benchmark.",
        }
    )
    capsule["version"] = OVERLAY_VERSION
    capsule["description"] = (
        "Experimental DSL-B overlay. Source knowledge remains unchanged; "
        "only local pedagogical logical rules are added."
    )

    uses_capsules = module.get("usesCapsules")
    if not isinstance(uses_capsules, list) or len(uses_capsules) != 1:
        raise RuntimeError("expected exactly one module capsule dependency")
    dependency = uses_capsules[0]
    if not isinstance(dependency, dict):
        raise RuntimeError("invalid module capsule dependency")
    dependency["version"] = OVERLAY_VERSION
    module["version"] = OVERLAY_VERSION

    destination_rules = output / "capsules" / "role-boundaries" / RULE_RELATIVE
    destination_rules.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(rules, destination_rules)
    write_json(capsule_path, capsule)
    write_json(module_path, module)

    validate_world(output, args.contracts_root.resolve())
    overlay = {
        "schemaVersion": "0.1",
        "overlayId": "management-progressive-dsl-b-v0",
        "dslLevel": "DSL-B",
        "sourceWorld": str(source),
        "sourceCapsuleVersion": source_capsule_version,
        "sourceModuleVersion": source_module_version,
        "overlayCapsuleVersion": OVERLAY_VERSION,
        "overlayModuleVersion": OVERLAY_VERSION,
        "logicalRulesPath": RULE_RELATIVE,
        "logicalRulesHash": file_hash(destination_rules),
        "sourceWorldModified": False,
    }
    write_json(output / "dsl-b-overlay.json", overlay)
    print("Built and validated management DSL-B overlay")
    print(f"Source capsule: {source_capsule_version}")
    print(f"Overlay capsule: {OVERLAY_VERSION}")
    print(f"Rules hash: {overlay['logicalRulesHash']}")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
