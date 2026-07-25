:- module(base_fact_view, [
    incident_fact/7,
    base_source/5,
    slice_fact/6,
    inspect_facts/4
]).

:- use_module('../data/epoch_data.pl').
:- use_module(library(pairs)).


incident_fact(
    Entity,
    DirectionMode,
    outgoing,
    FactId,
    Entity,
    Predicate,
    Object
) :-
    direction_includes(DirectionMode, outgoing),
    epoch_data:fact(FactId, Entity, Predicate, Object).
incident_fact(
    Entity,
    DirectionMode,
    incoming,
    FactId,
    Subject,
    Predicate,
    iri(Entity)
) :-
    direction_includes(DirectionMode, incoming),
    epoch_data:fact(FactId, Subject, Predicate, iri(Entity)),
    Subject \== Entity.


direction_includes(outgoing, outgoing).
direction_includes(incoming, incoming).
direction_includes(both, outgoing).
direction_includes(both, incoming).


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


slice_fact(FactId, Layer, Subject, Predicate, Object, SliceFact) :-
    base_source(FactId, Subject, Predicate, Object, Source),
    SliceFact = fact{
        factId: Source.factId,
        layer: Layer,
        subject: Source.subject,
        predicate: Source.predicate,
        object: Source.object,
        origins: Source.origins
    }.


inspect_facts(Entity, DirectionMode, Maximum, Facts) :-
    findall(
        FactId-base_fact(FactId, Subject, Predicate, Object),
        incident_fact(
            Entity,
            DirectionMode,
            _,
            FactId,
            Subject,
            Predicate,
            Object
        ),
        Pairs0
    ),
    keysort(Pairs0, Pairs),
    pairs_values(Pairs, SortedFacts),
    take_at_most(Maximum, SortedFacts, Selected),
    maplist(base_fact_source, Selected, Facts).


base_fact_source(
    base_fact(FactId, Subject, Predicate, Object),
    Source
) :-
    base_source(FactId, Subject, Predicate, Object, Source).


take_at_most(Maximum, Values, Selected) :-
    length(Values, Count),
    (   Count =< Maximum
    ->  Selected = Values
    ;   length(Selected, Maximum),
        append(Selected, _, Values)
    ).


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
