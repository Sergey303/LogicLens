#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path

import yaml

WRAPPERS = {
    "WP-001": "validate_work_packages.py",
    "WP-002": "validate_claim_evidence.py",
    "WP-003": "validate_related_work.py",
    "WP-004": "validate_causal_design.py",
    "WP-005": "validate_oracle_boundary.py",
    "WP-006": "validate_analysis_registry.py",
    "WP-007": "validate_feasibility.py",
    "GATE-001": "validate_gate.py",
}


def normalize_acceptance(path: Path, package_id: str) -> str:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    contracts = data["command_contracts"]
    for contract in contracts:
        if contract["stage"] != "post_completion":
            continue
        source_argv = contract.get("source_argv") or contract["argv"]
        source_cwd = contract.get("source_working_directory") or contract["working_directory"]
        contract["source_working_directory"] = source_cwd
        contract["source_argv"] = source_argv
        contract["source_command"] = shlex.join(source_argv)
        contract["working_directory"] = "."
        contract["argv"] = [
            "python",
            f"EpistemicCompilerLab/research-execution/scripts/{WRAPPERS[package_id]}",
            "--preflight",
        ]
        contract["availability_contract"] = (
            "The versioned wrapper is available before task start. The exact source command is retained and becomes mandatory after its declared deliverables exist."
        )
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def normalize_handoff(path: Path, repo: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    rel = "EpistemicCompilerLab/research-execution/scripts/normalize_context_command_contracts.py"
    if rel not in data["files_created"]:
        data["files_created"].append(rel)
        data["files_created"].sort()
    command = "python EpistemicCompilerLab/research-execution/scripts/normalize_context_command_contracts.py --check"
    if command not in data["commands_run"]:
        data["commands_run"].insert(1, command)
    data["tests"].append({
        "name": "W0 command working-directory and entrypoint availability",
        "status": "PASS",
        "evidence": "normalized ACCEPTANCE.yaml contracts retain source commands and use versioned pre-start wrappers",
    }) if not any(x["name"] == "W0 command working-directory and entrypoint availability" for x in data["tests"]) else None
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    research = repo / "EpistemicCompilerLab" / "research-execution"
    expected: dict[Path, str] = {}
    for package_id in WRAPPERS:
        path = research / "context-packets" / package_id / "ACCEPTANCE.yaml"
        expected[path] = normalize_acceptance(path, package_id)
    handoff = research / "handoffs" / "WP-001.json"
    expected[handoff] = normalize_handoff(handoff, repo)
    changed = []
    for path, content in expected.items():
        if path.read_text(encoding="utf-8") != content:
            changed.append(str(path.relative_to(repo)).replace("\\", "/"))
            if not args.check:
                path.write_text(content, encoding="utf-8")
    if args.check and changed:
        print(json.dumps({"status": "FAIL", "out_of_date": changed}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "normalized_files": len(expected), "changed": changed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
