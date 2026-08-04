#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import source_proposal as sp
from document_evidence_pdf_bridge_fixture import build_workspace
from source_proposal.pdf_link import load_pdf_schemas, resolve_pdf_seed


def main() -> int:
    schemas = sp.load_schemas(ROOT / "contracts")
    pdf_schemas = load_pdf_schemas(ROOT / "contracts")
    with tempfile.TemporaryDirectory(prefix="document-evidence-bridge-") as temp_name:
        temporary = Path(temp_name)
        world, proposal, seed_path, fragment = build_workspace(
            root=ROOT,
            temporary=temporary,
            schemas=schemas,
            pdf_schemas=pdf_schemas,
        )
        resolved = temporary / "resolved"
        resolve_pdf_seed(
            proposal_root=proposal,
            seed_path=seed_path,
            output=resolved,
            schemas=schemas,
            pdf_schemas=pdf_schemas,
        )
        sp.prepare_extraction(
            world_root=world,
            proposal_root=proposal,
            prompt_path=ROOT / "prompts/generic/source-assertion-proposer.md",
            schemas=schemas,
            contracts_root=ROOT / "contracts",
        )
        sp.import_assertion_proposal(
            world_root=world,
            proposal_root=proposal,
            candidate_path=resolved / "assertion-candidate.json",
            schemas=schemas,
            contracts_root=ROOT / "contracts",
        )
        sp.import_grounding_review(
            proposal_root=proposal,
            review_path=resolved / "grounding-review.json",
            schemas=schemas,
        )
        package_root = temporary / "package"
        package = sp.execute_gate(
            proposal_root=proposal,
            output=package_root,
            swipl="swipl",
            timeout_seconds=20,
            schemas=schemas,
        )
        sp.verify_package(
            package_root=package_root,
            swipl="swipl",
            timeout_seconds=20,
            schemas=schemas,
        )
        selected_path = package_root / "files/evidence/selected-fragments.jsonl"
        selected = json.loads(selected_path.read_bytes())
        if selected != fragment or package["gate"]["status"] != "passed":
            raise AssertionError("Document Evidence provenance changed before the SWI-Prolog gate")
    print("Document Evidence PDF bridge to SWI-Prolog passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
