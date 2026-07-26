:- module(traversal_policy, [
    traversal_predicate/1
]).

:- use_module('view_policy.pl').


rdf_type('http://www.w3.org/1999/02/22-rdf-syntax-ns#type').


% The default zero-epoch policy follows every IRI-valued relation except
% reviewed non-traversable categories. Unknown ordinary predicates therefore
% remain useful without becoming an allow-list maintenance problem.
traversal_predicate(Predicate) :-
    \+ rdf_type(Predicate),
    \+ view_policy:technical_predicate(Predicate).
