:- module(runtime_limits, [
    hard_limits/1,
    effective_fact_limits/3,
    effective_traversal_limits/5
]).


hard_limits(_{
    maxDepth: 2,
    maxNodes: 1000,
    maxFacts: 5000,
    maxOccurrences: 5000,
    maxPathLength: 2,
    maxOutputBytes: 1048576,
    timeoutMs: 5000
}).


default_fact_limits(_{
    maxFacts: 1000,
    maxOutputBytes: 524288,
    timeoutMs: 2000
}).


default_traversal_limits(_{
    maxNodes: 500,
    maxFacts: 2000,
    maxOccurrences: 2000,
    maxPathLength: 2,
    maxOutputBytes: 1048576,
    timeoutMs: 3000
}).


effective_fact_limits(Requested, Effective, Diagnostics) :-
    default_fact_limits(Defaults),
    hard_limits(Hard),
    effective_limit(maxFacts, Requested, Defaults, Hard, MaxFacts, D1),
    effective_limit(maxOutputBytes, Requested, Defaults, Hard, MaxOutputBytes, D2),
    effective_limit(timeoutMs, Requested, Defaults, Hard, TimeoutMs, D3),
    Effective = _{
        maxFacts: MaxFacts,
        maxOutputBytes: MaxOutputBytes,
        timeoutMs: TimeoutMs
    },
    append([D1, D2, D3], Diagnostics0),
    sort(Diagnostics0, Diagnostics).


effective_traversal_limits(
    RequestedDepth,
    Requested,
    EffectiveDepth,
    Effective,
    Diagnostics
) :-
    hard_limits(Hard),
    default_traversal_limits(Defaults),
    clamp_value(maxDepth, RequestedDepth, Hard.maxDepth, EffectiveDepth, DepthDiagnostics),
    effective_limit(maxNodes, Requested, Defaults, Hard, MaxNodes, D1),
    effective_limit(maxFacts, Requested, Defaults, Hard, MaxFacts, D2),
    effective_limit(maxOccurrences, Requested, Defaults, Hard, MaxOccurrences, D3),
    effective_limit(maxPathLength, Requested, Defaults, Hard, MaxPathLength, D4),
    effective_limit(maxOutputBytes, Requested, Defaults, Hard, MaxOutputBytes, D5),
    effective_limit(timeoutMs, Requested, Defaults, Hard, TimeoutMs, D6),
    path_length_diagnostics(EffectiveDepth, MaxPathLength, PathDiagnostics),
    Effective = _{
        maxNodes: MaxNodes,
        maxFacts: MaxFacts,
        maxOccurrences: MaxOccurrences,
        maxPathLength: MaxPathLength,
        maxOutputBytes: MaxOutputBytes,
        timeoutMs: TimeoutMs
    },
    append(
        [
            DepthDiagnostics,
            D1,
            D2,
            D3,
            D4,
            D5,
            D6,
            PathDiagnostics
        ],
        Diagnostics0
    ),
    sort(Diagnostics0, Diagnostics).


path_length_diagnostics(EffectiveDepth, MaxPathLength, []) :-
    EffectiveDepth =< MaxPathLength,
    !.
path_length_diagnostics(EffectiveDepth, MaxPathLength, [Diagnostic]) :-
    Diagnostic = diagnostic{
        code: max_path_length,
        severity: warning,
        message: "Path-length limit stops traversal before effective depth.",
        context: _{
            effectiveDepth: EffectiveDepth,
            maxPathLength: MaxPathLength
        }
    }.


effective_limit(Key, Requested, Defaults, Hard, Effective, Diagnostics) :-
    (   get_dict(Key, Requested, Value)
    ->  true
    ;   get_dict(Key, Defaults, Value)
    ),
    get_dict(Key, Hard, Maximum),
    clamp_value(Key, Value, Maximum, Effective, Diagnostics).


clamp_value(_, Value, Maximum, Value, []) :-
    Value =< Maximum,
    !.
clamp_value(Key, Value, Maximum, Maximum, [Diagnostic]) :-
    Diagnostic = diagnostic{
        code: limit_clamped,
        severity: warning,
        message: "Requested limit exceeded the reviewed hard limit.",
        context: _{
            limit: Key,
            requested: Value,
            effective: Maximum
        }
    }.
