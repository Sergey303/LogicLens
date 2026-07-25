:- module(subgraph, [
    subgraph/3,
    subgraph1/3,
    subgraph2/3
]).

:- use_module('base_fact_view.pl').
:- use_module('label_rules.pl').
:- use_module('occurrence_identity.pl').
:- use_module('runtime_limits.pl').
:- use_module('traversal_policy.pl').
:- use_module(library(assoc)).
:- use_module(library(error)).
:- use_module(library(pairs)).


subgraph1(Root, Options0, Result) :-
    put_dict(depth, Options0, 1, Options),
    subgraph(Root, Options, Result).


subgraph2(Root, Options0, Result) :-
    put_dict(depth, Options0, 2, Options),
    subgraph(Root, Options, Result).


subgraph(Root, Options0, Result) :-
    must_be(atom, Root),
    must_be(dict, Options0),
    option_value(Options0, depth, 1, RequestedDepth),
    option_value(Options0, direction, both, Direction),
    option_value(Options0, limits, _{}, RequestedLimits),
    runtime_limits:effective_traversal_limits(
        RequestedDepth,
        RequestedLimits,
        EffectiveDepth,
        EffectiveLimits,
        LimitDiagnostics
    ),
    occurrence_identity:occurrence_identity(
        Root,
        [],
        RootOccurrenceId,
        _
    ),
    root_state(EffectiveDepth, EffectiveLimits.maxPathLength, RootState),
    RootOccurrence = occurrence{
        occurrenceId: RootOccurrenceId,
        nodeId: Root,
        layer: 0,
        pathLength: 0,
        parentOccurrenceId: null,
        viaFactId: null,
        direction: root,
        state: RootState
    },
    empty_assoc(Nodes0),
    put_assoc(Root, Nodes0, node_info(0), Nodes),
    empty_assoc(Facts),
    empty_assoc(Occurrences0),
    put_assoc(RootOccurrenceId, Occurrences0, RootOccurrence, Occurrences),
    empty_assoc(OccurrenceFacts),
    InitialState = state{
        nodes: Nodes,
        nodeCount: 1,
        facts: Facts,
        factCount: 0,
        occurrences: Occurrences,
        occurrenceCount: 1,
        occurrenceFacts: OccurrenceFacts,
        diagnostics: LimitDiagnostics
    },
    (   RootState == expanded
    ->  Queue = [task(0, RootOccurrenceId, Root, [Root], [])]
    ;   Queue = []
    ),
    process_queue(
        Queue,
        Root,
        Direction,
        EffectiveDepth,
        EffectiveLimits,
        InitialState,
        FinalState
    ),
    build_result(
        Root,
        RequestedDepth,
        Direction,
        RequestedLimits,
        EffectiveDepth,
        EffectiveLimits,
        Options0,
        FinalState,
        Result
    ),
    !.


root_state(Depth, PathLength, expanded) :-
    Depth > 0,
    PathLength > 0,
    !.
root_state(_, _, boundary).


process_queue([], _, _, _, _, State, State).
process_queue(
    Queue0,
    Root,
    DirectionMode,
    EffectiveDepth,
    Limits,
    State0,
    State
) :-
    sort_tasks(Queue0, [Task|Rest]),
    expand_task(
        Task,
        Root,
        DirectionMode,
        EffectiveDepth,
        Limits,
        State0,
        State1,
        Children
    ),
    append(Rest, Children, Queue1),
    process_queue(
        Queue1,
        Root,
        DirectionMode,
        EffectiveDepth,
        Limits,
        State1,
        State
    ).


sort_tasks(Tasks, Sorted) :-
    map_list_to_pairs(task_key, Tasks, Pairs),
    keysort(Pairs, SortedPairs),
    pairs_values(SortedPairs, Sorted).


task_key(task(Layer, OccurrenceId, _, _, _), key(Layer, OccurrenceId)).


expand_task(
    task(Layer, OccurrenceId, Node, PathNodes, Steps),
    Root,
    DirectionMode,
    EffectiveDepth,
    Limits,
    State0,
    State,
    Children
) :-
    incident_candidates(Node, DirectionMode, Candidates),
    FactLayer is Layer + 1,
    process_candidates(
        Candidates,
        OccurrenceId,
        Layer,
        FactLayer,
        PathNodes,
        Steps,
        Root,
        EffectiveDepth,
        Limits,
        State0,
        State,
        Children
    ).


