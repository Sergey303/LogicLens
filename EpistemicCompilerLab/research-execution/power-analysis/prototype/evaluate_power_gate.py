#!/usr/bin/env python3
"""Evaluate the WP-006 R2 power gate without reading scientific outcomes.

The evaluator is deliberately fail-closed. A real POWER_GATE_PASS requires:
- the frozen R2 Monte-Carlo candidate and its hash;
- locally resolved independent acceptance for WP-004, WP-005 and WP-007;
- a frozen READY inventory whose dependency-artifact hashes match the resolved attestations;
- sufficient eligible base_scenario_id count and independent source-family clusters;
- no HOLDOUT or REPLICATION access.

Synthetic fixtures can test gate logic but can never produce a real PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parents[2]
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_DEPENDENCIES = {
    "WP004_CAUSAL_ARMS": "wp004_arm_binding_artifact_sha256",
    "WP005_ORACLE_SCORER": "wp005_scorer_artifact_sha256",
    "WP007_FEASIBILITY": "wp007_feasibility_artifact_sha256",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_repo_path(value: str) -> Path:
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise RuntimeError(f"path escapes repository: {value}") from exc
    return path


def validate_input(data: dict[str, Any]) -> None:
    expected_top = {
        "schema_version", "work_package_id", "evidence_class", "r2_power",
        "dependency_resolution", "inventory", "blinded_update", "sealed_access",
    }
    require(set(data) == expected_top, "gate input top-level fields drift")
    require(data["schema_version"] == "2.0.0", "gate input schema version drift")
    require(data["work_package_id"] == "WP-006", "gate work package drift")
    require(data["evidence_class"] in {"REAL_LOCAL_GIT_RESOLUTION", "SYNTHETIC_TEST_FIXTURE"}, "invalid evidence class")

    r2 = data["r2_power"]
    require(set(r2) == {"result_path", "result_sha256", "producer_grid_floor", "type_I_gate_pass", "joint_power_gate_pass"}, "R2 power fields drift")
    require(isinstance(r2["result_path"], str) and r2["result_path"], "R2 result path missing")
    require(isinstance(r2["result_sha256"], str) and HEX64.fullmatch(r2["result_sha256"]) is not None, "invalid R2 result hash")
    require(isinstance(r2["producer_grid_floor"], int) and r2["producer_grid_floor"] >= 820, "R2 producer floor below accepted producer candidate")
    require(r2["type_I_gate_pass"] is True, "R2 Type-I gate is not PASS")
    require(r2["joint_power_gate_pass"] is True, "R2 joint-power lower-bound gate is not PASS")

    dep = data["dependency_resolution"]
    require(set(dep) == {"path", "sha256", "all_required_dependencies_accepted"}, "dependency-resolution fields drift")
    require(isinstance(dep["path"], str) and dep["path"], "dependency-resolution path missing")
    require(isinstance(dep["sha256"], str) and HEX64.fullmatch(dep["sha256"]) is not None, "invalid dependency-resolution hash")
    require(isinstance(dep["all_required_dependencies_accepted"], bool), "dependency acceptance flag is not boolean")

    inv = data["inventory"]
    require(inv.get("status") in {"NOT_READY", "READY"}, "invalid inventory status")
    if inv["status"] == "NOT_READY":
        require(set(inv) == {"status", "reason"}, "NOT_READY inventory fields drift")
        require(isinstance(inv["reason"], str) and inv["reason"].strip(), "NOT_READY inventory reason missing")
    else:
        expected_inventory = {
            "status", "eligible_base_scenario_ids", "independent_source_family_clusters",
            "eligible_inventory_sha256", "primary_treatment_arm_id", "primary_control_arm_id",
            "wp004_arm_binding_artifact_sha256", "wp005_scorer_artifact_sha256",
            "wp007_feasibility_artifact_sha256", "model_profile_assignment_frozen",
            "source_family_grouping_frozen",
        }
        require(set(inv) == expected_inventory, "READY inventory fields drift")
        require(isinstance(inv["eligible_base_scenario_ids"], int) and inv["eligible_base_scenario_ids"] >= 1, "invalid eligible base_scenario_id count")
        require(isinstance(inv["independent_source_family_clusters"], int) and inv["independent_source_family_clusters"] >= 1, "invalid source-family cluster count")
        require(inv["primary_treatment_arm_id"] != inv["primary_control_arm_id"], "primary treatment/control arm IDs must differ")
        require(inv["model_profile_assignment_frozen"] is True, "model-profile assignment is not frozen")
        require(inv["source_family_grouping_frozen"] is True, "source-family grouping is not frozen")
        for key in [
            "eligible_inventory_sha256", "wp004_arm_binding_artifact_sha256",
            "wp005_scorer_artifact_sha256", "wp007_feasibility_artifact_sha256",
        ]:
            require(isinstance(inv[key], str) and HEX64.fullmatch(inv[key]) is not None, f"invalid inventory SHA-256: {key}")

    blinded = data["blinded_update"]
    require(set(blinded) == {"status", "required_eligible_n", "report_path", "report_sha256"}, "blinded-update fields drift")
    require(blinded["status"] in {"NOT_USED", "USED"}, "invalid blinded-update status")
    require(isinstance(blinded["required_eligible_n"], int) and blinded["required_eligible_n"] >= r2["producer_grid_floor"], "blinded update lowered required N")
    if blinded["status"] == "NOT_USED":
        require(blinded["required_eligible_n"] == r2["producer_grid_floor"], "NOT_USED blinded update changed N")
        require(blinded["report_path"] is None and blinded["report_sha256"] is None, "NOT_USED blinded update carries a report")
    else:
        require(isinstance(blinded["report_path"], str) and blinded["report_path"], "USED blinded update missing report path")
        require(isinstance(blinded["report_sha256"], str) and HEX64.fullmatch(blinded["report_sha256"]) is not None, "USED blinded update missing report hash")

    require(data["sealed_access"] == {"holdout_accessed": False, "replication_accessed": False}, "sealed split access detected")


def verify_r2_result(data: dict[str, Any]) -> dict[str, Any]:
    declared = data["r2_power"]
    path = resolve_repo_path(declared["result_path"])
    require(path.is_file(), "R2 result file missing")
    require(sha256_file(path) == declared["result_sha256"], "R2 result hash mismatch")
    result = load_json(path)
    require(result["work_package_id"] == "WP-006", "R2 result package drift")
    require(result["analysis_unit"] == "base_scenario_id", "R2 result analysis unit drift")
    require(result["selected_R2_grid_floor"] == declared["producer_grid_floor"], "R2 floor mismatch")
    require(result["acceptance_conditions"]["type_I_upper_bound_le_0_055"] is True, "committed R2 Type-I condition failed")
    require(result["acceptance_conditions"]["joint_power_lower_bound_ge_0_90"] is True, "committed R2 joint-power condition failed")
    require(result["acceptance_conditions"]["final_N_accepted_by_independent_review"] is False, "producer R2 result self-accepts final N")
    require(result["acceptance_conditions"]["HOLDOUT_or_REPLICATION_accessed"] is False, "R2 result indicates sealed access")
    return result


def verify_dependency_resolution(data: dict[str, Any]) -> dict[str, Any]:
    declared = data["dependency_resolution"]
    path = resolve_repo_path(declared["path"])
    require(path.is_file(), "dependency-resolution file missing")
    require(sha256_file(path) == declared["sha256"], "dependency-resolution hash mismatch")
    resolution = load_json(path)
    require(resolution["work_package_id"] == "WP-006", "dependency-resolution package drift")
    require(resolution["evidence_class"] == data["evidence_class"], "dependency-resolution evidence class mismatch")
    deps = resolution["dependencies"]
    require(isinstance(deps, list) and len(deps) == 3, "dependency-resolution count drift")
    ids = {dep["dependency_id"] for dep in deps}
    require(ids == set(REQUIRED_DEPENDENCIES), "required dependency IDs drift")
    all_accepted_actual = all(dep.get("resolved_status") == "ACCEPTED" for dep in deps)
    require(resolution["all_required_dependencies_accepted"] is all_accepted_actual, "resolution aggregate acceptance flag mismatch")
    require(declared["all_required_dependencies_accepted"] is all_accepted_actual, "gate input dependency acceptance flag mismatch")
    if data["evidence_class"] == "REAL_LOCAL_GIT_RESOLUTION":
        require(resolution.get("fixture_or_free_text_can_satisfy_acceptance") is False, "real resolution permits fixture/free-text acceptance")
    return resolution


def verify_blinded_update(data: dict[str, Any]) -> bool:
    blinded = data["blinded_update"]
    if blinded["status"] == "NOT_USED":
        return True
    path = resolve_repo_path(blinded["report_path"])
    require(path.is_file(), "blinded-update report missing")
    require(sha256_file(path) == blinded["report_sha256"], "blinded-update report hash mismatch")
    report = load_json(path)
    # The current R2 contract does not yet freeze the full report schema. Refuse a
    # real PASS instead of guessing how to interpret a future report.
    require(report.get("work_package_id") == "WP-006", "blinded-update report package drift")
    return False


def artifact_binding_pass(inventory: dict[str, Any], resolution: dict[str, Any]) -> bool:
    if inventory["status"] != "READY":
        return False
    by_id = {dep["dependency_id"]: dep for dep in resolution["dependencies"]}
    for dependency_id, inventory_key in REQUIRED_DEPENDENCIES.items():
        dep = by_id[dependency_id]
        if dep.get("resolved_status") != "ACCEPTED":
            return False
        accepted = dep.get("accepted_artifacts")
        if not isinstance(accepted, list) or not accepted:
            return False
        hashes = {artifact.get("sha256") for artifact in accepted}
        if inventory[inventory_key] not in hashes:
            return False
    return True


def evaluate(data: dict[str, Any], resolution: dict[str, Any], blinded_schema_ready: bool) -> dict[str, Any]:
    r2 = data["r2_power"]
    inventory = data["inventory"]
    required_n = max(r2["producer_grid_floor"], data["blinded_update"]["required_eligible_n"])
    dependencies_ready = resolution["all_required_dependencies_accepted"] is True
    inventory_ready = inventory["status"] == "READY"
    artifact_bindings_ok = artifact_binding_pass(inventory, resolution) if inventory_ready and dependencies_ready else False
    available_n = inventory.get("eligible_base_scenario_ids") if inventory_ready else None
    clusters = inventory.get("independent_source_family_clusters") if inventory_ready else None
    n_gate_pass = bool(inventory_ready and available_n >= required_n)
    cluster_gate_pass = bool(inventory_ready and clusters >= 30)

    if data["evidence_class"] == "SYNTHETIC_TEST_FIXTURE":
        logical_pass = bool(
            dependencies_ready and inventory_ready and artifact_bindings_ok and
            n_gate_pass and cluster_gate_pass and blinded_schema_ready
        )
        status = "SYNTHETIC_LOGIC_PASS_ONLY" if logical_pass else "SYNTHETIC_LOGIC_FAIL"
        power_gate_pass = False
    elif not dependencies_ready:
        status = "NOT_EVALUATED_DEPENDENCIES"
        power_gate_pass = False
    elif not inventory_ready:
        status = "NOT_EVALUATED_INVENTORY"
        power_gate_pass = False
    elif not blinded_schema_ready:
        status = "NOT_EVALUATED_BLINDED_UPDATE"
        power_gate_pass = False
    else:
        power_gate_pass = bool(artifact_bindings_ok and n_gate_pass and cluster_gate_pass)
        status = "POWER_GATE_PASS" if power_gate_pass else "POWER_GATE_FAIL"

    return {
        "schema_version": "2.0.0",
        "work_package_id": "WP-006",
        "status": status,
        "evidence_class": data["evidence_class"],
        "power_gate_pass": power_gate_pass,
        "required_eligible_n": required_n,
        "available_eligible_n": available_n,
        "minimum_independent_source_family_clusters": 30,
        "available_independent_source_family_clusters": clusters,
        "dependencies_ready": dependencies_ready,
        "inventory_ready": inventory_ready,
        "artifact_binding_pass": artifact_bindings_ok,
        "n_gate_pass": n_gate_pass,
        "cluster_gate_pass": cluster_gate_pass,
        "blinded_update_schema_ready": blinded_schema_ready,
        "r2_type_I_gate_pass": r2["type_I_gate_pass"],
        "r2_joint_power_gate_pass": r2["joint_power_gate_pass"],
        "confirmatory_access_authorized": False,
        "gate_001_authorized": False,
        "holdout_accessed": False,
        "replication_accessed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate WP-006 R2 confirmatory power gate")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    data = load_json(args.input)
    validate_input(data)
    verify_r2_result(data)
    resolution = verify_dependency_resolution(data)
    blinded_schema_ready = verify_blinded_update(data)
    result = evaluate(data, resolution, blinded_schema_ready)

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(json.dumps(result, sort_keys=True))

    if args.require_pass and not (
        data["evidence_class"] == "REAL_LOCAL_GIT_RESOLUTION" and
        result["status"] == "POWER_GATE_PASS" and
        result["power_gate_pass"] is True
    ):
        return 3
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"WP-006 R2 power gate evaluation failed: {exc}", file=sys.stderr)
        raise
