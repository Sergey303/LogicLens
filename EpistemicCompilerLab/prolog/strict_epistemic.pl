:- module(strict_epistemic, [
    assertion/4,
    source_ref/2,
    claim_status/2,
    claim_evidence/3,
    decision/2,
    decision_reason/2,
    decision_frame/2
]).

source_ref(source_a_positive, _{
    file:"EpistemicCompilerLab/sources/strict-epistemic-v0.md",
    section:"Source S-A-positive"
}).
source_ref(source_b_negative, _{
    file:"EpistemicCompilerLab/sources/strict-epistemic-v0.md",
    section:"Source S-B-negative"
}).
source_ref(source_d_positive, _{
    file:"EpistemicCompilerLab/sources/strict-epistemic-v0.md",
    section:"Source S-D-positive"
}).
source_ref(source_d_negative, _{
    file:"EpistemicCompilerLab/sources/strict-epistemic-v0.md",
    section:"Source S-D-negative"
}).

assertion(ep_a_positive, uses_material(revision_a, asd2), source_a_positive, positive).
assertion(ep_b_negative, uses_material(revision_b, asd2), source_b_negative, negative).
assertion(ep_d_positive, uses_material(revision_d, asd2), source_d_positive, positive).
assertion(ep_d_negative, uses_material(revision_d, asd2), source_d_negative, negative).

positive_evidence(Proposition, AssertionId) :-
    assertion(AssertionId, Proposition, _, positive).

negative_evidence(Proposition, AssertionId) :-
    assertion(AssertionId, Proposition, _, negative).

claim_status(Proposition, conflicting) :-
    positive_evidence(Proposition, _),
    negative_evidence(Proposition, _),
    !.
claim_status(Proposition, supported) :-
    positive_evidence(Proposition, _),
    \+ negative_evidence(Proposition, _),
    !.
claim_status(Proposition, refuted) :-
    negative_evidence(Proposition, _),
    \+ positive_evidence(Proposition, _),
    !.
claim_status(Proposition, unknown) :-
    \+ positive_evidence(Proposition, _),
    \+ negative_evidence(Proposition, _).

claim_evidence(Proposition, supported, Evidence) :-
    findall(Id, positive_evidence(Proposition, Id), Evidence).
claim_evidence(Proposition, refuted, Evidence) :-
    findall(Id, negative_evidence(Proposition, Id), Evidence).
claim_evidence(Proposition, conflicting, Evidence) :-
    findall(Id, assertion(Id, Proposition, _, _), Evidence).
claim_evidence(_, unknown, []).

decision(Proposition, answer_supported) :-
    claim_status(Proposition, supported).
decision(Proposition, answer_refuted) :-
    claim_status(Proposition, refuted).
decision(Proposition, abstain_unknown) :-
    claim_status(Proposition, unknown).
decision(Proposition, report_conflict) :-
    claim_status(Proposition, conflicting).

decision_reason(Proposition, evidence_supports_claim) :-
    claim_status(Proposition, supported).
decision_reason(Proposition, evidence_refutes_claim) :-
    claim_status(Proposition, refuted).
decision_reason(Proposition, insufficient_loaded_evidence) :-
    claim_status(Proposition, unknown).
decision_reason(Proposition, incompatible_loaded_assertions) :-
    claim_status(Proposition, conflicting).

decision_frame(Proposition, Frame) :-
    claim_status(Proposition, Status),
    claim_evidence(Proposition, Status, Evidence),
    decision(Proposition, Action),
    decision_reason(Proposition, Reason),
    Frame = _{
        proposition:Proposition,
        status:Status,
        action:Action,
        reason:Reason,
        evidence:Evidence
    }.
