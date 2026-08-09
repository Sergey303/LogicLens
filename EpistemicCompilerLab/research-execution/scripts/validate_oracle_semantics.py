#!/usr/bin/env python3
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXECUTION_ROOT = HERE.parent
ORACLE = EXECUTION_ROOT / "oracle"

REQUIRED_SCORE_FIELDS = {
    "schema_valid",
    "query_predicate",
    "query_arguments",
    "query_arity",
    "scope_version",
    "clarification",
    "status",
    "action",
    "allowed_or_forbidden_conclusion",
    "evidence_roots",
    "provenance",
    "proof_trace",
    "warnings",
    "language_or_rendering_contract",
}

REQUIRED_INVARIANTS = {
    "INV-CANON",
    "INV-TYPE-ARITY",
    "INV-SCOPE-VERSION-TIME",
    "INV-RULE-FIXPOINT",
    "INV-OPEN-WORLD",
    "INV-FOUR-STATE",
    "INV-EVIDENCE-ROOTS",
    "INV-PROOF-NORMAL-FORM",
    "INV-POLICY",
    "INV-CLARIFICATION",
    "INV-INVALID-QUERY",
    "INV-RUNTIME-ERROR",
    "INV-WARNINGS",
    "INV-ALTERNATIVE-FREEZE",
    "INV-PROVENANCE",
    "INV-RENDERER",
    "INV-PACKET-SEPARATION",
    "INV-TRACK-SEPARATION",
}


def fail(message):
    raise AssertionError(message)


def require(condition, message):
    if not condition:
        fail(message)


def load_json(name):
    return json.loads((ORACLE / name).read_text(encoding="utf-8"))


def load_csv(name):
    with (ORACLE / name).open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def validate_semantic_registry():
    registry = load_json("SEMANTIC_REGISTRY.json")
    require(registry["semantic_version"] == "wp005.semantic.v1", "semantic version drift")
    require(registry["canonical_json"]["whitespace"] == "none", "canonical JSON whitespace drift")
    require(registry["canonical_json"]["trailing_newline"] is False, "canonical JSON trailing newline must be false")
    require(registry["identifier"]["canonical_pattern"] == "^[a-z][a-z0-9_.-]*$", "identifier pattern drift")
    require(registry["identifier"]["case_folding"] is False, "implicit identifier case folding forbidden")
    require(registry["typed_argument_rules"]["arity"] == "exact declared predicate arity", "arity semantics drift")
    require(registry["typed_argument_rules"]["argument_order"] == "preserved and semantically significant", "argument order drift")
    require(registry["scope"]["dimensions"] == ["jurisdiction", "domain", "tenant"], "scope dimension drift")
    require("exact equality only" in registry["version_and_time"]["version_comparison"], "version equality drift")
    require("effective_from <= query_time" in registry["version_and_time"]["effective"], "effective-time rule missing")
    require(registry["proposition_normal_form"]["polarity_excluded_from_identity"] is True, "polarity must be excluded from proposition identity")
    require(registry["assertions"]["absence_is_negative"] is False, "absence must not become negative evidence")
    require(registry["rules"]["priority"] == "none", "unexpected rule priority")
    require(registry["rules"]["exceptions"] == "none", "unexpected exceptions")
    require(registry["rules"]["negation_as_failure"] is False, "negation-as-failure forbidden")
    require(registry["evidence"]["minimality_claim"] is False, "evidence roots must not claim minimality")
    require("every valid derivation" in registry["evidence"]["polarity_evidence_roots"], "evidence root completeness rule missing")
    require(registry["proof_normal_form"]["cycles"] == "invalid_proof", "proof cycle rule drift")
    require(registry["proof_normal_form"]["unresolvable_edge"] == "invalid_proof", "proof edge resolution rule drift")

    truth = {(row["positive_derivation"], row["negative_derivation"]): row["status"] for row in registry["truth_table"]}
    require(truth == {
        (True, False): "supported",
        (False, True): "refuted",
        (True, True): "conflicting",
        (False, False): "unknown",
    }, "four-state truth table is incomplete or wrong")

    require(set(registry["outcomes"]["semantic_status"]) == {"supported", "refuted", "conflicting", "unknown"}, "semantic status set drift")
    require(set(registry["outcomes"]["query_outcome"]) == {"valid", "needs_clarification", "invalid_query", "runtime_error"}, "query outcome set drift")
    require("never mapped" in registry["outcomes"]["runtime_error"], "runtime error must be separate from semantic status")
    require("no positive and no negative derivation" in registry["outcomes"]["unknown"], "unknown semantics drift")
    return registry