incident_candidates(Node, DirectionMode, Candidates) :-
    findall(
        Key-candidate(
            Direction,
            FactId,
            Subject,
            Predicate,
            Object,
            NextResource
        ),
        (
            base_fact_view:incident_fact(
                Node,
                DirectionMode,
                Direction,
                FactId,
                Subject,
                Predicate,
                Object
            ),
            candidate_next_resource(
                Direction,
                Subject,
                Object,
                NextResource
            ),
            direction_rank(Direction, DirectionRank),
            Key = key(FactId, DirectionRank, NextResource)
        ),
        Pairs0
    ),
    keysort(Pairs0, Pairs),
    pairs_values(Pairs, Candidates).


candidate_next_resource(outgoing, _, iri(Resource), Resource) :-
    !.
candidate_next_resource(incoming, Subject, iri(_), Subject) :-
    !.
candidate_next_resource(_, _, _, '').


direction_rank(outgoing, 1).
direction_rank(incoming, 2).


process_candidates(
    [],
    _,
    _,
    _,
    _,
    _,
    _,
    _,
    _,
    State,
    State,
    []
).
process_candidates(
    [Candidate|Rest],
    ParentOccurrenceId,
    ParentLayer,
    FactLayer,
    PathNodes,
    Steps,
    Root,
    EffectiveDepth,
    Limits,
    State0,
    State,
    Children
) :-
    admit_candidate_fact(
        Candidate,
        ParentOccurrenceId,
        FactLayer,
        Limits,
        State0,
        State1,
        FactVisible
    ),
    (   FactVisible == true
    ->  maybe_add_child(
            Candidate,
            ParentOccurrenceId,
            ParentLayer,
            PathNodes,
            Steps,
            Root,
            EffectiveDepth,
            Limits,
            State1,
            State2,
            CandidateChildren
        )
    ;   State2 = State1,
        CandidateChildren = []
    ),
    process_candidates(
        Rest,
        ParentOccurrenceId,
        ParentLayer,
        FactLayer,
        PathNodes,
        Steps,
        Root,
        EffectiveDepth,
        Limits,
        State2,
        State3,
        RestChildren
    ),
    append(CandidateChildren, RestChildren, Children),
    State = State3.


admit_candidate_fact(
    candidate(_, FactId, Subject, Predicate, Object, _),
    OccurrenceId,
    Layer,
    Limits,
    State0,
    State,
    Visible
) :-
    get_dict(facts, State0, Facts0),
    (   get_assoc(FactId, Facts0, Existing)
    ->  update_earliest_fact_layer(
            FactId,
            Layer,
            Existing,
            Facts0,
            Facts
        ),
        put_dict(facts, State0, Facts, State1),
        Visible = true
    ;   State0.factCount < Limits.maxFacts
    ->  base_fact_view:slice_fact(
            FactId,
            Layer,
            Subject,
            Predicate,
            Object,
            SliceFact
        ),
        put_assoc(FactId, Facts0, SliceFact, Facts),
        NextCount is State0.factCount + 1,
        put_dict(_{facts:Facts, factCount:NextCount}, State0, State1),
        Visible = true
    ;   limit_diagnostic(
            max_facts,
            "Global fact limit omitted additional facts.",
            _{maximum:Limits.maxFacts},
            Diagnostic
        ),
        add_diagnostic(Diagnostic, State0, State1),
        Visible = false
    ),
    (   Visible == true
    ->  add_occurrence_fact(
            OccurrenceId,
            FactId,
            Layer,
            State1,
            State
        )
    ;   State = State1
    ).


update_earliest_fact_layer(FactId, Layer, Existing, Facts0, Facts) :-
    (   Layer < Existing.layer
    ->  put_dict(layer, Existing, Layer, Updated),
        put_assoc(FactId, Facts0, Updated, Facts)
    ;   Facts = Facts0
    ).


add_occurrence_fact(OccurrenceId, FactId, Layer, State0, State) :-
    Key = OccurrenceId-FactId,
    Mapping = occurrence_fact{
        occurrenceId: OccurrenceId,
        factId: FactId,
        layer: Layer
    },
    OccurrenceFacts0 = State0.occurrenceFacts,
    (   get_assoc(Key, OccurrenceFacts0, _)
    ->  OccurrenceFacts = OccurrenceFacts0
    ;   put_assoc(Key, OccurrenceFacts0, Mapping, OccurrenceFacts)
    ),
    put_dict(occurrenceFacts, State0, OccurrenceFacts, State).


