:- module(cli_runtime, [
    handle_request/3
]).

:- use_module('../data/epoch_data.pl').
:- use_module('generic_view.pl').
:- use_module('subgraph.pl').
:- use_module(library(http/json)).
:- use_module(library(lists)).
:- use_module(library(pairs)).
:- use_module(library(time)).


protocol_version("0.1").
loaded_epoch(0).
loaded_revision(0).
json_safe_max_integer(9007199254740991).


hard_fact_limits(_{
    maxFacts: 5000,
    maxOutputBytes: 2000000,
    timeoutMs: 5000
}).

default_fact_limits(_{
    maxFacts: 1000,
    maxOutputBytes: 1000000,
    timeoutMs: 2000
}).


hard_traversal_limits(_{
    maxDepth: 2,
    maxNodes: 1000,
    maxFacts: 5000,
    maxOccurrences: 5000,
    maxPathLength: 2,
    maxOutputBytes: 2000000,
    timeoutMs: 5000
}).

default_traversal_limits(_{
    maxNodes: 250,
    maxFacts: 1000,
    maxOccurrences: 1000,
    maxPathLength: 2,
    maxOutputBytes: 1000000,
    timeoutMs: 2000
}).


handle_request(Request, Response, ExitCode) :-
    reported_context(Request, ReportedRequestId, ReportedCommand),
    catch(
        run_request(Request, Response0, OutputLimit),
        Error,
        request_error_response(
            Error,
            ReportedRequestId,
            ReportedCommand,
            Response0
        )
    ),
    (   Response0.status == ok
    ->  enforce_output_limit(
            OutputLimit,
            ReportedRequestId,
            ReportedCommand,
            Response0,
            Response,
            ExitCode
        )
    ;   Response = Response0,
        ExitCode = 1
    ).


reported_context(Request, RequestId, Command) :-
    (   is_dict(Request),
        get_dict(requestId, Request, CandidateRequestId),
        valid_request_id(CandidateRequestId)
    ->  RequestId = CandidateRequestId
    ;   RequestId = null
    ),
    (   is_dict(Request),
        get_dict(command, Request, CandidateCommand),
        string(CandidateCommand),
        string_length(CandidateCommand, CommandLength),
        between(1, 256, CommandLength)
    ->  Command = CandidateCommand
    ;   Command = null
    ).


run_request(Request, Response, OutputLimit) :-
    validate_envelope(Request, RequestId, Command, Options),
    prepare_command(
        Command,
        Options,
        Prepared,
        EffectiveLimits,
        LimitDiagnostics,
        TimeoutMs,
        OutputLimit
    ),
    Seconds is TimeoutMs / 1000,
    catch(
        call_with_time_limit(
            Seconds,
            execute_command(
                Command,
                Prepared,
                EffectiveLimits,
                Result,
                CommandDiagnostics
            )
        ),
        time_limit_exceeded,
        throw(cli_error(
            "timeout",
            "The reviewed command time limit was exceeded.",
            _{timeoutMs: TimeoutMs}
        ))
    ),
    append(LimitDiagnostics, CommandDiagnostics, Diagnostics0),
    sort(Diagnostics0, Diagnostics),
    success_response(RequestId, Command, Result, Diagnostics, Response).


