"""Deterministic record, workspace, and seed data for PDF link contracts."""

from __future__ import annotations

from typing import Any

from capsule import domain_hash, sha256
from source_proposal.pdf_link import PDF_RECORD_DOMAIN

PROPOSAL_ID = "scrum-guide-2020-v0"
SOURCE_ID = "scrum-guide-2020"
SOURCE_URI = "https://example.com/scrum-guide.pdf"
QUOTE = "The Product Owner is accountable for maximizing the value of the product."


def record(pdf: bytes, document_ir: dict[str, Any], document_hash: str) -> dict[str, Any]:
    """Build a no-source-retention PDF link record."""
    value = {
        "schemaVersion": "0.1",
        "proposalId": PROPOSAL_ID,
        "worldId": "management",
        "capsuleId": "management.role-boundaries",
        "sourceId": SOURCE_ID,
        "title": "The Scrum Guide",
        "locator": SOURCE_URI,
        "license": {
            "id": "CC-BY-SA-4.0",
            "status": "confirmed",
            "attribution": "Ken Schwaber and Jeff Sutherland",
        },
        "retentionPolicy": "no-source-retention",
        "sourceManifestHash": sha256(b"fixture\n"),
        "pdf": {
            "contentHash": sha256(pdf),
            "bytes": len(pdf),
            "mediaType": "application/pdf",
            "finalUrl": SOURCE_URI,
        },
        "processor": document_ir["processor"],
        "documentIr": {
            "path": "document/canonical-document-ir.json",
            "hash": document_hash,
            "pageCount": 1,
            "blockCount": len(document_ir["pages"][0]["blocks"]),
        },
    }
    value["snapshotHash"] = domain_hash(PDF_RECORD_DOMAIN, value)
    return value


def workspace(
    snapshot_hash: str,
    document_hash: str,
    fragments_hash: str,
    fragment_count: int,
) -> dict[str, Any]:
    """Build the fragmented source-proposal workspace envelope."""
    return {
        "schemaVersion": "0.1",
        "proposalId": PROPOSAL_ID,
        "worldId": "management",
        "capsuleId": "management.role-boundaries",
        "sourceId": SOURCE_ID,
        "stage": "fragmented",
        "artifacts": {
            "snapshot": {
                "metadataPath": "snapshot/pdf-link-record.json",
                "hash": snapshot_hash,
                "retentionPolicy": "no-source-retention",
                "documentIrPath": "document/canonical-document-ir.json",
                "documentIrHash": document_hash,
            },
            "fragments": {
                "path": "fragments/fragments.jsonl",
                "count": fragment_count,
                "hash": fragments_hash,
            },
        },
    }


def seed() -> dict[str, Any]:
    """Build one exact-quote assertion seed for the real Prolog gate."""
    return {
        "schemaVersion": "0.1",
        "seedId": "scrum-guide-product-owner-v0",
        "proposalId": PROPOSAL_ID,
        "sourceId": SOURCE_ID,
        "assertions": [
            {
                "assertionId": "scrum.po.product-value.support",
                "target": {
                    "predicate": "owns_outcome",
                    "arguments": ["role.product_owner", "outcome.product_value"],
                },
                "stance": "support",
                "dependencyGroup": "scrum.guide.2020.product_owner",
                "scope": {"framework": "Scrum", "version": "2020-11"},
                "generalisability": "context-dependent",
                "evidence": [{"pageNumber": 1, "quote": QUOTE}],
                "reviewNote": "The fixture directly states Product Owner accountability.",
            }
        ],
        "abstentions": [],
    }
