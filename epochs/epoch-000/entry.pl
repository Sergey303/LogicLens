:- use_module('rules/cli_runtime.pl').
:- use_module(library(http/json)).

:- initialization(main, main).


main :-
    set_prolog_flag(encoding, utf8),
    catch(
        json_read_dict(user_input, Request, [value_string_as(string)]),
        Error,
        bootstrap_failure(Error)
    ),
    cli_runtime:handle_request(Request, Response, ExitCode),
    json_write_dict(current_output, Response, [width(0)]),
    nl,
    flush_output(current_output),
    halt(ExitCode).


bootstrap_failure(Error) :-
    print_message(error, Error),
    halt(2).
