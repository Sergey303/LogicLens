#!/usr/bin/env python3
"""Gate a client-selected Document Evidence fragment through real SWI-Prolog."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def digest(content: bytes) -> str:
    """Return a domain-prefixed SHA-256 digest."""
    return "sha256:" + hashlib.sha256(content).hexdigest()


def arguments() -> argparse.Namespace:
    """Parse explicit service and output artifact paths."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--fragment", type=Path, required=True)
    parser.add_argument("--service-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def write_receipt(
    output: Path,
    service_receipt: bytes,
    fragment_bytes: bytes,
    fragment: dict[str, Any],
    package: dict[str, Any],
    canonical_json: Any,
) -> bytes:
    """Write the stable verified-decision receipt."""
    receipt = {
        "schemaVersion": "0.1",
        "scenario": "eng-148-pdf-fragment-proposal-swi",
        "serviceReceiptSha256": digest(service_receipt),
        "selectedFragmentSha256": digest(fragment_bytes),
        "selectedFragmentId": fragment["fragmentId"],
        "packageSha256": digest(canonical_json(package)),
        "gateStatus": package["gate"]["status"],
        "reviewClass": package["reviewClass"],
        "activation": package["activation"],
        "decisionFrame": {
            "status": "verified",
            "predicate": "owns_outcome",
            "arguments": ["role.product_owner", "outcome.product_value"],
            "stance": "support",
            "sourceFragmentId": fragment["fragmentId"],
        },
        "modelOutputAcceptedAutomatically": False,
        "consumerReadsDatabase": False,
        "consumerReadsBlobPath": False,
    }
    content = canonical_json(receipt)
    (output / "decision-receipt.json").write_bytes(content)
    return content


def main() -> int:
    """Build the proposal, run the real gate, and emit one stable receipt."""
    args = arguments()
    sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
    source_proposal = importlib.import_module("source_proposal")
    bridge_fixture = importlib.import_module("tests.document_evidence_pdf_bridge_fixture")
    pdf_link = importlib.import_module("source_proposal.pdf_link")
    capsule = importlib.import_module("capsule")
    schemas = source_proposal.load_schemas(ROOT / "contracts")
    pdf_schemas = pdf_link.load_pdf_schemas(ROOT / "contracts")

    fragment_bytes = args.fragment.read_bytes()
    fragment = json.loads(fragment_bytes)
    capsule.schema_check(fragment, schemas["fragment"], "ENG-148 service fragment")
    service_receipt = args.service_receipt.read_bytes()
    args.output.mkdir(parents=True, exist_ok=True)
    workspace_root = args.output / "workspace"
    shutil.rmtree(workspace_root, ignore_errors=True)

    original_loader = bridge_fixture.load_fragment
    bridge_fixture.load_fragment = lambda _root, _schemas: (fragment_bytes, fragment)
    try:
        world, proposal, seed_path, expected = bridge_fixture.build_workspace(
            root=ROOT,
            temporary=workspace_root,
            schemas=schemas,
            pdf_schemas=pdf_schemas,
        )
    finally:
        bridge_fixture.load_fragment = original_loader
    if expected != fragment:
        raise AssertionError("The proposal workspace did not retain the client-selected fragment.")

    resolved = workspace_root / "resolved"
    pdf_link.resolve_pdf_seed(proposal, seed_path, resolved, schemas, pdf_schemas)
    source_proposal.prepare_extraction(
        world,
        proposal,
        ROOT / "prompts/generic/source-assertion-proposer.md",
        schemas,
        ROOT / "contracts",
    )
    source_proposal.import_assertion_proposal(
        world,
        proposal,
        resolved / "assertion-candidate.json",
        schemas,
        ROOT / "contracts",
    )
    source_proposal.import_grounding_review(
        proposal,
        resolved / "grounding-review.json",
        schemas,
    )
    package_root = args.output / "package"
    package = source_proposal.execute_gate(proposal, package_root, "swipl", 20, schemas)
    source_proposal.verify_package(package_root, "swipl", 20, schemas)
    selected = (package_root / "files/evidence/selected-fragments.jsonl").read_bytes()
    if selected != fragment_bytes or package["gate"]["status"] != "passed":
        raise AssertionError("ENG-148 provenance changed before the SWI-Prolog gate.")
    receipt = write_receipt(
        args.output,
        service_receipt,
        fragment_bytes,
        fragment,
        package,
        capsule.canonical_json,
    )
    print(receipt.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
