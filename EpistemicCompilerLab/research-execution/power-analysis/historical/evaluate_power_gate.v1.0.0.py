#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTO = ROOT / "prototype"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_shape(data):
    require(data.get("schema_version") == "1.0.0", "gate input schema version drift")
    require(set(data) == {"schema_version", "wp004_arm_binding", "wp005_scorer", "inventory", "nuisance", "evidence", "sealed_access"}, "gate input top-level fields drift")
    binding = data["wp004_arm_binding"]
    require(binding["treatment_arm_id"].strip(), "treatment arm ID missing")
    require(binding["control_arm_id"].strip(), "control arm ID missing")
    require(binding["treatment_arm_id"] != binding["control_arm_id"], "treatment/control arm IDs must differ")
    require(data["wp005_scorer"]["semantic_version"] == "wp005.semantic.v1", "WP-005 semantic version drift")
    inv = data["inventory"]
    require(isinstance(inv["eligible_paired_n"], int) and inv["eligible_paired_n"] >= 1, "invalid eligible paired N")
    require(isinstance(inv["independent_source_family_clusters"], int) and inv["independent_source_family_clusters"] >= 1, "invalid cluster count")
    nuisance = data["nuisance"]
    require(nuisance["source"] in {"frozen_primary_planning", "single_blinded_nuisance_update"}, "invalid nuisance source")
    require(0.08 <= nuisance["discordance_q"] <= 1, "discordance q outside valid range")
    require(nuisance["mean_cluster_size"] >= 1, "mean cluster size < 1")
    require(0 <= nuisance["icc"] < 1, "ICC outside [0,1)")
    require(0 <= nuisance["attrition"] < 1, "attrition outside [0,1)")
    sealed = data["sealed_access"]
    require(sealed == {
        "holdout_accessed": False,
        "replication_accessed": False,
        "directional_confirmatory_effect_seen_by_power_analyst": False,
    }, "power gate cannot run after sealed/directional effect access")
    for group, keys in [
        (binding, ["contract_sha256"]),
        (data["wp005_scorer"], ["scorer_sha256"]),
        (inv, ["benchmark_manifest_sha256", "cluster_size_summary_sha256", "attrition_ledger_sha256"]),
        (nuisance, ["report_sha256"]),
        (data["evidence"], ["calculator_sha256", "validator_sha256", "power_protocol_sha256"]),
    ]:
        for key in keys:
            require(isinstance(group[key], str) and len(group[key]) == 64 and all(c in "0123456789abcdef" for c in group[key]), f"invalid SHA-256 field {key}")
    for group, keys in [
        (binding, ["independent_review_ref"]),
        (data["wp005_scorer"], ["independent_review_ref"]),
        (data["evidence"], ["independent_statistical_review_ref"]),
    ]:
        for key in keys:
            require(isinstance(group[key], str) and group[key].strip(), f"missing review reference {key}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate WP-006 confirmatory power gate without reading outcomes")
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    validate_shape(data)

    contract = json.loads((ROOT / "PRIMARY_ANALYSIS_CONTRACT.json").read_text(encoding="utf-8"))
    scenarios = json.loads((ROOT / "POWER_SCENARIOS.json").read_text(encoding="utf-8"))
    calc = load_module("wp006_calculate_power_gate", PROTO / "calculate_power.py")

    require(contract["primary_estimand"]["se_soi_absolute"] == 0.08, "SESOI drift")
    require(contract["hypothesis"]["alpha_two_sided"] == 0.05, "alpha drift")
    require(contract["hypothesis"]["target_power_at_sesoi"] == 0.90, "target power drift")
    require(contract["multiplicity"]["primary_confirmatory_contrasts"] == 1, "primary contrast count drift")

    nuisance = data["nuisance"]
    if nuisance["source"] == "frozen_primary_planning":
        frozen = scenarios["primary_planning"]
        require(nuisance["discordance_q"] == frozen["discordance_q"], "frozen nuisance q drift")
        require(nuisance["mean_cluster_size"] == frozen["mean_cluster_size"], "frozen nuisance cluster size drift")
        require(nuisance["icc"] == frozen["icc"], "frozen nuisance ICC drift")
        require(nuisance["attrition"] == frozen["attrition"], "frozen nuisance attrition drift")

    required_n = calc.minimum_n(
        0.08,
        nuisance["discordance_q"],
        nuisance["mean_cluster_size"],
        nuisance["icc"],
        nuisance["attrition"],
        0.05,
        0.90,
    )
    eligible_n = data["inventory"]["eligible_paired_n"]
    clusters = data["inventory"]["independent_source_family_clusters"]
    achieved_planning_power = calc.power_for_n(
        eligible_n,
        0.08,
        nuisance["discordance_q"],
        nuisance["mean_cluster_size"],
        nuisance["icc"],
        nuisance["attrition"],
        0.05,
    )

    n_pass = eligible_n >= required_n and achieved_planning_power >= 0.90
    cluster_pass = clusters >= 30
    decision = "POWER_GATE_PASS" if n_pass and cluster_pass else "POWER_GATE_FAIL"

    output = {
        "schema_version": "1.0.0",
        "work_package_id": "WP-006",
        "decision": decision,
        "primary_sesoi": 0.08,
        "alpha_two_sided": 0.05,
        "target_power": 0.90,
        "nuisance_source": nuisance["source"],
        "required_eligible_n": required_n,
        "available_eligible_n": eligible_n,
        "planning_power_at_available_n": achieved_planning_power,
        "n_gate_pass": n_pass,
        "minimum_independent_clusters": 30,
        "available_independent_clusters": clusters,
        "cluster_gate_pass": cluster_pass,
        "input_sha256": sha256_file(args.input),
        "holdout_accessed": False,
        "replication_accessed": False,
        "directional_effect_used": False,
    }
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"WP-006 power gate evaluation failed: {exc}", file=sys.stderr)
        raise
