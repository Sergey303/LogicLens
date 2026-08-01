:- begin_tests(strict_epistemic).

:- use_module('../prolog/strict_epistemic').
:- use_module('../prolog/strict_epistemic_request').

test(supported_status) :-
    claim_status(uses_material(revision_a, asd2), supported).

test(refuted_status) :-
    claim_status(uses_material(revision_b, asd2), refuted).

test(unknown_status_is_not_refuted) :-
    Proposition = uses_material(revision_c, asd2),
    claim_status(Proposition, unknown),
    \+ claim_status(Proposition, refuted).

test(conflicting_status_precedes_support_or_refutation) :-
    Proposition = uses_material(revision_d, asd2),
    claim_status(Proposition, conflicting),
    \+ claim_status(Proposition, supported),
    \+ claim_status(Proposition, refuted).

test(supported_evidence_is_positive_only) :-
    claim_evidence(
        uses_material(revision_a, asd2),
        supported,
        [ep_a_positive]
    ).

test(refuted_evidence_is_negative_only) :-
    claim_evidence(
        uses_material(revision_b, asd2),
        refuted,
        [ep_b_negative]
    ).

test(conflict_preserves_both_assertions) :-
    claim_evidence(
        uses_material(revision_d, asd2),
        conflicting,
        Evidence
    ),
    msort(Evidence, [ep_d_negative, ep_d_positive]).

test(unknown_has_no_evidence) :-
    claim_evidence(uses_material(revision_c, asd2), unknown, []).

test(decision_policy_is_status_specific) :-
    decision(uses_material(revision_a, asd2), answer_supported),
    decision(uses_material(revision_b, asd2), answer_refuted),
    decision(uses_material(revision_c, asd2), abstain_unknown),
    decision(uses_material(revision_d, asd2), report_conflict).

test(decision_frame_separates_status_action_and_evidence) :-
    decision_frame(uses_material(revision_d, asd2), Frame),
    get_dict(status, Frame, conflicting),
    get_dict(action, Frame, report_conflict),
    get_dict(reason, Frame, incompatible_loaded_assertions),
    get_dict(evidence, Frame, Evidence),
    msort(Evidence, [ep_d_negative, ep_d_positive]).

test(provenance_is_addressable) :-
    assertion(ep_a_positive, _, SourceId, positive),
    source_ref(SourceId, Ref),
    get_dict(file, Ref, "EpistemicCompilerLab/sources/strict-epistemic-v0.md"),
    get_dict(section, Ref, "Source S-A-positive").

test(irrelevant_assertions_do_not_change_target_statuses) :-
    assertion(ep_e_positive, uses_material(revision_e, asd7), _, positive),
    assertion(ep_f_negative, uses_material(revision_f, asd9), _, negative),
    claim_status(uses_material(revision_a, asd2), supported),
    claim_status(uses_material(revision_c, asd2), unknown).

test(complete_request_is_json_ready) :-
    request_frame(revision_a, asd2, Frame),
    get_dict(askField, Frame, null),
    get_dict(proposition, Frame, Proposition),
    get_dict(predicate, Proposition, uses_material),
    get_dict(revision, Proposition, revision_a),
    get_dict(material, Proposition, asd2).

test(missing_revision_requests_clarification) :-
    request_frame(missing, asd2, Frame),
    get_dict(proposition, Frame, null),
    get_dict(status, Frame, not_evaluated),
    get_dict(action, Frame, ask_clarification),
    get_dict(askField, Frame, revision).

test(missing_material_requests_clarification) :-
    request_frame(revision_a, missing, Frame),
    get_dict(proposition, Frame, null),
    get_dict(status, Frame, not_evaluated),
    get_dict(action, Frame, ask_clarification),
    get_dict(askField, Frame, material).

:- end_tests(strict_epistemic).
