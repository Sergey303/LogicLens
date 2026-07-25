#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class CliResult:
    exit_code: int
    stdout: bytes
    stderr: bytes
    document: dict[str, Any] | None


class ContractTests:
    def __init__(self, entry: Path, schema: Path) -> None:
        self.entry = entry.resolve()
        with schema.open("r", encoding="utf-8") as stream:
            self.schema = json.load(stream)
        self.validator = Draft202012Validator(self.schema)

    def request(
        self,
        request: dict[str, Any],
        *,
        expected_status: str,
        expected_exit_zero: bool,
    ) -> CliResult:
        payload = json.dumps(
            request,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        result = self.raw(payload)

        if expected_exit_zero != (result.exit_code == 0):
            raise AssertionError(
                f"Unexpected exit code {result.exit_code}.\n"
                f"stdout={result.stdout!r}\n"
                f"stderr={result.stderr!r}"
            )
        if result.document is None:
            raise AssertionError(
                f"CLI did not return JSON. stdout={result.stdout!r}, "
                f"stderr={result.stderr!r}"
            )

        errors = sorted(
            self.validator.iter_errors(result.document),
            key=lambda error: list(error.absolute_path),
        )
        if errors:
            details = "\n".join(
                f"{list(error.absolute_path)}: {error.message}" for error in errors
            )
            raise AssertionError(f"Response does not satisfy the protocol schema:\n{details}")

        actual_status = result.document.get("status")
        if actual_status != expected_status:
            raise AssertionError(
                f"Expected status {expected_status!r}, got {actual_status!r}: "
                f"{result.document!r}"
            )
        return result

    def raw(self, payload: bytes) -> CliResult:
        completed = subprocess.run(
            ["swipl", "-q", "-s", str(self.entry), "--"],
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        document: dict[str, Any] | None = None
        stripped = completed.stdout.strip()
        if stripped:
            try:
                parsed = json.loads(stripped.decode("utf-8"))
                if isinstance(parsed, dict):
                    document = parsed
            except (UnicodeDecodeError, json.JSONDecodeError):
                document = None
        return CliResult(
            completed.returncode,
            completed.stdout,
            completed.stderr,
            document,
        )

    def run(self) -> None:
        self.health()
        self.utf8_and_entity_view()
        self.inspect_facts()
        self.validation_errors()
        self.subgraph_paths()
        self.cycle()
        self.limit_clamping()
        self.deterministic_low_limits()
        self.output_limit()
        self.no_execution_surface()
        self.invalid_json_is_process_failure()

    def base_request(self, request_id: str, command: str, options: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": "0.1",
            "requestId": request_id,
            "command": command,
            "epoch": 0,
            "revision": 0,
            "options": options,
        }

    def health(self) -> None:
        result = self.request(
            self.base_request("health-1", "health", {}),
            expected_status="ok",
            expected_exit_zero=True,
        )
        document = required_document(result)
        assert document["command"] == "health"
        assert document["result"]["epoch"] == 0
        assert document["result"]["revision"] == 0
        assert document["result"]["hardLimits"]["maxDepth"] == 2
        assert document["result"]["manifests"]["dataHash"].startswith("sha256:")
        assert document["result"]["manifests"]["ontologyHash"].startswith("sha256:")

    def utf8_and_entity_view(self) -> None:
        request_id = 'кириллица-"-\\-id'
        request = self.base_request(
            request_id,
            "entity-view",
            {
                "entityId": "urn:logiclens:person:alex",
                "language": "ru",
                "includeRawProlog": True,
            },
        )
        first = self.request(
            request,
            expected_status="ok",
            expected_exit_zero=True,
        )
        second = self.request(
            request,
            expected_status="ok",
            expected_exit_zero=True,
        )
        assert first.stdout == second.stdout
        document = required_document(first)
        assert document["requestId"] == request_id
        assert document["result"]["title"] == "Алексей Ветров"
        assert "fact(" in document["result"]["rawProlog"]

    def inspect_facts(self) -> None:
        result = self.request(
            self.base_request(
                "inspect-1",
                "inspect-facts",
                {"entityId": "urn:logiclens:person:alex"},
            ),
            expected_status="ok",
            expected_exit_zero=True,
        )
        document = required_document(result)
        assert document["result"]["totalFactCount"] == 8
        assert len(document["result"]["facts"]) == 8

    def validation_errors(self) -> None:
        unknown = self.request(
            self.base_request("bad-command", "consult", {}),
            expected_status="error",
            expected_exit_zero=False,
        )
        assert required_document(unknown)["error"]["code"] == "unknown_command"

        wrong_version = self.base_request("bad-version", "health", {})
        wrong_version["protocolVersion"] = "99"
        version_result = self.request(
            wrong_version,
            expected_status="error",
            expected_exit_zero=False,
        )
        assert required_document(version_result)["error"]["code"] == "unsupported_protocol"

        missing_id = self.base_request("temporary", "health", {})
        del missing_id["requestId"]
        missing_result = self.request(
            missing_id,
            expected_status="error",
            expected_exit_zero=False,
        )
        assert required_document(missing_result)["requestId"] is None

        stale = self.base_request("stale", "health", {})
        stale["revision"] = 1
        stale_result = self.request(
            stale,
            expected_status="error",
            expected_exit_zero=False,
        )
        stale_document = required_document(stale_result)
        assert stale_document["error"]["code"] == "stale_state"
        assert stale_document["revision"] == 0

        wrong_options = self.request(
            self.base_request(
                "wrong-options",
                "entity-view",
                {
                    "entityId": "urn:logiclens:person:alex",
                    "rootId": "not-allowed",
                },
            ),
            expected_status="error",
            expected_exit_zero=False,
        )
        assert required_document(wrong_options)["error"]["code"] == "invalid_request"

    def subgraph_paths(self) -> None:
        request = self.base_request(
            "subgraph-person",
            "subgraph",
            {
                "rootId": "urn:logiclens:person:alex",
                "depth": 2,
                "direction": "both",
                "language": "ru",
            },
        )
        first = self.request(
            request,
            expected_status="ok",
            expected_exit_zero=True,
        )
        second = self.request(
            request,
            expected_status="ok",
            expected_exit_zero=True,
        )
        assert first.stdout == second.stdout
        document = required_document(first)
        subgraph = document["result"]

        iis_nodes = [
            node for node in subgraph["nodes"]
            if node["nodeId"] == "urn:logiclens:org:iis"
        ]
        assert len(iis_nodes) == 1

        iis_occurrences = sorted(
            occurrence["occurrenceId"]
            for occurrence in subgraph["occurrences"]
            if occurrence["nodeId"] == "urn:logiclens:org:iis"
        )
        assert iis_occurrences == [
            "o:sha256:1e52067cf824aa7e73935434ad5d5fa742b34d4687bdd318d069d50d432f84b5",
            "o:sha256:fe5b8e79cc9abe39cb85c1cfd644a9cc6765a25489dabba9be69741805db8dfb",
        ]

        assert all(
            node["nodeId"] != "http://fogid.net/o/person"
            for node in subgraph["nodes"]
        )
        assert any(
            fact["predicate"] == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
            for fact in subgraph["facts"]
        )

    def cycle(self) -> None:
        result = self.request(
            self.base_request(
                "cycle",
                "subgraph",
                {
                    "rootId": "urn:logiclens:org:lab",
                    "depth": 2,
                    "direction": "both",
                },
            ),
            expected_status="ok",
            expected_exit_zero=True,
        )
        occurrences = required_document(result)["result"]["occurrences"]
        cycle = [
            occurrence for occurrence in occurrences
            if occurrence["occurrenceId"]
            == "o:sha256:f9196db5e8b7a1f53c9e709c38962a543c30feb9ff85e1a73e57eaaf85844280"
        ]
        assert len(cycle) == 1
        assert cycle[0]["state"] == "cycle"

    def limit_clamping(self) -> None:
        result = self.request(
            self.base_request(
                "clamp",
                "subgraph",
                {
                    "rootId": "urn:logiclens:person:alex",
                    "depth": 999,
                    "direction": "both",
                    "limits": {
                        "maxNodes": 999999,
                        "maxFacts": 999999,
                        "maxOccurrences": 999999,
                        "maxPathLength": 999999,
                        "maxOutputBytes": 999999999,
                        "timeoutMs": 999999,
                    },
                },
            ),
            expected_status="ok",
            expected_exit_zero=True,
        )
        document = required_document(result)
        assert document["result"]["effective"]["depth"] == 2
        assert any(
            diagnostic["code"] == "limit_clamped"
            for diagnostic in document["diagnostics"]
        )

    def deterministic_low_limits(self) -> None:
        request = self.base_request(
            "low-limits",
            "subgraph",
            {
                "rootId": "urn:logiclens:person:alex",
                "depth": 2,
                "direction": "both",
                "limits": {"maxNodes": 2},
            },
        )
        first = self.request(
            request,
            expected_status="ok",
            expected_exit_zero=True,
        )
        second = self.request(
            request,
            expected_status="ok",
            expected_exit_zero=True,
        )
        assert first.stdout == second.stdout
        nodes = [node["nodeId"] for node in required_document(first)["result"]["nodes"]]
        assert nodes == [
            "urn:logiclens:authority:paper-author",
            "urn:logiclens:person:alex",
        ]

    def output_limit(self) -> None:
        result = self.request(
            self.base_request(
                "output-limit",
                "inspect-facts",
                {
                    "entityId": "urn:logiclens:person:alex",
                    "limits": {"maxOutputBytes": 1},
                },
            ),
            expected_status="error",
            expected_exit_zero=False,
        )
        assert required_document(result)["error"]["code"] == "output_limit_exceeded"

    def no_execution_surface(self) -> None:
        for forbidden in ("filePath", "module", "predicate", "goal", "query"):
            result = self.request(
                self.base_request(
                    f"forbidden-{forbidden}",
                    "subgraph",
                    {
                        "rootId": "urn:logiclens:person:alex",
                        "depth": 1,
                        "direction": "both",
                        forbidden: "malicious",
                    },
                ),
                expected_status="error",
                expected_exit_zero=False,
            )
            assert required_document(result)["error"]["code"] == "invalid_request"

    def invalid_json_is_process_failure(self) -> None:
        result = self.raw(b'{"protocolVersion":')
        assert result.exit_code != 0
        assert result.document is None


def required_document(result: CliResult) -> dict[str, Any]:
    if result.document is None:
        raise AssertionError("Expected JSON document")
    return result.document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tests = ContractTests(args.entry, args.schema)
    tests.run()
    print("Prolog CLI contract tests passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # noqa: BLE001 - test runner must print full failure context
        print(f"Prolog CLI contract tests failed: {error}", file=sys.stderr)
        raise
