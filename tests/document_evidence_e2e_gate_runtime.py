# Copyright (c) 2026 Sergey Leshtaev
"""Runtime for the ENG-148 client-selected PDF evidence gate."""

from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from document_evidence_e2e_workspace import align_snapshot

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class _ReceiptInputs:
    service_receipt: bytes
    fragment_bytes: bytes
    fragment: dict[str, Any]
    package: dict[str, Any]
    canonical_json: Callable[[dict[str, Any]], bytes]


def _digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _write_receipt(output: Path, inputs: _ReceiptInputs) -> bytes:
    receipt = {
        "schemaVersion": "0.1",
        "scenario": "eng-148-pdf-fragment-proposal-swi",
        "serviceReceiptSha256": _digest(inputs.service_receipt),
        "selectedFragmentSha256": _digest(inputs.fragment_bytes),
        "selectedFragmentId": inputs.fragment["fragmentId"],
        "packageSha256": _digest(inputs.canonical_json(inputs.package)),
        "gateStatus": inputs.package["gate"]["status"],
        "reviewClass": inputs.package["reviewClass"],
        "activation": inputs.package["activation"],
        "decisionFrame": {
            "status": "verified",
            "predicate": "owns_outcome",
            "arguments": ["role.product_owner", "outcome.product_value"],
            "stance": "support",
            "sourceFragmentId": inputs.fragment["fragmentId"],
        },
        "modelOutputAcceptedAutomatically": False,
        "consumerReadsDatabase": False,
        "consumerReadsBlobPath": False,
    }
    content = inputs.canonical_json(receipt)
    (output / "decision-receipt.json").write_bytes(content)
    return content


def run(fragment_path: Path, service_receipt_path: Path, output: Path) -> None:
    """Build the proposal, run the real gate, and emit one stable receipt."""
    sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
    source_proposal = importlib.import_module("source_proposal")
    fixture = importlib.import_module("tests.document_evidence_pdf_bridge_fixture")
    pdf_link = importlib.import_module("source_proposal.pdf_link")
    capsule = importlib.import_module("capsule")
    schemas = source_proposal.load_schemas(ROOT / "contracts")
    pdf_schemas = pdf_link.load_pdf_schemas(ROOT / "contracts")
    fragment_bytes = fragment_path.read_bytes()
    fragment = json.loads(fragment_bytes)
    capsule.schema_check(fragment, schemas["fragment"], "ENG-148 service fragment")
    service_receipt = service_receipt_path.read_bytes()
    output.mkdir(parents=True, exist_ok=True)
    workspace_root = output / "workspace"
    shutil.rmtree(workspace_root, ignore_errors=True)

    original_loader = fixture.load_fragment
    fixture.load_fragment = lambda _root, _schemas: (fragment_bytes, fragment)
    try:
        world, proposal, seed_path, expected = fixture.build_workspace(
            root=ROOT,
            temporary=workspace_root,
            schemas=schemas,
            pdf_schemas=pdf_schemas,
        )
    finally:
        fixture.load_fragment = original_loader
    if expected != fragment:
        message = "The proposal workspace did not retain the selected fragment."
        raise AssertionError(message)
    align_snapshot(proposal, fragment, schemas, capsule.canonical_json)

    resolved = workspace_root / "resolved"
    pdf_link.resolve_pdf_seed(
        proposal_root=proposal,
        seed_path=seed_path,
        output=resolved,
        schemas=schemas,
        pdf_schemas=pdf_schemas,
    )
    source_proposal.prepare_extraction(
        world_root=world,
        proposal_root=proposal,
        prompt_path=ROOT / "prompts/generic/source-assertion-proposer.md",
        schemas=schemas,
        contracts_root=ROOT / "contracts",
    )
    source_proposal.import_assertion_proposal(
        world_root=world,
        proposal_root=proposal,
        candidate_path=resolved / "assertion-candidate.json",
        schemas=schemas,
        contracts_root=ROOT / "contracts",
    )
    source_proposal.import_grounding_review(
        proposal_root=proposal,
        review_path=resolved / "grounding-review.json",
        schemas=schemas,
    )
    package_root = output / "package"
    package = source_proposal.execute_gate(
        proposal_root=proposal,
        output=package_root,
        swipl="swipl",
        timeout_seconds=20,
        schemas=schemas,
    )
    source_proposal.verify_package(
        package_root=package_root,
        swipl="swipl",
        timeout_seconds=20,
        schemas=schemas,
    )
    selected = (package_root / "files/evidence/selected-fragments.jsonl").read_bytes()
    if selected != fragment_bytes or package["gate"]["status"] != "passed":
        message = "ENG-148 provenance changed before the SWI-Prolog gate."
        raise AssertionError(message)
    inputs = _ReceiptInputs(
        service_receipt, fragment_bytes, fragment, package, capsule.canonical_json
    )
    receipt = _write_receipt(output, inputs)
    sys.stdout.write(receipt.decode("utf-8") + "\n")
