#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import source_pipeline_contract_test as base
import source_proposal as sp
from capsule import json_lines, json_object, validate_world
from source_proposal import gate as gate_module


def build_package(root: Path, repo: Path, world: Path, schemas: dict) -> Path:
    workspace = root / "proposal"
    sp.snapshot_source(
        world_root=world,
        capsule_id="management.role-boundaries",
        source_id="internal-learning-model",
        proposal_id="activation-fixture-v0",
        output=workspace,
        repository_root=repo,
        allow_network=False,
        max_bytes=100000,
        schemas=schemas,
        contracts_root=ROOT / "contracts",
    )
    sp.fragment_workspace(workspace, schemas)
    sp.prepare_extraction(
        world_root=world,
        proposal_root=workspace,
        prompt_path=(
            ROOT / "prompts" / "generic" / "source-assertion-proposer.md"
        ),
        schemas=schemas,
        contracts_root=ROOT / "contracts",
    )
    fragments = json_lines(
        workspace / "fragments" / "fragments.jsonl",
        "fragments",
    )
    fragment_id = fragments[0]["fragmentId"]
    candidate = {
        "schemaVersion": "0.1",
        "proposalId": "activation-fixture-v0",
        "sourceId": "internal-learning-model",
        "provider": {"kind": "fixture", "name": "activation-contract"},
        "assertions": [
            {
                "assertionId": "fixture.activation.support",
                "target": {
                    "predicate": "contributes_to",
                    "arguments": [
                        "role.team_lead",
                        "outcome.technical_direction",
                    ],
                },
                "stance": "support",
                "grounding": [fragment_id],
                "dependencyGroup": "fixture.activation",
                "generalisability": "context-dependent",
            }
        ],
        "abstentions": [],
    }
    candidate_path = root / "candidate.json"
    base.write_json(candidate_path, candidate)
    sp.import_assertion_proposal(
        world_root=world,
        proposal_root=workspace,
        candidate_path=candidate_path,
        schemas=schemas,
        contracts_root=ROOT / "contracts",
    )
    review = {
        "schemaVersion": "0.1",
        "reviewId": "activation-review-v0",
        "proposalId": "activation-fixture-v0",
        "reviewer": {"kind": "agent", "id": "activation-contract"},
        "decisions": [
            {
                "assertionId": "fixture.activation.support",
                "decision": "accept",
                "grounding": "direct",
                "evidenceQuotes": [
                    {
                        "fragmentId": fragment_id,
                        "quote": (
                            "Team Lead задаёт локальное техническое направление"
                        ),
                    }
                ],
                "note": "The fixture directly supports the assertion.",
            }
        ],
    }
    review_path = root / "review.json"
    base.write_json(review_path, review)
    sp.import_grounding_review(
        proposal_root=workspace,
        review_path=review_path,
        schemas=schemas,
    )

    package = root / "package"
    swipl = shutil.which("swipl")
    original_gate = gate_module.run_swipl_gate
    if not swipl:
        gate_module.run_swipl_gate = lambda *args, **kwargs: None
        swipl = "activation-contract-stub"
    try:
        sp.execute_gate(
            proposal_root=workspace,
            output=package,
            swipl=swipl,
            timeout_seconds=20,
            schemas=schemas,
        )
    finally:
        gate_module.run_swipl_gate = original_gate
    return package


def expect_failure(action, message: str) -> None:
    try:
        action()
    except sp.SourcePipelineError:
        return
    raise AssertionError(message)


