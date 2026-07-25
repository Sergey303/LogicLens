:- module(generic_view, [
    entity_view/3,
    entity_prolog/2,
    incident_fact/6
]).

:- use_module('../data/epoch_data.pl').
:- use_module('label_rules.pl').
:- use_module('view_policy.pl').
:- use_module(library(lists)).
:- use_module(library(pairs)).


entity_view(Entity, Options, View) :-
    label_rules:resource_label(Entity, Options, Title),
    findall(
        group_key(Direction, Predicate)-base_fact(
            FactId,
            Subject,
            Predicate,
            Object
        ),
        incident_fact(
            Entity,
            Direction,
            FactId,
            Subject,
            Predicate,
            Object
        ),
        Pairs0
    ),
    keysort(Pairs0, Pairs),
    group_pairs_by_key(Pairs, GroupedFacts),
    maplist(build_group(Options), GroupedFacts, Groups0),
    sort_groups(Groups0, Groups),
    View = entity_view{
        kind: entity_view,
        entity: Entity,
        title: Title,
        groups: Groups,
        diagnostics: []
    },
    !.


incident_fact(
    Entity,
    outgoing,
    FactId,
    Entity,
    Predicate,
    Object
) :-
    epoch_data:fact(FactId, Entity, Predicate, Object).
incident_fact(
    Entity,
    incoming,
    FactId,
    Subject,
    Predicate,
    iri(Entity)
) :-
    epoch_data:fact(FactId, Subject, Predicate, iri(Entity)),
    Subject \== Entity.


build_group(
    Options,
    group_key(Direction, Predicate)-Facts0,
    Group
) :-
    label_rules:predicate_label(
        Predicate,
        Direction,
        Options,
        Label,
        Priority
    ),
    (   view_policy:technical_predicate(Predicate)
    ->  Technical = true
    ;   Technical = false
    ),
    sort_facts(Facts0, Facts),
    maplist(fact_value(Direction, Options), Facts, Values),
    Group = group{
        direction: Direction,
        predicate: Predicate,
        label: Label,
        priority: Priority,
        technical: Technical,
        values: Values
    }.


fact_value(
    outgoing,
    Options,
    base_fact(FactId, Subject, Predicate, Object),
    Value
) :-
    base_source(FactId, Subject, Predicate, Object, Source),
    outgoing_value(Object, Options, Source, Value).
fact_value(
    incoming,
    Options,
    base_fact(FactId, Subject, Predicate, Object),
    Value
) :-
    base_source(FactId, Subject, Predicate, Object, Source),
    label_rules:resource_label(Subject, Options, Label),
    Value = value{
        kind: resourceLink,
        targetId: Subject,
        label: Label,
        source: Source
    }.


outgoing_value(iri(Resource), Options, Source, Value) :-
    label_rules:resource_label(Resource, Options, Label),
    Value = value{
        kind: resourceLink,
        targetId: Resource,
        label: Label,
        source: Source
    }.
outgoing_value(literal(Text, plain), _, Source, Value) :-
    Value = value{
        kind: text,
        text: Text,
        literalKind: plain,
        language: null,
        datatype: null,
        source: Source
    }.
outgoing_value(literal(Text, lang(Language)), _, Source, Value) :-
    Value = value{
        kind: text,
        text: Text,
        literalKind: language,
        language: Language,
        datatype: null,
        source: Source
    }.
outgoing_value(literal(Text, datatype(Datatype)), _, Source, Value) :-
    Value = value{
        kind: text,
        text: Text,
        literalKind: datatype,
        language: null,
        datatype: Datatype,
        source: Source
    }.


base_source(FactId, Subject, Predicate, Object, Source) :-
    object_dict(Object, ObjectDict),
    findall(
        OriginId,
        epoch_data:fact_origin(FactId, OriginId),
        Origins0
    ),
    sort(Origins0, Origins),
    Source = source{
        kind: base,
        factId: FactId,
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


sort_facts(Facts, Sorted) :-
    map_list_to_pairs(fact_sort_key, Facts, Pairs),
    keysort(Pairs, SortedPairs),
    pairs_values(SortedPairs, Sorted).


fact_sort_key(base_fact(FactId, _, _, _), FactId).


sort_groups(Groups, Sorted) :-
    map_list_to_pairs(group_sort_key, Groups, Pairs),
    keysort(Pairs, SortedPairs),
    pairs_values(SortedPairs, Sorted).


group_sort_key(
    Group,
    key(TechnicalRank, PriorityKey, DirectionRank, Predicate)
) :-
    (   Group.technical == true
    ->  TechnicalRank = 1
    ;   TechnicalRank = 0
    ),
    (   Group.priority == null
    ->  PriorityKey = "~"
    ;   PriorityKey = Group.priority
    ),
    direction_rank(Group.direction, DirectionRank),
    Predicate = Group.predicate.


direction_rank(outgoing, 0).
direction_rank(incoming, 1).


entity_prolog(Entity, Text) :-
    findall(
        base_fact(FactId, Subject, Predicate, Object),
        incident_fact(
            Entity,
            _,
            FactId,
            Subject,
            Predicate,
            Object
        ),
        Facts0
    ),
    sort_facts(Facts0, Facts),
    with_output_to(
        string(Text),
        forall(
            member(base_fact(FactId, Subject, Predicate, Object), Facts),
            (
                write_term(
                    fact(FactId, Subject, Predicate, Object),
                    [quoted(true), numbervars(true)]
                ),
                write('.'),
                nl
            )
        )
    ),
    !.
