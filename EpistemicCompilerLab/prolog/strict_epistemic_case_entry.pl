:- use_module(library(http/json)).
:- use_module(strict_epistemic_case).
:- initialization(main, main).

main(Argv) :-
    catch(dispatch(Argv, Result), Error, error_result(Error, Result)),
    json_write_dict(current_output, Result, [width(0)]),
    nl.

dispatch(
    ['case-frame', Revision, Material, PositiveCsv, NegativeCsv],
    Result
) :-
    case_frame(Revision, Material, PositiveCsv, NegativeCsv, Result).
dispatch(_, _{
    status:invalid_request,
    usage:[
        "case-frame <revision|missing> <material|missing> "
        "<positive-ids|none> <negative-ids|none>"
    ]
}).

error_result(Error, _{status:error, message:Message}) :-
    message_to_string(Error, Message).
