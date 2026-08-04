"""Verify selected Document Evidence XLSX provenance through SWI-Prolog."""

from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Build, review, gate, and verify one selected worksheet-cell fixture."""
    sys.path[:0] = [str(ROOT / "tests"), str(ROOT), str(ROOT / "tools")]
    sp = importlib.import_module("source_proposal")
    bridge_fixture = importlib.import_module("document_evidence_xlsx_bridge_fixture")
    schemas = sp.load_schemas(ROOT / "contracts")

    with tempfile.TemporaryDirectory(prefix="document-evidence-xlsx-") as temp_name:
        temporary = Path(temp_name)
        world, proposal, candidate_path, review_path, fragment = (
            bridge_fixture.build_workspace(
                root=ROOT,
                temporary=temporary,
                schemas=schemas,
            )
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
            candidate_path=candidate_path,
            schemas=schemas,
            contracts_root=ROOT / "contracts",
        )
        sp.import_grounding_review(
            proposal_root=proposal,
            review_path=review_path,
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
            message = "XLSX provenance changed before the SWI-Prolog gate"
            raise AssertionError(message)
        if (
            selected["text"] != "Confirmed"
            or selected["sourceAnchor"]["cellReference"] != "D9"
        ):
            message = "Selected XLSX cell evidence changed"
            raise AssertionError(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