def validate_policy(registry):
    policy = load_json("POLICY_TABLE.json")
    require(policy["semantic_version"] == registry["semantic_version"], "policy semantic version mismatch")
    require(policy["policy_may_change_status"] is False, "policy cannot change status")
    rows = {(row["query_outcome"], row["status"]): row for row in policy["mappings"]}
    expected = {
        ("needs_clarification", None): ("request_clarification", None, ["clarification_required"]),
        ("invalid_query", None): ("reject_query", None, ["invalid_query"]),
        ("runtime_error", None): ("report_runtime_error", None, ["runtime_error"]),
        ("valid", "supported"): ("answer_supported", "affirm", []),
        ("valid", "refuted"): ("answer_refuted", "deny", []),
        ("valid", "conflicting"): ("abstain_conflict", None, ["conflicting_evidence"]),
        ("valid", "unknown"): ("abstain_unknown", None, ["insufficient_evidence"]),
    }
    require(set(rows) == set(expected), "policy mapping keys incomplete or extra")
    for key, (action, conclusion, warnings) in expected.items():
        row = rows[key]
        require(row["action"] == action, f"policy action mismatch for {key}")
        require(row["allowed_conclusion"] == conclusion, f"policy conclusion mismatch for {key}")
        require(row["mandatory_warnings"] == warnings, f"policy warnings mismatch for {key}")
        if key[1] in {"conflicting", "unknown"} or key[0] != "valid":
            require(set(row["forbidden_conclusions"]) == {"affirm", "deny"}, f"abstention/query error must forbid affirm/deny for {key}")
    return policy


def validate_packet_contract():
    packet = load_json("ORACLE_PACKET_CONTRACT.json")
    components = packet["components"]
    oracle = components["b_oracle_input_packet"]
    forbidden = set(oracle["forbidden"])
    required_forbidden = {
        "expected_status", "expected_action", "expected_conclusion", "expected_warnings",
        "expected_evidence_roots", "expected_provenance", "expected_proof_trace", "expected_frame",
        "student_response", "production_frame", "production_oracle_output", "model_metrics",
    }
    require(required_forbidden <= forbidden, "B-oracle forbidden outcome/model fields incomplete")
    require("outcome_gold_registry" not in oracle["allowed"], "outcome gold must not be allowed to B-oracle")
    require(components["outcome_gold_registry"]["visible_to_b_oracle_during_computation"] is False, "outcome gold visible to B-oracle")
    require(components["query_adjudication_registry"]["freeze_before_first_model_output"] is True, "query alternatives not pre-model frozen")
    require(components["outcome_gold_registry"]["freeze_before_first_model_output"] is True, "outcome gold not pre-model frozen")
    scorer = components["b_scorer_packet"]
    require("b_oracle_output_hash_frozen" in scorer["available_only_after"], "scorer may run before B output freeze")
    require("outcome_gold_registry_hash_frozen" in scorer["available_only_after"], "scorer may run before gold freeze")
    require(packet["post_model_governance"]["acceptable_alternative_addition_after_first_model_output"] == "prohibited", "post-model alternative expansion allowed")
    require(packet["tracks"]["gold_query_execution"]["must_not_validate"] == ["natural_question_interpretation", "student_query_formation"], "gold-query claim boundary drift")
    require(packet["tracks"]["oracle_frame_renderer_ceiling"]["must_not_validate"] == ["question_interpretation", "query_formation", "formal_execution"], "renderer ceiling boundary drift")
    return packet


