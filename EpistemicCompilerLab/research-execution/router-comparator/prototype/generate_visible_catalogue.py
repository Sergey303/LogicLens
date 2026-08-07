from __future__ import annotations
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
REGISTRY = PACKAGE / "ROUTING_CAPABILITY_REGISTRY.yaml"
IO_SCHEMAS = PACKAGE / "CAPABILITY_IO_SCHEMAS.json"
OUT = ROOT / "generated"


def resolve_schema_ref(ref: str, schemas: dict) -> dict:
    prefix = "CAPABILITY_IO_SCHEMAS.json#/capabilities/"
    if not ref.startswith(prefix):
        raise ValueError(f"unsupported schema ref: {ref}")
    tail = ref[len(prefix):]
    capability_id, kind = tail.rsplit("/", 1)
    return schemas["capabilities"][capability_id][kind]


def build(surface: str) -> bytes:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    schemas = json.loads(IO_SCHEMAS.read_text(encoding="utf-8"))
    key = "neutral_surface" if surface == "neutral" else "schema_adapted_dev_surface"

    payload = {
        "schema_version": "1.1.0",
        "surface": surface,
        "capabilities": [
            {
                "handle": item["handle"],
                "kind": item["kind"],
                "label": item[key]["label"],
                "description": item[key]["description"],
                "input_schema": resolve_schema_ref(item["input_schema_ref"], schemas),
                "result_schema": resolve_schema_ref(item["result_schema_ref"], schemas),
                "provenance_required": item["provenance_required"],
                "side_effects": item["side_effects"],
                "tool_budget": item["tool_budget"],
                "failure_semantics": item["failure_semantics"],
            }
            for item in registry["capabilities"]
        ],
    }
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for surface in ("neutral", "adapted"):
        path = OUT / f"qwen-catalogue.{surface}.json"
        path.write_bytes(build(surface))
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
