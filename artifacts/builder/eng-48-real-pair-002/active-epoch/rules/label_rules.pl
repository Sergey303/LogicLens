:- module(label_rules, [
    resource_label/3,
    predicate_label/5,
    compact_identifier/2
]).

:- use_module('../data/epoch_data.pl').
:- use_module('../ontology/ontology_data.pl').
:- use_module(library(apply)).
:- use_module(library(lists)).
:- use_module(library(pairs)).


name_predicate('http://fogid.net/o/name').


resource_label(Resource, Options, Label) :-
    language_preferences(Options, Preferences),
    findall(
        candidate(Language, Text, FactId),
        resource_name_candidate(Resource, Language, Text, FactId),
        DataCandidates
    ),
    DataCandidates \== [],
    !,
    select_label(DataCandidates, Preferences, Label).
resource_label(Resource, Options, Label) :-
    language_preferences(Options, Preferences),
    findall(
        candidate(Language, Text, ontology),
        ontology_data:ontology_label(Resource, forward, Language, Text),
        OntologyCandidates
    ),
    OntologyCandidates \== [],
    !,
    select_label(OntologyCandidates, Preferences, Label).
resource_label(Resource, _, Label) :-
    compact_identifier(Resource, Label).


predicate_label(Predicate, Direction, Options, Label, Priority) :-
    language_preferences(Options, Preferences),
    preferred_predicate_direction(Direction, PreferredDirection),
    predicate_candidates(Predicate, PreferredDirection, Candidates),
    (   Candidates \== []
    ->  select_label(Candidates, Preferences, Label)
    ;   PreferredDirection == inverse,
        predicate_candidates(Predicate, forward, ForwardCandidates),
        ForwardCandidates \== []
    ->  select_label(ForwardCandidates, Preferences, Label)
    ;   compact_identifier(Predicate, Label)
    ),
    (   ontology_data:ontology_priority(Predicate, FoundPriority)
    ->  Priority = FoundPriority
    ;   Priority = null
    ).


resource_name_candidate(Resource, Language, Text, FactId) :-
    name_predicate(NamePredicate),
    epoch_data:fact(
        FactId,
        Resource,
        NamePredicate,
        literal(Text, LiteralKind)
    ),
    literal_language(LiteralKind, Language).


predicate_candidates(Predicate, Direction, Candidates) :-
    findall(
        candidate(Language, Text, ontology),
        predicate_label_candidate(Predicate, Direction, Language, Text),
        Candidates
    ).


predicate_label_candidate(Predicate, Direction, Language, Text) :-
    ontology_data:ontology_label(Predicate, Direction, Language, Text).
predicate_label_candidate(
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
    forward,
    ru,
    "тип"
).
predicate_label_candidate(
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
    forward,
    en,
    "type"
).


preferred_predicate_direction(outgoing, forward).
preferred_predicate_direction(incoming, inverse).


literal_language(plain, plain).
literal_language(lang(Language), Language).
literal_language(datatype(_), plain).


language_preferences(Options, Preferences) :-
    (   is_dict(Options),
        get_dict(languages, Options, Requested),
        is_list(Requested)
    ->  include(atom, Requested, AtomLanguages),
        append(AtomLanguages, [plain], WithPlain),
        list_to_set(WithPlain, Preferences)
    ;   Preferences = [ru, en, plain]
    ).


select_label(Candidates, Preferences, Label) :-
    map_list_to_pairs(
        candidate_sort_key(Preferences),
        Candidates,
        Pairs
    ),
    keysort(Pairs, [_-candidate(_, Label, _)|_]).


candidate_sort_key(
    Preferences,
    candidate(Language, Text, Source),
    key(Rank, Language, Text, Source)
) :-
    (   nth0(Index, Preferences, Language)
    ->  Rank = Index
    ;   Rank = 1000
    ).


compact_identifier(Resource, Label) :-
    atom_codes(Resource, Codes),
    reverse(Codes, Reversed),
    compact_reversed_codes(Reversed, SegmentReversed),
    (   SegmentReversed == []
    ->  atom_string(Resource, Label)
    ;   reverse(SegmentReversed, SegmentCodes),
        string_codes(Label, SegmentCodes)
    ).


compact_reversed_codes([], []).
compact_reversed_codes([Code|_], []) :-
    identifier_separator(Code),
    !.
compact_reversed_codes([Code|Rest], [Code|Segment]) :-
    compact_reversed_codes(Rest, Segment).


identifier_separator(0'#).
identifier_separator(0'/).
identifier_separator(0':).
