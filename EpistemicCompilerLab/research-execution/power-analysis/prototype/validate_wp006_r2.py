#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXECUTION_ROOT = ROOT.parent
REPO_ROOT = ROOT.parents[3]
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    authority = load_json(ROOT / "WP006_STATISTICAL_AUTHORITY.json")
    primary = load_json(ROOT / "PRIMARY_ANALYSIS_CONTRACT.json")
    blinded = load_json(ROOT / "BLINDED_NUISANCE_UPDATE_PROTOCOL.json")
    simulation = load_json(ROOT / "R2_SIMULATION_SCENARIOS.json")
    result = load_json(ROOT / "R2_SIMULATION_RESULT.json")
    sim_evidence = load_json(ROOT / "R2_SIMULATION_EVIDENCE.json")
    gate_evidence = load_json(ROOT / "R2_POWER_GATE_EVIDENCE.json")
    bindings = load_json(ROOT / "POWER_DEPENDENCY_BINDINGS.json")
    power_pointer = load_json(ROOT / "POWER_SCENARIOS.json")
    gate_schema = load_json(ROOT / "POWER_GATE_INPUT.schema.json")

    legacy_pointer = (EXECUTION_ROOT / "statistics" / "ANALYSIS_REGISTRY.yaml").read_text(encoding="utf-8")
    legacy_snapshot = (EXECUTION_ROOT / "statistics" / "historical" / "ANALYSIS_REGISTRY.v1.0.0.yaml").read_text(encoding="utf-8")

    # One statistical authority / historical v1 preserved but inactive.
    require(authority["work_package_id"] == "WP-006", "authority package drift")
    require(authority["normative_package"] == "EpistemicCompilerLab/research-execution/power-analysis", "normative package drift")
    require(authority["legacy_statistics_registry"]["status"] == "SUPERSEDED_HISTORICAL_POINTER_ONLY", "legacy registry still active")
    require("status: SUPERSEDED_HISTORICAL_POINTER" in legacy_pointer, "statistics/ANALYSIS_REGISTRY is not a supersession pointer")
    require("point estimate at least 0.08" in legacy_snapshot, "historical v1 snapshot not preserved")
    require("point estimate at least 0.08" not in legacy_pointer, "rejected hard point-estimate rule leaked into current pointer")
    require(power_pointer["status"] == "SUPERSEDED_ANALYTICAL_POINTER", "old POWER_SCENARIOS still active")
    require(power_pointer["normative_R2_simulation"] == "R2_SIMULATION_SCENARIOS.json", "R2 simulation pointer drift")

    # Primary unit / endpoint / nesting / hypothesis.
    estimand = primary["primary_estimand"]
    nesting = primary["observation_nesting"]
    hypothesis = primary["hypothesis"]
    require(estimand["unit"] == "base_scenario_id", "primary unit is not base_scenario_id")
    require(estimand["outcome"] == "publication_composite_correctness", "primary endpoint drift")
    require(estimand["se_soi_absolute"] == 0.08, "SESOI drift")
    require(estimand["se_soi_role"] == "planning_relevance_alternative_not_hard_observed_point_threshold", "SESOI role drift")
    require(nesting["independent_analysis_unit"] == "base_scenario_id", "nesting unit drift")
    for key in ["paraphrase_is_independent_unit", "repeat_is_independent_unit", "model_seed_is_independent_unit", "training_seed_is_independent_unit", "infrastructure_rerun_is_independent_unit"]:
        require(nesting[key] is False, f"pseudoreplication allowed: {key}")
    require(nesting["declared_runtime_failure"] == "incorrect_before_repeat_and_paraphrase_aggregation", "runtime failure denominator drift")
    require(hypothesis["null"] == "delta = 0" and hypothesis["alpha_two_sided"] == 0.05, "primary superiority hypothesis drift")
    require(hypothesis["hard_point_estimate_at_least_sesoi_retain_rule"] is False, "hard SESOI point gate reintroduced")
    analysis = primary["primary_analysis"]
    require(analysis["cluster_id"] == "source_family_id", "cluster id drift")
    require("CR1" in analysis["variance"], "CR1 variance missing")
    require(analysis["reference_distribution"] == "Student_t_with_df_equal_independent_source_family_clusters_minus_1", "finite-cluster Student-t rule drift")
    require(analysis["minimum_independent_clusters"] == 30, "minimum cluster count drift")

    # Joint confirmatory success, not HOLDOUT-only power.
    sets = primary["confirmatory_sets"]
    require("two-sided cluster-robust p<0.05" in sets["HOLDOUT"]["success"], "HOLDOUT significance rule drift")
    require("point estimate > 0" in sets["REPLICATION"]["success"], "replication direction rule drift")
    require(sets["joint_success"]["target_probability_at_SESOI"] == 0.90, "joint target drift")
    require("joint Monte-Carlo lower-bound gate" in sets["joint_success"]["power_method"], "joint uncertainty gate missing")

    # Frozen R2 generator explicitly carries heterogeneity + scored failures.
    require(simulation["analysis_unit"] == "base_scenario_id", "simulation unit drift")
    require(len(simulation["strata"]["domains"]) == 3 and len(simulation["strata"]["model_profiles"]) == 4, "domain/model heterogeneity incomplete")
    require(simulation["failure_generator"]["scoring"].startswith("all generated failures set"), "failure scoring missing")
    require("never remove" in simulation["failure_generator"]["scoring"], "failure attrition reintroduced")
    require(simulation["clustering"]["reference_distribution"] == "Student t with df=G-1", "simulation finite-cluster reference drift")
    require(simulation["power_search"]["candidate_eligible_n_grid"][:2] == [802, 820], "frozen N grid start drift")
    require(simulation["power_search"]["repetitions_per_candidate"] == 20000, "power MC repetitions drift")
    require(simulation["power_search"]["seed"] == 158062, "power MC seed drift")
    require(simulation["type_I_calibration"]["independent_source_family_clusters"] == 30, "Type-I boundary cluster count drift")
    require(simulation["type_I_calibration"]["repetitions"] == 30000, "Type-I repetitions drift")
    require(simulation["type_I_calibration"]["seed"] == 158063, "Type-I seed drift")
    require(simulation["power_search"]["seed_shopping"] is False, "seed shopping allowed")

    # Committed Monte-Carlo result: 802 fails lower-bound gate, 820 passes.
    require(result["analysis_unit"] == "base_scenario_id", "result unit drift")
    require(result["evidence_class"] == "ACCEPTANCE_CANDIDATE", "result is diagnostic only")
    require(result["selected_R2_grid_floor"] == 820, "R2 producer floor drift")
    require(result["power_search"][0]["eligible_n"] == 802 and result["power_search"][0]["joint_lower_bound_gate_pass"] is False, "N=802 must remain failed")
    require(result["power_search"][0]["joint_success_wilson_one_sided_95_lower"] < 0.90, "N=802 lower bound unexpectedly passes")
    require(result["power_search"][1]["eligible_n"] == 820 and result["power_search"][1]["joint_lower_bound_gate_pass"] is True, "N=820 must be first pass")
    require(result["power_search"][1]["joint_success_wilson_one_sided_95_lower"] >= 0.90, "N=820 lower bound below target")
    require(result["type_I_calibration"]["independent_source_family_clusters"] == 30, "result Type-I cluster count drift")
    require(result["type_I_calibration"]["type_I_gate_pass"] is True, "Type-I gate failed")
    require(result["type_I_calibration"]["two_sided_false_positive_wilson_one_sided_95_upper"] <= 0.055, "Type-I upper bound too high")
    require(result["acceptance_conditions"]["final_N_accepted_by_independent_review"] is False, "producer result self-accepts final N")
    for key in ["WP004_exact_arm_binding_accepted", "WP005_scorer_accepted", "WP007_feasibility_accepted", "HOLDOUT_or_REPLICATION_accessed"]:
        require(result["acceptance_conditions"][key] is False, f"premature R2 acceptance/access: {key}")

    # Execution evidence hashes/run and numerical environment are frozen.
    require(sim_evidence["github_actions"]["result"] == "PASS", "R2 simulation execution evidence not PASS")
    require(sim_evidence["result"]["N_802_pass"] is False and sim_evidence["result"]["N_820_pass"] is True, "simulation evidence N decisions drift")
    require(sim_evidence["environment"] == {"runner": "ubuntu-24.04", "python": "3.11.15", "numpy": "2.3.4", "scipy": "1.16.3"}, "numerical environment drift")
    require(HEX64.fullmatch(sim_evidence["github_actions"]["artifact_zip_sha256"]) is not None, "simulation artifact hash invalid")

    # Blinded nuisance update can only maintain/increase N using conservative bounds.
    require(blinded["decision_rule"]["accepted_R2_required_n_is_floor"] is True, "R2 N is not a floor")
    require(blinded["uncertainty_protection"]["favorable_point_estimate_may_reduce_required_n"] is False, "favorable nuisance estimate may lower N")
    require("max(accepted_R2_required_n" in blinded["decision_rule"]["updated_required_n"], "non-decreasing update formula missing")
    require(blinded["decision_rule"]["runtime_failures"].startswith("remain scored incorrect"), "runtime failures converted to attrition")

    # Real dependency gate cannot be satisfied by fixtures/free text.
    require(bindings["status"] == "DEPENDENCIES_PENDING", "upstream bindings should still be pending")
    require(all(dep["status"] == "PENDING" for dep in bindings["dependencies"]), "producer package falsely marks dependency accepted")
    require(all(dep["candidate_sha"] is None and dep["review_commit_sha"] is None and dep["attestation_path"] is None and dep["attestation_sha256"] is None for dep in bindings["dependencies"]), "pending dependency carries fake acceptance material")
    evidence_enum = gate_schema["properties"]["evidence_class"]["enum"]
    require(set(evidence_enum) == {"REAL_LOCAL_GIT_RESOLUTION", "SYNTHETIC_TEST_FIXTURE"}, "gate evidence classes drift")
    require(gate_evidence["real_dependency_resolution"]["gate_result"] == "NOT_EVALUATED_DEPENDENCIES", "real gate prematurely evaluated")
    require(gate_evidence["real_dependency_resolution"]["power_gate_pass"] is False, "real gate prematurely PASS")
    require(gate_evidence["negative_fixture"]["result"] == "KILLED", "fake dependency fixture survived")
    require(gate_evidence["synthetic_positive_logic_fixture"]["gate_result"] == "SYNTHETIC_LOGIC_PASS_ONLY", "synthetic fixture semantics drift")
    require(gate_evidence["synthetic_positive_logic_fixture"]["power_gate_pass"] is False, "synthetic fixture produced real PASS")
    require(HEX64.fullmatch(gate_evidence["github_actions"]["artifact_zip_sha256"]) is not None, "gate artifact hash invalid")

    # Authority remains producer planning only.
    numeric = authority["current_numeric_status"]
    require(numeric["R2_producer_grid_floor"] == 820, "authority R2 floor drift")
    require(numeric["accepted_required_N"] is None, "producer authority self-accepted final N")
    require(authority["confirmatory_access"] == {"HOLDOUT": False, "REPLICATION": False, "GATE_001": False}, "confirmatory access opened")
    require(authority["independence"]["producer_cannot_accept_own_R2_remediation"] is True, "producer independence guard missing")

    print(json.dumps({
        "work_package": "WP-006",
        "r2_contract": "PASS",
        "analysis_unit": "base_scenario_id",
        "producer_R2_grid_floor": 820,
        "N_802_joint_lower": result["power_search"][0]["joint_success_wilson_one_sided_95_lower"],
        "N_820_joint_lower": result["power_search"][1]["joint_success_wilson_one_sided_95_lower"],
        "type_I_upper_30_clusters": result["type_I_calibration"]["two_sided_false_positive_wilson_one_sided_95_upper"],
        "real_power_gate": "NOT_EVALUATED_DEPENDENCIES",
        "final_N_accepted": False,
        "independent_review": "NOT_PERFORMED_BY_THIS_VALIDATOR",
        "holdout_replication_access": "NONE"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
