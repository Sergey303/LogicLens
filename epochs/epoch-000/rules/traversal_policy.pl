:- module(traversal_policy, [
    traversal_allowed/1,
    non_traversable_predicate/1
]).

:- use_module('view_policy.pl').


rdf_type('http://www.w3.org/1999/02/22-rdf-syntax-ns#type').


non_traversable_predicate(Predicate) :-
    rdf_type(Predicate).
non_traversable_predicate(Predicate) :-
    view_policy:technical_predicate(Predicate).


traversal_allowed(Predicate) :-
    \+ non_traversable_predicate(Predicate).
