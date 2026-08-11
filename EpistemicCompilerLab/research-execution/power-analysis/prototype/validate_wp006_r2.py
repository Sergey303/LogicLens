#!/usr/bin/env python3
"""Compatibility validator for the frozen R2 statistical design after R3 endpoint normalization.

R3 changes only the canonical primary endpoint identifier. The numerical R2
simulation, selected producer floor, Type-I calibration, joint-power result,
dependency gate and sealed-data boundary remain unchanged. Exact endpoint
identity is validated by validate_wp006_r3_endpoint.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTO = ROOT / "prototype"
CANONICAL = "scenario_level_exact_epistemic_contract_accuracy"
LEGACY = "publication_composite_correctness"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> int:
    endpoint_check = subprocess.run(
        [sys.executable, str(PROTO / "validate_wp006_r3_endpoint.py")],
        cwd=ROOT.parents[3],
        text=True,
        capture_output=True,
        check=False,
    )
    if endpoint_check.returncode != 0:
        raise RuntimeError(
            "R3 endpoint identity validator failed:\n"
            f"stdout={endpoint_check.stdout}\nstderr={endpoint_check.stderr}"
        )
    endpoint_result = json.loads(endpoint_check.stdout.strip().splitlines()[-1])
    require(endpoint_result["endpoint_identity"] == "PASS", "R3 endpoint identity not PASS")
    require(endpoint_result["canonical_endpoint_id"] == CANONICAL, "canonical endpoint drift")
    require(endpoint_result["R2_numeric_design_changed"] is False, "endpoint normalization claims R2 numeric change")

    authority = load("WP006_STATISTICAL_AUTHORITY.json")
    primary = load("PRIMARY_ANALYSIS_CONTRACT.json")
    blinded = load("BLINDED_NUISANCE_UPDATE_PROTOCOL.json")
    simulation = load("R2_SIMULATION_SCENARIOS.json")
    result = load("R2_SIMULATION_RESULT.json")
    sim_evidence = load("R2_SIMULATION_EVIDENCE.json")
    gate_evidence = load("R2_POWER_GATE_EVIDENCE.json")
    bindings = load("POWER_DEPENDENCY_BINDINGS.json")
    power_pointer = load("POWER_SCENARIOS.json")

    require(authority["work_package_id"] == "WP-006", "authority package drift")
    require(authority["primary"]["endpoint"] == CANONICAL, "authority primary endpoint drift")
    require(authority["primary"]["legacy_response_composite_alias"] == LEGACY, "authority legacy alias drift")
    require(authority["current_numeric_status"]["R2_producer_grid_floor"] == 820, "R2 producer floor drift")
    require(authority["current_numeric_status"]["accepted_required_N"] is None, "final N prematurely accepted")
    require(authority["confirmatory_access"] == {"HOLDOUT": False, "REPLICATION": False, "GATE_001": False}, "confirmatory access opened")

    estimand = primary["primary_estimand"]
    nesting = primary["observation_nesting"]
    hypothesis = primary["hypothesis"]
    require(estimand["unit"] == "base_scenario_id", "primary unit drift")
    require(estimand["outcome"] == CANONICAL, "primary endpoint not canonical")
    require(estimand["legacy_response_composite_alias"] == LEGACY, "primary legacy alias drift")
    require(estimand["se_soi_absolute"] == 0.08, "SESOI drift")
    require(estimand["se_soi_role"] == "planning_relevance_alternative_not_hard_observed_point_threshold", "SESOI role drift")
    require(nesting["independent_analysis_unit"] == "base_scenario_id", "nesting unit drift")
    require(nesting["mandatory_paraphrases_per_base_scenario"] == 2, "paraphrase count drift")
    require(nesting["repeats_per_paraphrase"] == 3, "repeat count drift")
    for key in ["paraphrase_is_independent_unit", "repeat_is_independent_unit", "model_seed_is_independent_unit", "training_seed_is_independent_unit", "infrastructure_rerun_is_independent_unit"]:
        require(nesting[key] is False, f"pseudoreplication allowed: {key}")
    require(nesting["declared_runtime_failure"] == "incorrect_before_repeat_and_paraphrase_aggregation", "runtime failure denominator drift")
    require(hypothesis["null"] == "delta = 0" and hypothesis["alpha_two_sided"] == 0.05, "hypothesis drift")
    require(hypothesis["target_power_at_sesoi"] == 0.90, "target power drift")
    require(hypothesis["hard_point_estimate_at_least_sesoi_retain_rule"] is False, "hard SESOI point gate reintroduced")
    require(primary["primary_analysis"]["cluster_id"] == "source_family_id", "cluster id drift")
    require(primary["primary_analysis"]["reference_distribution"] == "Student_t_with_df_equal_independent_source_family_clusters_minus_1", "finite-cluster reference drift")
    require(primary["primary_analysis"]["minimum_independent_clusters"] == 30, "minimum clusters drift")

    sets = primary["confirmatory_sets"]
    require("two-sided cluster-robust p<0.05" in sets["HOLDOUT"]["success"], "HOLDOUT success rule drift")
    require("point estimate > 0" in sets["REPLICATION"]["success"], "REPLICATION direction rule drift")
    require(sets["joint_success"]["target_probability_at_SESOI"] == 0.90, "joint success target drift")

    require(blinded["immutable_parameters"]["primary_outcome"] == CANONICAL, "blinded endpoint drift")
    require(blinded["uncertainty_protection"]["favorable_point_estimate_may_reduce_required_n"] is False, "nuisance update may lower N")
    require(blinded["decision_rule"]["accepted_R2_required_n_is_floor"] is True, "R2 floor not preserved")
    require("max(accepted_R2_required_n" in blinded["decision_rule"]["updated_required_n"], "non-decreasing N rule missing")
    require(blinded["decision_rule"]["runtime_failures"].startswith("remain scored incorrect"), "runtime failures converted to attrition")

    # Frozen R2 numerical design/result: no endpoint-name remediation is allowed to change these decisions.
    require(simulation["analysis_unit"] == "base_scenario_id", "R2 simulation unit drift")
    require(len(simulation["strata"]["domains"]) == 3 and len(simulation["strata"]["model_profiles"]) == 4, "R2 heterogeneity design drift")
    require(simulation["power_search"]["candidate_eligible_n_grid"][:2] == [802, 820], "R2 candidate N grid drift")
    require(simulation["power_search"]["repetitions_per_candidate"] == 20000 and simulation["power_search"]["seed"] == 158062, "R2 power MC contract drift")
    require(simulation["type_I_calibration"]["independent_source_family_clusters"] == 30, "R2 Type-I cluster boundary drift")
    require(simulation["type_I_calibration"]["repetitions"] == 30000 and simulation["type_I_calibration"]["seed"] == 158063, "R2 Type-I MC contract drift")
    require(result["analysis_unit"] == "base_scenario_id", "R2 result unit drift")
    require(result["selected_R2_grid_floor"] == 820, "R2 selected floor drift")
    require(result["power_search"][0]["eligible_n"] == 802 and result["power_search"][0]["joint_lower_bound_gate_pass"] is False, "N=802 decision drift")
    require(result["power_search"][1]["eligible_n"] == 820 and result["power_search"][1]["joint_lower_bound_gate_pass"] is True, "N=820 decision drift")
    require(result["power_search"][1]["joint_success_wilson_one_sided_95_lower"] >= 0.90, "N=820 lower-bound drift")
    require(result["type_I_calibration"]["type_I_gate_pass"] is True, "Type-I gate drift")
    require(result["type_I_calibration"]["two_sided_false_positive_wilson_one_sided_95_upper"] <= 0.055, "Type-I upper bound drift")
    require(result["acceptance_conditions"]["final_N_accepted_by_independent_review"] is False, "R2 result self-accepts final N")
    require(result["acceptance_conditions"]["HOLDOUT_or_REPLICATION_accessed"] is False, "sealed access recorded in R2 result")
    require(sim_evidence["github_actions"]["result"] == "PASS", "R2 simulation execution evidence not PASS")
    require(sim_evidence["result"]["N_802_pass"] is False and sim_evidence["result"]["N_820_pass"] is True, "R2 evidence N decisions drift")

    require(power_pointer["status"] == "SUPERSEDED_ANALYTICAL_POINTER", "old analytical power authority became active")
    require(bindings["status"] == "DEPENDENCIES_PENDING", "upstream dependencies prematurely accepted")
    require(all(dep["status"] == "PENDING" for dep in bindings["dependencies"]), "pending dependency drift")
    require(gate_evidence["real_dependency_resolution"]["gate_result"] == "NOT_EVALUATED_DEPENDENCIES", "real power gate prematurely evaluated")
    require(gate_evidence["real_dependency_resolution"]["power_gate_pass"] is False, "real power gate prematurely PASS")
    require(gate_evidence["negative_fixture"]["result"] == "KILLED", "fake dependency fixture survived")
    require(gate_evidence["synthetic_positive_logic_fixture"]["gate_result"] == "SYNTHETIC_LOGIC_PASS_ONLY", "synthetic gate semantics drift")
    require(gate_evidence["synthetic_positive_logic_fixture"]["power_gate_pass"] is False, "synthetic fixture produced real PASS")

    print(json.dumps({
        "work_package": "WP-006",
        "compatibility_contract": "R3_ENDPOINT_NORMALIZED_R2_NUMERIC_DESIGN_UNCHANGED",
        "endpoint_identity": "PASS",
        "canonical_endpoint_id": CANONICAL,
        "analysis_unit": "base_scenario_id",
        "producer_R2_grid_floor": 820,
        "N_802_joint_lower": result["power_search"][0]["joint_success_wilson_one_sided_95_lower"],
        "N_820_joint_lower": result["power_search"][1]["joint_success_wilson_one_sided_95_lower"],
        "type_I_upper_30_clusters": result["type_I_calibration"]["two_sided_false_positive_wilson_one_sided_95_upper"],
        "real_power_gate": "NOT_EVALUATED_DEPENDENCIES",
        "final_N_accepted": False,
        "independent_statistical_review": "NOT_PERFORMED_BY_THIS_VALIDATOR",
        "holdout_replication_access": "NONE"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
