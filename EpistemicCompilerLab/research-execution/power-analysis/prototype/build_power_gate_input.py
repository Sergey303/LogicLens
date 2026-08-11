#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parents[3]
R2_RESULT = ROOT / "R2_SIMULATION_RESULT.json"
DEFAULT_INVENTORY = ROOT / "POWER_GATE_INVENTORY.current.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolution", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence-class", choices=["REAL_LOCAL_GIT_RESOLUTION", "SYNTHETIC_TEST_FIXTURE"], default="REAL_LOCAL_GIT_RESOLUTION")
    args = parser.parse_args()

    resolution = load(args.resolution)
    inventory_doc = load(args.inventory)
    if inventory_doc["work_package_id"] != "WP-006":
        raise RuntimeError("inventory work package drift")
    if inventory_doc["status"] == "NOT_READY":
        inventory = {"status": "NOT_READY", "reason": inventory_doc["reason"]}
    elif inventory_doc["status"] == "READY":
        inventory = {key: value for key, value in inventory_doc.items() if key not in {"schema_version", "work_package_id"}}
    else:
        raise RuntimeError(f"invalid inventory status: {inventory_doc['status']}")

    r2 = load(R2_RESULT)
    payload = {
        "schema_version": "2.0.0",
        "work_package_id": "WP-006",
        "evidence_class": args.evidence_class,
        "r2_power": {
            "result_path": repo_relative(R2_RESULT),
            "result_sha256": sha256_file(R2_RESULT),
            "producer_grid_floor": int(r2["selected_R2_grid_floor"]),
            "type_I_gate_pass": bool(r2["acceptance_conditions"]["type_I_upper_bound_le_0_055"]),
            "joint_power_gate_pass": bool(r2["acceptance_conditions"]["joint_power_lower_bound_ge_0_90"]),
        },
        "dependency_resolution": {
            "path": repo_relative(args.resolution),
            "sha256": sha256_file(args.resolution),
            "all_required_dependencies_accepted": bool(resolution["all_required_dependencies_accepted"]),
        },
        "inventory": inventory,
        "blinded_update": {
            "status": "NOT_USED",
            "required_eligible_n": int(r2["selected_R2_grid_floor"]),
            "report_path": None,
            "report_sha256": None,
        },
        "sealed_access": {"holdout_accessed": False, "replication_accessed": False},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