def mutation_ids():
    text = (ORACLE / "MUTATION_MATRIX.yaml").read_text(encoding="utf-8")
    ids = re.findall(r"^\s*- mutation_id:\s*([A-Z0-9-]+)\s*$", text, flags=re.MULTILINE)
    require(len(ids) == len(set(ids)), "duplicate mutation IDs")
    require(len(ids) >= 42, "mutation matrix unexpectedly small")
    for critical in ["MUT-PACKET-001", "MUT-PACKET-002", "MUT-TRACK-001", "MUT-INFRA-002", "MUT-ALTERNATIVE-001"]:
        require(critical in ids, f"missing critical mutation {critical}")
    require("critical_kill_rate_required: 1.0" in text, "100% critical kill rate not frozen")
    require("no_equivalent_mutant_waiver_after_model_outputs: true" in text, "post-model equivalent-mutant waiver not forbidden")
    return set(ids)


def validate_vectors_and_coverage(mutations):
    vector_doc = load_json("CONFORMANCE_VECTORS.json")
    vectors = vector_doc["vectors"]
    by_id = {row["vector_id"]: row for row in vectors}
    require(len(by_id) == len(vectors), "duplicate conformance vector ID")
    require(len(vectors) >= 36, "positive/negative conformance corpus too small")

    rows = load_csv("INVARIANT_COVERAGE_MATRIX.csv")
    require({row["invariant_id"] for row in rows} == REQUIRED_INVARIANTS, "invariant coverage set incomplete or extra")
    seen_score_fields = set()
    for row in rows:
        inv = row["invariant_id"]
        pos = row["positive_vector"]
        neg = row["negative_vector"]
        require(pos in by_id and neg in by_id, f"coverage references unknown vector for {inv}")
        require(by_id[pos]["invariant_id"] == inv and by_id[pos]["kind"] == "positive", f"positive vector mismatch for {inv}")
        require(by_id[neg]["invariant_id"] == inv and by_id[neg]["kind"] == "negative", f"negative vector mismatch for {inv}")
        mapped_mutations = [item for item in row["mutation_ids"].split(";") if item]
        require(mapped_mutations, f"no mutation mapped for {inv}")
        require(set(mapped_mutations) <= mutations, f"unknown mutation mapped for {inv}")
        require(row["expected_A_result"].strip(), f"missing expected A result for {inv}")
        require(row["expected_B_result"].strip(), f"missing expected B result for {inv}")
        fields = {item for item in row["expected_scorer_fields"].split(";") if item}
        require(fields, f"no scorer field mapped for {inv}")
        require(fields <= REQUIRED_SCORE_FIELDS, f"unknown scorer field for {inv}: {fields - REQUIRED_SCORE_FIELDS}")
        seen_score_fields |= fields
    require(seen_score_fields == REQUIRED_SCORE_FIELDS, f"score field coverage incomplete: missing {REQUIRED_SCORE_FIELDS - seen_score_fields}")


def validate_human_audit():
    audit = load_json("HUMAN_AUDIT_PROTOCOL.json")
    sample = audit["sample"]
    require(sample["size"] == 120, "human audit sample size drift")
    require(sample["selection_seed"] == 157005, "human audit selection seed drift")
    require(sample["hash_function"] == "SHA-256", "human audit hash function drift")
    require(sample["primary_status_quota"] == {"supported": 30, "refuted": 30, "conflicting": 30, "unknown": 30}, "human audit status quotas drift")
    require(set(sample["mandatory_coverage_dimensions"]) == {"domain", "status", "difficulty", "source_family", "mutation_family"}, "human audit coverage dimensions incomplete")
    require(audit["reviewers"]["independent_reviewers_per_case"] == 2, "human audit needs two blind reviewers")
    require(audit["reviewers"]["adjudicator_on_disagreement"] == 1, "human audit adjudicator missing")
    acceptance = audit["acceptance"]
    require(acceptance["pre_adjudication_exact_case_agreement_min"] == 0.95, "human audit global threshold drift")
    require(acceptance["per_stratum_pre_adjudication_agreement_min"] == 0.90, "human audit stratum threshold drift")
    require(acceptance["post_adjudication_unresolved_disagreements"] == 0, "human audit unresolved disagreements must be zero")
    require(acceptance["semantic_or_scorer_errors_allowed"] == 0, "human audit must allow zero semantic/scorer errors")


