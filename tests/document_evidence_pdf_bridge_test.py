#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import pdf_link_contract_test as pdf_fixture
import source_proposal as sp
from capsule import canonical_json, schema_check, sha256
from source_proposal.common import write_workspace
from source_proposal.pdf_link import load_pdf_schemas, resolve_pdf_seed

PROPOSAL_ID = "document-evidence-pdf-v1"
SOURCE_ID = "document-evidence-pdf"
SNAPSHOT_HASH = "sha256:" + "f" * 64
QUOTE = "The Product Owner is accountable for maximizing the value of the product."


def main() -> int:
    schemas = sp.load_schemas(ROOT / "contracts")
    pdf_schemas = load_pdf_schemas(ROOT / "contracts")
    fixture_path = (
        ROOT
        / "services/document-evidence/tests/fixtures/pdf-source-proposal-fragment-v1.jsonl"
    )
    fragment_bytes = fixture_path.read_bytes()
    fragment = json.loads(fragment_bytes)
    schema_check(fragment, schemas["fragment"], "Document Evidence bridge fragment")

    with tempfile.TemporaryDirectory(prefix="document-evidence-bridge-") as temp_name:
        root = Path(temp_name)
        world = pdf_fixture.build_world(root)
        source_manifest_path = world / "capsules/role-boundaries/sources/manifest.json"
        source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
        source_manifest["sources"][0].update(
            {
                "id": SOURCE_ID,
                "title": "Document Evidence PDF fixture",
                "locator": "https://example.com/document-evidence.pdf",
            }
        )
        pdf_fixture.write_json(source_manifest_path, source_manifest)

        proposal = root / "proposal"
        (proposal / "snapshot").mkdir(parents=True)
        (proposal / "fragments").mkdir()
        (proposal / "fragments/fragments.jsonl").write_bytes(fragment_bytes)
        record = {
            "schemaVersion": "0.1",
            "proposalId": PROPOSAL_ID,
            "worldId": "management",
            "capsuleId": "management.role-boundaries",
            "sourceId": SOURCE_ID,
            "title": "Document Evidence PDF fixture",
            "locator": "https://example.com/document-evidence.pdf",
            "license": source_manifest["sources"][0]["license"],
            "retentionPolicy": "no-source-retention",
            "sourceManifestHash": sha256(canonical_json(source_manifest)),
            "pdf": {
                "contentHash": fragment["processor"]["artifactSha256"],
                "bytes": 128,
                "mediaType": "application/pdf",
                "finalUrl": "https://example.com/document-evidence.pdf",
            },
            "processor": {
                "name": fragment["processor"]["name"],
                "version": fragment["processor"]["version"],
                "configurationHash": "sha256:" + "c" * 64,
            },
            "documentIr": {
                "path": "service://document-evidence/revisions/rev-1/ir",
                "hash": "sha256:" + "d" * 64,
                "pageCount": 1,
                "blockCount": 1,
            },
            "snapshotHash": SNAPSHOT_HASH,
        }
        schema_check(record, pdf_schemas["pdfRecord"], "Document Evidence PDF record")
        (proposal / "snapshot/pdf-link-record.json").write_bytes(canonical_json(record))
        workspace = {
            "schemaVersion": "0.1",
            "proposalId": PROPOSAL_ID,
            "worldId": "management",
            "capsuleId": "management.role-boundaries",
            "sourceId": SOURCE_ID,
            "stage": "fragmented",
            "artifacts": {
                "snapshot": {
                    "metadataPath": "snapshot/pdf-link-record.json",
                    "hash": SNAPSHOT_HASH,
                    "retentionPolicy": "no-source-retention",
                },
                "fragments": {
                    "path": "fragments/fragments.jsonl",
                    "count": 1,
                    "hash": sha256(fragment_bytes),
                },
            },
        }
        write_workspace(proposal, workspace, schemas)
        seed = {
            "schemaVersion": "0.1",
            "seedId": "document-evidence-product-owner-v1",
            "proposalId": PROPOSAL_ID,
            "sourceId": SOURCE_ID,
            "assertions": [
                {
                    "assertionId": "document-evidence.po.product-value.support",
                    "target": {
                        "predicate": "owns_outcome",
                        "arguments": ["role.product_owner", "outcome.product_value"],
                    },
                    "stance": "support",
                    "dependencyGroup": "document-evidence.pdf.product-owner",
                    "scope": {"source": "Document Evidence Service"},
                    "generalisability": "context-dependent",
                    "evidence": [{"pageNumber": 1, "quote": QUOTE}],
                    "reviewNote": "The retained service fragment directly supports the assertion.",
                }
            ],
            "abstentions": [],
        }
        seed_path = root / "seed.json"
        pdf_fixture.write_json(seed_path, seed)
        resolved = root / "resolved"
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
        package_root = root / "package"
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
