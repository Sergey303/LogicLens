#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml


def load(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_dir():
        if not any(path.iterdir()):
            raise ValueError(f"empty directory: {path}")
        return {"directory": str(path)}
    if path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return path.read_text(encoding="utf-8")


def main(package_id: str) -> int:
    ap = argparse.ArgumentParser(description=f"Artifact-level acceptance entrypoint for {package_id}")
    ap.add_argument("--preflight", action="store_true")
    args, unknown = ap.parse_known_args()
    if args.preflight:
        print(json.dumps({"package": package_id, "status": "AVAILABLE", "unknown_args": unknown}))
        return 0
    paths = [Path(x) for x in unknown if not x.startswith("-")]
    existing = [p for p in paths if p.exists()]
    if paths and not existing:
        print(json.dumps({"package": package_id, "status": "FAIL", "reason": "no referenced artifact exists"}))
        return 1
    for path in existing:
        load(path)
    print(json.dumps({"package": package_id, "status": "PASS", "checked": [str(p) for p in existing]}))
    return 0
