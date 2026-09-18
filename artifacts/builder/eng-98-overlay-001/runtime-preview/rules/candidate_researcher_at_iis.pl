:- module(candidate_researcher_at_iis, [researcher_at_iis/2]).
:- use_module('../data/epoch_data.pl').

researcher_at_iis(Person, EvidenceFactIds) :-
    epoch_data:fact(FParticipant, Participation, 'http://fogid.net/o/participant', iri(Person)),
    epoch_data:fact(FOrganization, Participation, 'http://fogid.net/o/in-org', iri('urn:logiclens:org:iis')),
    epoch_data:fact(FRole, Participation, 'http://fogid.net/o/role', literal("исследователь", lang('ru'))),
    sort([FParticipant, FOrganization, FRole], EvidenceFactIds).
