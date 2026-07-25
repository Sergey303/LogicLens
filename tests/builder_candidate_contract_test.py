#!/usr/bin/env python3
"""Contract verification for the provider-neutral epoch candidate pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Callable


class VerificationError(AssertionError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--fixture", required=True, type=Path)
    return parser.parse_args()


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def tree(root: Path) -> dict[PurePosixPath, bytes]:
    result: dict[PurePosixPath, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            result[PurePosixPath(path.relative_to(root).as_posix())] = (
                "SYMLINK:" + str(path.readlink())
            ).encode("utf-8")
        elif path.is_file():
            result[PurePosixPath(path.relative_to(root).as_posix())] = path.read_bytes()
    return result


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path, content in sorted(tree(root).items(), key=lambda item: str(item[0])):
        path_bytes = str(path).encode("utf-8")
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, separators=(",", ": "))
        + "\n",
        encoding="utf-8",
    )


def run_builder(
    baseline: Path,
    proposal: Path,
    schema: Path,
    output: Path,
    report: Path,
) -> subprocess.CompletedProcess[str]:
    root = repository_root()
    return subprocess.run(
        [
            sys.executable,
            str(root / "tools" / "build_epoch_candidate.py"),
            "--baseline",
            str(baseline),
            "--proposal",
            str(proposal),
            "--schema",
            str(schema),
            "--output",
            str(output),
            "--report",
            str(report),
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=90,
    )


def require_success(completed: subprocess.CompletedProcess[str]) -> None:
    if completed.returncode != 0:
        raise VerificationError(
            f"candidate build failed: stdout={completed.stdout!r}, "
            f"stderr={completed.stderr!r}"
        )


def require_failure(
    completed: subprocess.CompletedProcess[str],
    expected_text: str,
) -> None:
    if completed.returncode == 0:
        raise VerificationError(
            f"candidate build unexpectedly succeeded: {completed.stdout!r}"
        )
    combined = completed.stdout + completed.stderr
    if expected_text not in combined:
        raise VerificationError(
            f"failure did not contain {expected_text!r}: {combined!r}"
        )


def copy_fixture(source: Path, target: Path) -> Path:
    shutil.copytree(source, target)
    return target


def verify_valid_candidate(
    baseline: Path,
    schema: Path,
    fixture: Path,
) -> None:
    before = tree_digest(baseline)
    with tempfile.TemporaryDirectory(prefix="logiclens-builder-valid-") as temporary:
        root = Path(temporary)
        output_a = root / "candidate-a"
        output_b = root / "candidate-b"
        report_a = root / "report-a.json"
        report_b = root / "report-b.json"

        first = run_builder(baseline, fixture, schema, output_a, report_a)
        second = run_builder(baseline, fixture, schema, output_b, report_b)
        require_success(first)
        require_success(second)

        if tree(output_a) != tree(output_b):
            raise VerificationError("identical proposals must build byte-identical packages")
        if report_a.read_bytes() != report_b.read_bytes():
            raise VerificationError("identical proposals must produce byte-identical reports")

        manifest = read_json(output_a / "candidate-manifest.json")
        report = read_json(report_a)
        if manifest.get("stage") != "candidate":
            raise VerificationError("candidate manifest stage is not candidate")
        if manifest.get("candidateId") != "fixture-candidate-member-v0":
            raise VerificationError("candidate manifest lost candidate identity")
        if report.get("candidateId") != manifest.get("candidateId"):
            raise VerificationError("comparison report candidate identity mismatch")
        if report.get("comparison", {}).get("runtimeOutputsEqual") is not True:
            raise VerificationError("candidate must preserve stable runtime smoke output")
        if report.get("comparison", {}).get("modifiedActiveFiles") != []:
            raise VerificationError("candidate report must not claim active-file changes")
        validation = report.get("validation")
        if not isinstance(validation, list) or not validation:
            raise VerificationError("comparison report is missing validation results")
        if any(item.get("status") != "passed" for item in validation):
            raise VerificationError("accepted candidate contains a failed validation")

        expected_added = {
            "rules/candidate_member.pl",
            "tests/candidate_member_tests.pl",
            "ui/component-bindings.json",
        }
        if set(report["comparison"]["addedFiles"]) != expected_added:
            raise VerificationError("comparison report added-file set is incorrect")

    if tree_digest(baseline) != before:
        raise VerificationError("valid candidate build modified the active baseline")


def negative_case(
    baseline: Path,
    schema: Path,
    fixture: Path,
    name: str,
    mutate: Callable[[Path], None],
    expected_text: str,
) -> None:
    before = tree_digest(baseline)
    with tempfile.TemporaryDirectory(prefix=f"logiclens-builder-{name}-") as temporary:
        root = Path(temporary)
        proposal = copy_fixture(fixture, root / "proposal")
        mutate(proposal)
        completed = run_builder(
            baseline,
            proposal,
            schema,
            root / "candidate",
            root / "report.json",
        )
        require_failure(completed, expected_text)
    if tree_digest(baseline) != before:
        raise VerificationError(f"negative case {name} modified the active baseline")


def mutate_path_traversal(proposal: Path) -> None:
    value = read_json(proposal / "proposal.json")
    value["files"][0]["path"] = "../escape.pl"
    write_json(proposal / "proposal.json", value)


def mutate_missing_test(proposal: Path) -> None:
    value = read_json(proposal / "proposal.json")
    value["files"] = [item for item in value["files"] if item["kind"] != "test"]
    write_json(proposal / "proposal.json", value)
    shutil.rmtree(proposal / "files" / "tests")


def mutate_dangerous_prolog(proposal: Path) -> None:
    rule = proposal / "files" / "rules" / "candidate_member.pl"
    rule.write_text(
        ":- module(candidate_member, [candidate_member/1]).\n"
        ":- use_module('../data/epoch_data.pl').\n"
        "candidate_member(_) :- shell('echo forbidden').\n",
        encoding="utf-8",
    )


def mutate_unknown_component(proposal: Path) -> None:
    path = proposal / "files" / "ui" / "component-bindings.json"
    value = read_json(path)
    value["bindings"][0]["component"] = "Table"
    write_json(path, value)


def mutate_undeclared_file(proposal: Path) -> None:
    (proposal / "files" / "rules" / "extra.pl").write_text(
        "extra_fact(ok).\n",
        encoding="utf-8",
    )


def mutate_base_revision(proposal: Path) -> None:
    value = read_json(proposal / "proposal.json")
    value["base"]["revision"] = 1
    write_json(proposal / "proposal.json", value)


def mutate_unreviewed_directive(proposal: Path) -> None:
    rule = proposal / "files" / "rules" / "candidate_member.pl"
    rule.write_text(
        ":- module(candidate_member, [candidate_member/1]).\n"
        ":- use_module('../data/epoch_data.pl').\n"
        ":- initialization(true).\n"
        "candidate_member(Entity) :- epoch_data:fact(_, Entity, _, _).\n",
        encoding="utf-8",
    )


def verify_output_overlap(
    baseline: Path,
    schema: Path,
    fixture: Path,
) -> None:
    before = tree_digest(baseline)
    with tempfile.TemporaryDirectory(prefix="logiclens-builder-overlap-") as temporary:
        proposal = copy_fixture(fixture, Path(temporary) / "proposal")
        completed = run_builder(
            baseline,
            proposal,
            schema,
            proposal / "files" / "candidate-output",
            Path(temporary) / "report.json",
        )
        require_failure(completed, "output overlaps proposal")
    if tree_digest(baseline) != before:
        raise VerificationError("overlap rejection modified the active baseline")


def main() -> int:
    args = parse_args()
    baseline = args.baseline.resolve()
    schema = args.schema.resolve()
    fixture = args.fixture.resolve()

    tests: list[tuple[str, Callable[[], None]]] = [
        (
            "valid deterministic candidate",
            lambda: verify_valid_candidate(baseline, schema, fixture),
        ),
        (
            "path traversal",
            lambda: negative_case(
                baseline,
                schema,
                fixture,
                "path-traversal",
                mutate_path_traversal,
                "unsafe candidate file path",
            ),
        ),
        (
            "missing candidate test",
            lambda: negative_case(
                baseline,
                schema,
                fixture,
                "missing-test",
                mutate_missing_test,
                "candidate must declare at least one test file",
            ),
        ),
        (
            "dangerous Prolog call",
            lambda: negative_case(
                baseline,
                schema,
                fixture,
                "dangerous-prolog",
                mutate_dangerous_prolog,
                "forbidden call",
            ),
        ),
        (
            "unknown UI component",
            lambda: negative_case(
                baseline,
                schema,
                fixture,
                "unknown-component",
                mutate_unknown_component,
                "unknown UI component",
            ),
        ),
        (
            "undeclared candidate file",
            lambda: negative_case(
                baseline,
                schema,
                fixture,
                "undeclared-file",
                mutate_undeclared_file,
                "candidate contains undeclared files",
            ),
        ),
        (
            "wrong base revision",
            lambda: negative_case(
                baseline,
                schema,
                fixture,
                "wrong-revision",
                mutate_base_revision,
                "candidate revision does not match",
            ),
        ),
        (
            "unreviewed directive",
            lambda: negative_case(
                baseline,
                schema,
                fixture,
                "unreviewed-directive",
                mutate_unreviewed_directive,
                "unreviewed directives",
            ),
        ),
        (
            "output overlap",
            lambda: verify_output_overlap(baseline, schema, fixture),
        ),
    ]

    for index, (name, test) in enumerate(tests, start=1):
        test()
        print(f"ok {index} - {name}")
    print(f"1..{len(tests)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        VerificationError,
        OSError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
