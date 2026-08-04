#!/usr/bin/env python3
"""Offline contract test for the progressive management Codex A/B ablation runner."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from capsule_contract_test import build_fixture, write_json, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / "tools" / "capsule.py"
RUNNER = (
    ROOT
    / "EpistemicCompilerLab"
    / "progressive-dsl"
    / "management-course"
    / "run_codex_dsl_ablation.py"
)
CONTRACTS = ROOT / "contracts"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def compile_package(world: Path, output: Path) -> None:
    run(
        [
            sys.executable,
            str(CAPSULE),
            "--contracts-root",
            str(CONTRACTS),
            "compile",
            "--world-root",
            str(world),
            "--capsule",
            "fixture.capsule",
            "--output",
            str(output),
        ]
    )


def build_world(root: Path) -> tuple[Path, Path, Path]:
    world = build_fixture(root)
    capsule = world / "capsules" / "fixture"
    module = world / "modules" / "fixture"
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
                    "id": "may_delegate",
                    "arguments": [
                        {"name": "owner", "type": "role"},
                        {"name": "outcome", "type": "outcome"},
                        {"name": "delegate", "type": "role"},
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
                {"id": "outcome.strategy", "kind": "outcome"},
                {"id": "outcome.work", "kind": "outcome"},
            ],
        },
    )
    write_jsonl(
        capsule / "prepared" / "assertions.jsonl",
        [
            {
                "assertionId": "fixture.owner.strategy",
                "target": {
                    "predicate": "owns",
                    "arguments": ["role.a", "outcome.strategy"],
                },
                "stance": "support",
                "provenance": ["fixture-source#strategy"],
                "dependencyGroup": "fixture.strategy",
                "generalisability": "local",
            },
            {
                "assertionId": "fixture.delegate.work",
                "target": {
                    "predicate": "owns",
                    "arguments": ["role.b", "outcome.work"],
                },
                "stance": "support",
                "provenance": ["fixture-source#work"],
                "dependencyGroup": "fixture.work",
                "generalisability": "local",
            },
        ],
    )
    package_a = root / "package-a"
    compile_package(world, package_a)

    capsule_record = json.loads((capsule / "capsule.json").read_text(encoding="utf-8"))
    capsule_record["version"] = "0.2.0"
    capsule_record["ruleFiles"].append(
        {"path": "rules/logical-rules.jsonl", "kind": "rules"}
    )
    write_json(capsule / "capsule.json", capsule_record)
    module_record = json.loads((module / "module.json").read_text(encoding="utf-8"))
    module_record["version"] = "0.2.0"
    module_record["usesCapsules"][0]["version"] = "0.2.0"
    write_json(module / "module.json", module_record)
    write_jsonl(
        capsule / "rules" / "logical-rules.jsonl",
        [
            {
                "schemaVersion": "0.1",
                "ruleId": "fixture.delegate.rule",
                "head": {
                    "stance": "support",
                    "target": {
                        "predicate": "may_delegate",
                        "arguments": ["role.a", "outcome.work", "role.b"],
                    },
                },
                "body": {
                    "all": [
                        {
                            "claim": {
                                "predicate": "owns",
                                "arguments": ["role.a", "outcome.strategy"],
                            },
                            "requires": "supported",
                        },
                        {
                            "claim": {
                                "predicate": "owns",
                                "arguments": ["role.b", "outcome.work"],
                            },
                            "requires": "supported",
                        },
                    ]
                },
                "scope": {"experiment": "fixture"},
                "generalisability": "local",
            }
        ],
    )
    package_b = root / "package-b"
    compile_package(world, package_b)
    return world, package_a, package_b


def write_case(path: Path, package_a: Path) -> None:
    package_hash = json.loads(
        (package_a / "capsule-package.json").read_text(encoding="utf-8")
    )["packageHash"]
    write_jsonl(
        path,
        [
            {
                "schemaVersion": "0.1",
                "caseId": "fixture.delegate",
                "family": "capsule-favoured",
                "question": "May role A delegate work to role B?",
                "publicContext": {"experiment": "fixture"},
                "goldClaims": [
                    {
                        "claimId": "c1",
                        "mandatory": True,
                        "quoteOrMeaning": "Role A may delegate work to role B.",
                        "target": {
                            "predicate": "may_delegate",
                            "arguments": ["role.a", "outcome.work", "role.b"],
                        },
                        "weight": 1.0,
                    }
                ],
                "goldQueries": [
                    {
                        "queryId": "q1",
                        "operation": "derived-strict-claim",
                        "target": {
                            "predicate": "may_delegate",
                            "arguments": ["role.a", "outcome.work", "role.b"],
                        },
                    }
                ],
                "minimumDslLevel": "DSL-B",
                "expectedByLevel": {
                    "DSL-A": {
                        "status": "unknown",
                        "action": "abstain_and_request_context",
                        "evidenceIds": [],
                        "warnings": ["insufficient-loaded-evidence"],
                    },
                    "DSL-B": {
                        "status": "supported",
                        "action": "answer_with_source_scope",
                        "evidenceIds": ["rule:fixture.delegate.rule"],
                        "ruleIds": ["fixture.delegate.rule"],
                        "warnings": ["derived-evidence-present", "local-only"],
                    },
                },
                "answerRubric": {
                    "requiredSignals": ["local scope"],
                    "forbiddenSignals": ["universal law"],
                },
                "requiredAbstention": False,
                "sourceHashes": [package_hash],
            }
        ],
    )


def write_fake_adapter(path: Path) -> None:
    path.write_text(
        r'''#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--working-directory")
parser.add_argument("--schema")
parser.add_argument("--output", required=True)
parser.add_argument("--events", required=True)
parser.add_argument("--codex")
parser.add_argument("--timeout-seconds")
parser.add_argument("--model")
args = parser.parse_args()
prompt = sys.stdin.read()
start = prompt.index("BEGIN_EXPERIMENT_INPUT_JSON") + len("BEGIN_EXPERIMENT_INPUT_JSON")
end = prompt.index("END_EXPERIMENT_INPUT_JSON")
payload = json.loads(prompt[start:end].strip())
frame = payload.get("verifiedFrame")
if frame is None:
    status = "supported"
    action = "answer_with_source_scope"
    evidence = []
    proof = []
    warnings = []
    used = False
    scope = ""
else:
    status = frame["status"]
    action = frame["action"]
    evidence = []
    for stance in ("support", "oppose"):
        for item in frame.get("evidence", {}).get(stance, []):
            evidence.append(item if isinstance(item, str) else item["assertionId"])
    proof = [
        item["nodeId"]
        for item in frame.get("proof", {}).get("nodes", [])
    ]
    warnings = frame.get("warnings", [])
    used = True
    scope = "Only in the declared fixture experiment." if warnings else ""
strength = {
    "supported": "qualified" if warnings else "assert",
    "refuted": "qualified" if warnings else "assert",
    "unknown": "abstain",
    "conflicting": "report_conflict",
}[status]
response = {
    "schemaVersion": "0.1",
    "answer": "Fixture answer.",
    "epistemicStatus": status,
    "action": action,
    "conclusionStrength": strength,
    "abstain": status == "unknown",
    "usedVerifiedFrame": used,
    "evidenceIds": sorted(set(evidence)),
    "proofNodeIds": sorted(set(proof)),
    "warnings": sorted(set(warnings)),
    "scopeStatement": scope,
}
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
Path(args.events).parent.mkdir(parents=True, exist_ok=True)
Path(args.output).write_text(json.dumps(response), encoding="utf-8")
Path(args.events).write_text(json.dumps({"type":"turn.completed"}) + "\n", encoding="utf-8")
print("fake provider completed")
''',
        encoding="utf-8",
    )


def metric(summary: dict, condition: str) -> dict:
    return next(item for item in summary["metrics"] if item["condition"] == condition)


def main() -> int:
    if not shutil.which("swipl"):
        raise AssertionError("SWI-Prolog is required")
    with tempfile.TemporaryDirectory(prefix="progressive-codex-contract-") as name:
        root = Path(name)
        _, package_a, package_b = build_world(root)
        cases = root / "cases.jsonl"
        write_case(cases, package_a)
        fake_adapter = root / "fake_adapter.py"
        write_fake_adapter(fake_adapter)
        output = root / "experiment"
        completed = run(
            [
                sys.executable,
                str(RUNNER),
                "--logiclens-root",
                str(ROOT),
                "--cases",
                str(cases),
                "--dsl-a-package",
                str(package_a),
                "--dsl-b-package",
                str(package_b),
                "--output-root",
                str(output),
                "--adapter",
                str(fake_adapter),
                "--codex",
                "fake",
                "--swipl",
                shutil.which("swipl") or "swipl",
            ]
        )
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        if summary["callCount"] != 3 or summary["caseCount"] != 1:
            raise AssertionError("unexpected experiment dimensions")
        direct = metric(summary, "direct")
        gold_a = metric(summary, "gold-a")
        gold_b = metric(summary, "gold-b")
        if direct["taskStatusAccuracy"] != 1.0:
            raise AssertionError("direct task score mismatch")
        if direct["usedFrameAccuracy"] != 1.0:
            raise AssertionError("direct frame-use score mismatch")
        if gold_a["frameStatusAccuracy"] != 1.0:
            raise AssertionError("DSL-A frame adherence mismatch")
        if gold_a["taskStatusAccuracy"] != 0.0:
            raise AssertionError("DSL-A should differ from DSL-B task gold")
        if gold_a["abstentionAccuracy"] != 1.0:
            raise AssertionError("DSL-A abstention mismatch")
        if gold_b["taskStatusAccuracy"] != 1.0:
            raise AssertionError("DSL-B task score mismatch")
        if gold_b["frameStatusAccuracy"] != 1.0:
            raise AssertionError("DSL-B frame adherence mismatch")
        if gold_b["evidenceExactRate"] != 1.0:
            raise AssertionError("DSL-B evidence fidelity mismatch")
        if gold_b["meanProofNodeRecall"] != 1.0:
            raise AssertionError("DSL-B proof recall mismatch")
        if not Path(str(output) + ".zip").is_file():
            raise AssertionError("experiment ZIP was not created")
        if "[CGR_ARTIFACT]" not in completed.stdout:
            raise AssertionError("artifact marker is missing")
    print("Progressive management Codex ablation contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
