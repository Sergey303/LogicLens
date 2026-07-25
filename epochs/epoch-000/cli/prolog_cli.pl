:- module(prolog_cli, [
    run/1
]).

:- use_module('../rules/base_fact_view.pl').
:- use_module('../rules/epoch_state.pl').
:- use_module('../rules/generic_view.pl').
:- use_module('../rules/runtime_limits.pl').
:- use_module('../rules/subgraph.pl').
:- use_module(library(error)).
:- use_module(library(http/json)).
:- use_module(library(lists)).
:- use_module(library(time)).
:- use_module(library(utf8)).


protocol_version("0.1").
safe_integer_max(9007199254740991).


run(ExitCode) :-
    json_read_dict(user_input, Request),
    reported_request_id(Request, ReportedRequestId),
    reported_command(Request, ReportedCommand),
    catch(
        execute_request(Request, Response0, MaximumOutputBytes),
        protocol_error(Code, Message, Details),
        (
            error_response(
                ReportedRequestId,
                ReportedCommand,
                Code,
                Message,
                Details,
                Response0
            ),
            MaximumOutputBytes = control
        )
    ),
    finalize_response(
        Response0,
        MaximumOutputBytes,
        ReportedRequestId,
        ReportedCommand,
        Response,
        ExitCode
    ),
    write_response(Response).


execute_request(Request, Response, MaximumOutputBytes) :-
    validate_request(Request, Validated),
    execute_command(
        Validated.command,
        Validated.options,
        Result,
        Diagnostics,
        MaximumOutputBytes
    ),
    success_response(
        Validated.requestId,
        Validated.command,
        Result,
        Diagnostics,
        Response
    ).


validate_request(Request, Validated) :-
    require_dict(Request, "Request must be a JSON object."),
    require_exact_keys(
        Request,
        [protocolVersion, requestId, command, epoch, revision, options],
        []
    ),
    required_text(Request, requestId, 256, RequestId),
    required_text(Request, protocolVersion, 32, ProtocolVersion),
    protocol_version(SupportedVersion),
    (   ProtocolVersion == SupportedVersion
    ->  true
    ;   throw(protocol_error(
            unsupported_protocol,
            "Unsupported protocolVersion.",
            _{requested:ProtocolVersion, supported:SupportedVersion}
        ))
    ),
    required_text(Request, command, 256, CommandText),
    command_atom(CommandText, Command),
    required_safe_integer(Request, epoch, RequestedEpoch),
    required_safe_integer(Request, revision, RequestedRevision),
    epoch_state:loaded_epoch(LoadedEpoch),
    epoch_state:loaded_revision(LoadedRevision),
    (   RequestedEpoch =:= LoadedEpoch,
        RequestedRevision =:= LoadedRevision
    ->  true
    ;   throw(protocol_error(
            stale_state,
            "Requested epoch or revision does not match the loaded state.",
            _{
                requestedEpoch:RequestedEpoch,
                requestedRevision:RequestedRevision,
                loadedEpoch:LoadedEpoch,
                loadedRevision:LoadedRevision
            }
        ))
    ),
    get_dict(options, Request, RawOptions),
    validate_command_options(Command, RawOptions, Options),
    Validated = request{
        requestId: RequestId,
        command: Command,
        options: Options
    }.


command_atom("health", health).
command_atom("inspect-facts", inspect_facts).
command_atom("entity-view", entity_view).
command_atom("subgraph", subgraph).
command_atom(Command, _) :-
    throw(protocol_error(
        unknown_command,
        "Command is not part of the closed v0 command set.",
        _{command:Command}
    )).


command_text(health, "health").
command_text(inspect_facts, "inspect-facts").
command_text(entity_view, "entity-view").
command_text(subgraph, "subgraph").


validate_command_options(health, Raw, _{}) :-
    require_dict(Raw, "health options must be an object."),
    require_exact_keys(Raw, [], []).
validate_command_options(inspect_facts, Raw, Options) :-
    require_dict(Raw, "inspect-facts options must be an object."),
    require_exact_keys(Raw, [entityId], [limits]),
    required_identifier(Raw, entityId, EntityId),
    optional_limits(Raw, fact, Limits),
    Options = _{entityId:EntityId, limits:Limits}.
