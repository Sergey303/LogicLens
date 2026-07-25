:- begin_tests(epistemic_compiler_knowledge).

:- use_module('../prolog/knowledge').

test(before_transition_revision_a) :-
    current_material(a, 20260630, asd2, Proof),
    memberchk("rule:before_transition", Proof).

test(before_transition_revision_b) :-
    current_material(b, 20260630, asd2, _).

test(after_transition_revision_a_exception) :-
    current_material(a, 20260701, asd2, Proof),
    memberchk("rule:revision_a_exception", Proof),
    memberchk("assertion:a1042", Proof).

test(after_transition_revision_b_default) :-
    current_material(b, 20260810, asd100500, Proof),
    memberchk("rule:default_after_transition", Proof).

test(unknown_revision, [fail]) :-
    current_material(c, 20260810, _, _).

test(evidence_is_optional_and_addressable) :-
    expansion(
        asd100500,
        evidence,
        exp_asd100500_evidence,
        _
    ),
    expansion_payload(
        exp_asd100500_evidence,
        Payload
    ),
    get_dict(
        file,
        Payload,
        "EpistemicCompilerLab/sources/materials.md"
    ).

test(exception_expansion) :-
    expansion(
        asd100500,
        exceptions,
        exp_asd100500_exceptions,
        _
    ),
    expansion_payload(
        exp_asd100500_exceptions,
        Payload
    ),
    get_dict(revisions, Payload, ["a"]).

:- end_tests(epistemic_compiler_knowledge).