maybe_add_child(
    candidate(Direction, FactId, Subject, Predicate, Object, NextResource),
    ParentOccurrenceId,
    ParentLayer,
    PathNodes,
    Steps,
    Root,
    EffectiveDepth,
    Limits,
    State0,
    State,
    Children
) :-
    ChildLayer is ParentLayer + 1,
    edge_target(Direction, Subject, Object, NextResource, Target),
    traversal_policy:traversal_allowed(Predicate),
    ChildLayer =< EffectiveDepth,
    ChildLayer =< Limits.maxPathLength,
    !,
    add_child_occurrence(
        Target,
        Direction,
        FactId,
        ParentOccurrenceId,
        ChildLayer,
        PathNodes,
        Steps,
        Root,
        EffectiveDepth,
        Limits,
        State0,
        State,
        Children
    ).
maybe_add_child(_, _, ParentLayer, _, _, _, EffectiveDepth, Limits, State0, State, []) :-
    (   ParentLayer < EffectiveDepth,
        ParentLayer >= Limits.maxPathLength
    ->  limit_diagnostic(
            max_path_length,
            "Path-length limit stopped further expansion.",
            _{maximum:Limits.maxPathLength},
            Diagnostic
        ),
        add_diagnostic(Diagnostic, State0, State)
    ;   State = State0
    ).


edge_target(outgoing, _, iri(Target), Target, Target).
edge_target(incoming, Subject, iri(_), Subject, Subject).


add_child_occurrence(
    Target,
    Direction,
    FactId,
    ParentOccurrenceId,
    ChildLayer,
    PathNodes,
    Steps,
    Root,
    EffectiveDepth,
    Limits,
    State0,
    State,
    Children
) :-
    (   memberchk(Target, PathNodes)
    ->  NodeAllowed = true,
        Cycle = true,
        State1 = State0
    ;   admit_node(Target, ChildLayer, Limits, State0, State1, NodeAllowed),
        Cycle = false
    ),
    (   NodeAllowed == false
    ->  State = State1,
        Children = []
    ;   State1.occurrenceCount >= Limits.maxOccurrences
    ->  limit_diagnostic(
            max_occurrences,
            "Global occurrence limit omitted additional paths.",
            _{maximum:Limits.maxOccurrences},
            Diagnostic
        ),
        add_diagnostic(Diagnostic, State1, State),
        Children = []
    ;   append(Steps, [step(FactId, Direction)], ChildSteps),
        occurrence_identity:occurrence_identity(
            Root,
            ChildSteps,
            OccurrenceId,
            _
        ),
        occurrence_state(
            Cycle,
            ChildLayer,
            EffectiveDepth,
            Limits.maxPathLength,
            OccurrenceState
        ),
        ChildOccurrence = occurrence{
            occurrenceId: OccurrenceId,
            nodeId: Target,
            layer: ChildLayer,
            pathLength: ChildLayer,
            parentOccurrenceId: ParentOccurrenceId,
            viaFactId: FactId,
            direction: Direction,
            state: OccurrenceState
        },
        add_occurrence(ChildOccurrence, State1, State2),
        (   OccurrenceState == expanded
        ->  append(PathNodes, [Target], ChildPathNodes),
            Children = [task(
                ChildLayer,
                OccurrenceId,
                Target,
                ChildPathNodes,
                ChildSteps
            )]
        ;   Children = []
        ),
        State = State2
    ).


admit_node(Target, Layer, Limits, State0, State, Allowed) :-
    Nodes0 = State0.nodes,
    (   get_assoc(Target, Nodes0, node_info(ExistingLayer))
    ->  (   Layer < ExistingLayer
        ->  put_assoc(Target, Nodes0, node_info(Layer), Nodes)
        ;   Nodes = Nodes0
        ),
        put_dict(nodes, State0, Nodes, State),
        Allowed = true
    ;   State0.nodeCount < Limits.maxNodes
    ->  put_assoc(Target, Nodes0, node_info(Layer), Nodes),
        NextCount is State0.nodeCount + 1,
        put_dict(_{nodes:Nodes, nodeCount:NextCount}, State0, State),
        Allowed = true
    ;   limit_diagnostic(
            max_nodes,
            "Global node limit omitted additional resources.",
            _{maximum:Limits.maxNodes},
            Diagnostic
        ),
        add_diagnostic(Diagnostic, State0, State),
        Allowed = false
    ).


occurrence_state(true, _, _, _, cycle).
occurrence_state(false, Layer, EffectiveDepth, MaxPathLength, expanded) :-
    Layer < EffectiveDepth,
    Layer < MaxPathLength,
    !.
