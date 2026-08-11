#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EXEC = ROOT.parent
CANONICAL = "scenario_level_exact_epistemic_contract_accuracy"
LEGACY = "publication_composite_correctness"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> int:
    endpoint = load_json(ROOT / "ENDPOINT_IDENTITY_CONTRACT.json")
    authority = load_json(ROOT / "WP006_STATISTICAL_AUTHORITY.json")
    primary = load_json(ROOT / "PRIMARY_ANALYSIS_CONTRACT.json")
    blinded = load_json(ROOT / "BLINDED_NUISANCE_UPDATE_PROTOCOL.json")
    r2_scenarios = load_json(ROOT / "R2_SIMULATION_SCENARIOS.json")
    r2_result = load_json(ROOT / "R2_SIMULATION_RESULT.json")
    r2_evidence = load_json(ROOT / "R2_SIMULATION_EVIDENCE.json")
    wp002 = load_yaml(EXEC / "CLAIM_EVIDENCE_MATRIX.yaml")
    wp004 = load_yaml(EXEC / "ESTIMANDS.yaml")
    wp005_text = (EXEC / "oracle" / "SEMANTIC_SPEC.md").read_text(encoding="utf-8")
    task_text = (EXEC / "context-packets" / "WP-006" / "TASK.md").read_text(encoding="utf-8")
    sesoi_text = (ROOT / "SESOI_UTILITY_CONTRACT.md").read_text(encoding="utf-8")

    # Endpoint identity contract itself.
    require(endpoint["work_package_id"] == "WP-006", "endpoint contract package drift")
    require(endpoint["canonical_endpoint_id"] == CANONICAL, "canonical endpoint drift")
    require(LEGACY in endpoint["legacy_aliases"], "legacy alias missing")
    require(endpoint["legacy_aliases"][LEGACY]["may_appear_as_primary_endpoint_id_after_this_contract"] is False, "legacy alias may still act as primary ID")
    scoring = endpoint["scoring_function"]
    require(scoring["repeat_aggregation"]["mandatory_repeats_per_paraphrase"] == 3, "repeat count drift")
    require(scoring["repeat_aggregation"]["rule"] == "at_least_2_of_3_response_level_publication_composites_are_true", "repeat aggregation drift")
    require(scoring["paraphrase_aggregation"]["mandatory_paraphrases_per_base_scenario_id"] == 2, "paraphrase count drift")
    require(scoring["paraphrase_aggregation"]["rule"] == "all_2_mandatory_paraphrases_pass_repeat_aggregation", "paraphrase aggregation drift")
    event = scoring["scenario_level_binary_event"]
    require(event["id"] == CANONICAL and event["unit"] == "base_scenario_id", "scenario event identity drift")
    require("runtime/model failures remain incorrect" in event["denominator"], "runtime failure denominator drift")
    non_change = endpoint["statistical_non_change"]
    require(non_change["R2_SIMULATION_SCENARIOS_json_bytes_must_remain_unchanged_for_this_remediation"] is True, "R2 scenario mutation allowed")
    require(non_change["R2_SIMULATION_RESULT_json_bytes_must_remain_unchanged_for_this_remediation"] is True, "R2 result mutation allowed")
    require(non_change["R2_SIMULATION_EVIDENCE_json_bytes_must_remain_unchanged_for_this_remediation"] is True, "R2 evidence mutation allowed")
    require(non_change["producer_R2_grid_floor"] == 820, "R2 producer floor drift in endpoint contract")

    # Active WP-006 authority now uses the exact flagship ID.
    require(authority["endpoint_identity_contract"] == "ENDPOINT_IDENTITY_CONTRACT.json", "authority endpoint contract link missing")
    require(authority["primary"]["endpoint"] == CANONICAL, "WP-006 authority primary endpoint not normalized")
    require(authority["primary"]["legacy_response_composite_alias"] == LEGACY, "authority legacy alias drift")
    require(authority["current_numeric_status"]["R2_producer_grid_floor"] == 820, "authority R2 floor changed")
    require(authority["current_numeric_status"]["accepted_required_N"] is None, "final N prematurely accepted")
    require(authority["confirmatory_access"] == {"HOLDOUT": False, "REPLICATION": False, "GATE_001": False}, "confirmatory access opened")

    estimand = primary["primary_estimand"]
    nesting = primary["observation_nesting"]
    require(estimand["outcome"] == CANONICAL, "primary analysis endpoint not canonical")
    require(estimand["legacy_response_composite_alias"] == LEGACY, "primary analysis legacy alias drift")
    require(estimand["unit"] == "base_scenario_id", "primary unit drift")
    require(nesting["mandatory_paraphrases_per_base_scenario"] == 2, "primary contract paraphrase count drift")
    require(nesting["repeats_per_paraphrase"] == 3, "primary contract repeat count drift")
    require(nesting["repeat_aggregation"] == "at_least_2_of_3_response_level_publication_composites_correct", "primary contract repeat aggregation drift")
    require(CANONICAL in nesting["scenario_aggregation"], "primary contract scenario aggregation does not bind canonical endpoint")
    require(nesting["declared_runtime_failure"] == "incorrect_before_repeat_and_paraphrase_aggregation", "primary runtime-failure treatment drift")
    require(primary["publication_composite"]["role"] == "response_level_component_of_the_canonical_scenario_endpoint", "publication composite still masquerades as primary endpoint")

    immutable = blinded["immutable_parameters"]
    require(immutable["primary_outcome"] == CANONICAL, "blinded-update primary endpoint drift")
    require(immutable["legacy_response_composite_alias"] == LEGACY, "blinded-update legacy alias drift")
    require(blinded["decision_rule"]["runtime_failures"].startswith("remain scored incorrect"), "blinded update changes runtime-failure denominator")

    # Cross-package exact identity.
    require(wp002["primary_design"]["endpoint"] == CANONICAL, "WP-002 endpoint identity drift")
    require(wp002["primary_design"]["unit_of_analysis"] == "base_scenario_id", "WP-002 unit drift")
    require(wp004["primary"]["endpoint"] == CANONICAL, "WP-004 endpoint identity drift")
    require(wp004["primary"]["unit"] == "base_scenario_id", "WP-004 unit drift")
    require("The composite publication correctness endpoint is true only when every publication-critical applicable field is true." in wp005_text, "WP-005 response composite definition missing")
    require("Malformed output is incorrect." in wp005_text, "WP-005 malformed-output rule missing")
    require("infrastructure failure and cannot be silently excluded or imputed as correct" in wp005_text, "WP-005 failure denominator rule missing")

    # Human-readable active contracts must use canonical ID as primary.
    require(f"**`{CANONICAL}`**" in task_text, "WP-006 TASK does not name canonical endpoint")
    require(f"**`{CANONICAL}`**" in sesoi_text, "SESOI contract does not name canonical endpoint")

    # R2 numerical evidence is reused only as the exact same binary-event planning result.
    require(r2_scenarios["analysis_unit"] == "base_scenario_id", "R2 scenario unit drift")
    require(r2_result["analysis_unit"] == "base_scenario_id", "R2 result unit drift")
    require(r2_result["selected_R2_grid_floor"] == 820, "R2 result floor drift")
    require(r2_result["power_search"][0]["eligible_n"] == 802 and r2_result["power_search"][0]["joint_lower_bound_gate_pass"] is False, "N=802 decision drift")
    require(r2_result["power_search"][1]["eligible_n"] == 820 and r2_result["power_search"][1]["joint_lower_bound_gate_pass"] is True, "N=820 decision drift")
    require(r2_result["acceptance_conditions"]["final_N_accepted_by_independent_review"] is False, "R2 result self-accepts final N")
    require(r2_evidence["result"]["N_802_pass"] is False and r2_evidence["result"]["N_820_pass"] is True, "R2 evidence decision drift")

    # No accidental second current primary ID outside explicitly historical/legacy contexts.
    active_strings = {
        "authority": json.dumps(authority, sort_keys=True),
        "primary": json.dumps(primary, sort_keys=True),
        "blinded": json.dumps(blinded, sort_keys=True),
    }
    for name, text in active_strings.items():
        require(CANONICAL in text, f"{name} missing canonical endpoint")

    print(json.dumps({
        "schema_version": "1.0.0",
        "work_package_id": "WP-006",
        "linear_issue": "ENG-158",
        "endpoint_identity": "PASS",
        "canonical_endpoint_id": CANONICAL,
        "legacy_response_composite_alias": LEGACY,
        "cross_package_exact_identifier_match": True,
        "response_scorer_changed": False,
        "repeat_paraphrase_aggregation_changed": False,
        "denominator_or_failure_treatment_changed": False,
        "R2_numeric_design_changed": False,
        "producer_R2_grid_floor": 820,
        "final_N_accepted": False,
        "independent_statistical_review": "NOT_PERFORMED_BY_THIS_VALIDATOR",
        "holdout_replication_access": "NONE",
        "gate_001": "NOT_APPROVED"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
