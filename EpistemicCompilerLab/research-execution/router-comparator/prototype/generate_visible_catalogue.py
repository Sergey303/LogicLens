from __future__ import annotations
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
REGISTRY = PACKAGE / "ROUTING_CAPABILITY_REGISTRY.yaml"
OUT = ROOT / "generated"


def build(surface: str) -> bytes:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    key = "neutral_surface" if surface == "neutral" else "schema_adapted_dev_surface"
    payload = {
        "schema_version": "1.0.0",
        "surface": surface,
        "capabilities": [
            {
                "handle": item["handle"],
                "kind": item["kind"],
                "label": item[key]["label"],
                "description": item[key]["description"],
                "input_fields": item["input_fields"],
                "result_contract": item["result_contract"],
                "side_effects": item["side_effects"],
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
