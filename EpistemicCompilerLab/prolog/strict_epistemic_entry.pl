:- use_module(library(http/json)).
:- use_module(strict_epistemic_request).
:- initialization(main, main).

main(Argv) :-
    catch(dispatch(Argv, Result), Error, error_result(Error, Result)),
    json_write_dict(current_output, Result, [width(0)]),
    nl.

dispatch(['request-frame', Revision, Material], Result) :-
    request_frame(Revision, Material, Result).
dispatch(_, _{
    status: invalid_request,
    usage: ["request-frame <revision|missing> <material|missing>"]
}).

error_result(Error, _{
    status: error,
    message: Message
}) :-
    message_to_string(Error, Message).
