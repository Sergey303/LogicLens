:- module(subgraph, [
    build_subgraph/8,
    occurrence_id/3
]).

:- use_module('../data/epoch_data.pl').
:- use_module('label_rules.pl').
:- use_module('traversal_policy.pl').
:- use_module(library(lists)).
:- use_module(library(pairs)).
:- use_module(library(sha)).


build_subgraph(
    Root,
    RequestedDepth,
    EffectiveDepth,
    Direction,
    LabelOptions,
    Limits,
    Result,
    Diagnostics
) :-
    occurrence_id(Root, [], RootOccurrenceId),
    root_state(EffectiveDepth, RootState),
    RootOccurrence = occurrence(
        RootOccurrenceId,
        Root,
        0,
        null,
        null,
        null,
        RootState,
        [],
        [Root]
    ),
    initial_queue(
        EffectiveDepth,
        RootOccurrenceId,
        Root,
        Queue
    ),
    State0 = state{
        nodes: [node(Root, 0)],
        facts: [],
        occurrences: [RootOccurrence],
        occurrence_facts: [],
        queue: Queue,
        halted: false,
        truncated: false,
        diagnostics: []
    },
    traverse(EffectiveDepth, Direction, Limits, State0, State),
    finalize_result(
        Root,
        RequestedDepth,
        EffectiveDepth,
        Direction,
        LabelOptions,
        Limits,
        State,
        Result,
        Diagnostics
    ).


root_state(0, boundary) :- !.
root_state(_, expanded).


initial_queue(0, _, _, []) :- !.
initial_queue(_, OccurrenceId, Root, [work(OccurrenceId, Root, 0, [], [Root])]).


traverse(_, _, _, State, State) :-
    State.halted == true,
    !.
traverse(_, _, _, State, State) :-
    State.queue == [],
    !.
traverse(EffectiveDepth, Direction, Limits, State0, State) :-
    pop_next_work(State0.queue, Work, RemainingQueue),
    State1 = State0.put(queue, RemainingQueue),
    expand_work(
        Work,
        EffectiveDepth,
        Direction,
        Limits,
        State1,
        State2
    ),
    traverse(EffectiveDepth, Direction, Limits, State2, State).


pop_next_work(Queue, Work, Remaining) :-
    map_list_to_pairs(work_key, Queue, Pairs),
    keysort(Pairs, [_-Work|RestPairs]),
    pairs_values(RestPairs, Remaining).


work_key(work(OccurrenceId, _, Depth, _, _), key(Depth, OccurrenceId)).


expand_work(
    work(OccurrenceId, Node, Depth, Steps, PathNodes),
    EffectiveDepth,
    Direction,
    Limits,
    State0,
    State
) :-
    Layer is Depth + 1,
    ordered_candidates(Node, Direction, Candidates),
    process_candidates(
        Candidates,
        OccurrenceId,
        Layer,
        Depth,
        Steps,
        PathNodes,
        EffectiveDepth,
        Limits,
        State0,
        State
    ).


ordered_candidates(Node, DirectionMode, Candidates) :-
    findall(
        Key-Candidate,
        incident_candidate(Node, DirectionMode, Key, Candidate),
        Pairs0
    ),
    keysort(Pairs0, Pairs),
    pairs_values(Pairs, Candidates).


incident_candidate(
    Node,
    DirectionMode,
    key(FactId, 0, NextKey),
    candidate(FactId, outgoing, Node, Predicate, Object, Next, Traversable)
) :-
    direction_allowed(DirectionMode, outgoing),
    epoch_data:fact(FactId, Node, Predicate, Object),
    outgoing_target(Predicate, Object, Next, NextKey, Traversable).
incident_candidate(
    Node,
    DirectionMode,
    key(FactId, 1, Subject),
    candidate(FactId, incoming, Subject, Predicate, iri(Node), Subject, Traversable)
) :-
    direction_allowed(DirectionMode, incoming),
    epoch_data:fact(FactId, Subject, Predicate, iri(Node)),
    traversal_flag(Predicate, Traversable).


direction_allowed(outgoing, outgoing).
direction_allowed(incoming, incoming).
direction_allowed(both, outgoing).
direction_allowed(both, incoming).


outgoing_target(Predicate, iri(Resource), Resource, Resource, Traversable) :-
    !,
    traversal_flag(Predicate, Traversable).
outgoing_target(_, _, null, '', false).


traversal_flag(Predicate, true) :-
    traversal_policy:traversal_predicate(Predicate),
    !.
traversal_flag(_, false).


process_candidates([], _, _, _, _, _, _, _, State, State).
process_candidates(_, _, _, _, _, _, _, _, State, State) :-
    State.halted == true,
    !.