validate_envelope(Request, RequestId, Command, Options) :-
    require_dict(Request, "request must be a JSON object"),
    require_exact_keys(
        Request,
        [protocolVersion, requestId, command, epoch, revision, options],
        [protocolVersion, requestId, command, epoch, revision, options]
    ),
    get_dict(protocolVersion, Request, Version),
    require_string(Version, 1, 32, protocolVersion),
    get_dict(requestId, Request, RequestId),
    (   valid_request_id(RequestId)
    ->  true
    ;   throw_invalid_field(requestId)
    ),
    get_dict(command, Request, CommandText),
    require_string(CommandText, 1, 256, command),
    get_dict(epoch, Request, RequestedEpoch),
    require_safe_non_negative_integer(RequestedEpoch, epoch),
    get_dict(revision, Request, RequestedRevision),
    require_safe_non_negative_integer(RequestedRevision, revision),
    get_dict(options, Request, Options),
    require_dict(Options, "options must be a JSON object"),
    protocol_version(ExpectedVersion),
    (   Version == ExpectedVersion
    ->  true
    ;   throw(cli_error(
            "unsupported_protocol",
            "The requested protocol version is not supported.",
            _{requested: Version, supported: ExpectedVersion}
        ))
    ),
    loaded_epoch(LoadedEpoch),
    loaded_revision(LoadedRevision),
    (   RequestedEpoch =:= LoadedEpoch,
        RequestedRevision =:= LoadedRevision
    ->  true
    ;   throw(cli_error(
            "stale_state",
            "The requested epoch or revision does not match the loaded state.",
            _{
                requestedEpoch: RequestedEpoch,
                requestedRevision: RequestedRevision,
                loadedEpoch: LoadedEpoch,
                loadedRevision: LoadedRevision
            }
        ))
    ),
    command_atom(CommandText, Command).


command_atom("health", health).
command_atom("inspect-facts", 'inspect-facts').
command_atom("entity-view", 'entity-view').
command_atom("subgraph", subgraph).
command_atom(Command, _) :-
    throw(cli_error(
        "unknown_command",
        "The command is not part of the closed protocol command set.",
        _{command: Command}
    )).


prepare_command(
    health,
    Options,
    prepared{},
    HardLimits,
    [],
    TimeoutMs,
    OutputLimit
) :-
    require_exact_keys(Options, [], []),
    hard_traversal_limits(HardLimits),
    TimeoutMs = HardLimits.timeoutMs,
    OutputLimit = HardLimits.maxOutputBytes.
prepare_command(
    'inspect-facts',
    Options,
    prepared{entity: Entity},
    EffectiveLimits,
    Diagnostics,
    TimeoutMs,
    OutputLimit
) :-
    require_exact_keys(Options, [entityId], [entityId, limits]),
    get_dict(entityId, Options, EntityText),
    require_string(EntityText, 1, 4096, entityId),
    atom_string(Entity, EntityText),
    optional_limits(Options, RequestedLimits),
    validate_limit_dict(
        RequestedLimits,
        [maxFacts, maxOutputBytes, timeoutMs]
    ),
    effective_fact_limits(RequestedLimits, EffectiveLimits, Diagnostics),
    TimeoutMs = EffectiveLimits.timeoutMs,
    OutputLimit = EffectiveLimits.maxOutputBytes.
prepare_command(
    'entity-view',
    Options,
    prepared{
        entity: Entity,
        labelOptions: LabelOptions,
        includeRawProlog: IncludeRawProlog
    },
    EffectiveLimits,
    Diagnostics,
    TimeoutMs,
    OutputLimit
) :-
    require_exact_keys(
        Options,
        [entityId],
        [entityId, language, includeRawProlog, limits]
    ),
    get_dict(entityId, Options, EntityText),
    require_string(EntityText, 1, 4096, entityId),
    atom_string(Entity, EntityText),
    label_options(Options, LabelOptions),
    optional_boolean(Options, includeRawProlog, false, IncludeRawProlog),
    optional_limits(Options, RequestedLimits),
    validate_limit_dict(
        RequestedLimits,
        [maxFacts, maxOutputBytes, timeoutMs]
    ),
    effective_fact_limits(RequestedLimits, EffectiveLimits, Diagnostics),
    TimeoutMs = EffectiveLimits.timeoutMs,
    OutputLimit = EffectiveLimits.maxOutputBytes.