def main() -> int:
    schemas = sp.load_schemas(ROOT / "contracts")
    contracts = ROOT / "contracts"
    with tempfile.TemporaryDirectory(
        prefix="source-activation-test-"
    ) as temp_name:
        root = Path(temp_name)
        repo, world = base.build_fixture(root)
        package = build_package(root, repo, world, schemas)

        expect_failure(
            lambda: sp.stage_activation(
                package_root=package,
                world_root=world,
                output_world_root=root / "rejected",
                expected_current_version="0.1.0",
                new_version="0.1.1",
                allow_provisional=False,
                swipl=None,
                timeout_seconds=20,
                schemas=schemas,
                contracts_root=contracts,
            ),
            "provisional activation succeeded without override",
        )

        staged = root / "staged-world"
        activation = sp.stage_activation(
            package_root=package,
            world_root=world,
            output_world_root=staged,
            expected_current_version="0.1.0",
            new_version="0.1.1",
            allow_provisional=True,
            swipl=None,
            timeout_seconds=20,
            schemas=schemas,
            contracts_root=contracts,
        )
        assert activation["status"] == "staged"
        assert activation["approvalMode"] == "provisional-override"
        assert activation["assertionIds"] == ["fixture.activation.support"]

        validated = validate_world(staged, contracts)
        capsule = validated["capsules"]["management.role-boundaries"]
        assert capsule["manifest"]["version"] == "0.1.1"
        assertions = json_lines(
            capsule["root"] / "prepared" / "assertions.jsonl",
            "staged assertions",
        )
        assert {item["assertionId"] for item in assertions} == {
            "fixture.accepted",
            "fixture.activation.support",
        }
        module = json_object(
            staged / "modules" / "fixture" / "module.json",
            "staged module",
        )
        assert module["version"] == "0.1.1"
        assert module["usesCapsules"] == [
            {"id": "management.role-boundaries", "version": "0.1.1"}
        ]
        record_path = (
            capsule["root"]
            / "activations"
            / "activation-fixture-v0-0.1.1.json"
        )
        record = json_object(record_path, "activation record")
        assert record["packageHash"] == activation["packageHash"]

        expect_failure(
            lambda: sp.finalize_activation(
                source_world_root=world,
                staged_world_root=staged,
                output_world_root=root / "no-approval",
                activation_id=activation["activationId"],
                expected_activation_hash=activation["activationHash"],
                approve_provisional=False,
                contracts_root=contracts,
            ),
            "provisional finalization succeeded without approval",
        )
        expect_failure(
            lambda: sp.finalize_activation(
                source_world_root=world,
                staged_world_root=staged,
                output_world_root=root / "wrong-hash",
                activation_id=activation["activationId"],
                expected_activation_hash="sha256:" + "0" * 64,
                approve_provisional=True,
                contracts_root=contracts,
            ),
            "finalization accepted the wrong staged hash",
        )

        activated_world = root / "activated-world"
        activated = sp.finalize_activation(
            source_world_root=world,
            staged_world_root=staged,
            output_world_root=activated_world,
            activation_id=activation["activationId"],
            expected_activation_hash=activation["activationHash"],
            approve_provisional=True,
            contracts_root=contracts,
        )
        assert activated["status"] == "activated"
        assert activated["activationHash"] != activation["activationHash"]
        validate_world(activated_world, contracts)
        activated_record = json_object(
            activated_world
            / "capsules"
            / "role-boundaries"
            / "activations"
            / "activation-fixture-v0-0.1.1.json",
            "activated record",
        )
        assert activated_record == activated

        tampered = root / "tampered-staged"
        shutil.copytree(staged, tampered)
        (tampered / "README.md").write_text(
            "# unrelated staged edit\n",
            encoding="utf-8",
        )
        expect_failure(
            lambda: sp.finalize_activation(
                source_world_root=world,
                staged_world_root=tampered,
                output_world_root=root / "tampered-output",
                activation_id=activation["activationId"],
                expected_activation_hash=activation["activationHash"],
                approve_provisional=True,
                contracts_root=contracts,
            ),
            "finalization accepted an unrelated staged edit",
        )

        expect_failure(
            lambda: sp.stage_activation(
                package_root=package,
                world_root=staged,
                output_world_root=root / "duplicate",
                expected_current_version="0.1.1",
                new_version="0.1.2",
                allow_provisional=True,
                swipl=None,
                timeout_seconds=20,
                schemas=schemas,
                contracts_root=contracts,
            ),
            "duplicate assertion activation succeeded",
        )

    print("Source proposal activation contract verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
