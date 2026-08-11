#!/usr/bin/env python3
"""Fail-closed WP-005 blind-gold/oracle lifecycle governance validator.

This validator is producer-side contract evidence only. It validates one lifecycle
across ACCEPTANCE, machine-readable lifecycle, gold protocol, packet contract and
independence prose, then executes frozen negative regression fixtures in memory.
It does not implement Path B, run the human audit, or approve GATE-001.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXECUTION_ROOT = HERE.parent
ORACLE = EXECUTION_ROOT / "oracle"
PACKET_DIR = EXECUTION_ROOT / "context-packets" / "WP-005"
ACCEPTANCE = PACKET_DIR / "ACCEPTANCE.v1.3.yaml"
BOUNDARY = ORACLE / "INDEPENDENCE_BOUNDARY.md"

EXPECTED_OUTCOME_FIELDS = {
    "case_id",
    "alternative_id",
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
    "disagreement",
    "third_adjudication_if_needed",
    "source_locators",
    "reason_code",
}
EXPECTED_QUERY_FIELDS = {
    "case_id",
    "question_hash",
    "alternative_id",
    "normalized_query",
    "interpretation_requirements",
    "clarification_expected",
    "adjudicator_identities",
    "independent_decisions",
    "disagreement",
    "third_adjudication_if_needed",
    "source_and_registry_evidence",
    "reason_code",
}
EXACT_EVIDENCE_FIELDS = {
    "expected_positive_evidence_roots",
    "expected_negative_evidence_roots",
    "expected_proof_normal_form",
}
LEGACY_GENERIC_FIELDS = {"expected_evidence_roots", "expected_proof_trace"}
B_STAGE = "isolated_B_oracle_computes_without_outcome_gold_mount"
GOLD_FREEZE_STAGE = "outcome_gold_registry_hash_frozen"
CONSISTENCY_STAGE = "B_vs_outcome_gold_consistency_checked"
SCORER_STAGE = "scorer_source_and_hash_frozen"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(name: str) -> dict:
    return json.loads((ORACLE / name).read_text(encoding="utf-8"))


def parse_yaml_top_level_list(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    marker = f"{key}:"
    try:
        start = next(i for i, line in enumerate(lines) if line == marker)
    except StopIteration as exc:
        raise AssertionError(f"acceptance missing top-level {key}") from exc
    values: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("  - "):
            values.append(line[4:].strip())
            continue
        if line.startswith("  ") or not line.strip():
            continue
        break
    require(values, f"acceptance top-level {key} is empty")
    return values


def require_order(values: list[str], before: str, after: str, label: str) -> None:
    require(before in values and after in values, f"{label}: missing lifecycle stage")
    require(values.index(before) < values.index(after), f"{label}: {before} must precede {after}")


def validate_bundle(
    protocol: dict,
    packet: dict,
    lifecycle: dict,
    acceptance_text: str,
    boundary_text: str,
) -> None:
    require(protocol["work_package_id"] == "WP-005", "gold protocol work package drift")
    require(packet["work_package_id"] == "WP-005", "packet work package drift")
    require(lifecycle["work_package_id"] == "WP-005", "lifecycle work package drift")

    acceptance_order = parse_yaml_top_level_list(acceptance_text, "freeze_order")
    lifecycle_order = lifecycle["freeze_order"]
    require(
        acceptance_order == lifecycle_order,
        "acceptance/lifecycle freeze order mismatch",
    )
    require(
        protocol.get("freeze_order") == lifecycle_order,
        "gold protocol/lifecycle freeze order mismatch",
    )
    require(
        protocol.get("lifecycle_contract") == "ORACLE_LIFECYCLE_CONTRACT.json",
        "gold protocol does not bind lifecycle contract",
    )
    require(
        packet.get("lifecycle_contract") == "ORACLE_LIFECYCLE_CONTRACT.json",
        "packet does not bind lifecycle contract",
    )
    require(
        packet.get("gold_adjudication_protocol") == "GOLD_ADJUDICATION_PROTOCOL.json",
        "packet does not bind gold protocol",
    )

    # Lifecycle causal direction: gold is immutable before B, but invisible to B.
    require_order(lifecycle_order, GOLD_FREEZE_STAGE, B_STAGE, "lifecycle")
    require_order(lifecycle_order, B_STAGE, "B_oracle_output_hash_frozen", "lifecycle")
    require_order(lifecycle_order, "B_oracle_output_hash_frozen", CONSISTENCY_STAGE, "lifecycle")
    require_order(lifecycle_order, CONSISTENCY_STAGE, SCORER_STAGE, "lifecycle")
    require_order(lifecycle_order, SCORER_STAGE, "first_scored_model_output_may_exist", "lifecycle")

    roles = protocol["roles"]
    require(roles["query_adjudicators_per_case"] == 2, "query gold requires two independent adjudicators")
    require(roles["outcome_adjudicators_per_case"] == 2, "outcome gold requires two independent adjudicators")
    require(roles["third_adjudicator_on_disagreement"] == 1, "third adjudicator missing")
    forbidden_roles = set(roles["forbidden_roles"])
    require(
        {
            "Path_A_implementer_for_same_candidate",
            "Path_B_implementer_for_same_candidate",
            "B_scorer_implementer_for_same_candidate",
            "model_output_analyst_for_same_candidate",
            "teacher_target_generator_for_same_candidate",
        }
        <= forbidden_roles,
        "gold adjudicator conflict-of-interest list incomplete",
    )

    query = protocol["query_adjudication"]
    outcome = protocol["outcome_adjudication"]
    require(query["completion_stage"] == "blind_query_adjudication_completed", "query completion stage drift")
    require(query["registry_freeze_stage"] == "query_adjudication_registry_hash_frozen", "query freeze stage drift")
    require(outcome["completion_stage"] == "blind_outcome_gold_adjudication_completed", "outcome completion stage drift")
    require(outcome["registry_freeze_stage"] == GOLD_FREEZE_STAGE, "outcome freeze stage drift")
    require(query["unresolved_disagreement"] == "case_not_eligible_for_freeze", "query disagreement must fail closed")
    require(outcome["unresolved_disagreement"] == "case_not_eligible_for_freeze", "outcome disagreement must fail closed")
    require(outcome["manual_derivation_required"] is True, "outcome gold manual derivation not required")
    require(set(query["recorded_output"]) == EXPECTED_QUERY_FIELDS, "query gold recorded vocabulary drift")
    require(set(outcome["recorded_output"]) == EXPECTED_OUTCOME_FIELDS, "outcome gold recorded vocabulary drift")

    for forbidden in ["Path_A_output", "Path_B_output", "student_or_teacher_output", "model_metrics"]:
        require(forbidden in query["forbidden_inputs"], f"query adjudicator can see forbidden input: {forbidden}")
    for forbidden in [
        "Path_A_output",
        "Path_B_output",
        "production_expected_frame",
        "student_or_teacher_output",
        "model_metrics",
        "post_model_error_analysis",
    ]:
        require(forbidden in outcome["forbidden_inputs"], f"outcome adjudicator can see forbidden input: {forbidden}")

    protocol_b = protocol["B_oracle_governance"]
    require(protocol_b["execution_after_outcome_gold_freeze"] is True, "B may execute before outcome gold freeze")
    require(protocol_b["outcome_gold_mount_during_execution"] == "prohibited", "outcome gold may be mounted to B")
    require(protocol_b["B_output_may_override_gold"] is False, "B may override gold")
    require(protocol_b["gold_may_be_repaired_from_B"] is False, "gold may be repaired from B")

    components = packet["components"]
    oracle = components["b_oracle_input_packet"]
    query_registry = components["query_adjudication_registry"]
    outcome_registry = components["outcome_gold_registry"]
    consistency = components["b_gold_consistency_check"]
    scorer = components["b_scorer_packet"]

    packet_text = json.dumps(packet, sort_keys=True)
    legacy_present = [field for field in LEGACY_GENERIC_FIELDS if field in packet_text]
    require(not legacy_present, f"legacy generic evidence vocabulary present: {sorted(legacy_present)}")

    required_oracle_forbidden = {
        "outcome_gold_registry",
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
    require("outcome_gold_registry" not in oracle["allowed"], "B-oracle may access outcome gold")
    require(oracle["lifecycle_activation_stage"] == B_STAGE, "B-oracle activation stage drift")

    require(set(query_registry["allowed_fields"]) == EXPECTED_QUERY_FIELDS, "packet query registry vocabulary differs from gold protocol")
    require(set(outcome_registry["allowed_fields"]) == EXPECTED_OUTCOME_FIELDS, "packet outcome registry vocabulary differs from gold protocol")
    require(EXACT_EVIDENCE_FIELDS <= set(outcome_registry["allowed_fields"]), "packet exact evidence/proof fields incomplete")
    require(query_registry["freeze_stage"] == "query_adjudication_registry_hash_frozen", "packet query freeze stage drift")
    require(outcome_registry["freeze_stage"] == GOLD_FREEZE_STAGE, "packet outcome freeze stage drift")
    require(query_registry["freeze_before_b_oracle_execution"] is True, "query registry may remain mutable before B")
    require(outcome_registry["freeze_before_b_oracle_execution"] is True, "outcome gold may remain mutable before B")
    require(outcome_registry["freeze_before_first_model_output"] is True, "outcome gold not pre-model frozen")
    require(outcome_registry["visible_to_b_oracle_during_computation"] is False, "outcome gold visible during B-oracle computation")
    require(outcome_registry["expected_value_authority"] is True, "outcome gold is not scorer authority")

    require(consistency["lifecycle_stage"] == CONSISTENCY_STAGE, "B/gold consistency stage drift")
    require(consistency["unexplained_disagreement"] == "block_scoring_and_benchmark_freeze", "B/gold disagreement not fail closed")
    require(consistency["B_may_override_gold"] is False, "B/gold check permits B override")
    require(consistency["gold_may_be_repaired_from_B"] is False, "B/gold check permits gold repair from B")

    expected_scorer_prerequisites = lifecycle["phase_contracts"][SCORER_STAGE]["requires_completed_before_activation"] + [SCORER_STAGE]
    require(scorer["lifecycle_activation_stage"] == SCORER_STAGE, "B-scorer activation stage drift")
    require(scorer["available_only_after"] == expected_scorer_prerequisites, "B-scorer activation order drift")
    require(scorer["expected_value_authority"] == "outcome_gold_registry", "B-scorer expected-value authority drift")

    lifecycle_consistency = lifecycle["phase_contracts"][CONSISTENCY_STAGE]
    require(lifecycle_consistency["expected_value_authority"] == "outcome_gold_registry", "lifecycle expected-value authority drift")
    require(lifecycle_consistency["B_may_override_gold"] is False, "lifecycle permits B override")
    require(lifecycle_consistency["gold_may_be_repaired_from_B"] is False, "lifecycle permits gold repair from B")

    governance = protocol["post_model_governance"]
    require(governance["in_place_query_alternative_addition"] == "prohibited", "post-model query alternative expansion allowed")
    require(governance["in_place_outcome_alternative_addition"] == "prohibited", "post-model outcome alternative expansion allowed")
    require(governance["gold_repair_from_model_behavior"] == "prohibited", "post-model gold repair allowed")
    require(governance["gold_repair_from_B"] == "prohibited", "gold repair from B allowed")
    require("current_confirmatory_eligibility_invalidated" in governance["new_legitimate_ambiguity"], "new ambiguity must invalidate current confirmatory version")

    packet_governance = packet["post_model_governance"]
    require(packet_governance["acceptable_alternative_addition_after_first_model_output"] == "prohibited", "packet permits post-model alternative addition")
    require(packet_governance["outcome_gold_edit_after_first_model_output"] == "prohibited", "packet permits post-model outcome gold edit")
    require(packet_governance["gold_repair_from_model_behavior"] == "prohibited", "packet permits model-driven gold repair")
    require(packet_governance["gold_repair_from_B"] == "prohibited", "packet permits B-driven gold repair")

    # Acceptance must bind the machine-readable lifecycle and regression fixtures.
    for required_token in [
        "oracle/ORACLE_LIFECYCLE_CONTRACT.json",
        "oracle/ORACLE_LIFECYCLE_NEGATIVE_FIXTURES.json",
        "acceptance_freeze_order_must_equal_mirror: true",
        "gold_protocol_freeze_order_must_equal_mirror: true",
        "packet_stage_bindings_must_match_mirror: true",
        "independence_boundary_order_must_match_mirror: true",
        "stale_generic_evidence_vocabulary_forbidden: true",
        "outcome_gold_frozen_before_B_execution: true",
        "outcome_gold_visible_to_B_during_execution: false",
    ]:
        require(required_token in acceptance_text, f"acceptance missing lifecycle binding: {required_token}")

    # Prose is not the machine source of truth, but it must state the same stages in order.
    section_start = boundary_text.find("The exact lifecycle is:")
    section_end = boundary_text.find("This order intentionally", section_start)
    require(section_start >= 0 and section_end > section_start, "independence boundary lifecycle section missing")
    lifecycle_section = boundary_text[section_start:section_end]
    positions = []
    for stage in lifecycle_order:
        pos = lifecycle_section.find(stage)
        require(pos >= 0, f"independence boundary missing lifecycle stage: {stage}")
        positions.append(pos)
    require(positions == sorted(positions), "independence boundary lifecycle order drift")
    for token in [
        "Outcome gold is the **expected-value authority for scoring**",
        "not mounted, readable, importable or otherwise visible to B-oracle",
        "B may not override gold",
        "gold may not be repaired from B",
    ]:
        require(token in boundary_text, f"independence boundary missing lifecycle statement: {token}")


def mutate_fixture(fixture: dict, protocol: dict, packet: dict, lifecycle: dict) -> tuple[dict, dict, dict]:
    p = copy.deepcopy(protocol)
    k = copy.deepcopy(packet)
    l = copy.deepcopy(lifecycle)
    mutation = fixture["mutation"]

    if mutation == "replace_exact_evidence_fields_with_legacy_generic_fields_in_packet":
        legacy = fixture["legacy_fields"]
        removed = set(fixture["removed_required_fields"])
        for component_name, field_name in [
            ("b_oracle_input_packet", "forbidden"),
            ("query_adjudication_registry", "forbidden_fields"),
            ("outcome_gold_registry", "allowed_fields"),
        ]:
            values = list(k["components"][component_name][field_name])
            values = [item for item in values if item not in removed]
            for item in legacy:
                if item not in values:
                    values.append(item)
            k["components"][component_name][field_name] = values
        return p, k, l

    if mutation == "move_B_execution_before_blind_outcome_gold_completion_in_lifecycle_and_protocol":
        order = list(l["freeze_order"])
        order.remove(B_STAGE)
        insert_at = order.index("blind_outcome_gold_adjudication_completed")
        order.insert(insert_at, B_STAGE)
        l["freeze_order"] = order
        p["freeze_order"] = list(order)
        return p, k, l

    raise AssertionError(f"unknown negative fixture mutation: {mutation}")


def validate_negative_fixtures(
    protocol: dict,
    packet: dict,
    lifecycle: dict,
    acceptance_text: str,
    boundary_text: str,
) -> list[str]:
    fixture_doc = load_json("ORACLE_LIFECYCLE_NEGATIVE_FIXTURES.json")
    require(fixture_doc["work_package_id"] == "WP-005", "negative fixture work package drift")
    fixtures = fixture_doc["fixtures"]
    require(len(fixtures) == 2, "expected exactly two lifecycle regression fixtures")
    killed: list[str] = []
    for fixture in fixtures:
        require(fixture["expected_result"] == "FAIL", f"fixture {fixture['fixture_id']} must expect FAIL")
        mutated_protocol, mutated_packet, mutated_lifecycle = mutate_fixture(fixture, protocol, packet, lifecycle)
        try:
            validate_bundle(mutated_protocol, mutated_packet, mutated_lifecycle, acceptance_text, boundary_text)
        except AssertionError as exc:
            expected = fixture["expected_error_contains"]
            require(expected in str(exc), f"fixture {fixture['fixture_id']} failed for wrong reason: {exc}")
            killed.append(fixture["fixture_id"])
        else:
            raise AssertionError(f"negative fixture survived: {fixture['fixture_id']}")
    require(len(killed) == len(fixtures), "not all lifecycle regression fixtures were killed")
    return killed


def main() -> None:
    protocol = load_json("GOLD_ADJUDICATION_PROTOCOL.json")
    packet = load_json("ORACLE_PACKET_CONTRACT.json")
    lifecycle = load_json("ORACLE_LIFECYCLE_CONTRACT.json")
    acceptance_text = ACCEPTANCE.read_text(encoding="utf-8")
    boundary_text = BOUNDARY.read_text(encoding="utf-8")

    validate_bundle(protocol, packet, lifecycle, acceptance_text, boundary_text)
    killed = validate_negative_fixtures(protocol, packet, lifecycle, acceptance_text, boundary_text)

    print(
        json.dumps(
            {
                "work_package": "WP-005",
                "gold_governance": "PASS",
                "lifecycle_consistency": "PASS",
                "freeze_order_stages": len(lifecycle["freeze_order"]),
                "outcome_gold_frozen_before_B": True,
                "outcome_gold_visible_to_B_oracle": False,
                "expected_value_authority": "outcome_gold_registry",
                "legacy_generic_evidence_vocabulary": "FORBIDDEN",
                "negative_fixtures_killed": killed,
                "post_model_gold_repair": "PROHIBITED",
                "independent_review": "NOT_PERFORMED_BY_THIS_VALIDATOR",
                "gate_001": "NOT_APPROVED_BY_THIS_VALIDATOR",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"WP-005 gold-governance validation failed: {exc}", file=sys.stderr)
        raise