def validate_audit_tool_trust():
    trust = load_json("AUDIT_TOOL_TRUST_MANIFEST.json")
    require(len(trust["required_observation_channels"]) >= 16, "audit observation channels incomplete")
    require(set(trust["channel_status_values"]) == {"observed_pass", "observed_fail", "not_observable"}, "audit channel status vocabulary drift")
    require("not_observable prevents PASS" in trust["fail_closed_rule"], "unobservable audit channel is not fail closed")
    require(len(trust["negative_controls"]) == 16, "audit negative-control count must be exactly 16")
    require(trust["negative_control_acceptance"]["required_detected"] == 16, "all audit negative controls must be detected")
    require(trust["negative_control_acceptance"]["correct_reason_required"] is True, "audit control reason must be checked")
    require(trust["negative_control_acceptance"]["always_fail_detector_rejected_by_positive_controls"] is True, "audit positive controls must reject always-fail detector")
    require(trust["known_blind_spots_policy"]["report_required"] is True, "audit blind-spots report required")
    require(trust["known_blind_spots_policy"]["empty_report_allowed"] is False, "audit blind-spots report cannot be silently empty")
    require(trust["known_blind_spots_policy"]["unmitigated_required_channel"] == "blocks_pass", "unmitigated audit blind spot must block PASS")


def validate_docs():
    spec = (ORACLE / "SEMANTIC_SPEC.md").read_text(encoding="utf-8")
    boundary = (ORACLE / "INDEPENDENCE_BOUNDARY.md").read_text(encoding="utf-8")
    audit_plan = (ORACLE / "DEPENDENCY_AUDIT_PLAN.md").read_text(encoding="utf-8")
    for required in ["SEMANTIC_REGISTRY.json", "POLICY_TABLE.json", "ORACLE_PACKET_CONTRACT.json", "INVARIANT_COVERAGE_MATRIX.csv", "HUMAN_AUDIT_PROTOCOL.json"]:
        require(required in spec, f"semantic spec does not reference {required}")
    require("outcome_gold_registry" in spec, "semantic spec does not separate outcome gold")
    require("does not validate student query formation" in spec, "semantic spec query-track limitation missing")
    require("outcome-gold registry" in boundary, "independence boundary does not separate outcome gold")
    require("gold-query execution agreement" in boundary, "independence boundary missing track limitation")
    require("AUDIT_TOOL_TRUST_MANIFEST.json" in audit_plan, "dependency audit plan missing audit-tool trust manifest")
    require("sample size exactly `120`" in audit_plan, "dependency audit plan missing quantitative human audit")


def main():
    for name in [
        "SEMANTIC_SPEC.md",
        "SEMANTIC_REGISTRY.json",
        "POLICY_TABLE.json",
        "ORACLE_PACKET_CONTRACT.json",
        "CONFORMANCE_VECTORS.json",
        "INVARIANT_COVERAGE_MATRIX.csv",
        "INDEPENDENCE_BOUNDARY.md",
        "MUTATION_MATRIX.yaml",
        "DEPENDENCY_AUDIT_PLAN.md",
        "HUMAN_AUDIT_PROTOCOL.json",
        "AUDIT_TOOL_TRUST_MANIFEST.json",
    ]:
        require((ORACLE / name).is_file(), f"missing oracle artifact: {name}")

    registry = validate_semantic_registry()
    validate_policy(registry)
    validate_packet_contract()
    mutations = mutation_ids()
    validate_vectors_and_coverage(mutations)
    validate_human_audit()
    validate_audit_tool_trust()
    validate_docs()

    print(json.dumps({
        "work_package": "WP-005",
        "semantic_version": registry["semantic_version"],
        "semantic_contract": "PASS",
        "invariants": len(REQUIRED_INVARIANTS),
        "score_fields_covered": len(REQUIRED_SCORE_FIELDS),
        "critical_mutation_ids_present": len(mutations),
        "human_audit_sample": 120,
        "independent_review": "NOT_PERFORMED_BY_THIS_VALIDATOR",
        "gate_001": "NOT_APPROVED_BY_THIS_VALIDATOR"
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"WP-005 semantic validation failed: {exc}", file=sys.stderr)
        raise
