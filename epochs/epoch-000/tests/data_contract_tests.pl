:- begin_tests(epoch_data_contract).

:- use_module('../data/epoch_data.pl').


test(exact_fact_count) :-
    aggregate_all(count, epoch_data:fact(_, _, _, _), 29).


test(exact_origin_count) :-
    aggregate_all(count, epoch_data:origin(_, _), 10).


test(fact_origins_reference_existing_terms, [
    forall(epoch_data:fact_origin(FactId, OriginId))
]) :-
    epoch_data:fact(FactId, _, _, _),
    epoch_data:origin(OriginId, _).


test(every_fact_has_an_origin, [
    forall(epoch_data:fact(FactId, _, _, _))
]) :-
    once(epoch_data:fact_origin(FactId, _)).


test(every_origin_is_used, [
    forall(epoch_data:origin(OriginId, _))
]) :-
    once(epoch_data:fact_origin(_, OriginId)).


test(fact_identifiers_are_atoms, [
    forall(epoch_data:fact(FactId, Subject, Predicate, _))
]) :-
    atom(FactId),
    atom(Subject),
    atom(Predicate).


test(iri_objects_are_atoms, [
    forall(epoch_data:fact(_, _, _, iri(Resource)))
]) :-
    atom(Resource).


test(literal_lexical_values_are_strings, [
    forall(epoch_data:fact(_, _, _, literal(Lexical, _)))
]) :-
    string(Lexical).


test(origin_source_metadata_uses_strings, [
    forall(epoch_data:origin(
        OriginId,
        archival(SourcePath, SourceDbId, EntityId)
    ))
]) :-
    atom(OriginId),
    string(SourcePath),
    string(SourceDbId),
    atom(EntityId).


:- end_tests(epoch_data_contract).