process_candidates(
    [Candidate|Rest],
    OccurrenceId,
    Layer,
    Depth,
    Steps,
    PathNodes,
    EffectiveDepth,
    Limits,
    State0,
    State
) :-
    process_candidate(
        Candidate,
        OccurrenceId,
        Layer,
        Depth,
        Steps,
        PathNodes,
        EffectiveDepth,
        Limits,
        State0,
        State1
    ),
    process_candidates(
        Rest,
        OccurrenceId,
        Layer,
        Depth,
        Steps,
        PathNodes,
        EffectiveDepth,
        Limits,
        State1,
        State
    ).


process_candidate(
    candidate(FactId, StepDirection, Subject, Predicate, Object, Next, Traversable),
    OccurrenceId,
    Layer,
    Depth,
    Steps,
    PathNodes,
    EffectiveDepth,
    Limits,
    State0,
    State
) :-
    admit_fact(
        FactId,
        Layer,
        Subject,
        Predicate,
        Object,
        Limits.maxFacts,
        State0,
        State1,
        Admitted,
        ExposedHere
    ),
    (   Admitted == true,
        ExposedHere == true
    ->  add_occurrence_fact(OccurrenceId, FactId, Layer, State1, State2)
    ;   State2 = State1
    ),
    (   Admitted == true,
        ExposedHere == true,
        Traversable == true
    ->  admit_child_occurrence(
            FactId,
            StepDirection,
            Next,
            Depth,
            Steps,
            PathNodes,
            EffectiveDepth,
            Limits,
            State2,
            State
        )
    ;   State = State2
    ).


admit_fact(FactId, Layer, _, _, _, _, State, State, true, ExposedHere) :-
    existing_fact_layer(FactId, State.facts, ExistingLayer),
    !,
    (   ExistingLayer =:= Layer
    ->  ExposedHere = true
    ;   ExposedHere = false
    ).
admit_fact(FactId, Layer, Subject, Predicate, Object, MaxFacts, State0, State, Admitted, ExposedHere) :-
    length(State0.facts, Count),
    (   Count < MaxFacts
    ->  State = State0.put(
            facts,
            [slice_fact(FactId, Layer, Subject, Predicate, Object)|State0.facts]
        ),
        Admitted = true,
        ExposedHere = true
    ;   block_on_limit(maxFacts, State0, State),
        Admitted = false,
        ExposedHere = false
    ).


existing_fact_layer(FactId, [slice_fact(FactId, Layer, _, _, _)|_], Layer) :- !.
existing_fact_layer(FactId, [_|Rest], Layer) :-
    existing_fact_layer(FactId, Rest, Layer).


add_occurrence_fact(OccurrenceId, FactId, Layer, State, State) :-
    memberchk(
        occurrence_fact(OccurrenceId, FactId, Layer),
        State.occurrence_facts
    ),
    !.
add_occurrence_fact(OccurrenceId, FactId, Layer, State0, State) :-
    State = State0.put(
        occurrence_facts,
        [occurrence_fact(OccurrenceId, FactId, Layer)|State0.occurrence_facts]
    ).


admit_child_occurrence(
    FactId,
    StepDirection,
    Next,
    Depth,
    Steps,
    PathNodes,
    EffectiveDepth,
    Limits,
    State0,
    State
) :-
    append(Steps, [step(FactId, StepDirection)], ChildSteps),
    occurrence_id_from_steps(ChildSteps, PathNodes, Next, ChildOccurrenceId),
    (   occurrence_exists(ChildOccurrenceId, State0.occurrences)
    ->  State = State0
    ;   precheck_node_limit(Next, Limits.maxNodes, State0, NodeAllowed),
        (   NodeAllowed == false
        ->  block_on_limit(maxNodes, State0, State)
        ;   precheck_occurrence_limit(
                Limits.maxOccurrences,
                State0,
                OccurrenceAllowed
            ),
            (   OccurrenceAllowed == false
            ->  block_on_limit(maxOccurrences, State0, State)
            ;   create_child_occurrence(
                    FactId,
                    StepDirection,
                    Next,
                    Depth,
                    ChildSteps,
                    PathNodes,
                    EffectiveDepth,
                    Limits,
                    ChildOccurrenceId,
                    State0,
                    State
                )
            )
        )
    ).


occurrence_id_from_steps(Steps, PathNodes, _, OccurrenceId) :-
    PathNodes = [Root|_],
    occurrence_id(Root, Steps, OccurrenceId).


occurrence_exists(Id, [occurrence(Id, _, _, _, _, _, _, _, _)|_]) :- !.
occurrence_exists(Id, [_|Rest]) :- occurrence_exists(Id, Rest).


precheck_node_limit(Node, _, State, true) :-
    node_exists(Node, State.nodes),
    !.
