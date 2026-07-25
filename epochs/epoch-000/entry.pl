:- use_module('cli/prolog_cli.pl').

:- initialization(main, main).


main :-
    catch(
        prolog_cli:run(ExitCode),
        Error,
        (
            print_message(error, Error),
            ExitCode = 3
        )
    ),
    halt(ExitCode).
