:- module(strict_epistemic_case, [case_frame/5]).

case_frame(missing, _, _, _, Frame) :-
    !,
    clarification_frame(revision, Frame).
case_frame(_, missing, _, _, Frame) :-
    !,
    clarification_frame(material, Frame).
case_frame(Revision, Material, PositiveCsv, NegativeCsv, Frame) :-
    csv_ids(PositiveCsv, Positive),
    csv_ids(NegativeCsv, Negative),
    case_status(Positive, Negative, Status),
    status_evidence(Status, Positive, Negative, Evidence),
    status_policy(Status, Action, Reason),
    Frame = _{
        proposition:_{
            predicate:uses_material,
            revision:Revision,
            material:Material
        },
        status:Status,
        action:Action,
        reason:Reason,
        evidence:Evidence,
        askField:null
    }.

csv_ids(none, []) :- !.
csv_ids(Csv, Ids) :-
    atomic_list_concat(Ids, ',', Csv).

case_status([], [], unknown).
case_status([_|_], [], supported).
case_status([], [_|_], refuted).
case_status([_|_], [_|_], conflicting).

status_evidence(supported, Positive, _, Positive).
status_evidence(refuted, _, Negative, Negative).
status_evidence(unknown, _, _, []).
status_evidence(conflicting, Positive, Negative, Evidence) :-
    append(Positive, Negative, Combined),
    sort(Combined, Evidence).

status_policy(supported, answer_supported, evidence_supports_claim).
status_policy(refuted, answer_refuted, evidence_refutes_claim).
status_policy(unknown, abstain_unknown, insufficient_loaded_evidence).
status_policy(conflicting, report_conflict, incompatible_loaded_assertions).

clarification_frame(Field, _{
    proposition:null,
    status:not_evaluated,
    action:ask_clarification,
    reason:missing_required_field,
    evidence:[],
    askField:Field
}).
