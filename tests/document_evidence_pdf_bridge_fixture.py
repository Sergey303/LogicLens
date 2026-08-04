from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pdf_link_contract_test as pdf_fixture
from capsule import canonical_json, schema_check, sha256
from source_proposal.common import write_workspace

PROPOSAL_ID = "document-evidence-pdf-v1"
SOURCE_ID = "document-evidence-pdf"
SNAPSHOT_HASH = "sha256:" + "f" * 64
QUOTE = "The Product Owner is accountable for maximizing the value of the product."


def load_fragment(root: Path, schemas: dict[str, dict[str, Any]]) -> tuple[bytes, dict[str, Any]]:
    path = root / "services/document-evidence/tests/fixtures/pdf-source-proposal-fragment-v1.jsonl"
    content = path.read_bytes()
    fragment = json.loads(content)
    schema_check(fragment, schemas["fragment"], "Document Evidence bridge fragment")
    return content, fragment


def build_workspace(
    *,
    root: Path,
    temporary: Path,
    schemas: dict[str, dict[str, Any]],
    pdf_schemas: dict[str, dict[str, Any]],
) -> tuple[Path, Path, Path, dict[str, Any]]:
    fragment_bytes, fragment = load_fragment(root, schemas)
    world = pdf_fixture.build_world(temporary)
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

    proposal = temporary / "proposal"
    (proposal / "snapshot").mkdir(parents=True)
    (proposal / "fragments").mkdir()
    (proposal / "fragments/fragments.jsonl").write_bytes(fragment_bytes)
    record = _pdf_record(source_manifest, fragment)
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
    seed_path = temporary / "seed.json"
    pdf_fixture.write_json(seed_path, _seed())
    return world, proposal, seed_path, fragment


def _pdf_record(source_manifest: dict[str, Any], fragment: dict[str, Any]) -> dict[str, Any]:
    return {
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


def _seed() -> dict[str, Any]:
    return {
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
