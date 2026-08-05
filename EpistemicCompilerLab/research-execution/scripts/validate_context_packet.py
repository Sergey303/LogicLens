#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import yaml

PACKET = ["TASK.md", "REQUIRED_READING.md", "INPUT_MANIFEST.json", "ALLOWED_PATHS.txt", "FORBIDDEN_PATHS.txt", "ACCEPTANCE.yaml", "HANDOFF_SCHEMA.json"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", required=True)
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[3]
    research = repo / "EpistemicCompilerLab" / "research-execution"
    packet = research / "context-packets" / args.package
    findings = []
    for name in PACKET:
        if not (packet / name).is_file():
            findings.append(f"missing:{name}")
    if findings:
        print(json.dumps({"status": "FAIL", "findings": findings}, indent=2))
        return 1
    manifest = json.loads((packet / "INPUT_MANIFEST.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = repo / entry["path"]
        if not path.is_file():
            findings.append(f"input_missing:{entry['path']}")
        elif sha(path) != entry["sha256"]:
            findings.append(f"input_hash:{entry['path']}")
    acceptance = yaml.safe_load((packet / "ACCEPTANCE.yaml").read_text(encoding="utf-8"))
    if acceptance["work_package_id"] != args.package:
        findings.append("acceptance_package_mismatch")
    for command in acceptance["command_contracts"]:
        cwd = repo / command["working_directory"]
        if not cwd.is_dir():
            findings.append(f"cwd_missing:{command['working_directory']}")
        argv = command["argv"]
        if len(argv) > 1 and argv[1].endswith(".py") and not (cwd / argv[1]).is_file():
            findings.append(f"script_missing:{argv[1]}")
    print(json.dumps({"status": "FAIL" if findings else "PASS", "package": args.package, "findings": findings}, indent=2))
    return 1 if findings else 0

if __name__ == "__main__":
    raise SystemExit(main())
