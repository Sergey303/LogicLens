:- module(epistemic_compiler_knowledge, [
    current_material/4,
    expansion/4,
    expansion_payload/2,
    assertion_source/2
]).

supported_revision(a).
supported_revision(b).

assertion_source(a1042, _{
    file:"EpistemicCompilerLab/sources/materials.md",
    section:"ASD100500"
}).

current_material(Revision, Date, asd2, ["rule:before_transition"]) :-
    supported_revision(Revision),
    integer(Date),
    Date < 20260701.

current_material(a, Date, asd2, [
    "rule:revision_a_exception",
    "assertion:a1042"
]) :-
    integer(Date),
    Date >= 20260701.

current_material(b, Date, asd100500, [
    "rule:default_after_transition",
    "assertion:a1042"
]) :-
    integer(Date),
    Date >= 20260701.

expansion(
    asd100500,
    evidence,
    exp_asd100500_evidence,
    "Original source section for the replacement rule"
).

expansion(
    asd100500,
    exceptions,
    exp_asd100500_exceptions,
    "Hardware revisions that do not use the default material"
).

expansion_payload(exp_asd100500_evidence, _{
    type:"markdown",
    file:"EpistemicCompilerLab/sources/materials.md",
    section:"ASD100500"
}).

expansion_payload(exp_asd100500_exceptions, _{
    type:"rule_summary",
    revisions:["a"],
    material:"asd2",
    condition:"date >= 20260701"
}).