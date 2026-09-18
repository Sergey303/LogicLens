:- module(candidate_researcher_at_iis, [researcher_at_iis/2]).
:- use_module('../data/epoch_data.pl').

researcher_at_iis(Person, EvidenceFactIds) :-
    epoch_data:fact(FactIdA, Person, 'http://fogid.net/o/participant', iri('urn:logiclens:participation:work')),
    epoch_data:fact(FactIdB, 'urn:logiclens:org:iis', 'http://fogid.net/o/in-org', iri('urn:logiclens:participation:work')),
    epoch_data:fact(FactIdC, 'urn:logiclens:participation:work', 'http://fogid.net/o/role', literal('исследователь', lang('ru'))),
    sort([FactIdA, FactIdB, FactIdC], EvidenceFactIds).