precheck_node_limit(_, MaxNodes, State, Allowed) :-
    length(State.nodes, Count),
    ( Count < MaxNodes -> Allowed = true ; Allowed = false ).


precheck_occurrence_limit(MaxOccurrences, State, Allowed) :-
    length(State.occurrences, Count),
    ( Count < MaxOccurrences -> Allowed = true ; Allowed = false ).


node_exists(Node, [node(Node, _)|_]) :- !.
node_exists(Node, [_|Rest]) :- node_exists(Node, Rest).


create_child_occurrence(
    FactId,
    StepDirection,
    Next,
    Depth,
    ChildSteps,
    PathNodes,
    EffectiveDepth,
    Limits,
    ChildOccurrenceId,
    State0,
    State
) :-
    ChildDepth is Depth + 1,
    append(PathNodes, [Next], ChildPathNodes),
    child_state(
        Next,
        PathNodes,
        ChildDepth,
        EffectiveDepth,
        Limits.maxPathLength,
        ChildState
    ),
    current_parent(ChildSteps, State0, ParentOccurrenceId),
    ChildOccurrence = occurrence(
        ChildOccurrenceId,
        Next,
        ChildDepth,
        ParentOccurrenceId,
        FactId,
        StepDirection,
        ChildState,
        ChildSteps,
        ChildPathNodes
    ),
    add_node_if_missing(Next, ChildDepth, State0, State1),
    State2 = State1.put(
        occurrences,
        [ChildOccurrence|State1.occurrences]
    ),
    add_work_if_expanded(ChildOccurrence, State2, State).


current_parent(ChildSteps, State, ParentOccurrenceId) :-
    append(ParentSteps, [_], ChildSteps),
    member(
        occurrence(ParentOccurrenceId, _, _, _, _, _, _, ParentSteps, _),
        State.occurrences
    ),
    !.


child_state(Node, PathNodes, _, _, _, cycle_reference) :-
    memberchk(Node, PathNodes),
    !.
child_state(_, _, ChildDepth, EffectiveDepth, MaxPathLength, expanded) :-
    ChildDepth < EffectiveDepth,
    ChildDepth < MaxPathLength,
    !.
child_state(_, _, _, _, _, boundary).


add_node_if_missing(Node, _, State, State) :-
    node_exists(Node, State.nodes),
    !.
add_node_if_missing(Node, Distance, State0, State) :-
    State = State0.put(nodes, [node(Node, Distance)|State0.nodes]).


add_work_if_expanded(
    occurrence(Id, Node, Depth, _, _, _, expanded, Steps, PathNodes),
    State0,
    State
) :-
    !,
    State = State0.put(
        queue,
        [work(Id, Node, Depth, Steps, PathNodes)|State0.queue]
    ).
add_work_if_expanded(_, State, State).


block_on_limit(Limit, State, State) :-
    State.halted == true,
    !.
block_on_limit(Limit, State0, State) :-
    atom_string(Limit, LimitText),
    Diagnostic = diagnostic{
        code: "limit_reached",
        severity: warning,
        message: "Traversal stopped at the first deterministic global limit.",
        context: _{limit: LimitText}
    },
    State = State0.put(_{
        halted: true,
        truncated: true,
        diagnostics: [Diagnostic|State0.diagnostics]
    }).


finalize_result(
    Root,
    RequestedDepth,
    EffectiveDepth,
    Direction,
    LabelOptions,
    Limits,
    State,
    Result,
    Diagnostics
) :-
    sort_nodes(State.nodes, SortedNodes),
    maplist(node_dict(LabelOptions), SortedNodes, NodeDicts),
    sort_facts(State.facts, SortedFacts),
    maplist(fact_dict, SortedFacts, FactDicts),
    sort_occurrences(State.occurrences, SortedOccurrences),
    maplist(occurrence_dict, SortedOccurrences, OccurrenceDicts),
    occurrence_fact_dicts(
        SortedOccurrences,
        State.occurrence_facts,
        OccurrenceFactDicts
    ),
    sort(State.diagnostics, Diagnostics),
    Result = subgraph_result{
        kind: subgraph,
        root: Root,
        requestedDepth: RequestedDepth,
        effectiveDepth: EffectiveDepth,
        direction: Direction,
        effectiveLimits: Limits,
        truncated: State.truncated,
        nodes: NodeDicts,
        facts: FactDicts,
        occurrences: OccurrenceDicts,
        occurrenceFacts: OccurrenceFactDicts
    }.


sort_nodes(Nodes, Sorted) :-
    map_list_to_pairs(node_key, Nodes, Pairs),
    keysort(Pairs, SortedPairs),
    pairs_values(SortedPairs, Sorted).


