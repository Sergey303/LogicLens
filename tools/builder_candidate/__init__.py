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
