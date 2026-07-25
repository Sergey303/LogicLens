:- begin_tests(bounded_subgraph).

:- use_module('../rules/subgraph.pl').
:- use_module(library(apply)).


person('urn:logiclens:person:alex').
lab('urn:logiclens:org:lab').
iis('urn:logiclens:org:iis').
person_type('http://fogid.net/o/person').
rdf_type('http://www.w3.org/1999/02/22-rdf-syntax-ns#type').


default_labels(_{languages:[ru, en]}).

default_limits(_{
    maxDepth: 2,
    maxNodes: 250,
    maxFacts: 1000,
    maxOccurrences: 1000,
    maxPathLength: 2,
    maxOutputBytes: 1000000,
    timeoutMs: 2000
}).


test(root_occurrence_id_matches_independent_golden_vector) :-
    person(Person),
    subgraph:occurrence_id(Person, [], OccurrenceId),
    assertion(OccurrenceId ==
        'o:sha256:9892029c35cacef35d34c23f38394c4f147ab61dec58c73b0c26057141a4c881').


test(incoming_step_occurrence_id_matches_independent_golden_vector) :-
    person(Person),
    FactId = 'f:sha256:b0a5e5a69a3150e22a03e67cd709be47d8cb7319d6dc8b0cdc574cc0a582c2b3',
    subgraph:occurrence_id(Person, [step(FactId, incoming)], OccurrenceId),
    assertion(OccurrenceId ==
        'o:sha256:f01e1dc555c9969bb81e4cf8b67c55530621498e8104a2a70b13aeaa09e2f869').


test(outgoing_step_occurrence_id_uses_distinct_direction_tag) :-
    person(Person),
    FactId = 'f:sha256:b0a5e5a69a3150e22a03e67cd709be47d8cb7319d6dc8b0cdc574cc0a582c2b3',
    subgraph:occurrence_id(Person, [step(FactId, outgoing)], OccurrenceId),
    assertion(OccurrenceId ==
        'o:sha256:0fbe68cbe0e47b33ddca5f5b62f8f52f67f2b2cdaef5190e10d59068bb3c43e5').


test(depth_zero_contains_only_root_node_and_occurrence) :-
    person(Person),
    default_labels(Labels),
    default_limits(Limits),
    subgraph:build_subgraph(
        Person, 0, 0, both, Labels, Limits, Result, Diagnostics
    ),
    assertion(Diagnostics == []),
    assertion(Result.facts == []),
    Result.nodes = [RootNode],
    assertion(RootNode.id == Person),
    Result.occurrences = [RootOccurrence],
    assertion(RootOccurrence.nodeId == Person),
    assertion(RootOccurrence.depth == 0),
    assertion(RootOccurrence.state == boundary).


test(two_semantic_paths_to_iis_share_one_node, [nondet]) :-
    person(Person),
    iis(Iis),
    default_labels(Labels),
    default_limits(Limits),
    subgraph:build_subgraph(
        Person, 2, 2, both, Labels, Limits, Result, Diagnostics
    ),
    assertion(Diagnostics == []),
    include(node_is(Iis), Result.nodes, IisNodes),
    length(IisNodes, 1),
    include(occurrence_is(Iis), Result.occurrences, IisOccurrences),
    length(IisOccurrences, 2),
    forall(
        member(Occurrence, IisOccurrences),
        assertion(Occurrence.depth == 2)
    ).


test(rdf_type_is_visible_but_class_is_not_traversed, [nondet]) :-
    person(Person),
    person_type(PersonType),
    rdf_type(RdfType),
    default_labels(Labels),
    default_limits(Limits),
    subgraph:build_subgraph(
        Person, 1, 1, both, Labels, Limits, Result, _
    ),
    assertion(\+ (
        member(Node, Result.nodes),
        get_dict(id, Node, PersonType)
    )),
    assertion((
        member(Fact, Result.facts),
        get_dict(predicate, Fact, RdfType)
    )).


test(two_node_cycle_creates_terminal_cycle_occurrence, [nondet]) :-
    lab(Lab),
    default_labels(Labels),
    default_limits(Limits),
    subgraph:build_subgraph(
        Lab, 2, 2, outgoing, Labels, Limits, Result, _
    ),
    include(cycle_occurrence, Result.occurrences, Cycles),
    length(Cycles, 1),
    Cycles = [Cycle],
    assertion(Cycle.nodeId == Lab),
    assertion(Cycle.depth == 2),
    assertion(Cycle.state == cycle_reference).


test(node_limit_selects_stable_root_only_subset) :-
    person(Person),
    default_labels(Labels),
    default_limits(Limits0),
    Limits = Limits0.put(maxNodes, 1),
    subgraph:build_subgraph(
        Person, 2, 2, both, Labels, Limits, First, FirstDiagnostics
    ),
    subgraph:build_subgraph(
        Person, 2, 2, both, Labels, Limits, Second, SecondDiagnostics
    ),
    assertion(First == Second),
    assertion(FirstDiagnostics =@= SecondDiagnostics),
    assertion(First.truncated == true),
    First.nodes = [Root],
    assertion(Root.id == Person).


test(repeated_full_traversal_is_structurally_equal) :-
    person(Person),
    default_labels(Labels),
    default_limits(Limits),
    subgraph:build_subgraph(
        Person, 2, 2, both, Labels, Limits, First, FirstDiagnostics
    ),
    subgraph:build_subgraph(
        Person, 2, 2, both, Labels, Limits, Second, SecondDiagnostics
    ),
    assertion(First == Second),
    assertion(FirstDiagnostics =@= SecondDiagnostics).


node_is(Id, Node) :- Node.id == Id.
occurrence_is(Id, Occurrence) :- Occurrence.nodeId == Id.
cycle_occurrence(Occurrence) :- Occurrence.state == cycle_reference.


:- end_tests(bounded_subgraph).