validate_command_options(entity_view, Raw, Options) :-
    require_dict(Raw, "entity-view options must be an object."),
    require_exact_keys(
        Raw,
        [entityId],
        [language, includeRawProlog, limits]
    ),
    required_identifier(Raw, entityId, EntityId),
    optional_language(Raw, Language),
    optional_boolean(Raw, includeRawProlog, false, IncludeRawProlog),
    optional_limits(Raw, fact, Limits),
    Options = _{
        entityId: EntityId,
        language: Language,
        includeRawProlog: IncludeRawProlog,
        limits: Limits
    }.
validate_command_options(subgraph, Raw, Options) :-
    require_dict(Raw, "subgraph options must be an object."),
    require_exact_keys(
        Raw,
        [rootId, depth, direction],
        [language, limits]
    ),
    required_identifier(Raw, rootId, RootId),
    required_non_negative_integer(Raw, depth, Depth),
    required_text(Raw, direction, 32, DirectionText),
    direction_atom(DirectionText, Direction),
    optional_language(Raw, Language),
    optional_limits(Raw, traversal, Limits),
    Options = _{
        rootId: RootId,
        depth: Depth,
        direction: Direction,
        language: Language,
        limits: Limits
    }.


direction_atom("outgoing", outgoing).
direction_atom("incoming", incoming).
direction_atom("both", both).
direction_atom(Direction, _) :-
    throw(protocol_error(
        invalid_request,
        "direction must be outgoing, incoming, or both.",
        _{direction:Direction}
    )).


execute_command(health, _, Result, [], MaximumOutputBytes) :-
    runtime_limits:hard_limits(HardLimits),
    epoch_state:manifest_summary(Manifests),
    epoch_state:loaded_epoch(Epoch),
    epoch_state:loaded_revision(Revision),
    Result = _{
        kind: health,
        protocolVersion: "0.1",
        epoch: Epoch,
        revision: Revision,
        commands: ["health", "inspect-facts", "entity-view", "subgraph"],
        hardLimits: HardLimits,
        manifests: Manifests
    },
    MaximumOutputBytes = HardLimits.maxOutputBytes.
execute_command(inspect_facts, Options, Result, Diagnostics, MaximumOutputBytes) :-
    runtime_limits:effective_fact_limits(
        Options.limits,
        Effective,
        LimitDiagnostics
    ),
    call_bounded(
        Effective.timeoutMs,
        inspect_facts_result(
            Options.entityId,
            Effective.maxFacts,
            Result,
            ResultDiagnostics
        )
    ),
    append(LimitDiagnostics, ResultDiagnostics, Diagnostics0),
    sort(Diagnostics0, Diagnostics),
    MaximumOutputBytes = Effective.maxOutputBytes.
execute_command(entity_view, Options, Result, Diagnostics, MaximumOutputBytes) :-
    runtime_limits:effective_fact_limits(
        Options.limits,
        Effective,
        LimitDiagnostics
    ),
    language_options(Options.language, ViewOptions),
    call_bounded(
        Effective.timeoutMs,
        entity_view_result(
            Options.entityId,
            ViewOptions,
            Options.includeRawProlog,
            Effective.maxFacts,
            Result
        )
    ),
    Diagnostics = LimitDiagnostics,
    MaximumOutputBytes = Effective.maxOutputBytes.
execute_command(subgraph, Options, Result, Diagnostics, MaximumOutputBytes) :-
    runtime_limits:effective_traversal_limits(
        Options.depth,
        Options.limits,
        _,
        Effective,
        _
    ),
    language_options(Options.language, LanguageOptions),
    put_dict(
        _{
            depth: Options.depth,
            direction: Options.direction,
            limits: Options.limits
        },
        LanguageOptions,
        TraversalOptions
    ),
    call_bounded(
        Effective.timeoutMs,
        subgraph:subgraph(Options.rootId, TraversalOptions, Result)
    ),
    Diagnostics = Result.diagnostics,
    MaximumOutputBytes = Result.effective.limits.maxOutputBytes.


