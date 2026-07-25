:- begin_tests(epistemic_compiler_knowledge).

:- use_module('../prolog/knowledge').

material_solutions(Revision, Date, Solutions) :-
    findall(
        Material-Proof,
        current_material(Revision, Date, Material, Proof),
        Solutions
    ).

test(before_transition_revision_a) :-
    material_solutions(a, 20260630, [asd2-Proof]),
    memberchk("rule:before_transition", Proof).

test(before_transition_revision_b) :-
    material_solutions(b, 20260630, [asd2-_]).

test(after_transition_revision_a_exception) :-
    material_solutions(a, 20260701, [asd2-Proof]),
    memberchk("rule:revision_a_exception", Proof),
    memberchk("assertion:a1042", Proof).

test(after_transition_revision_b_default) :-
    material_solutions(b, 20260810, [asd100500-Proof]),
    memberchk("rule:default_after_transition", Proof).

test(unknown_revision) :-
    material_solutions(c, 20260810, []).

test(evidence_is_optional_and_addressable) :-
    findall(
        Ref-Summary,
        expansion(asd100500, evidence, Ref, Summary),
        [exp_asd100500_evidence-_]
    ),
    expansion_payload(exp_asd100500_evidence, Payload),
    get_dict(
        file,
        Payload,
        "EpistemicCompilerLab/sources/materials.md"
    ).

test(exception_expansion) :-
    findall(
        Ref-Summary,
        expansion(asd100500, exceptions, Ref, Summary),
        [exp_asd100500_exceptions-_]
    ),
    expansion_payload(exp_asd100500_exceptions, Payload),
    get_dict(revisions, Payload, ["a"]).

:- end_tests(epistemic_compiler_knowledge).
