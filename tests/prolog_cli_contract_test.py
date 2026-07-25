#!/usr/bin/env python3
"""Process-level verification for the LogicLens Prolog CLI v0 contract."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PERSON = "urn:logiclens:person:alex"
IIS = "urn:logiclens:org:iis"
PERSON_CLASS = "http://fogid.net/o/person"
AUTHORITY = "urn:logiclens:authority:paper-author"
ROOT_OCCURRENCE = (
    "o:sha256:9892029c35cacef35d34c23f38394c4f147ab61dec58c73b0c26057141a4c881"
)
FIRST_PERSON_FACTS = [
    "f:sha256:3242677a145c47ae3bc6037b8877beb244659c99fbbec00b87f8977ec60afaae",
    "f:sha256:4462f979698ea067c9e2c0f3845e961bf84728aa82ecb91448742cd1b3ff9bb0",
]


class CliFailure(AssertionError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epoch", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    return parser.parse_args()


def request(command: str, options: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "protocolVersion": "0.1",
        "requestId": f"test-{command}",
        "command": command,
        "epoch": 0,
        "revision": 0,
        "options": options,
    }
    value.update(overrides)
    return value


def run_cli(
    epoch: Path,
    payload: dict[str, Any] | str,
) -> tuple[subprocess.CompletedProcess[str], bytes, dict[str, Any] | None]:
    stdin_text = (
        payload
        if isinstance(payload, str)
        else json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
    completed = subprocess.run(
        ["swipl", "-q", "-s", str(epoch / "entry.pl"), "--"],
        input=stdin_text,
        text=True,
        capture_output=True,
        cwd=epoch,
        check=False,
        timeout=15,
        env=os.environ.copy(),
    )
    stdout_bytes = completed.stdout.encode("utf-8")
    nonempty_lines = [line for line in completed.stdout.splitlines() if line.strip()]
    parsed: dict[str, Any] | None = None
    if nonempty_lines:
        if len(nonempty_lines) != 1:
            raise CliFailure(
                f"expected one stdout JSON line, got {len(nonempty_lines)}: {completed.stdout!r}"
            )
        parsed_value = json.loads(nonempty_lines[0])
        if not isinstance(parsed_value, dict):
            raise CliFailure(f"response is not an object: {parsed_value!r}")
        parsed = parsed_value
    return completed, stdout_bytes, parsed


def require_ok(
    epoch: Path,
    validator: Draft202012Validator,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], bytes]:
    completed, stdout, response = run_cli(epoch, payload)
    if completed.returncode != 0:
        raise CliFailure(
            f"expected success, exit={completed.returncode}, stderr={completed.stderr!r}, "
            f"stdout={completed.stdout!r}"
        )
    if response is None:
        raise CliFailure("successful process returned no response")
    validator.validate(response)
    if response.get("status") != "ok":
        raise CliFailure(f"expected status=ok: {response!r}")
    return response, stdout


def require_stable_ok(
    epoch: Path,
    validator: Draft202012Validator,
    payload: dict[str, Any],
) -> dict[str, Any]:
    first, first_stdout = require_ok(epoch, validator, payload)
    second, second_stdout = require_ok(epoch, validator, payload)
    assert first_stdout == second_stdout, "identical request must be byte-identical"
    assert first == second
    return first


def require_error(
    epoch: Path,
    validator: Draft202012Validator,
    payload: dict[str, Any],
    code: str,
) -> tuple[dict[str, Any], bytes]:
    completed, stdout, response = run_cli(epoch, payload)
    if completed.returncode == 0:
        raise CliFailure(f"expected non-zero exit: {completed.stdout!r}")
    if response is None:
        raise CliFailure(
            f"expected structured command error, stderr={completed.stderr!r}"
        )
    validator.validate(response)
    if response.get("status") != "error" or response.get("error", {}).get("code") != code:
        raise CliFailure(f"expected error {code}: {response!r}")
    return response, stdout


def limit_diagnostic(response: dict[str, Any], limit: str) -> dict[str, Any]:
    matches = [
        item
        for item in response["diagnostics"]
        if item["code"] == "limit_reached"
        and item.get("context", {}).get("limit") == limit
    ]
    assert len(matches) == 1, response["diagnostics"]
    return matches[0]


def assert_reference_integrity(result: dict[str, Any]) -> None:
    fact_ids = {fact["factId"] for fact in result["facts"]}
    occurrence_ids = {
        occurrence["occurrenceId"] for occurrence in result["occurrences"]
    }
    for occurrence in result["occurrences"]:
        parent = occurrence["parentOccurrenceId"]
        via_fact = occurrence["viaFactId"]
        assert parent is None or parent in occurrence_ids
        assert via_fact is None or via_fact in fact_ids
    for mapping in result["occurrenceFacts"]:
        assert mapping["occurrenceId"] in occurrence_ids
        assert set(mapping["factIds"]).issubset(fact_ids)


def test_health(epoch: Path, validator: Draft202012Validator) -> None:
    response, _ = require_ok(epoch, validator, request("health", {}))
    result = response["result"]
    assert result["kind"] == "health"
    assert result["availableCommands"] == [
        "health",
        "inspect-facts",
        "entity-view",
        "subgraph",
    ]
    assert result["hardLimits"]["maxDepth"] == 2


def test_stdin_unicode_and_generic_view(
    epoch: Path, validator: Draft202012Validator
) -> None:
    payload = request(
        "entity-view",
        {
            "entityId": PERSON,
            "language": "ru",
            "includeRawProlog": True,
        },
        requestId='кириллица-"-\\-request',
    )
    response, _ = require_ok(epoch, validator, payload)
    assert response["requestId"] == 'кириллица-"-\\-request'
    result = response["result"]
    assert result["view"]["title"] == "Алексей Ветров"
    assert "fact(" in result["rawProlog"]


def test_inspect_facts(epoch: Path, validator: Draft202012Validator) -> None:
    response, _ = require_ok(
        epoch,
        validator,
        request("inspect-facts", {"entityId": PERSON}),
    )
    facts = response["result"]["facts"]
    assert len(facts) == 8
    assert facts == sorted(facts, key=lambda fact: fact["factId"])
    assert all("origins" in fact for fact in facts)


def test_subgraph_semantics(epoch: Path, validator: Draft202012Validator) -> None:
    payload = request(
        "subgraph",
        {"rootId": PERSON, "depth": 2, "direction": "both", "language": "ru"},
    )
    response = require_stable_ok(epoch, validator, payload)
    result = response["result"]
    nodes = result["nodes"]
    assert len([node for node in nodes if node["id"] == IIS]) == 1
    assert not any(node["id"] == PERSON_CLASS for node in nodes)
    iis_occurrences = [
        occurrence
        for occurrence in result["occurrences"]
        if occurrence["nodeId"] == IIS
    ]
    assert len(iis_occurrences) == 2
    assert all(occurrence["depth"] == 2 for occurrence in iis_occurrences)
    root_occurrences = [
        occurrence
        for occurrence in result["occurrences"]
        if occurrence["depth"] == 0
    ]
    assert len(root_occurrences) == 1
    assert root_occurrences[0]["occurrenceId"] == ROOT_OCCURRENCE
    assert_reference_integrity(result)


def test_cycle(epoch: Path, validator: Draft202012Validator) -> None:
    response, _ = require_ok(
        epoch,
        validator,
        request(
            "subgraph",
            {
                "rootId": "urn:logiclens:org:lab",
                "depth": 2,
                "direction": "outgoing",
            },
        ),
    )
    cycles = [
        occurrence
        for occurrence in response["result"]["occurrences"]
        if occurrence["state"] == "cycle_reference"
    ]
    assert len(cycles) == 1
    assert cycles[0]["nodeId"] == "urn:logiclens:org:lab"


def test_max_nodes_limit(epoch: Path, validator: Draft202012Validator) -> None:
    payload = request(
        "subgraph",
        {
            "rootId": PERSON,
            "depth": 2,
            "direction": "both",
            "limits": {"maxNodes": 1},
        },
    )
    response = require_stable_ok(epoch, validator, payload)
    result = response["result"]
    assert result["truncated"] is True
    assert [node["id"] for node in result["nodes"]] == [PERSON]
    limit_diagnostic(response, "maxNodes")
    assert_reference_integrity(result)


def test_max_facts_limit(epoch: Path, validator: Draft202012Validator) -> None:
    payload = request(
        "subgraph",
        {
            "rootId": PERSON,
            "depth": 2,
            "direction": "both",
            "limits": {"maxFacts": 2},
        },
    )
    response = require_stable_ok(epoch, validator, payload)
    result = response["result"]
    assert result["truncated"] is True
    assert [fact["factId"] for fact in result["facts"]] == FIRST_PERSON_FACTS
    assert {item["nodeId"] for item in result["occurrences"]} == {PERSON, AUTHORITY}
    limit_diagnostic(response, "maxFacts")
    assert_reference_integrity(result)


def test_max_occurrences_limit(
    epoch: Path, validator: Draft202012Validator
) -> None:
    payload = request(
        "subgraph",
        {
            "rootId": PERSON,
            "depth": 2,
            "direction": "both",
            "limits": {"maxOccurrences": 2},
        },
    )
    response = require_stable_ok(epoch, validator, payload)
    result = response["result"]
    assert result["truncated"] is True
    assert len(result["occurrences"]) == 2
    assert {item["nodeId"] for item in result["occurrences"]} == {PERSON, AUTHORITY}
    assert len([item for item in result["occurrences"] if item["depth"] == 0]) == 1
    limit_diagnostic(response, "maxOccurrences")
    assert_reference_integrity(result)


def test_max_path_length(epoch: Path, validator: Draft202012Validator) -> None:
    payload = request(
        "subgraph",
        {
            "rootId": PERSON,
            "depth": 2,
            "direction": "both",
            "limits": {"maxPathLength": 1},
        },
    )
    response = require_stable_ok(epoch, validator, payload)
    result = response["result"]
    assert result["effectiveDepth"] == 1
    assert result["effectiveLimits"]["maxPathLength"] == 1
    assert all(item["depth"] <= 1 for item in result["occurrences"])
    assert not any(item["nodeId"] == IIS for item in result["occurrences"])
    assert any(
        item["code"] == "limit_clamped"
        and item["context"]["requested"] == 2
        and item["context"]["effective"] == 1
        for item in response["diagnostics"]
    )
    assert_reference_integrity(result)


def test_depth_clamp(epoch: Path, validator: Draft202012Validator) -> None:
    response, _ = require_ok(
        epoch,
        validator,
        request(
            "subgraph",
            {"rootId": PERSON, "depth": 100, "direction": "both"},
        ),
    )
    assert response["result"]["effectiveDepth"] == 2
    assert any(item["code"] == "limit_clamped" for item in response["diagnostics"])


def create_timeout_epoch(epoch: Path, root: Path) -> Path:
    target = root / "epoch-000-timeout"
    shutil.copytree(epoch, target)
    facts_path = target / "data" / "facts.generated.pl"
    with facts_path.open("a", encoding="utf-8", newline="\n") as stream:
        for index in range(100_000):
            stream.write(
                "fact('f:test:timeout:%06d', '%s', "
                "'urn:logiclens:test:timeout-value', literal(\"x\", plain)).\n"
                % (index, PERSON)
            )
    return target


def test_real_timeout(epoch: Path, validator: Draft202012Validator) -> None:
    with tempfile.TemporaryDirectory(prefix="logiclens-timeout-") as directory:
        timeout_epoch = create_timeout_epoch(epoch, Path(directory))
        payload = request(
            "subgraph",
            {
                "rootId": PERSON,
                "depth": 1,
                "direction": "both",
                "limits": {"timeoutMs": 1},
            },
        )
        first, first_stdout = require_error(
            timeout_epoch, validator, payload, "timeout"
        )
        second, second_stdout = require_error(
            timeout_epoch, validator, payload, "timeout"
        )
        assert first_stdout == second_stdout
        assert first == second
        assert first["error"]["details"] == {"timeoutMs": 1}


def test_closed_protocol_errors(
    epoch: Path, validator: Draft202012Validator
) -> None:
    require_error(epoch, validator, request("arbitrary-query", {}), "unknown_command")
    require_error(
        epoch,
        validator,
        request("health", {}, protocolVersion="9.9"),
        "unsupported_protocol",
    )
    require_error(
        epoch,
        validator,
        request(
            "subgraph",
            {
                "rootId": PERSON,
                "depth": 1,
                "direction": "both",
                "rawGoal": "halt",
            },
        ),
        "invalid_request",
    )
    require_error(
        epoch,
        validator,
        request("entity-view", {"entityId": PERSON, "limits": {"maxFacts": 1}}),
        "fact_limit_exceeded",
    )
    require_error(
        epoch,
        validator,
        request("health", {}, epoch=1),
        "stale_state",
    )


def test_output_limit(epoch: Path, validator: Draft202012Validator) -> None:
    require_error(
        epoch,
        validator,
        request(
            "inspect-facts",
            {"entityId": PERSON, "limits": {"maxOutputBytes": 1}},
        ),
        "output_limit_exceeded",
    )


def test_invalid_json_is_process_failure(epoch: Path) -> None:
    completed, _, response = run_cli(epoch, '{"protocolVersion":')
    assert completed.returncode == 2
    assert response is None
    assert completed.stderr.strip()


def main() -> int:
    args = parse_args()
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    tests = [
        lambda: test_health(args.epoch, validator),
        lambda: test_stdin_unicode_and_generic_view(args.epoch, validator),
        lambda: test_inspect_facts(args.epoch, validator),
        lambda: test_subgraph_semantics(args.epoch, validator),
        lambda: test_cycle(args.epoch, validator),
        lambda: test_max_nodes_limit(args.epoch, validator),
        lambda: test_max_facts_limit(args.epoch, validator),
        lambda: test_max_occurrences_limit(args.epoch, validator),
        lambda: test_max_path_length(args.epoch, validator),
        lambda: test_depth_clamp(args.epoch, validator),
        lambda: test_real_timeout(args.epoch, validator),
        lambda: test_closed_protocol_errors(args.epoch, validator),
        lambda: test_output_limit(args.epoch, validator),
        lambda: test_invalid_json_is_process_failure(args.epoch),
    ]
    for index, test in enumerate(tests, start=1):
        test()
        print(f"ok {index} - {test.__code__.co_firstlineno}")
    print(f"1..{len(tests)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, CliFailure, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
