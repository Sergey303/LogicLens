#!/usr/bin/env python3
"""Exercise the text source proposal pipeline and tamper detection."""

from __future__ import annotations

import importlib
import shutil
import sys
import tempfile
from pathlib import Path

from contract_fixture_support import write_json
from source_pipeline_contract_assertions import (
    assert_link_only_is_rejected,
    assert_tamper_is_rejected,
    skip_swipl_gate,
)
from source_pipeline_contract_data import candidate, review
from source_pipeline_world_fixture import build_fixture

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FRAGMENT_COUNT = 2


def main() -> int:
    """Run snapshot, proposal, review, Prolog gate, and negative contracts."""
    sys.path.insert(0, str(ROOT / "tools"))
    source_proposal = importlib.import_module("source_proposal")
    gate_module = importlib.import_module("source_proposal.gate")
    capsule = importlib.import_module("capsule")
    schemas = source_proposal.load_schemas(ROOT / "contracts")

    with tempfile.TemporaryDirectory(prefix="source-pipeline-test-") as temp_name:
        root = Path(temp_name)
        repository, world = build_fixture(root)
        workspace = root / "proposal"
        snapshot = source_proposal.snapshot_source(
            world_root=world,
            capsule_id="management.role-boundaries",
            source_id="internal-learning-model",
            proposal_id="internal-learning-model-v0",
            output=workspace,
            repository_root=repository,
            allow_network=False,
            max_bytes=100_000,
            schemas=schemas,
            contracts_root=ROOT / "contracts",
        )
        assert snapshot["stage"] == "snapshot"
        fragmented = source_proposal.fragment_workspace(workspace, schemas)
        assert (
            fragmented["artifacts"]["fragments"]["count"]
            == EXPECTED_FRAGMENT_COUNT
        )
        source_proposal.prepare_extraction(
            world_root=world,
            proposal_root=workspace,
            prompt_path=ROOT / "prompts/generic/source-assertion-proposer.md",
            schemas=schemas,
            contracts_root=ROOT / "contracts",
        )
        fragments = capsule.json_lines(
            workspace / "fragments/fragments.jsonl",
            "fragments",
        )
        fragment_id = fragments[0]["fragmentId"]
        candidate_path = root / "candidate.json"
        write_json(candidate_path, candidate(fragment_id))
        source_proposal.import_assertion_proposal(
            world_root=world,
            proposal_root=workspace,
            candidate_path=candidate_path,
            schemas=schemas,
            contracts_root=ROOT / "contracts",
        )
        review_path = root / "review.json"
        write_json(review_path, review(fragment_id))
        reviewed = source_proposal.import_grounding_review(
            proposal_root=workspace,
            review_path=review_path,
            schemas=schemas,
        )
        assert reviewed["artifacts"]["review"]["class"] == "provisional"
        swipl = shutil.which("swipl")
        original_gate = gate_module.run_swipl_gate
        if not swipl:
            gate_module.run_swipl_gate = skip_swipl_gate
            swipl = "contract-test-stub"
        try:
            package = source_proposal.execute_gate(
                proposal_root=workspace,
                output=root / "package",
                swipl=swipl,
                timeout_seconds=20,
                schemas=schemas,
            )
            assert package["activation"] == "not-performed"
            assert package["reviewClass"] == "provisional"
            source_proposal.verify_package(
                package_root=root / "package",
                swipl=swipl if shutil.which("swipl") else None,
                timeout_seconds=20,
                schemas=schemas,
            )
        finally:
            gate_module.run_swipl_gate = original_gate
        assert_tamper_is_rejected(source_proposal, root, schemas)
        assert_link_only_is_rejected(source_proposal, root, repository, world, schemas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
