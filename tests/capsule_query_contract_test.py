#!/usr/bin/env python3
"""Contract test for verified JSON queries over compiled capsule packages."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from capsule_contract_test import build_fixture, write_json, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
CAPSULE_TOOL = ROOT / "tools" / "capsule.py"
QUERY_TOOL = ROOT / "tools" / "capsule_query.py"
CONTRACTS = ROOT / "contracts"


def command(
    tool: Path,
    *args: str,
    success: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(tool), "--contracts-root", str(CONTRACTS), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if success and result.returncode != 0:
        raise AssertionError(result.stderr)
    if not success and result.returncode == 0:
        raise AssertionError("command unexpectedly succeeded")
    return result


def request(path: Path, predicate: str, arguments: list[Any]) -> None:
    write_json(
        path,
        {
            "schemaVersion": "0.1",
            "operation": "strict-claim",
            "target": {
                "predicate": predicate,
                "arguments": arguments,
            },
        },
    )


def query(
    package: Path,
    request_path: Path,
    swipl: str,
    *,
    success: bool = True,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any] | None]:
    result = command(
        QUERY_TOOL,
        "--package",
        str(package),
        "--request",
        str(request_path),
        "--swipl",
        swipl,
        success=success,
    )
    if not success:
        error = json.loads(result.stderr)
        if error.get("schemaVersion") != "0.1" or "error" not in error:
            raise AssertionError("query failure did not return structured JSON")
        return result, None
    return result, json.loads(result.stdout)


def main() -> int:
    swipl = shutil.which("swipl")
    if not swipl:
        raise AssertionError("SWI-Prolog is required for capsule query contract")

    with tempfile.TemporaryDirectory(prefix="logiclens-capsule-query-") as temp_name:
        temp = Path(temp_name)
        world = build_fixture(temp)
        write_json(
            world / "semantic" / "predicates.json",
            {
                "schemaVersion": "0.1",
                "predicates": [
                    {
                        "id": "owns",
                        "arguments": [
                            {"name": "role", "type": "role"},
                            {"name": "outcome", "type": "outcome"},
                        ],
                        "valueSpace": "strict_claim",
                        "world": "open",
                        "negation": "explicit_evidence",
                    }
                ],
            },
        )
        write_json(
            world / "semantic" / "roles.json",
            {
                "schemaVersion": "0.1",
                "roles": [
                    {"id": "role.a"},
                    {"id": "role.b"},
                ],
            },
        )
        write_json(
            world / "semantic" / "vocabulary.json",
            {
                "schemaVersion": "0.1",
                "concepts": [
                    {"id": "outcome.supported", "kind": "outcome"},
                    {"id": "outcome.refuted", "kind": "outcome"},
                    {"id": "outcome.conflicting", "kind": "outcome"},
                    {"id": "outcome.unknown", "kind": "outcome"},
                ],
            },
        )
        write_jsonl(
            world / "capsules" / "fixture" / "prepared" / "assertions.jsonl",
            [
                {
                    "assertionId": "fixture.support",
                    "target": {
                        "predicate": "owns",
                        "arguments": ["role.a", "outcome.supported"],
                    },
                    "stance": "support",
                    "provenance": ["fixture-source#support"],
                    "dependencyGroup": "fixture.support.group",
                    "scope": {"organisation": "fixture"},
                    "generalisability": "context-dependent",
                    "note": "Supported fixture claim.",
                },
                {
                    "assertionId": "fixture.refute",
                    "target": {
                        "predicate": "owns",
                        "arguments": ["role.a", "outcome.refuted"],
                    },
                    "stance": "oppose",
                    "provenance": ["fixture-source#refute"],
                    "dependencyGroup": "fixture.refute.group",
                    "generalisability": "universal",
                },
                {
                    "assertionId": "fixture.conflict.support",
                    "target": {
                        "predicate": "owns",
                        "arguments": ["role.a", "outcome.conflicting"],
                    },
                    "stance": "support",
                    "provenance": ["fixture-source#conflict-support"],
                    "dependencyGroup": "fixture.conflict.a",
                    "generalisability": "local",
                },
                {
                    "assertionId": "fixture.conflict.oppose",
                    "target": {
                        "predicate": "owns",
                        "arguments": ["role.a", "outcome.conflicting"],
                    },
                    "stance": "oppose",
                    "provenance": ["fixture-source#conflict-oppose"],
                    "dependencyGroup": "fixture.conflict.b",
                    "generalisability": "local",
                },
            ],
        )

        package = temp / "package"
        command(
            CAPSULE_TOOL,
            "compile",
            "--world-root",
            str(world),
            "--capsule",
            "fixture.capsule",
            "--output",
            str(package),
        )
        command(CAPSULE_TOOL, "verify", "--package", str(package))

        supported_request = temp / "supported.json"
        request(supported_request, "owns", ["role.a", "outcome.supported"])
        first, supported = query(package, supported_request, swipl)
        second, repeated = query(package, supported_request, swipl)
        if first.stdout != second.stdout or supported != repeated:
            raise AssertionError("capsule query output is not deterministic")
        assert supported is not None
        assert supported["status"] == "supported"
        assert supported["action"] == "answer_with_source_scope"
        assert supported["warnings"] == ["context-dependent"]
        assert [
            item["assertionId"]
            for item in supported["evidence"]["support"]
        ] == ["fixture.support"]
        source = supported["evidence"]["support"][0]["sources"][0]
        assert source["id"] == "fixture-source"
        assert source["title"] == "Fixture"
        assert supported["runtime"]["verifiedAgainstGeneratedAssertions"] is True

        refuted_request = temp / "refuted.json"
        request(refuted_request, "owns", ["role.a", "outcome.refuted"])
        _, refuted = query(package, refuted_request, swipl)
        assert refuted is not None
        assert refuted["status"] == "refuted"
        assert refuted["action"] == "explain_explicit_role_boundary"
        assert [
            item["assertionId"]
            for item in refuted["evidence"]["oppose"]
        ] == ["fixture.refute"]

        conflict_request = temp / "conflicting.json"
        request(conflict_request, "owns", ["role.a", "outcome.conflicting"])
        _, conflict = query(package, conflict_request, swipl)
        assert conflict is not None
        assert conflict["status"] == "conflicting"
        assert conflict["warnings"] == [
            "incompatible-loaded-assertions",
            "local-only",
        ]
        assert conflict["dependencyGroups"] == [
            "fixture.conflict.a",
            "fixture.conflict.b",
        ]

        unknown_request = temp / "unknown.json"
        request(unknown_request, "owns", ["role.a", "outcome.unknown"])
        _, unknown = query(package, unknown_request, swipl)
        assert unknown is not None
        assert unknown["status"] == "unknown"
        assert unknown["evidence"] == {"oppose": [], "support": []}
        assert unknown["action"] == "abstain_and_request_context"
        assert unknown["warnings"] == ["insufficient-loaded-evidence"]

        unknown_predicate = temp / "unknown-predicate.json"
        request(unknown_predicate, "undeclared", ["role.a", "outcome.unknown"])
        result, _ = query(package, unknown_predicate, swipl, success=False)
        assert json.loads(result.stderr)["error"]["code"] == "unknown_predicate"

        bad_arity = temp / "bad-arity.json"
        request(bad_arity, "owns", ["role.a"])
        result, _ = query(package, bad_arity, swipl, success=False)
        assert json.loads(result.stderr)["error"]["code"] == "arity_mismatch"

        bad_identifier = temp / "bad-id.json"
        request(bad_identifier, "owns", ["role.missing", "outcome.unknown"])
        result, _ = query(package, bad_identifier, swipl, success=False)
        assert json.loads(result.stderr)["error"]["code"] == "argument_type_mismatch"

        generated = package / "files" / "generated" / "assertions.pl"
        generated.write_text(
            generated.read_text(encoding="utf-8") + "% tampered\n",
            encoding="utf-8",
        )
        query(package, supported_request, swipl, success=False)

    print("Capsule query contract verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
