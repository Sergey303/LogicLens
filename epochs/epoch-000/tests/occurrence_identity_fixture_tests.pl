:- begin_tests(occurrence_identity_fixture).

:- use_module('../rules/subgraph.pl').
:- use_module(library(http/json)).


test(all_shared_golden_vectors_match_prolog) :-
    fixture_file(Path),
    setup_call_cleanup(
        open(Path, read, Stream, [encoding(utf8)]),
        json_read_dict(Stream, Document, [value_string_as(string)]),
        close(Stream)
    ),
    assertion(Document.encodingVersion == 1),
    Cases = Document.cases,
    length(Cases, 5),
    maplist(assert_vector, Cases).


fixture_file(Path) :-
    source_file(fixture_file(_), SourceFile),
    file_directory_name(SourceFile, Directory),
    directory_file_path(
        Directory,
        'occurrence-id-v1-golden.json',
        Path
    ).


assert_vector(Vector) :-
    atom_string(Root, Vector.root),
    maplist(step_term, Vector.steps, Steps),
    subgraph:occurrence_id(Root, Steps, ActualId),
    atom_string(ActualId, ActualIdText),
    assertion(ActualIdText == Vector.occurrenceId).


step_term(Step, step(FactId, Direction)) :-
    atom_string(FactId, Step.factId),
    direction_atom(Step.direction, Direction).


direction_atom("outgoing", outgoing).
direction_atom("incoming", incoming).


:- end_tests(occurrence_identity_fixture).
