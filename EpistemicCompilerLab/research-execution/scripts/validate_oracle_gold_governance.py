#!/usr/bin/env python3
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXECUTION_ROOT = HERE.parent
ORACLE = EXECUTION_ROOT / "oracle"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load(name):
    return json.loads((ORACLE / name).read_text(encoding="utf-8"))


def main():
    protocol = load("GOLD_ADJUDICATION_PROTOCOL.json")
    packet = load("ORACLE_PACKET_CONTRACT.json")

    require(protocol["work_package_id"] == "WP-005", "gold protocol work package drift")
    roles = protocol["roles"]
    require(roles["query_adjudicators_per_case"] == 2, "query gold requires two independent adjudicators")
    require(roles["outcome_adjudicators_per_case"] == 2, "outcome gold requires two independent adjudicators")
    require(roles["third_adjudicator_on_disagreement"] == 1, "third adjudicator missing")
    forbidden_roles = set(roles["forbidden_roles"])
    require({
        "Path_A_implementer_for_same_candidate",
        "Path_B_implementer_for_same_candidate",
        "B_scorer_implementer_for_same_candidate",
        "model_output_analyst_for_same_candidate",
        "teacher_target_generator_for_same_candidate",
    } <= forbidden_roles, "gold adjudicator conflict-of-interest list incomplete")

    query = protocol["query_adjudication"]
    outcome = protocol["outcome_adjudication"]
    for forbidden in ["Path_A_output", "Path_B_output", "student_or_teacher_output", "model_metrics"]:
        require(forbidden in query["forbidden_inputs"], f"query adjudicator can see forbidden input: {forbidden}")
    for forbidden in ["Path_A_output", "Path_B_output", "production_expected_frame", "student_or_teacher_output", "model_metrics", "post_model_error_analysis"]:
        require(forbidden in outcome["forbidden_inputs"], f"outcome adjudicator can see forbidden input: {forbidden}")
    require(outcome["manual_derivation_required"] is True, "outcome gold manual derivation not required")
    require(query["unresolved_disagreement"] == "case_not_eligible_for_freeze", "query disagreement must fail closed")
    require(outcome["unresolved_disagreement"] == "case_not_eligible_for_freeze", "outcome disagreement must fail closed")

    required_outcome_fields = {
        "expected_status",
        "expected_action",
        "expected_conclusion",
        "expected_warnings",
        "expected_positive_evidence_roots",
        "expected_negative_evidence_roots",
        "expected_provenance",
        "expected_proof_normal_form",
        "policy_id",
        "semantic_version",
        "adjudicator_identities",
        "independent_derivation_records",
        "third_adjudication_if_needed",
        "source_locators",
        "reason_code",
    }
    require(required_outcome_fields <= set(outcome["recorded_output"]), "outcome gold recorded fields incomplete")

    freeze = protocol["freeze_order"]
    expected_order = [
        "semantic_spec_registry_policy_hashes_frozen",
        "source_rule_query_packet_hashes_frozen",
        "query_adjudicators_complete_blind_decisions",
        "query_disagreements_adjudicated",
        "query_adjudication_registry_hash_frozen",
        "outcome_adjudicators_complete_blind_manual_derivations",
        "outcome_disagreements_adjudicated",
        "outcome_gold_registry_hash_frozen",
        "scorer_source_and_hash_frozen",
        "first_scored_model_output_may_exist",
    ]
    require(freeze == expected_order, "gold freeze order drift")

    governance = protocol["post_model_governance"]
    require(governance["in_place_query_alternative_addition"] == "prohibited", "post-model query alternative expansion allowed")
    require(governance["in_place_outcome_alternative_addition"] == "prohibited", "post-model outcome alternative expansion allowed")
    require(governance["gold_repair_from_model_behavior"] == "prohibited", "post-model gold repair allowed")
    require("current_confirmatory_eligibility_invalidated" in governance["new_legitimate_ambiguity"], "new ambiguity must invalidate current confirmatory version")

    components = packet["components"]
    require(packet["gold_adjudication_protocol"] == "GOLD_ADJUDICATION_PROTOCOL.json", "packet does not bind gold protocol")
    oracle = components["b_oracle_input_packet"]
    require("outcome_gold_registry" not in oracle["allowed"], "B-oracle may access outcome gold")
    required_oracle_forbidden = {
        "expected_status",
        "expected_action",
        "expected_conclusion",
        "expected_warnings",
        "expected_positive_evidence_roots",
        "expected_negative_evidence_roots",
        "expected_provenance",
        "expected_proof_normal_form",
        "expected_frame",
        "student_response",
        "production_frame",
        "production_oracle_output",
        "model_metrics",
    }
    require(required_oracle_forbidden <= set(oracle["forbidden"]), "B-oracle forbidden gold/model fields incomplete")

    query_registry = components["query_adjudication_registry"]
    outcome_registry = components["outcome_gold_registry"]
    require(query_registry["freeze_before_first_model_output"] is True, "query registry not pre-model frozen")
    require(outcome_registry["freeze_before_first_model_output"] is True, "outcome registry not pre-model frozen")
    require(outcome_registry["visible_to_b_oracle_during_computation"] is False, "outcome gold visible during B-oracle computation")
    require(required_outcome_fields <= set(outcome_registry["allowed_fields"]), "packet outcome gold fields disagree with gold protocol")

    scorer = components["b_scorer_packet"]
    order = scorer["available_only_after"]
    require(order == [
        "b_oracle_output_hash_frozen",
        "query_adjudication_registry_hash_frozen",
        "outcome_gold_registry_hash_frozen",
        "scorer_hash_frozen",
    ], "B-scorer activation order drift")

    packet_governance = packet["post_model_governance"]
    require(packet_governance["acceptable_alternative_addition_after_first_model_output"] == "prohibited", "packet permits post-model alternative addition")
    require(packet_governance["outcome_gold_edit_after_first_model_output"] == "prohibited", "packet permits post-model outcome gold edit")

    print(json.dumps({
        "work_package": "WP-005",
        "gold_governance": "PASS",
        "query_adjudicators_per_case": 2,
        "outcome_adjudicators_per_case": 2,
        "outcome_gold_visible_to_B_oracle": False,
        "post_model_gold_repair": "PROHIBITED",
        "independent_review": "NOT_PERFORMED_BY_THIS_VALIDATOR",
        "gate_001": "NOT_APPROVED_BY_THIS_VALIDATOR"
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"WP-005 gold-governance validation failed: {exc}", file=sys.stderr)
        raise