prepare_command(
    subgraph,
    Options,
    prepared{
        root: Root,
        requestedDepth: RequestedDepth,
        effectiveDepth: EffectiveDepth,
        direction: Direction,
        labelOptions: LabelOptions
    },
    EffectiveLimits,
    Diagnostics,
    TimeoutMs,
    OutputLimit
) :-
    require_exact_keys(
        Options,
        [rootId, depth, direction],
        [rootId, depth, direction, language, limits]
    ),
    get_dict(rootId, Options, RootText),
    require_string(RootText, 1, 4096, rootId),
    atom_string(Root, RootText),
    get_dict(depth, Options, RequestedDepth),
    require_bounded_non_negative_integer(RequestedDepth, depth),
    get_dict(direction, Options, DirectionText),
    direction_atom(DirectionText, Direction),
    label_options(Options, LabelOptions),
    optional_limits(Options, RequestedLimits),
    validate_limit_dict(
        RequestedLimits,
        [
            maxNodes,
            maxFacts,
            maxOccurrences,
            maxPathLength,
            maxOutputBytes,
            timeoutMs
        ]
    ),
    effective_traversal_limits(
        RequestedLimits,
        RequestedDepth,
        EffectiveDepth,
        EffectiveLimits,
        Diagnostics
    ),
    TimeoutMs = EffectiveLimits.timeoutMs,
    OutputLimit = EffectiveLimits.maxOutputBytes.


direction_atom(DirectionText, Direction) :-
    require_string(DirectionText, 1, 32, direction),
    (   DirectionText == "outgoing"
    ->  Direction = outgoing
    ;   DirectionText == "incoming"
    ->  Direction = incoming
    ;   DirectionText == "both"
    ->  Direction = both
    ;   throw(cli_error(
            "invalid_request",
            "direction must be outgoing, incoming, or both.",
            _{field: "direction"}
        ))
    ).


label_options(Options, _{languages: Languages}) :-
    (   get_dict(language, Options, LanguageText)
    ->  require_string(LanguageText, 1, 64, language),
        string_lower(LanguageText, LowerLanguage),
        atom_string(Language, LowerLanguage),
        language_fallbacks(Language, Languages)
    ;   Languages = [ru, en]
    ).


language_fallbacks(ru, [ru, en]) :- !.
language_fallbacks(en, [en, ru]) :- !.
language_fallbacks(Language, [Language, ru, en]).


optional_boolean(Options, Key, Default, Value) :-
    (   get_dict(Key, Options, Candidate)
    ->  (   memberchk(Candidate, [true, false])
        ->  Value = Candidate
        ;   throw_invalid_field(Key)
        )
    ;   Value = Default
    ).


optional_limits(Options, Limits) :-
    (   get_dict(limits, Options, Candidate)
    ->  require_dict(Candidate, "limits must be a JSON object"),
        Limits = Candidate
    ;   Limits = _{}
    ).


validate_limit_dict(Limits, AllowedKeys) :-
    require_exact_keys(Limits, [], AllowedKeys),
    dict_pairs(Limits, _, Pairs),
    forall(
        member(Key-Value, Pairs),
        require_bounded_positive_integer(Value, Key)
    ).


effective_fact_limits(Requested, Effective, Diagnostics) :-
    default_fact_limits(Defaults),
    hard_fact_limits(Hard),
    effective_limit(
        maxFacts,
        Requested,
        Defaults.maxFacts,
        Hard.maxFacts,
        MaxFacts,
        D1
    ),
    effective_limit(
        maxOutputBytes,
        Requested,
        Defaults.maxOutputBytes,
        Hard.maxOutputBytes,
        MaxOutputBytes,
        D2
    ),
    effective_limit(
        timeoutMs,
        Requested,
        Defaults.timeoutMs,
        Hard.timeoutMs,
        TimeoutMs,
        D3
    ),
    append([D1, D2, D3], Diagnostics),
    Effective = _{
        maxFacts: MaxFacts,
        maxOutputBytes: MaxOutputBytes,
        timeoutMs: TimeoutMs
    }.


