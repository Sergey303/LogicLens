#!/usr/bin/env python3
"""Contract test for ground logical DSL-B queries and proof DAGs."""
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
QUERY_TOOL = ROOT / "tools" / "capsule_query_dsl_b.py"
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
            "dslLevel": "DSL-B",
            "operation": "derived-strict-claim",
            "target": {"predicate": predicate, "arguments": arguments},
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
        payload = json.loads(result.stderr)
        if payload.get("schemaVersion") != "0.1" or "error" not in payload:
            raise AssertionError("DSL-B failure did not return structured JSON")
        return result, None
    return result, json.loads(result.stdout)


def configure_world(world: Path, rules: list[dict[str, Any]]) -> None:
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
                },
                {
                    "id": "must_escalate",
                    "arguments": [
                        {"name": "role", "type": "role"},
                        {"name": "risk", "type": "outcome"},
                        {"name": "target_role", "type": "role"},
                    ],
                    "valueSpace": "strict_claim",
                    "world": "open",
                    "negation": "explicit_evidence",
                },
            ],
        },
    )
    write_json(
        world / "semantic" / "roles.json",
        {
            "schemaVersion": "0.1",
            "roles": [{"id": "role.a"}, {"id": "role.b"}],
        },
    )
    write_json(
        world / "semantic" / "vocabulary.json",
        {
            "schemaVersion": "0.1",
            "concepts": [
                {"id": "outcome.supported", "kind": "outcome"},
                {"id": "outcome.refuted", "kind": "outcome"},
                {"id": "outcome.risk", "kind": "outcome"},
                {"id": "outcome.no-explicit-oppose", "kind": "outcome"},
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
                "generalisability": "local",
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
                "generalisability": "local",
            },
        ],
    )
    capsule_path = world / "capsules" / "fixture" / "capsule.json"
    capsule = json.loads(capsule_path.read_text(encoding="utf-8"))
    capsule["ruleFiles"].append(
        {"path": "rules/logical-rules.jsonl", "kind": "rules"}
    )
    write_json(capsule_path, capsule)
    write_jsonl(
        world / "capsules" / "fixture" / "rules" / "logical-rules.jsonl",
        rules,
    )


