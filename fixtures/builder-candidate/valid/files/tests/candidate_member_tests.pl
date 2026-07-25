:- begin_tests(candidate_member).
:- use_module('../rules/candidate_member.pl').

test(person_with_reviewed_fact_is_selected) :-
    candidate_member:candidate_member('urn:logiclens:person:alex').

:- end_tests(candidate_member).
