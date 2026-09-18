:- module(revision_runtime, [handle_request/3]).
:- use_module('cli_runtime.pl', []).
:- use_module('candidate_researcher_at_iis.pl').

protocol_version("0.1").
loaded_epoch(0).
loaded_revision(1).
derived_predicate("urn:logiclens:derived:researcher-at-iis").

handle_request(Request, Response, ExitCode) :-
    reported_context(Request, RequestId, Command),
    catch(
        handle_checked(Request, Response0, ExitCode0),
        Error,
        overlay_error_response(Error, RequestId, Command, Response0, ExitCode0)
    ),
    Response = Response0,
    ExitCode = ExitCode0.

handle_checked(Request, Response, ExitCode) :-
    (   request_state(Request, RequestedEpoch, RequestedRevision)
    ->  loaded_epoch(LoadedEpoch),
        loaded_revision(LoadedRevision),
        (   RequestedEpoch =:= LoadedEpoch,
            RequestedRevision =:= LoadedRevision
        ->  dispatch_current(Request, Response, ExitCode)
        ;   stale_state_response(
                Request,
                RequestedEpoch,
                RequestedRevision,
                Response,
                ExitCode
            )
        )
    ;   delegate_unvalidated(Request, Response, ExitCode)
    ).

request_state(Request, Epoch, Revision) :-
    is_dict(Request),
    get_dict(epoch, Request, Epoch),
    integer(Epoch),
    Epoch >= 0,
    get_dict(revision, Request, Revision),
    integer(Revision),
    Revision >= 0.

dispatch_current(Request, Response, ExitCode) :-
    (   get_dict(command, Request, "derived-query")
    ->  run_derived_request(Request, Response, ExitCode)
    ;   delegate_current(Request, Response, ExitCode)
    ).

delegate_current(Request, Response, ExitCode) :-
    put_dict(_{epoch: 0, revision: 0}, Request, BaselineRequest),
    cli_runtime:handle_request(BaselineRequest, BaselineResponse, ExitCode),
    patch_baseline_response(BaselineResponse, Response).

delegate_unvalidated(Request, Response, ExitCode) :-
    cli_runtime:handle_request(Request, BaselineResponse, ExitCode),
    patch_baseline_response(BaselineResponse, Response).

patch_baseline_response(BaselineResponse, Response) :-
    loaded_epoch(Epoch),
    loaded_revision(Revision),
    put_dict(_{epoch: Epoch, revision: Revision}, BaselineResponse, RevisionResponse),
    patch_health_commands(RevisionResponse, Response).

patch_health_commands(Response0, Response) :-
    (   get_dict(status, Response0, ok),
        get_dict(command, Response0, health),
        get_dict(result, Response0, Result0),
        get_dict(availableCommands, Result0, Commands0)
    ->  append(Commands0, ['derived-query'], Commands),
        put_dict(availableCommands, Result0, Commands, Result),
        put_dict(result, Response0, Result, Response)
    ;   Response = Response0
    ).

run_derived_request(Request, Response, ExitCode) :-
    validate_derived_request(Request, RequestId, PredicateIri),
    findall(
        row{entityId: Person, evidenceFactIds: EvidenceFactIds},
        candidate_researcher_at_iis:researcher_at_iis(Person, EvidenceFactIds),
        Rows0
    ),
    sort(Rows0, Rows),
    length(Rows, RowCount),
    (   RowCount =< 1000
    ->  true
    ;   throw(overlay_error(
            "result_limit_exceeded",
            "The reviewed derived result exceeds 1000 rows.",
            _{rowCount: RowCount, maxRows: 1000}
        ))
    ),
    protocol_version(Version),
    loaded_epoch(Epoch),
    loaded_revision(Revision),
    Response = response{
        protocolVersion: Version,
        requestId: RequestId,
        command: 'derived-query',
        status: ok,
        epoch: Epoch,
        revision: Revision,
        result: derived_result{
            kind: 'derived-query',
            predicate: PredicateIri,
            rows: Rows
        },
        diagnostics: []
    },
    ExitCode = 0.

validate_derived_request(Request, RequestId, PredicateIri) :-
    require_exact_keys(
        Request,
        [protocolVersion, requestId, command, epoch, revision, options]
    ),
    get_dict(protocolVersion, Request, Version),
    protocol_version(ExpectedVersion),
    (   Version == ExpectedVersion
    ->  true
    ;   throw(overlay_error(
            "unsupported_protocol",
            "The requested protocol version is not supported.",
            _{requested: Version, supported: ExpectedVersion}
        ))
    ),
    get_dict(requestId, Request, RequestId),
    require_string(RequestId, requestId),
    get_dict(options, Request, Options),
    require_exact_keys(Options, [predicate]),
    get_dict(predicate, Options, PredicateIri),
    require_string(PredicateIri, predicate),
    derived_predicate(ExpectedPredicate),
    (   PredicateIri == ExpectedPredicate
    ->  true
    ;   throw(overlay_error(
            "unknown_predicate",
            "The predicate is not part of the reviewed derived registry.",
            _{predicate: PredicateIri}
        ))
    ).

require_exact_keys(Dict, ExpectedKeys) :-
    (   is_dict(Dict)
    ->  dict_keys(Dict, Keys0),
        sort(Keys0, Keys),
        sort(ExpectedKeys, Expected),
        (   Keys == Expected
        ->  true
        ;   throw(overlay_error(
                "invalid_request",
                "The request contains missing or unknown fields.",
                _{}
            ))
        )
    ;   throw(overlay_error(
            "invalid_request",
            "The request must be a JSON object.",
            _{}
        ))
    ).

require_string(Value, Field) :-
    (   string(Value),
        string_length(Value, Length),
        between(1, 1024, Length)
    ->  true
    ;   throw(overlay_error(
            "invalid_request",
            "A reviewed string field is invalid.",
            _{field: Field}
        ))
    ).

stale_state_response(Request, RequestedEpoch, RequestedRevision, Response, 1) :-
    reported_context(Request, RequestId, Command),
    loaded_epoch(Epoch),
    loaded_revision(Revision),
    protocol_version(Version),
    Response = response{
        protocolVersion: Version,
        requestId: RequestId,
        command: Command,
        status: error,
        epoch: Epoch,
        revision: Revision,
        error: error{
            code: "stale_state",
            message: "The requested epoch or revision does not match the loaded state.",
            details: _{
                requestedEpoch: RequestedEpoch,
                requestedRevision: RequestedRevision,
                loadedEpoch: Epoch,
                loadedRevision: Revision
            }
        },
        diagnostics: []
    }.

reported_context(Request, RequestId, Command) :-
    (   is_dict(Request),
        get_dict(requestId, Request, CandidateRequestId),
        string(CandidateRequestId)
    ->  RequestId = CandidateRequestId
    ;   RequestId = null
    ),
    (   is_dict(Request),
        get_dict(command, Request, CandidateCommand),
        string(CandidateCommand)
    ->  Command = CandidateCommand
    ;   Command = null
    ).

overlay_error_response(
    overlay_error(Code, Message, Details),
    RequestId,
    Command,
    Response,
    1
) :-
    !,
    error_response(Code, Message, Details, RequestId, Command, Response).
overlay_error_response(_, RequestId, Command, Response, 1) :-
    error_response(
        "internal_error",
        "The reviewed derived command failed before producing a result.",
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
        error: error{code: Code, message: Message, details: Details},
        diagnostics: []
    }.
