:- begin_tests(candidate_researcher_at_iis).
:- use_module('../rules/candidate_researcher_at_iis.pl').

:- test(test_researcher_at_iis) :-
    researcher_at_iis('urn:logiclens:person:alex', EvidenceFactIds),
    member(f:sha256:4462f979698ea067c9e2c0f3845e961bf84728aa82ecb91448742cd1b3ff9bb0, EvidenceFactIds),
    member(f:sha256:9aa0dad76c25bdbbfde243a82b134e70a562d4843863f55dd1300dd1384955e5, EvidenceFactIds),
    member(f:sha256:67abb6c01dde5080956246e21c49cb00db0bf95376fa64213d04e4efe964271b, EvidenceFactIds).

:- end_tests(candidate_researcher_at_iis).
