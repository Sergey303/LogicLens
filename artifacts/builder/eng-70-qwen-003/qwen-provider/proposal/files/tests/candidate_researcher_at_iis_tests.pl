:- begin_tests(candidate_researcher_at_iis).
:- use_module('../rules/candidate_researcher_at_iis.pl').

:- end_tests(candidate_researcher_at_iis).
test(researcher_at_iis_test) :-
    researcher_at_iis(iri('urn:logiclens:person:alex'), [F1, F2, F3]),
    member(F1, ['f:sha256:b0a5e5a69a3150e22a03e67cd709be47d8cb7319d6dc8b0cdc574cc0a582c2b3', 'f:sha256:9aa0dad76c25bdbbfde243a82b134e70a562d4843863f55dd1300dd1384955e5', 'f:sha256:67abb6c01dde5080956246e21c49cb00db0bf95376fa64213d04e4efe964271b']).
    member(F2, ['f:sha256:b0a5e5a69a3150e22a03e67cd709be47d8cb7319d6dc8b0cdc574cc0a582c2b3', 'f:sha256:9aa0dad76c25bdbbfde243a82b134e70a562d4843863f55dd1300dd1384955e5', 'f:sha256:67abb6c01dde5080956246e21c49cb00db0bf95376fa64213d04e4efe964271b']).
    member(F3, ['f:sha256:b0a5e5a69a3150e22a03e67cd709be47d8cb7319d6dc8b0cdc574cc0a582c2b3', 'f:sha256:9aa0dad76c25bdbbfde243a82b134e70a562d4843863f55dd1300dd1384955e5', 'f:sha256:67abb6c01dde5080956246e21c49cb00db0bf95376fa64213d04e4efe964271b']).
