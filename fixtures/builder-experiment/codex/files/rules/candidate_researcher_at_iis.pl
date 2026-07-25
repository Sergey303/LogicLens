:- module(candidate_researcher_at_iis, [researcher_at_iis/2]).
:- use_module('../data/epoch_data.pl').

researcher_at_iis(Person, EvidenceFactIds) :-
    epoch_data:fact(OrganizationFact, Participation,
        'http://fogid.net/o/in-org', iri('urn:logiclens:org:iis')),
    epoch_data:fact(RoleFact, Participation,
        'http://fogid.net/o/role', literal("исследователь", lang('ru'))),
    epoch_data:fact(ParticipantFact, Participation,
        'http://fogid.net/o/participant', iri(Person)),
    sort([RoleFact, ParticipantFact, OrganizationFact], EvidenceFactIds).
