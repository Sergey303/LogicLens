#!/usr/bin/env python3
"""Verify plunit test cases stay clauses under the trusted candidate boundary."""

from __future__ import annotations

import sys
from pathlib import Path


class VerificationError(AssertionError):
    pass


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

    invalid = (
        ":- begin_tests(candidate_member).\n"
        ":- use_module('../rules/candidate_member.pl').\n"
        ":- test(is_member).\n"
        ":- end_tests(candidate_member).\n"
    ).encode("utf-8")
    try:
        cli.validate_prolog_file(path, invalid, "test", rule_paths)
    except cli.CandidateError as exc:
        if "unreviewed directives ['test']" not in str(exc):
            raise VerificationError(f"unexpected directive diagnostic: {exc}") from exc
    else:
        raise VerificationError("trusted validator accepted :- test(...)")

    print("ok 1 - ordinary plunit test clause remains accepted")
    print("ok 2 - test is absent from the trusted directive allowlist")
    print("ok 3 - :- test(...) remains rejected as unreviewed")
    print("1..3")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ImportError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
