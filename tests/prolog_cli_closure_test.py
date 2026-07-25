#!/usr/bin/env python3
"""Closure checks for every security and determinism claim in ADR-0007."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

import prolog_cli_contract_test as base


VOLATILE_KEYS = {
    "pid",
    "processId",
    "process_id",
    "timestamp",
    "timestampUtc",
    "startedAt",
    "finishedAt",
    "elapsed",
    "elapsedMs",
    "duration",
    "durationMs",
    "workingDirectory",
    "cwd",
    "temporaryPath",
    "tempPath",
    "nonce",
    "random",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epoch", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    return parser.parse_args()


def test_invalid_request_ids(
    epoch: Path,
    validator: Draft202012Validator,
) -> None:
    missing = base.request("health", {})
    del missing["requestId"]
    response, _ = base.require_error(epoch, validator, missing, "invalid_request")
    assert response["requestId"] is None
    assert response["command"] == "health"
    assert response["epoch"] == 0
    assert response["revision"] == 0

    invalid = base.request("health", {}, requestId="")
    response, _ = base.require_error(epoch, validator, invalid, "invalid_request")
    assert response["requestId"] is None
    assert response["command"] == "health"


def test_stale_revision_reports_loaded_state(
    epoch: Path,
    validator: Draft202012Validator,
) -> None:
    response, _ = base.require_error(
        epoch,
        validator,
        base.request("health", {}, revision=1),
        "stale_state",
    )
    assert response["epoch"] == 0
    assert response["revision"] == 0
    assert response["requestId"] == "test-health"


def test_command_option_isolation(
    epoch: Path,
    validator: Draft202012Validator,
) -> None:
    invalid_requests = [
        base.request("health", {"entityId": base.PERSON}),
        base.request(
            "inspect-facts",
            {"entityId": base.PERSON, "includeRawProlog": True},
        ),
        base.request(
            "entity-view",
            {"entityId": base.PERSON, "direction": "both"},
        ),
        base.request(
            "subgraph",
            {
                "rootId": base.PERSON,
                "depth": 1,
                "direction": "both",
                "includeRawProlog": True,
            },
        ),
    ]
    for payload in invalid_requests:
        base.require_error(epoch, validator, payload, "invalid_request")


def test_no_dynamic_execution_selectors(
    epoch: Path,
    validator: Draft202012Validator,
) -> None:
    forbidden_options: dict[str, Any] = {
        "module": "user",
        "filePath": "/tmp/evil.pl",
        "predicate": "shell",
        "query": "halt",
        "rawGoal": "halt",
        "consult": "evil.pl",
    }
    for field, value in forbidden_options.items():
        options = {
            "rootId": base.PERSON,
            "depth": 1,
            "direction": "both",
            field: value,
        }
        base.require_error(
            epoch,
            validator,
            base.request("subgraph", options),
            "invalid_request",
        )

    top_level = base.request("health", {})
    top_level["filePath"] = "/tmp/evil.pl"
    base.require_error(epoch, validator, top_level, "invalid_request")


def test_occurrence_direction_preserves_canonical_fact(
    epoch: Path,
    validator: Draft202012Validator,
) -> None:
    response, _ = base.require_ok(
        epoch,
        validator,
        base.request(
            "subgraph",
            {"rootId": base.PERSON, "depth": 1, "direction": "both"},
        ),
    )
    result = response["result"]
    facts = {fact["factId"]: fact for fact in result["facts"]}
    occurrences = {
        occurrence["occurrenceId"]: occurrence
        for occurrence in result["occurrences"]
    }

    checked = {"incoming": 0, "outgoing": 0}
    for occurrence in result["occurrences"]:
        if occurrence["depth"] == 0:
            continue
        parent = occurrences[occurrence["parentOccurrenceId"]]
        fact = facts[occurrence["viaFactId"]]
        assert fact["object"]["kind"] == "iri"
        if occurrence["direction"] == "outgoing":
            assert fact["subject"] == parent["nodeId"]
            assert fact["object"]["value"] == occurrence["nodeId"]
            checked["outgoing"] += 1
        elif occurrence["direction"] == "incoming":
            assert fact["object"]["value"] == parent["nodeId"]
            assert fact["subject"] == occurrence["nodeId"]
            checked["incoming"] += 1
        else:
            raise AssertionError(f"unexpected direction: {occurrence!r}")

    assert checked["incoming"] > 0
    assert checked["outgoing"] > 0


def test_unknown_ordinary_iri_predicate_is_traversable(
    epoch: Path,
    validator: Draft202012Validator,
) -> None:
    response, _ = base.require_ok(
        epoch,
        validator,
        base.request(
            "subgraph",
            {
                "rootId": "urn:logiclens:org:lab",
                "depth": 1,
                "direction": "outgoing",
            },
        ),
    )
    result = response["result"]
    facts = {fact["factId"]: fact for fact in result["facts"]}
    custom_occurrences = [
        occurrence
        for occurrence in result["occurrences"]
        if occurrence["depth"] == 1
        and facts[occurrence["viaFactId"]]["predicate"]
        == "urn:logiclens:test:related"
    ]
    assert len(custom_occurrences) == 1
    assert custom_occurrences[0]["nodeId"] == "urn:logiclens:org:archive"


def walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def test_deterministic_documents_exclude_volatile_fields(
    epoch: Path,
    validator: Draft202012Validator,
) -> None:
    payloads = [
        base.request("health", {}),
        base.request(
            "entity-view",
            {
                "entityId": base.PERSON,
                "language": "ru",
                "includeRawProlog": True,
            },
        ),
        base.request(
            "subgraph",
            {"rootId": base.PERSON, "depth": 2, "direction": "both"},
        ),
    ]
    for payload in payloads:
        response = base.require_stable_ok(epoch, validator, payload)
        present = VOLATILE_KEYS.intersection(walk_keys(response))
        assert not present, sorted(present)


def tree_digest(root: Path) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for path in sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix(),
    ):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        result.append((path.relative_to(root).as_posix(), digest))
    return result


def test_limits_do_not_modify_epoch_files(
    epoch: Path,
    validator: Draft202012Validator,
) -> None:
    before = tree_digest(epoch)
    base.require_error(
        epoch,
        validator,
        base.request(
            "inspect-facts",
            {"entityId": base.PERSON, "limits": {"maxOutputBytes": 1}},
        ),
        "output_limit_exceeded",
    )
    assert tree_digest(epoch) == before

    with tempfile.TemporaryDirectory(prefix="logiclens-cli-closure-") as directory:
        timeout_epoch = base.create_timeout_epoch(epoch, Path(directory))
        timeout_before = tree_digest(timeout_epoch)
        base.require_error(
            timeout_epoch,
            validator,
            base.request(
                "subgraph",
                {
                    "rootId": base.PERSON,
                    "depth": 1,
                    "direction": "both",
                    "limits": {"timeoutMs": 1},
                },
            ),
            "timeout",
        )
        assert tree_digest(timeout_epoch) == timeout_before


def main() -> int:
    args = parse_args()
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    tests = [
        lambda: test_invalid_request_ids(args.epoch, validator),
        lambda: test_stale_revision_reports_loaded_state(args.epoch, validator),
        lambda: test_command_option_isolation(args.epoch, validator),
        lambda: test_no_dynamic_execution_selectors(args.epoch, validator),
        lambda: test_occurrence_direction_preserves_canonical_fact(
            args.epoch, validator
        ),
        lambda: test_unknown_ordinary_iri_predicate_is_traversable(
            args.epoch, validator
        ),
        lambda: test_deterministic_documents_exclude_volatile_fields(
            args.epoch, validator
        ),
        lambda: test_limits_do_not_modify_epoch_files(args.epoch, validator),
    ]
    for index, test in enumerate(tests, start=1):
        test()
        print(f"ok {index} - {test.__code__.co_firstlineno}")
    print(f"1..{len(tests)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, base.CliFailure, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1) from exc
