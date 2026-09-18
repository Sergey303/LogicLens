:- module(candidate_researcher_at_iis, [researcher_at_iis/2]).
:- use_module('../data/epoch_data.pl').

researcher_at_iis(Person, EvidenceFactIds) :-
    epoch_data:fact(FactId1, Person, 'http://fogid.net/o/participant', iri('urn:logiclens:participation:work')),
    epoch_data:fact(FactId2, 'urn:logiclens:org:iis', 'http://fogid.net/o/in-org', iri('urn:logiclens:participation:work')),
    epoch_data:fact(FactId3, 'urn:logiclens:participation:work', 'http://fogid.net/o/role', literal('исследователь', lang('ru'))),
    sort([FactId1, FactId2, FactId3], EvidenceFactIds).
