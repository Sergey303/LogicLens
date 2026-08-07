:- set_prolog_flag(double_quotes, string).
% Generated from policy.ir.json. Do not hand-edit.

condition('n_write', 'asks_write', true, 'a_reject_write', 'n_claim').
condition('n_claim', 'goal_class', 'claim_resolution', 'n_claim_scope', 'n_prov').
condition('n_claim_scope', 'has_scope', true, 'n_claim_version', 'a_scope').
condition('n_claim_version', 'has_version', true, 'n_policy', 'a_version').
condition('n_policy', 'requires_strict_policy', true, 'a_prolog', 'a_db_claim').
condition('n_prov', 'goal_class', 'provenance_lookup', 'n_prov_scope', 'n_numeric').
condition('n_prov_scope', 'has_scope', true, 'n_prov_version', 'a_scope').
condition('n_prov_version', 'has_version', true, 'a_db_prov', 'a_version').
condition('n_numeric', 'goal_class', 'numeric_threshold', 'a_python', 'n_explain').
condition('n_explain', 'goal_class', 'explanation', 'a_explain', 'a_unsupported').
action('a_reject_write', 'reject.unsupported_write', '1.0.0').
action('a_scope', 'clarification.missing_scope', '1.0.0').
action('a_version', 'clarification.missing_version', '1.0.0').
action('a_prolog', 'prolog.resolve_epistemic', '1.0.0').
action('a_db_claim', 'db.resolve_claim', '1.0.0').
action('a_db_prov', 'db.lookup_provenance', '1.0.0').
action('a_python', 'python.threshold_check', '1.0.0').
action('a_explain', 'prompt.explain_result', '1.0.0').
action('a_unsupported', 'clarification.unsupported_goal', '1.0.0').

feature_value('goal_class', Goal, _, _, _, _, Goal).
feature_value('has_scope', _, HasScope, _, _, _, HasScope).
feature_value('has_version', _, _, HasVersion, _, _, HasVersion).
feature_value('asks_write', _, _, _, AsksWrite, _, AsksWrite).
feature_value('requires_strict_policy', _, _, _, _, RequiresPolicy, RequiresPolicy).

route(Goal, HasScope, HasVersion, AsksWrite, RequiresPolicy, Capability) :-
    walk('n_write', Goal, HasScope, HasVersion, AsksWrite, RequiresPolicy, Capability, []).

walk(Node, _, _, _, _, _, _, Seen) :- memberchk(Node, Seen), !, fail.
walk(Node, _, _, _, _, _, Capability, _) :- action(Node, Capability, _), !.
walk(Node, Goal, HasScope, HasVersion, AsksWrite, RequiresPolicy, Capability, Seen) :-
    condition(Node, Feature, Expected, IfTrue, IfFalse),
    feature_value(Feature, Goal, HasScope, HasVersion, AsksWrite, RequiresPolicy, Actual),
    ( Actual == Expected -> Next = IfTrue ; Next = IfFalse ),
    walk(Next, Goal, HasScope, HasVersion, AsksWrite, RequiresPolicy, Capability, [Node|Seen]).