effective_traversal_limits(
    Requested,
    RequestedDepth,
    EffectiveDepth,
    Effective,
    Diagnostics
) :-
    default_traversal_limits(Defaults),
    hard_traversal_limits(Hard),
    effective_limit(maxNodes, Requested, Defaults.maxNodes, Hard.maxNodes, MaxNodes, D1),
    effective_limit(maxFacts, Requested, Defaults.maxFacts, Hard.maxFacts, MaxFacts, D2),
    effective_limit(
        maxOccurrences,
        Requested,
        Defaults.maxOccurrences,
        Hard.maxOccurrences,
        MaxOccurrences,
        D3
    ),
    effective_limit(
        maxPathLength,
        Requested,
        Defaults.maxPathLength,
        Hard.maxPathLength,
        MaxPathLength,
        D4
    ),
    effective_limit(
        maxOutputBytes,
        Requested,
        Defaults.maxOutputBytes,
        Hard.maxOutputBytes,
        MaxOutputBytes,
        D5
    ),
    effective_limit(
        timeoutMs,
        Requested,
        Defaults.timeoutMs,
        Hard.timeoutMs,
        TimeoutMs,
        D6
    ),
    clamp_depth(
        RequestedDepth,
        Hard.maxDepth,
        MaxPathLength,
        EffectiveDepth,
        DepthDiagnostics
    ),
    append([D1, D2, D3, D4, D5, D6, DepthDiagnostics], Diagnostics),
    Effective = _{
        maxDepth: EffectiveDepth,
        maxNodes: MaxNodes,
        maxFacts: MaxFacts,
        maxOccurrences: MaxOccurrences,
        maxPathLength: MaxPathLength,
        maxOutputBytes: MaxOutputBytes,
        timeoutMs: TimeoutMs
    }.


effective_limit(Name, Requested, Default, Hard, Effective, Diagnostics) :-
    (   get_dict(Name, Requested, RequestedValue)
    ->  true
    ;   RequestedValue = Default
    ),
    (   RequestedValue > Hard
    ->  Effective = Hard,
        clamp_diagnostic(Name, RequestedValue, Hard, Diagnostic),
        Diagnostics = [Diagnostic]
    ;   Effective = RequestedValue,
        Diagnostics = []
    ).


clamp_depth(Requested, HardDepth, MaxPathLength, Effective, Diagnostics) :-
    min_list([Requested, HardDepth, MaxPathLength], Effective),
    (   Effective < Requested
    ->  clamp_diagnostic(maxDepth, Requested, Effective, Diagnostic),
        Diagnostics = [Diagnostic]
    ;   Diagnostics = []
    ).


clamp_diagnostic(Name, Requested, Effective, Diagnostic) :-
    atom_string(Name, NameText),
    Diagnostic = diagnostic{
        code: "limit_clamped",
        severity: warning,
        message: "A requested limit exceeded the reviewed effective bound.",
        context: _{
            limit: NameText,
            requested: Requested,
            effective: Effective
        }
    }.


execute_command(health, _, HardLimits, Result, []) :-
    Result = health_result{
        kind: health,
        protocolVersion: "0.1",
        manifestHashes: _{
            data: "sha256:b2ebcb0e07c6582664ea016c82429d7cd28a57f716d7e27ceabdc49ce4ece0ed"
        },
        availableCommands: [health, 'inspect-facts', 'entity-view', subgraph],
        hardLimits: HardLimits
    }.
execute_command(
    'inspect-facts',
    Prepared,
    EffectiveLimits,
    Result,
    Diagnostics
) :-
    inspect_facts(
        Prepared.entity,
        EffectiveLimits.maxFacts,
        Facts,
        Truncated
    ),
    limit_result_diagnostics(Truncated, maxFacts, Diagnostics),
    Result = inspect_result{
        kind: 'inspect-facts',
        entityId: Prepared.entity,
        effectiveLimits: EffectiveLimits,
        truncated: Truncated,
        facts: Facts
    }.
