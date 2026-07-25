:- begin_tests(prolog_text_escaping).


test(quoted_atom_round_trips_exact_codes) :-
    atom_codes(Expected, [
        97, 116, 111, 109, 39, 113, 117, 111, 116, 101,
        92, 115, 108, 97, 115, 104, 10, 108, 105, 110,
        101, 9, 101, 110, 100
    ]),
    escaping_generated:escaped_atom(Actual),
    assertion(Actual == Expected).


test(quoted_string_round_trips_exact_codes) :-
    string_codes(Expected, [
        115, 116, 114, 105, 110, 103, 32, 34, 113, 117,
        111, 116, 101, 34, 32, 39, 97, 112, 111, 115,
        116, 114, 111, 112, 104, 101, 39, 32, 92, 115,
        108, 97, 115, 104, 10, 108, 105, 110, 101, 9,
        101, 110, 100
    ]),
    escaping_generated:escaped_string(Actual),
    assertion(Actual == Expected).


:- end_tests(prolog_text_escaping).
