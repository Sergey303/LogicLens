"""Semantic world and review data for the selected XLSX bridge proof."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pdf_link_world_fixture import write_json

if TYPE_CHECKING:
    from pathlib import Path

PROPOSAL_ID = "document-evidence-xlsx-v1"
SOURCE_ID = "document-evidence-xlsx"
FRAGMENT_ID = "document-evidence-xlsx#ooxml-000001"


def configure_world(world: Path) -> None:
    """Replace the PDF fixture semantics with one typed document decision."""
    write_json(
        world / "semantic/vocabulary.json",
        {
            "schemaVersion": "0.1",
            "concepts": [
                {
                    "id": "document.package_check",
                    "kind": "document_artifact",
                    "labels": {"en": "package check"},
                },
                {
                    "id": "decision.confirmed",
                    "kind": "decision_status",
                    "labels": {"en": "confirmed"},
                },
            ],
        },
    )
    write_json(
        world / "semantic/predicates.json",
        {
            "schemaVersion": "0.1",
            "predicates": [
                {
                    "id": "has_decision",
                    "arguments": [
                        {"name": "document", "type": "document_artifact"},
                        {"name": "decision", "type": "decision_status"},
                    ],
                    "valueSpace": "strict_claim",
                    "world": "open",
                    "negation": "explicit_evidence",
                }
            ],
        },
    )
    manifest_path = world / "capsules/role-boundaries/sources/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sources"][0] = {
        "id": SOURCE_ID,
        "kind": "local-file",
        "title": "EngDoc package check fixture",
        "locator": "repository://engdoc-confirmed-package-checklist.xlsx",
        "repositoryPath": (
            "services/document-evidence/tests/fixtures/engdoc-confirmed-package-checklist.xlsx"
        ),
        "version": "demo-v0",
        "language": "en",
        "license": {
            "id": "project-owned-synthetic",
            "status": "internal",
            "attribution": "EngDoc Sentinel synthetic corpus",
        },
        "snapshotPolicy": "allowed-download",
    }
    write_json(manifest_path, manifest)


def candidate() -> dict[str, Any]:
    """Build one typed assertion grounded only in the selected cell."""
    return {
        "schemaVersion": "0.1",
        "proposalId": PROPOSAL_ID,
        "sourceId": SOURCE_ID,
        "provider": {"kind": "fixture", "name": "document-evidence-xlsx"},
        "assertions": [
            {
                "assertionId": "package-check.decision.confirmed",
                "target": {
                    "predicate": "has_decision",
                    "arguments": ["document.package_check", "decision.confirmed"],
                },
                "stance": "support",
                "grounding": [FRAGMENT_ID],
                "dependencyGroup": "engdoc.package-check.decision",
                "generalisability": "context-dependent",
            }
        ],
        "abstentions": [],
    }


def review() -> dict[str, Any]:
    """Accept the exact selected-cell quote as direct grounding."""
    return {
        "schemaVersion": "0.1",
        "reviewId": "xlsx-review-001",
        "proposalId": PROPOSAL_ID,
        "reviewer": {"kind": "agent", "id": "contract-test"},
        "decisions": [
            {
                "assertionId": "package-check.decision.confirmed",
                "decision": "accept",
                "grounding": "direct",
                "evidenceQuotes": [{"fragmentId": FRAGMENT_ID, "quote": "Confirmed"}],
                "note": "The selected worksheet cell directly records the decision.",
            }
        ],
    }
