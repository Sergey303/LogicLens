:- begin_tests(generic_entity_view).

:- use_module('../rules/generic_view.pl').
:- use_module('../rules/label_rules.pl').


person('urn:logiclens:person:alex').
paper('urn:logiclens:document:paper').
lab('urn:logiclens:org:lab').


default_options(_{languages:[ru, en]}).


test(person_title_prefers_russian_data_name) :-
    person(Person),
    default_options(Options),
    generic_view:entity_view(Person, Options, View),
    assertion(View.title == "Алексей Ветров").


test(document_title_falls_back_to_english) :-
    paper(Paper),
    default_options(Options),
    generic_view:entity_view(Paper, Options, View),
    assertion(View.title == "Verified Logic Interfaces").


test(organization_title_falls_back_to_plain) :-
    lab(Lab),
    default_options(Options),
    generic_view:entity_view(Lab, Options, View),
    assertion(View.title == "Logic Lab").


test(class_resource_uses_ontology_label) :-
    default_options(Options),
    label_rules:resource_label(
        'http://fogid.net/o/person',
        Options,
        Label
    ),
    assertion(Label == "Персона").


test(unknown_resource_uses_compact_identifier) :-
    default_options(Options),
    label_rules:resource_label(
        'urn:logiclens:unknown:sample',
        Options,
        Label
    ),
    assertion(Label == "sample").


test(person_has_exactly_eight_incident_facts_once) :-
    person(Person),
    default_options(Options),
    generic_view:entity_view(Person, Options, View),
    view_fact_ids(View, ViewFactIds),
    findall(
        FactId,
        generic_view:incident_fact(Person, _, FactId, _, _, _),
        IncidentFactIds0
    ),
    sort(IncidentFactIds0, IncidentFactIds),
    assertion(ViewFactIds == IncidentFactIds),
    assertion(ViewFactIds = [_, _, _, _, _, _, _, _]).


test(person_name_values_share_one_group) :-
    person(Person),
    default_options(Options),
    generic_view:entity_view(Person, Options, View),
    view_group(
        View,
        outgoing,
        'http://fogid.net/o/name',
        Group
    ),
    assertion(Group.label == "имя"),
    assertion(Group.values = [_, _]).


test(incoming_participant_uses_inverse_label_and_full_source) :-
    person(Person),
    default_options(Options),
    generic_view:entity_view(Person, Options, View),
    view_group(
        View,
        incoming,
        'http://fogid.net/o/participant',
        Group
    ),
    assertion(Group.label == "участник в орг."),
    assertion(Group.values = [Value]),
    assertion(Value.kind == resourceLink),
    assertion(Value.targetId == 'urn:logiclens:participation:work'),
    assertion(Value.source.subject == 'urn:logiclens:participation:work'),
    assertion(Value.source.predicate == 'http://fogid.net/o/participant'),
    assertion(Value.source.object.kind == iri),
    assertion(Value.source.object.value == Person).


test(unknown_technical_predicate_is_visible_and_marked) :-
    person(Person),
    default_options(Options),
    generic_view:entity_view(Person, Options, View),
    view_group(
        View,
        outgoing,
        'urn:logiclens:test:internal-code',
        Group
    ),
    assertion(Group.label == "internal-code"),
    assertion(Group.technical == true),
    assertion(Group.values = [Value]),
    assertion(Value.text == "A-17").


test(rdf_type_uses_builtin_label_and_class_resource_label) :-
    person(Person),
    default_options(Options),
    generic_view:entity_view(Person, Options, View),
    view_group(
        View,
        outgoing,
        'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
        Group
    ),
    assertion(Group.label == "тип"),
    assertion(Group.values = [Value]),
    assertion(Value.targetId == 'http://fogid.net/o/person'),
    assertion(Value.label == "Персона").


test(base_source_contains_all_origins) :-
    person(Person),
    default_options(Options),
    generic_view:entity_view(Person, Options, View),
    view_group(
        View,
        outgoing,
        'http://fogid.net/o/name',
        Group
    ),
    member(Value, Group.values),
    Value.text == "Алексей Ветров",
    assertion(Value.source.origins == [
        'origin:fixture-a:person-alex',
        'origin:fixture-b:person-alex'
    ]).


test(generic_view_is_structurally_deterministic) :-
    person(Person),
    default_options(Options),
    generic_view:entity_view(Person, Options, First),
    generic_view:entity_view(Person, Options, Second),
    assertion(First == Second).


test(raw_prolog_contains_all_and_only_incident_facts) :-
    person(Person),
    generic_view:entity_prolog(Person, Text),
    split_string(Text, "\n", "", Lines0),
    exclude(==(\"\"), Lines0, Lines),
    assertion(Lines = [_, _, _, _, _, _, _, _]),
    forall(
        member(Line, Lines),
        sub_string(Line, 0, 5, _, "fact(")
    ).


test(technical_group_is_sorted_after_normal_groups) :-
    person(Person),
    default_options(Options),
    generic_view:entity_view(Person, Options, View),
    last(View.groups, Last),
    assertion(Last.technical == true).


view_group(View, Direction, Predicate, Group) :-
    member(Group, View.groups),
    Group.direction == Direction,
    Group.predicate == Predicate,
    !.


view_fact_ids(View, FactIds) :-
    findall(
        FactId,
        (
            member(Group, View.groups),
            member(Value, Group.values),
            FactId = Value.source.factId
        ),
        FactIds0
    ),
    sort(FactIds0, FactIds).


:- end_tests(generic_entity_view).
