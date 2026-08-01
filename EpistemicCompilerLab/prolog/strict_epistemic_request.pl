:- module(strict_epistemic_request, [request_frame/3]).

:- use_module(strict_epistemic).

request_frame(missing, _, Frame) :-
    !,
    clarification_frame(revision, Frame).
request_frame(_, missing, Frame) :-
    !,
    clarification_frame(material, Frame).
request_frame(Revision, Material, Frame) :-
    Proposition = uses_material(Revision, Material),
    decision_frame(Proposition, Base),
    PropositionJson = _{
        predicate: uses_material,
        revision: Revision,
        material: Material
    },
    put_dict(proposition, Base, PropositionJson, WithProposition),
    put_dict(askField, WithProposition, null, Frame).

clarification_frame(Field, _{
    proposition: null,
    status: not_evaluated,
    action: ask_clarification,
    reason: missing_required_field,
    evidence: [],
    askField: Field
}).