inspect_facts_result(Entity, Maximum, Result, Diagnostics) :-
    findall(
        FactId,
        base_fact_view:incident_fact(
            Entity,
            both,
            _,
            FactId,
            _,
            _,
            _
        ),
        FactIds0
    ),
    sort(FactIds0, FactIds),
    length(FactIds, Total),
    base_fact_view:inspect_facts(Entity, both, Maximum, Facts),
    (   Total =< Maximum
    ->  Diagnostics = []
    ;   Diagnostics = [diagnostic{
            code: max_facts,
            severity: warning,
            message: "Fact limit truncated inspect-facts output.",
            context: _{total:Total, kept:Maximum}
        }]
    ),
    Result = _{
        kind: inspectFacts,
        entityId: Entity,
        facts: Facts,
        totalFactCount: Total
    }.


entity_view_result(
    Entity,
    ViewOptions,
    IncludeRawProlog,
    MaximumFacts,
    Result
) :-
    generic_view:entity_view(Entity, ViewOptions, View),
    view_fact_count(View, FactCount),
    (   FactCount =< MaximumFacts
    ->  true
    ;   throw(protocol_error(
            result_limit_exceeded,
            "entity-view exceeds maxFacts; no partial view was returned.",
            _{factCount:FactCount, maximum:MaximumFacts}
        ))
    ),
    (   IncludeRawProlog == true
    ->  generic_view:entity_prolog(Entity, RawProlog),
        put_dict(rawProlog, View, RawProlog, Result)
    ;   Result = View
    ).


view_fact_count(View, Count) :-
    findall(
        FactId,
        (
            member(Group, View.groups),
            member(Value, Group.values),
            FactId = Value.source.factId
        ),
        FactIds0
    ),
    sort(FactIds0, FactIds),
    length(FactIds, Count).


language_options(default, _{languages:[ru, en]}).
language_options(Language, _{languages:Languages}) :-
    Language \== default,
    (   Language == en
    ->  Languages = [en]
    ;   Languages = [Language, en]
    ).


call_bounded(TimeoutMs, Goal) :-
    Seconds is TimeoutMs / 1000.0,
    catch(
        call_with_time_limit(Seconds, Goal),
        time_limit_exceeded,
        throw(protocol_error(
            timeout,
            "Command exceeded the effective execution-time limit.",
            _{timeoutMs:TimeoutMs}
        ))
    ).


success_response(RequestId, Command, Result, Diagnostics, Response) :-
    command_text(Command, CommandText),
    epoch_state:loaded_epoch(Epoch),
    epoch_state:loaded_revision(Revision),
    Response = _{
        protocolVersion: "0.1",
        requestId: RequestId,
        command: CommandText,
        status: ok,
        epoch: Epoch,
        revision: Revision,
        result: Result,
        diagnostics: Diagnostics
    }.


error_response(RequestId, Command, Code, Message, Details, Response) :-
    epoch_state:loaded_epoch(Epoch),
    epoch_state:loaded_revision(Revision),
    Response = _{
        protocolVersion: "0.1",
        requestId: RequestId,
        command: Command,
        status: error,
        epoch: Epoch,
        revision: Revision,
        error: _{
            code: Code,
            message: Message,
            details: Details
        },
        diagnostics: []
    }.


finalize_response(
    Response0,
    control,
    _,
    _,
    Response0,
    2
) :-
    !.
finalize_response(
    Response0,
    MaximumOutputBytes,
    RequestId,
    Command,
    Response,
    ExitCode
) :-
    response_utf8_size(Response0, Size),
    (   Size =< MaximumOutputBytes
    ->  Response = Response0,
        (   Response0.status == ok
        ->  ExitCode = 0
        ;   ExitCode = 2
        )
    ;   error_response(
            RequestId,
            Command,
            output_limit_exceeded,
            "Success response exceeded maxOutputBytes.",
            _{maximum:MaximumOutputBytes, actual:Size},
            Response
        ),
        ExitCode = 2
    ).


response_utf8_size(Response, Size) :-
    with_output_to(
        string(Text),
        json_write_dict(current_output, Response, [width(0)])
    ),
    string_codes(Text, Codes),
    phrase(utf8_codes(Codes), Bytes),
    length(Bytes, Size).


write_response(Response) :-
    json_write_dict(current_output, Response, [width(0)]),
    nl.


reported_request_id(Request, RequestId) :-
    is_dict(Request),
    get_dict(requestId, Request, Value),
    valid_text(Value, 256, RequestId),
    !.
