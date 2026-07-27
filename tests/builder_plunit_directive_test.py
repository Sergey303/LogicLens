#!/usr/bin/env python3
"""Verify plunit tests remain clauses and registered inside non-empty suites."""

from __future__ import annotations

import sys
from pathlib import Path


class VerificationError(AssertionError):
    pass


def require_rejected(cli, path: Path, rule_paths: list[Path], source: str, text: str) -> None:
    try:
        cli.validate_prolog_file(path, source.encode("utf-8"), "test", rule_paths)
    except cli.CandidateError as exc:
        if text not in str(exc):
            raise VerificationError(f"unexpected validator diagnostic: {exc}") from exc
    else:
        raise VerificationError(f"trusted validator accepted invalid PlUnit source: {text}")


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    tools = repository / "tools"
    sys.path.insert(0, str(tools))
    try:
        import builder_candidate  # noqa: F401 - installs reviewed validator hooks
        from builder_candidate import cli
    finally:
        sys.path.remove(str(tools))

    if "test" in cli.ALLOWED_DIRECTIVES:
        raise VerificationError("trusted directive allowlist must not include test")

    path = Path("tests/candidate_member_tests.pl")
    rule_paths = [Path("rules/candidate_member.pl")]
    valid = (
        ":- begin_tests(candidate_member).\n"
        ":- use_module('../rules/candidate_member.pl').\n"
        "test(is_member) :- assertion(true).\n"
        ":- end_tests(candidate_member).\n"
    ).encode("utf-8")
    cli.validate_prolog_file(path, valid, "test", rule_paths)

    directive_test = (
        ":- begin_tests(candidate_member).\n"
        ":- use_module('../rules/candidate_member.pl').\n"
        ":- test(is_member).\n"
        ":- end_tests(candidate_member).\n"
    )
    require_rejected(
        cli,
        path,
        rule_paths,
        directive_test,
        "unreviewed directives ['test']",
    )

    qwen_empty_suite = (
        ":- begin_tests(candidate_member).\n"
        ":- use_module('../rules/candidate_member.pl').\n"
        ":- end_tests(candidate_member).\n"
        "test(is_member) :- assertion(true).\n"
    )
    require_rejected(
        cli,
        path,
        rule_paths,
        qwen_empty_suite,
        "has no registered tests",
    )

    outside_before_suite = (
        "test(is_member) :- assertion(true).\n"
        ":- begin_tests(candidate_member).\n"
        ":- use_module('../rules/candidate_member.pl').\n"
        "test(second) :- assertion(true).\n"
        ":- end_tests(candidate_member).\n"
    )
    require_rejected(
        cli,
        path,
        rule_paths,
        outside_before_suite,
        "outside begin_tests/end_tests",
    )

    mismatched_suite = (
        ":- begin_tests(candidate_member).\n"
        ":- use_module('../rules/candidate_member.pl').\n"
        "test(is_member) :- assertion(true).\n"
        ":- end_tests(other_suite).\n"
    )
    require_rejected(
        cli,
        path,
        rule_paths,
        mismatched_suite,
        "does not match begin_tests",
    )

    print("ok 1 - ordinary plunit test clause remains accepted")
    print("ok 2 - test is absent from the trusted directive allowlist")
    print("ok 3 - :- test(...) remains rejected as unreviewed")
    print("ok 4 - a suite closed before its test is rejected as empty")
    print("ok 5 - test clauses outside a suite are rejected")
    print("ok 6 - mismatched begin_tests/end_tests names are rejected")
    print("1..6")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ImportError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