node_key(node(Node, _), Node).


node_dict(LabelOptions, node(Node, Distance), Dict) :-
    label_rules:resource_label(Node, LabelOptions, Label),
    Dict = node{
        id: Node,
        minimumDistance: Distance,
        label: Label
    }.


sort_facts(Facts, Sorted) :-
    map_list_to_pairs(fact_key, Facts, Pairs),
    keysort(Pairs, SortedPairs),
    pairs_values(SortedPairs, Sorted).


fact_key(slice_fact(FactId, _, _, _, _), FactId).


fact_dict(slice_fact(FactId, Layer, Subject, Predicate, Object), Dict) :-
    object_dict(Object, ObjectDict),
    findall(
        OriginId,
        epoch_data:fact_origin(FactId, OriginId),
        Origins0
    ),
    sort(Origins0, Origins),
    Dict = fact{
        factId: FactId,
        layer: Layer,
        subject: Subject,
        predicate: Predicate,
        object: ObjectDict,
        origins: Origins
    }.


object_dict(iri(Resource), object{
    kind: iri,
    value: Resource
}).
object_dict(literal(Text, plain), object{
    kind: literal,
    literalKind: plain,
    lexical: Text,
    language: null,
    datatype: null
}).
object_dict(literal(Text, lang(Language)), object{
    kind: literal,
    literalKind: language,
    lexical: Text,
    language: Language,
    datatype: null
}).
object_dict(literal(Text, datatype(Datatype)), object{
    kind: literal,
    literalKind: datatype,
    lexical: Text,
    language: null,
    datatype: Datatype
}).


sort_occurrences(Occurrences, Sorted) :-
    map_list_to_pairs(occurrence_key, Occurrences, Pairs),
    keysort(Pairs, SortedPairs),
    pairs_values(SortedPairs, Sorted).


occurrence_key(
    occurrence(Id, _, Depth, _, _, _, _, _, _),
    key(Depth, Id)
).


occurrence_dict(
    occurrence(Id, Node, Depth, Parent, ViaFact, Direction, State, _, _),
    Dict
) :-
    Dict = occurrence{
        occurrenceId: Id,
        nodeId: Node,
        depth: Depth,
        parentOccurrenceId: Parent,
        viaFactId: ViaFact,
        direction: Direction,
        state: State
    }.


occurrence_fact_dicts(Occurrences, Mappings, Dicts) :-
    findall(
        key(Depth, OccurrenceId)-occurrence_facts{
            occurrenceId: OccurrenceId,
            factIds: FactIds
        },
        (
            member(
                occurrence(OccurrenceId, _, Depth, _, _, _, _, _, _),
                Occurrences
            ),
            findall(
                FactId,
                member(
                    occurrence_fact(OccurrenceId, FactId, _),
                    Mappings
                ),
                FactIds0
            ),
            sort(FactIds0, FactIds),
            FactIds \== []
        ),
        Pairs0
    ),
    keysort(Pairs0, Pairs),
    pairs_values(Pairs, Dicts).


occurrence_id(Root, Steps, OccurrenceId) :-
    atom_string(Root, RootText),
    string_bytes("LogicLensOccurrence", Prefix, utf8),
    field_bytes(RootText, RootField),
    steps_bytes(Steps, StepBytes),
    append([Prefix, [0, 1], RootField, StepBytes], CanonicalBytes),
    sha_hash(CanonicalBytes, Hash, [algorithm(sha256)]),
    hash_atom(Hash, HashAtom),
    atom_concat('o:sha256:', HashAtom, OccurrenceId).


field_bytes(Text, Bytes) :-
    string_bytes(Text, Utf8, utf8),
    length(Utf8, Length),
    unsigned_64_be(Length, Prefix),
    append(Prefix, Utf8, Bytes).


steps_bytes([], []).
steps_bytes([step(FactId, Direction)|Rest], Bytes) :-
    atom_string(FactId, FactText),
    field_bytes(FactText, FactBytes),
    direction_tag(Direction, DirectionTag),
    steps_bytes(Rest, RestBytes),
    append([FactBytes, [DirectionTag], RestBytes], Bytes).


direction_tag(outgoing, 1).
direction_tag(incoming, 2).


unsigned_64_be(Value, [B7, B6, B5, B4, B3, B2, B1, B0]) :-
    B7 is (Value >> 56) /\ 255,
    B6 is (Value >> 48) /\ 255,
    B5 is (Value >> 40) /\ 255,
    B4 is (Value >> 32) /\ 255,
    B3 is (Value >> 24) /\ 255,
    B2 is (Value >> 16) /\ 255,
    B1 is (Value >> 8) /\ 255,
    B0 is Value /\ 255.
