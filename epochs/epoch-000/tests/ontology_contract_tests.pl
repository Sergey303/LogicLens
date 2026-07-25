:- begin_tests(ontology_label_contract).

:- use_module('../ontology/ontology_data.pl').


test(person_is_a_class) :-
    ontology_data:ontology_term('http://fogid.net/o/person', class).


test(person_has_russian_and_english_labels) :-
    ontology_data:ontology_label(
        'http://fogid.net/o/person',
        forward,
        ru,
        "Персона"
    ),
    ontology_data:ontology_label(
        'http://fogid.net/o/person',
        forward,
        en,
        "Person"
    ).


test(participant_is_object_property_with_inverse_label) :-
    ontology_data:ontology_term(
        'http://fogid.net/o/participant',
        object_property
    ),
    ontology_data:ontology_label(
        'http://fogid.net/o/participant',
        forward,
        ru,
        "участник"
    ),
    ontology_data:ontology_label(
        'http://fogid.net/o/participant',
        inverse,
        ru,
        "участник в орг."
    ).


test(participant_priority_is_preserved) :-
    ontology_data:ontology_priority(
        'http://fogid.net/o/participant',
        "m"
    ).


test(name_is_datatype_property) :-
    ontology_data:ontology_term(
        'http://fogid.net/o/name',
        datatype_property
    ).


test(all_labels_reference_existing_terms, [
    forall(ontology_data:ontology_label(Resource, _, _, _))
]) :-
    ontology_data:ontology_term(Resource, _).


test(all_priorities_reference_existing_terms, [
    forall(ontology_data:ontology_priority(Resource, _))
]) :-
    ontology_data:ontology_term(Resource, _).


test(label_languages_are_atoms, [
    forall(ontology_data:ontology_label(_, _, Language, _))
]) :-
    atom(Language).


test(label_text_is_string, [
    forall(ontology_data:ontology_label(_, _, _, Text))
]) :-
    string(Text).


test(priority_is_string, [
    forall(ontology_data:ontology_priority(_, Priority))
]) :-
    string(Priority).


test(inverse_labels_belong_to_object_properties, [
    forall(ontology_data:ontology_label(Resource, inverse, _, _))
]) :-
    ontology_data:ontology_term(Resource, object_property).


test(nontrivial_ontology_was_extracted) :-
    aggregate_all(count, ontology_data:ontology_term(_, _), TermCount),
    aggregate_all(count, ontology_data:ontology_label(_, _, _, _), LabelCount),
    TermCount > 50,
    LabelCount > 100.


:- end_tests(ontology_label_contract).
