:- module(candidate_member, [candidate_member/1]).
:- use_module('../data/epoch_data.pl').

candidate_member(Entity) :-
    epoch_data:fact(_, Entity, _, _).
