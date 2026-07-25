:- begin_tests(prolog_cli_internal).

:- use_module('../cli/prolog_cli.pl').


test(timeout_becomes_protocol_error, [
    throws(protocol_error(timeout, _, _))
]) :-
    prolog_cli:call_bounded(1, sleep(0.05)).


:- end_tests(prolog_cli_internal).