execute_command(
    'entity-view',
    Prepared,
    EffectiveLimits,
    Result,
    []
) :-
    incident_fact_count(Prepared.entity, FactCount),
    (   FactCount =< EffectiveLimits.maxFacts
    ->  true
    ;   throw(cli_error(
            "fact_limit_exceeded",
            "The complete generic entity view exceeds maxFacts.",
            _{
                factCount: FactCount,
                maxFacts: EffectiveLimits.maxFacts
            }
        ))
    ),
    generic_view:entity_view(
        Prepared.entity,
        Prepared.labelOptions,
        View
    ),
    raw_prolog_value(Prepared, RawProlog),
    Result = entity_view_result{
        kind: 'entity-view',
        entityId: Prepared.entity,
        effectiveLimits: EffectiveLimits,
        view: View,
        rawProlog: RawProlog
    }.
execute_command(
    subgraph,
    Prepared,
    EffectiveLimits,
    Result,
    Diagnostics
) :-
    subgraph:build_subgraph(
        Prepared.root,
        Prepared.requestedDepth,
        Prepared.effectiveDepth,
        Prepared.direction,
        Prepared.labelOptions,
        EffectiveLimits,
        Result,
        Diagnostics
    ).


raw_prolog_value(Prepared, RawProlog) :-
    (   Prepared.includeRawProlog == true
    ->  generic_view:entity_prolog(Prepared.entity, RawProlog)
    ;   RawProlog = null
    ).


incident_fact_count(Entity, Count) :-
    findall(
        FactId,
        generic_view:incident_fact(Entity, _, FactId, _, _, _),
        FactIds0
    ),
    sort(FactIds0, FactIds),
    length(FactIds, Count).


inspect_facts(Entity, MaxFacts, Facts, Truncated) :-
    findall(
        FactId-base_fact(FactId, Subject, Predicate, Object),
        generic_view:incident_fact(
            Entity,
            _,
            FactId,
            Subject,
            Predicate,
            Object
        ),
        Pairs0
    ),
    sort(Pairs0, Pairs),
    pairs_values(Pairs, BaseFacts),
    take_prefix(MaxFacts, BaseFacts, Selected, Truncated),
    maplist(base_fact_dict, Selected, Facts).


take_prefix(Max, Values, Prefix, Truncated) :-
    length(Values, Count),
    (   Count =< Max
    ->  Prefix = Values,
        Truncated = false
    ;   length(Prefix, Max),
        append(Prefix, _, Values),
        Truncated = true
    ).


base_fact_dict(base_fact(FactId, Subject, Predicate, Object), Dict) :-
    object_dict(Object, ObjectDict),
    findall(
        OriginId,
        epoch_data:fact_origin(FactId, OriginId),
        Origins0
    ),
    sort(Origins0, Origins),
    Dict = fact{
        factId: FactId,
        subject: Subject,
        predicate: Predicate,
        object: ObjectDict,
        origins: Origins
    }.


object_dict(iri(Resource), object{
    kind: iri,
    value: Resource
}).
object_dict(literal(Text, plain), object{
    kind: literal,
    literalKind: plain,
    lexical: Text,
    language: null,
    datatype: null
}).
object_dict(literal(Text, lang(Language)), object{
    kind: literal,
    literalKind: language,
    lexical: Text,
    language: Language,
    datatype: null
}).
object_dict(literal(Text, datatype(Datatype)), object{
    kind: literal,
    literalKind: datatype,
    lexical: Text,
    language: null,
    datatype: Datatype
}).


limit_result_diagnostics(false, _, []).
limit_result_diagnostics(true, Limit, [Diagnostic]) :-
    atom_string(Limit, LimitText),
    Diagnostic = diagnostic{
        code: "limit_reached",
        severity: warning,
        message: "The deterministic result was truncated at a reviewed limit.",
        context: _{limit: LimitText}
    }.


