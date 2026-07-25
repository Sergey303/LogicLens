:- begin_tests(bounded_subgraph).

:- use_module('../rules/subgraph.pl').
:- use_module(library(http/json)).


person('urn:logiclens:person:alex').
iis('urn:logiclens:org:iis').
lab('urn:logiclens:org:lab').
archive('urn:logiclens:org:archive').
rdf_type('http://www.w3.org/1999/02/22-rdf-syntax-ns#type').


default_options(Depth, _{
    depth: Depth,
    direction: both,
    languages: [ru, en],
    limits: _{}
}).


test(depth_zero_returns_only_root) :-
    person(Person),
    default_options(0, Options),
    subgraph:subgraph(Person, Options, Result),
    Result.nodes = [Node],
    assertion(Node.nodeId == Person),
    assertion(Result.facts == []),
    Result.occurrences = [Occurrence],
    assertion(Occurrence.nodeId == Person),
    assertion(Occurrence.state == boundary),
    assertion(Result.occurrenceFacts == []).


test(depth_one_expands_root_incident_facts) :-
    person(Person),
    default_options(1, Options),
    subgraph:subgraph(Person, Options, Result),
    node_ids(Result, NodeIds),
    assertion(memberchk('urn:logiclens:participation:work', NodeIds)),
    assertion(memberchk('urn:logiclens:student:study', NodeIds)),
    assertion(memberchk('urn:logiclens:authority:paper-author', NodeIds)),
    assertion(\+ memberchk('urn:logiclens:org:iis', NodeIds)),
    assertion(\+ memberchk('urn:logiclens:document:paper', NodeIds)),
    fact_ids(Result, FactIds),
    assertion(memberchk(
        'f:sha256:3242677a145c47ae3bc6037b8877beb244659c99fbbec00b87f8977ec60afaae',
        FactIds
    )).


test(rdf_type_is_visible_but_not_traversed) :-
    person(Person),
    default_options(1, Options),
    subgraph:subgraph(Person, Options, Result),
    rdf_type(RdfType),
    member(Fact, Result.facts),
    Fact.predicate == RdfType,
    !,
    assertion(\+ node_with_id(Result, 'http://fogid.net/o/person')).


test(depth_two_keeps_two_iis_occurrences_and_one_node) :-
    person(Person),
    iis(Iis),
    default_options(2, Options),
    subgraph:subgraph(Person, Options, Result),
    include(node_is(Iis), Result.nodes, IisNodes),
    length(IisNodes, 1),
    include(occurrence_is(Iis), Result.occurrences, IisOccurrences),
    length(IisOccurrences, 2),
    occurrence_ids(IisOccurrences, OccurrenceIds),
    assertion(OccurrenceIds == [
        'o:sha256:1e52067cf824aa7e73935434ad5d5fa742b34d4687bdd318d069d50d432f84b5',
        'o:sha256:fe5b8e79cc9abe39cb85c1cfd644a9cc6765a25489dabba9be69741805db8dfb'
    ]).


test(unknown_relation_is_traversable) :-
    lab(Lab),
    archive(Archive),
    default_options(1, Options),
    subgraph:subgraph(Lab, Options, Result),
    assertion(node_with_id(Result, Archive)).


test(cycle_is_terminal_occurrence) :-
    lab(Lab),
    default_options(2, Options),
    subgraph:subgraph(Lab, Options, Result),
    occurrence_with_id(
        Result,
        'o:sha256:f9196db5e8b7a1f53c9e709c38962a543c30feb9ff85e1a73e57eaaf85844280',
        Occurrence
    ),
    assertion(Occurrence.nodeId == Lab),
    assertion(Occurrence.state == cycle).


test(outgoing_mode_does_not_follow_incoming_participation) :-
    person(Person),
    Options = _{
        depth: 1,
        direction: outgoing,
        languages: [ru, en],
        limits: _{}
    },
    subgraph:subgraph(Person, Options, Result),
    node_ids(Result, NodeIds),
    assertion(\+ memberchk('urn:logiclens:participation:work', NodeIds)),
    assertion(\+ memberchk('urn:logiclens:student:study', NodeIds)).


test(incoming_mode_preserves_canonical_fact) :-
    person(Person),
    Options = _{
        depth: 1,
        direction: incoming,
        languages: [ru, en],
        limits: _{}
    },
    subgraph:subgraph(Person, Options, Result),
    member(Fact, Result.facts),
    Fact.factId == 'f:sha256:b0a5e5a69a3150e22a03e67cd709be47d8cb7319d6dc8b0cdc574cc0a582c2b3',
    !,
    assertion(Fact.subject == 'urn:logiclens:participation:work'),
    assertion(Fact.predicate == 'http://fogid.net/o/participant'),
    assertion(Fact.object.kind == iri),
    assertion(Fact.object.value == Person).


