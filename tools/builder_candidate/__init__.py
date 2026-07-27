"""Provider-neutral candidate epoch packaging and verification."""

from __future__ import annotations

import re

from . import cli as _cli


# A Prolog directive starts a source line with `:-`. A rule body separator such
# as `candidate(X) :- epoch_data:fact(...)` must never be classified as a
# directive merely because the body begins with an identifier.
_cli.DIRECTIVE_NAME = re.compile(
    r"^\s*:-\s*([A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
_cli.USE_MODULE = re.compile(
    r"^\s*:-\s*use_module\s*\((.*?)\)\s*\.",
    re.MULTILINE | re.DOTALL,
)

# Candidate v0 is deliberately not a general Prolog sandbox. Reject direct and
# higher-order execution, reflection, mutable database, filesystem, process,
# network, environment, clock and randomness primitives before SWI loads the
# source. Execution still runs under independent timeout and output caps.
_cli.FORBIDDEN_PROLOG_CALLS = re.compile(
    r"(?:"
    r"\b(?:"
    r"shell|process_create|process_wait|process_kill|consult|load_files|"
    r"open|close|tell|told|see|seen|stream_property|current_stream|"
    r"current_input|current_output|set_input|set_output|with_output_to|"
    r"working_directory|delete_file|rename_file|copy_file|make_directory|"
    r"directory_files|expand_file_name|absolute_file_name|access_file|"
    r"exists_file|exists_directory|same_file|time_file|size_file|read_link|"
    r"tmp_file|tmp_file_stream|http_open|http_get|http_post|tcp_connect|"
    r"tcp_socket|udp_socket|socket|asserta|assertz|retract|retractall|"
    r"abolish|recorda|recordz|recorded|erase|nb_setval|nb_linkval|b_setval|"
    r"flag|set_prolog_flag|setenv|getenv|call|once|ignore|forall|findall|"
    r"bagof|setof|maplist|include|exclude|partition|convlist|foldl|scanl|"
    r"phrase|phrase_from_file|call_cleanup|setup_call_cleanup|catch|throw|"
    r"current_predicate|predicate_property|clause|nth_clause|clause_property|"
    r"source_file|current_module|current_prolog_flag|current_op|"
    r"current_atom|current_functor|read|read_term|read_term_from_atom|"
    r"atom_to_term|term_to_atom|get_time|sleep|random|random_between|"
    r"uuid|halt"
    r")\s*\(|=\.\."
    r")",
    re.IGNORECASE,
)

_PLUNIT_EVENT = re.compile(
    r"^\s*(?P<directive>:-\s*)?"
    r"(?P<kind>begin_tests|end_tests|test)\s*"
    r"\(\s*(?P<name>[a-z][A-Za-z0-9_]*)",
    re.MULTILINE,
)


def _validate_plunit_structure(path, text: str) -> None:
    """Require every candidate PlUnit suite to contain registered test clauses."""

    active_suite: str | None = None
    active_test_count = 0
    suite_count = 0

    for match in _PLUNIT_EVENT.finditer(text):
        kind = match.group("kind")
        name = match.group("name")
        is_directive = match.group("directive") is not None

        if kind == "begin_tests":
            if not is_directive:
                raise _cli.CandidateError(
                    f"candidate begin_tests must be a directive: {path}"
                )
            if active_suite is not None:
                raise _cli.CandidateError(
                    f"candidate PlUnit suites cannot be nested: {path}"
                )
            active_suite = name
            active_test_count = 0
            suite_count += 1
            continue

        if kind == "test":
            if is_directive:
                raise _cli.CandidateError(
                    f"candidate PlUnit test must be an ordinary clause: {path}"
                )
            if active_suite is None:
                raise _cli.CandidateError(
                    f"candidate PlUnit test is outside begin_tests/end_tests: {path}"
                )
            active_test_count += 1
            continue

        if not is_directive:
            raise _cli.CandidateError(
                f"candidate end_tests must be a directive: {path}"
            )
        if active_suite is None:
            raise _cli.CandidateError(
                f"candidate end_tests has no matching begin_tests: {path}"
            )
        if name != active_suite:
            raise _cli.CandidateError(
                f"candidate end_tests({name}) does not match "
                f"begin_tests({active_suite}): {path}"
            )
        if active_test_count == 0:
            raise _cli.CandidateError(
                f"candidate PlUnit suite {active_suite!r} has no registered tests: {path}"
            )
        active_suite = None
        active_test_count = 0

    if active_suite is not None:
        raise _cli.CandidateError(
            f"candidate begin_tests({active_suite}) has no matching end_tests: {path}"
        )
    if suite_count == 0:
        raise _cli.CandidateError(
            f"candidate test must contain a PlUnit suite: {path}"
        )


def _validate_prolog_file(path, content, kind, rule_paths) -> None:
    """Validate candidate Prolog while allowing quoted ontology IRI data.

    HTTP(S) strings are ordinary identifiers in LogicLens facts. Network access
    remains forbidden by the closed predicate list above. File URLs, UNC paths,
    absolute filesystem paths, unsafe directives and imports remain rejected.
    """

    text = _cli.decode_text(path, content)
    lowered = text.lower()
    if "file://" in lowered or "\\\\" in text:
        raise _cli.CandidateError(
            f"candidate Prolog contains an external filesystem path: {path}"
        )
    if re.search(
        r"(?:^|[^A-Za-z0-9_])(?:[A-Za-z]:[\\/]|/(?:tmp|etc|home|var|usr)/)",
        text,
    ):
        raise _cli.CandidateError(f"candidate Prolog contains an absolute path: {path}")

    forbidden = _cli.FORBIDDEN_PROLOG_CALLS.search(text)
    if forbidden:
        raise _cli.CandidateError(
            f"candidate Prolog uses forbidden call {forbidden.group(0)!r}: {path}"
        )

    directives = set(_cli.DIRECTIVE_NAME.findall(text))
    unknown_directives = sorted(directives - _cli.ALLOWED_DIRECTIVES)
    if unknown_directives:
        raise _cli.CandidateError(
            f"candidate Prolog uses unreviewed directives {unknown_directives}: {path}"
        )

    if kind == "rule":
        if "module" not in directives:
            raise _cli.CandidateError(f"candidate rule must declare a module: {path}")
    else:
        if "begin_tests" not in directives or "end_tests" not in directives:
            raise _cli.CandidateError(
                f"candidate test must use begin_tests/end_tests: {path}"
            )
        _validate_plunit_structure(path, text)

    allowed_rule_imports = {"'../data/epoch_data.pl'", '"../data/epoch_data.pl"'}
    allowed_test_imports = {
        f"'../rules/{rule_path.name}'" for rule_path in rule_paths
    } | {
        f'"../rules/{rule_path.name}"' for rule_path in rule_paths
    }
    allowed_imports = allowed_rule_imports if kind == "rule" else allowed_test_imports
    for raw_import in _cli.USE_MODULE.findall(text):
        normalized = "".join(raw_import.split())
        if normalized not in allowed_imports:
            raise _cli.CandidateError(
                f"candidate Prolog import is not allowlisted: {raw_import!r} in {path}"
            )


_cli.validate_prolog_file = _validate_prolog_file