occurrence_state(false, _, _, _, boundary).


add_occurrence(Occurrence, State0, State) :-
    Occurrences0 = State0.occurrences,
    OccurrenceId = Occurrence.occurrenceId,
    (   get_assoc(OccurrenceId, Occurrences0, Existing)
    ->  (   Existing == Occurrence
        ->  Occurrences = Occurrences0,
            Count = State0.occurrenceCount
        ;   throw(error(
                occurrence_id_collision(OccurrenceId),
                subgraph/3
            ))
        )
    ;   put_assoc(OccurrenceId, Occurrences0, Occurrence, Occurrences),
        Count is State0.occurrenceCount + 1
    ),
    put_dict(_{occurrences:Occurrences, occurrenceCount:Count}, State0, State).


limit_diagnostic(Code, Message, Context, diagnostic{
    code: Code,
    severity: warning,
    message: Message,
    context: Context
}).


add_diagnostic(Diagnostic, State0, State) :-
    Diagnostics0 = State0.diagnostics,
    (   memberchk(Diagnostic, Diagnostics0)
    ->  Diagnostics = Diagnostics0
    ;   Diagnostics = [Diagnostic|Diagnostics0]
    ),
    put_dict(diagnostics, State0, Diagnostics, State).


build_result(
    Root,
    RequestedDepth,
    Direction,
    RequestedLimits,
    EffectiveDepth,
    EffectiveLimits,
    Options,
    State,
    Result
) :-
    assoc_to_list(State.nodes, NodePairs),
    maplist(node_dict(Options), NodePairs, Nodes0),
    sort_nodes(Nodes0, Nodes),
    assoc_to_values(State.facts, Facts0),
    sort_facts(Facts0, Facts),
    assoc_to_values(State.occurrences, Occurrences0),
    sort_occurrences(Occurrences0, Occurrences),
    assoc_to_values(State.occurrenceFacts, OccurrenceFacts0),
    sort_occurrence_facts(OccurrenceFacts0, OccurrenceFacts),
    sort_diagnostics(State.diagnostics, Diagnostics),
    Result = subgraph{
        kind: subgraph,
        root: Root,
        requested: _{
            depth: RequestedDepth,
            direction: Direction,
            limits: RequestedLimits
        },
        effective: _{
            depth: EffectiveDepth,
            direction: Direction,
            limits: EffectiveLimits
        },
        nodes: Nodes,
        facts: Facts,
        occurrences: Occurrences,
        occurrenceFacts: OccurrenceFacts,
        diagnostics: Diagnostics
    }.


node_dict(Options, NodeId-node_info(Layer), Node) :-
    label_rules:resource_label(NodeId, Options, Label),
    Node = node{
        nodeId: NodeId,
        layer: Layer,
        label: Label
    }.


sort_nodes(Values, Sorted) :-
    map_list_to_pairs(node_key, Values, Pairs),
    keysort(Pairs, SortedPairs),
    pairs_values(SortedPairs, Sorted).


node_key(Node, Node.nodeId).


sort_facts(Values, Sorted) :-
    map_list_to_pairs(fact_key, Values, Pairs),
    keysort(Pairs, SortedPairs),
    pairs_values(SortedPairs, Sorted).


fact_key(Fact, Fact.factId).


sort_occurrences(Values, Sorted) :-
    map_list_to_pairs(occurrence_key, Values, Pairs),
    keysort(Pairs, SortedPairs),
    pairs_values(SortedPairs, Sorted).


occurrence_key(Occurrence, key(Occurrence.layer, Occurrence.occurrenceId)).


sort_occurrence_facts(Values, Sorted) :-
    map_list_to_pairs(occurrence_fact_key, Values, Pairs),
    keysort(Pairs, SortedPairs),
    pairs_values(SortedPairs, Sorted).


occurrence_fact_key(
    Mapping,
    key(Mapping.layer, Mapping.occurrenceId, Mapping.factId)
).


sort_diagnostics(Values, Sorted) :-
    map_list_to_pairs(diagnostic_key, Values, Pairs),
    keysort(Pairs, SortedPairs),
    pairs_values(SortedPairs, Sorted).


diagnostic_key(Diagnostic, key(Diagnostic.code, ContextString)) :-
    term_string(
        Diagnostic.context,
        ContextString,
        [quoted(true), numbervars(true)]
    ).


option_value(Dict, Key, Default, Value) :-
    (   get_dict(Key, Dict, Found)
    ->  Value = Found
    ;   Value = Default
    ).