def main() -> int:
    swipl = shutil.which("swipl")
    if not swipl:
        raise AssertionError("SWI-Prolog is required for DSL-B contract")

    with tempfile.TemporaryDirectory(prefix="logiclens-dsl-b-") as temp_name:
        temp = Path(temp_name)
        world = build_fixture(temp)
        rules = [
            {
                "schemaVersion": "0.1",
                "ruleId": "fixture.escalate",
                "head": {
                    "target": {
                        "predicate": "must_escalate",
                        "arguments": ["role.a", "outcome.risk", "role.b"],
                    },
                    "stance": "support",
                },
                "body": {
                    "all": [
                        {
                            "claim": {
                                "predicate": "owns",
                                "arguments": ["role.a", "outcome.supported"],
                            },
                            "requires": "supported",
                        },
                        {
                            "claim": {
                                "predicate": "owns",
                                "arguments": ["role.a", "outcome.refuted"],
                            },
                            "requires": "refuted",
                        },
                    ]
                },
                "generalisability": "local",
            },
            {
                "schemaVersion": "0.1",
                "ruleId": "fixture.not-explicit",
                "head": {
                    "target": {
                        "predicate": "owns",
                        "arguments": ["role.b", "outcome.no-explicit-oppose"],
                    },
                    "stance": "support",
                },
                "body": {
                    "all": [
                        {
                            "notExplicit": {
                                "target": {
                                    "predicate": "owns",
                                    "arguments": [
                                        "role.b",
                                        "outcome.no-explicit-oppose",
                                    ],
                                },
                                "stance": "oppose",
                            }
                        }
                    ]
                },
                "generalisability": "local",
            },
        ]
        configure_world(world, rules)

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

        derived_request = temp / "derived.json"
        request(
            derived_request,
            "must_escalate",
            ["role.a", "outcome.risk", "role.b"],
        )
        first, derived = query(package, derived_request, swipl)
        second, repeated = query(package, derived_request, swipl)
        if first.stdout != second.stdout or derived != repeated:
            raise AssertionError("DSL-B output is not deterministic")
        assert derived is not None
        assert derived["dslLevel"] == "DSL-B"
        assert derived["status"] == "supported"
        assert derived["evidence"] == {
            "support": ["rule:fixture.escalate"],
            "oppose": [],
        }
        assert derived["proof"]["supportRoots"] == ["rule:fixture.escalate"]
        nodes = {node["nodeId"]: node for node in derived["proof"]["nodes"]}
        assert nodes["rule:fixture.escalate"]["premises"] == [
            "assertion:fixture.refute",
            "assertion:fixture.support",
        ]
        assert nodes["assertion:fixture.support"]["stance"] == "support"
        assert nodes["assertion:fixture.refute"]["stance"] == "oppose"
        assert derived["warnings"] == ["derived-evidence-present", "local-only"]
        assert derived["runtime"]["verifiedAgainstLogicalRules"] is True

        not_explicit_request = temp / "not-explicit.json"
        request(
            not_explicit_request,
            "owns",
            ["role.b", "outcome.no-explicit-oppose"],
        )
        _, not_explicit = query(package, not_explicit_request, swipl)
        assert not_explicit is not None
        assert not_explicit["status"] == "supported"
        assert not_explicit["warnings"] == [
            "derived-evidence-present",
            "local-only",
            "not-explicit-premise-used",
        ]
        not_explicit_node = {
            node["nodeId"]: node for node in not_explicit["proof"]["nodes"]
        }["rule:fixture.not-explicit"]
        assert not_explicit_node["premises"] == []
        assert not_explicit_node["usedNotExplicit"] is True

        cycle_root = temp / "cycle"
        cycle_world = build_fixture(cycle_root)
        cycle_rules = [
            {
                "schemaVersion": "0.1",
                "ruleId": "fixture.cycle.a",
                "head": {
                    "target": {
                        "predicate": "owns",
                        "arguments": ["role.a", "outcome.risk"],
                    },
                    "stance": "support",
                },
                "body": {
                    "all": [
                        {
                            "claim": {
                                "predicate": "owns",
                                "arguments": [
                                    "role.b",
                                    "outcome.no-explicit-oppose",
                                ],
                            },
                            "requires": "supported",
                        }
                    ]
                },
                "generalisability": "local",
            },
            {
                "schemaVersion": "0.1",
                "ruleId": "fixture.cycle.b",
                "head": {
                    "target": {
                        "predicate": "owns",
                        "arguments": ["role.b", "outcome.no-explicit-oppose"],
                    },
                    "stance": "support",
                },
                "body": {
                    "all": [
                        {
                            "claim": {
                                "predicate": "owns",
                                "arguments": ["role.a", "outcome.risk"],
                            },
                            "requires": "supported",
                        }
                    ]
                },
                "generalisability": "local",
            },
        ]
        configure_world(cycle_world, cycle_rules)
        cycle_package = temp / "cycle-package"
        command(
            CAPSULE_TOOL,
            "compile",
            "--world-root",
            str(cycle_world),
            "--capsule",
            "fixture.capsule",
            "--output",
            str(cycle_package),
        )
        cycle_request = temp / "cycle-request.json"
        request(cycle_request, "owns", ["role.a", "outcome.risk"])
        failed, _ = query(cycle_package, cycle_request, swipl, success=False)
        assert json.loads(failed.stderr)["error"]["code"] == "logical_rule_cycle"

        generated = package / "files" / "generated" / "assertions.pl"
        generated.write_text(
            generated.read_text(encoding="utf-8") + "% tampered\n",
            encoding="utf-8",
        )
        query(package, derived_request, swipl, success=False)

    print("Ground logical DSL-B capsule query contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