test(limit_clamping_is_diagnosed) :-
    person(Person),
    Options = _{
        depth: 99,
        direction: both,
        languages: [ru, en],
        limits: _{
            maxNodes: 999999,
            maxFacts: 999999,
            maxOccurrences: 999999,
            maxPathLength: 999999,
            maxOutputBytes: 999999999,
            timeoutMs: 999999
        }
    },
    subgraph:subgraph(Person, Options, Result),
    assertion(Result.effective.depth == 2),
    assertion(Result.effective.limits.maxNodes == 1000),
    assertion(Result.effective.limits.maxFacts == 5000),
    assertion(Result.effective.limits.maxOccurrences == 5000),
    assertion(Result.effective.limits.maxPathLength == 2),
    assertion(member(
        diagnostic{code:limit_clamped, severity:warning, message:_, context:_},
        Result.diagnostics
    )).


test(low_node_limit_selects_stable_subset) :-
    person(Person),
    Options = _{
        depth: 2,
        direction: both,
        languages: [ru, en],
        limits: _{maxNodes:2}
    },
    subgraph:subgraph(Person, Options, First),
    subgraph:subgraph(Person, Options, Second),
    compact_json(First, FirstJson),
    compact_json(Second, SecondJson),
    assertion(FirstJson == SecondJson),
    node_ids(First, NodeIds),
    assertion(NodeIds == [
        'urn:logiclens:authority:paper-author',
        'urn:logiclens:person:alex'
    ]),
    assertion(member(
        diagnostic{code:max_nodes, severity:warning, message:_, context:_},
        First.diagnostics
    )).


test(low_fact_limit_selects_first_fact_only) :-
    person(Person),
    Options = _{
        depth: 2,
        direction: both,
        languages: [ru, en],
        limits: _{maxFacts:1}
    },
    subgraph:subgraph(Person, Options, Result),
    fact_ids(Result, FactIds),
    assertion(FactIds == [
        'f:sha256:3242677a145c47ae3bc6037b8877beb244659c99fbbec00b87f8977ec60afaae'
    ]),
    node_ids(Result, NodeIds),
    assertion(NodeIds == ['urn:logiclens:person:alex']),
    assertion(member(
        diagnostic{code:max_facts, severity:warning, message:_, context:_},
        Result.diagnostics
    )).


test(low_occurrence_limit_keeps_root_and_first_path) :-
    person(Person),
    Options = _{
        depth: 2,
        direction: both,
        languages: [ru, en],
        limits: _{maxOccurrences:2}
    },
    subgraph:subgraph(Person, Options, Result),
    length(Result.occurrences, 2),
    Result.occurrences = [RootOccurrence, ChildOccurrence],
    assertion(RootOccurrence.nodeId == Person),
    assertion(ChildOccurrence.nodeId == 'urn:logiclens:authority:paper-author'),
    assertion(member(
        diagnostic{code:max_occurrences, severity:warning, message:_, context:_},
        Result.diagnostics
    )).


test(path_length_limit_is_explicit) :-
    person(Person),
    Options = _{
        depth: 2,
        direction: both,
        languages: [ru, en],
        limits: _{maxPathLength:1}
    },
    subgraph:subgraph(Person, Options, Result),
    assertion(\+ node_with_id(Result, 'urn:logiclens:org:iis')),
    forall(
        member(Occurrence, Result.occurrences),
        assertion(Occurrence.pathLength =< 1)
    ),
    assertion(member(
        diagnostic{code:max_path_length, severity:warning, message:_, context:_},
        Result.diagnostics
    )).


test(all_occurrence_fact_references_are_valid) :-
    person(Person),
    default_options(2, Options),
    subgraph:subgraph(Person, Options, Result),
    forall(
        member(Mapping, Result.occurrenceFacts),
        (
            member(Occurrence, Result.occurrences),
            Occurrence.occurrenceId == Mapping.occurrenceId,
            member(Fact, Result.facts),
            Fact.factId == Mapping.factId
        )
    ).


node_ids(Result, NodeIds) :-
    findall(NodeId, (member(Node, Result.nodes), NodeId = Node.nodeId), NodeIds).


fact_ids(Result, FactIds) :-
    findall(FactId, (member(Fact, Result.facts), FactId = Fact.factId), FactIds).


node_with_id(Result, NodeId) :-
    member(Node, Result.nodes),
    Node.nodeId == NodeId,
    !.


occurrence_with_id(Result, OccurrenceId, Occurrence) :-
    member(Occurrence, Result.occurrences),
    Occurrence.occurrenceId == OccurrenceId,
    !.


node_is(NodeId, Node) :-
    Node.nodeId == NodeId.


occurrence_is(NodeId, Occurrence) :-
    Occurrence.nodeId == NodeId.


occurrence_ids(Occurrences, OccurrenceIds) :-
    findall(Id, (member(Occurrence, Occurrences), Id = Occurrence.occurrenceId), OccurrenceIds).


compact_json(Dict, Json) :-
    with_output_to(
        string(Json),
        json_write_dict(current_output, Dict, [width(0)])
    ).


:- end_tests(bounded_subgraph).