success_response(RequestId, Command, Result, Diagnostics, Response) :-
    protocol_version(Version),
    loaded_epoch(Epoch),
    loaded_revision(Revision),
    Response = response{
        protocolVersion: Version,
        requestId: RequestId,
        command: Command,
        status: ok,
        epoch: Epoch,
        revision: Revision,
        result: Result,
        diagnostics: Diagnostics
    }.


request_error_response(
    cli_error(Code, Message, Details),
    RequestId,
    Command,
    Response
) :-
    !,
    error_response(Code, Message, Details, RequestId, Command, Response).
request_error_response(_, RequestId, Command, Response) :-
    error_response(
        "internal_error",
        "The reviewed command failed before producing a result.",
        _{},
        RequestId,
        Command,
        Response
    ).


error_response(Code, Message, Details, RequestId, Command, Response) :-
    protocol_version(Version),
    loaded_epoch(Epoch),
    loaded_revision(Revision),
    Response = response{
        protocolVersion: Version,
        requestId: RequestId,
        command: Command,
        status: error,
        epoch: Epoch,
        revision: Revision,
        error: error{
            code: Code,
            message: Message,
            details: Details
        },
        diagnostics: []
    }.


enforce_output_limit(
    OutputLimit,
    RequestId,
    Command,
    Response0,
    Response,
    ExitCode
) :-
    response_byte_size(Response0, ByteSize),
    (   ByteSize =< OutputLimit
    ->  Response = Response0,
        ExitCode = 0
    ;   error_response(
            "output_limit_exceeded",
            "The deterministic success envelope exceeded maxOutputBytes.",
            _{measuredBytes: ByteSize, maxOutputBytes: OutputLimit},
            RequestId,
            Command,
            Response
        ),
        ExitCode = 1
    ).


response_byte_size(Response, ByteSize) :-
    with_output_to(
        string(Text),
        json_write_dict(current_output, Response, [width(0)])
    ),
    string_bytes(Text, Bytes, utf8),
    length(Bytes, ContentBytes),
    ByteSize is ContentBytes + 1.


valid_request_id(Value) :-
    string(Value),
    string_length(Value, Length),
    between(1, 256, Length).


require_dict(Value, _) :- is_dict(Value), !.
require_dict(_, Message) :-
    throw(cli_error("invalid_request", Message, _{})).


require_exact_keys(Dict, Required, Allowed) :-
    dict_pairs(Dict, _, Pairs),
    pairs_keys(Pairs, Present0),
    sort(Present0, Present),
    sort(Required, RequiredSorted),
    sort(Allowed, AllowedSorted),
    subtract(RequiredSorted, Present, Missing),
    subtract(Present, AllowedSorted, Unknown),
    (   Missing == [], Unknown == []
    ->  true
    ;   throw(cli_error(
            "invalid_request",
            "The JSON object has missing or unsupported fields.",
            _{missing: Missing, unknown: Unknown}
        ))
    ).


require_string(Value, Min, Max, _) :-
    string(Value),
    string_length(Value, Length),
    between(Min, Max, Length),
    !.
require_string(_, _, _, Field) :- throw_invalid_field(Field).


require_safe_non_negative_integer(Value, _) :-
    integer(Value),
    Value >= 0,
    json_safe_max_integer(Max),
    Value =< Max,
    !.
require_safe_non_negative_integer(_, Field) :- throw_invalid_field(Field).


require_bounded_non_negative_integer(Value, _) :-
    integer(Value),
    between(0, 2147483647, Value),
    !.
require_bounded_non_negative_integer(_, Field) :- throw_invalid_field(Field).


require_bounded_positive_integer(Value, _) :-
    integer(Value),
    between(1, 2147483647, Value),
    !.
require_bounded_positive_integer(_, Field) :- throw_invalid_field(Field).


throw_invalid_field(Field) :-
    atom_string(Field, FieldText),
    throw(cli_error(
        "invalid_request",
        "A request field has an invalid type, range, or value.",
        _{field: FieldText}
    )).