reported_request_id(_, null).


reported_command(Request, Command) :-
    is_dict(Request),
    get_dict(command, Request, Value),
    valid_text(Value, 256, Command),
    !.
reported_command(_, null).


require_dict(Value, _) :-
    is_dict(Value),
    !.
require_dict(_, Message) :-
    throw(protocol_error(invalid_request, Message, _{})).


require_exact_keys(Dict, Required, Optional) :-
    dict_pairs(Dict, _, Pairs),
    pairs_keys(Pairs, Actual0),
    sort(Actual0, Actual),
    append(Required, Optional, Allowed0),
    sort(Allowed0, Allowed),
    subtract(Actual, Allowed, Unsupported),
    subtract(Required, Actual, Missing),
    (   Unsupported == [],
        Missing == []
    ->  true
    ;   throw(protocol_error(
            invalid_request,
            "Object contains missing or unsupported properties.",
            _{missing:Missing, unsupported:Unsupported}
        ))
    ).


required_identifier(Dict, Key, Atom) :-
    required_text(Dict, Key, 4096, Text),
    atom_string(Atom, Text).


required_text(Dict, Key, MaximumLength, Text) :-
    (   get_dict(Key, Dict, Value),
        valid_text(Value, MaximumLength, Text)
    ->  true
    ;   throw(protocol_error(
            invalid_request,
            "Required text property is missing or invalid.",
            _{property:Key, maximumLength:MaximumLength}
        ))
    ).


valid_text(Value, MaximumLength, Text) :-
    (   string(Value)
    ->  Text = Value
    ;   atom(Value),
        \+ memberchk(Value, [true, false, null])
    ->  atom_string(Value, Text)
    ),
    string_length(Text, Length),
    Length >= 1,
    Length =< MaximumLength.


required_safe_integer(Dict, Key, Value) :-
    required_non_negative_integer(Dict, Key, Value),
    safe_integer_max(Maximum),
    (   Value =< Maximum
    ->  true
    ;   throw(protocol_error(
            invalid_request,
            "Integer exceeds the JSON-safe range.",
            _{property:Key, maximum:Maximum}
        ))
    ).


required_non_negative_integer(Dict, Key, Value) :-
    (   get_dict(Key, Dict, Value),
        integer(Value),
        Value >= 0
    ->  true
    ;   throw(protocol_error(
            invalid_request,
            "Required property must be a non-negative integer.",
            _{property:Key}
        ))
    ).


optional_language(Dict, Language) :-
    (   get_dict(language, Dict, _)
    ->  required_text(Dict, language, 64, Text),
        atom_string(Language, Text)
    ;   Language = default
    ).


optional_boolean(Dict, Key, Default, Value) :-
    (   get_dict(Key, Dict, Found)
    ->  (   memberchk(Found, [true, false])
        ->  Value = Found
        ;   throw(protocol_error(
                invalid_request,
                "Optional property must be boolean.",
                _{property:Key}
            ))
        )
    ;   Value = Default
    ).


optional_limits(Dict, Kind, Limits) :-
    (   get_dict(limits, Dict, Found)
    ->  validate_limits(Kind, Found, Limits)
    ;   Limits = _{}
    ).


validate_limits(fact, Raw, Raw) :-
    require_dict(Raw, "limits must be an object."),
    require_exact_keys(
        Raw,
        [],
        [maxFacts, maxOutputBytes, timeoutMs]
    ),
    validate_positive_limit_values(Raw).
validate_limits(traversal, Raw, Raw) :-
    require_dict(Raw, "limits must be an object."),
    require_exact_keys(
        Raw,
        [],
        [
            maxNodes,
            maxFacts,
            maxOccurrences,
            maxPathLength,
            maxOutputBytes,
            timeoutMs
        ]
    ),
    validate_positive_limit_values(Raw).


validate_positive_limit_values(Dict) :-
    dict_pairs(Dict, _, Pairs),
    forall(
        member(Key-Value, Pairs),
        (
            integer(Value),
            Value >= 1,
            Value =< 2147483647
        ->  true
        ;   throw(protocol_error(
                invalid_request,
                "Limit must be a positive 32-bit integer.",
                _{property:Key}
            ))
        )
    ).
