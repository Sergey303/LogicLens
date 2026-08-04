"""Build a generic source-proposal workspace from selected XLSX evidence."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from capsule import canonical_json, schema_check, sha256
from pdf_link_world_fixture import build_world, write_json
from source_proposal.common import write_workspace

if TYPE_CHECKING:
    from pathlib import Path

PROPOSAL_ID = "document-evidence-xlsx-v1"
SOURCE_ID = "document-evidence-xlsx"
SNAPSHOT_HASH = "sha256:" + "f" * 64
FRAGMENT_ID = "document-evidence-xlsx#ooxml-000001"


def build_workspace(
    *,
    root: Path,
    temporary: Path,
    schemas: dict[str, dict[str, Any]],
) -> tuple[Path, Path, Path, Path, dict[str, Any]]:
    """Create a fragmented local-file workspace and deterministic review inputs."""
    fragment_path = (
        root
        / "services/document-evidence/tests/fixtures/xlsx-source-proposal-fragment-v1.jsonl"
    )
    fragment_bytes = fragment_path.read_bytes()
    fragment = json.loads(fragment_bytes)
    schema_check(fragment, schemas["fragment"], "Document Evidence XLSX fragment")

    world = build_world(temporary)
    _configure_world(world)
    proposal = temporary / "proposal"
    (proposal / "snapshot").mkdir(parents=True)
    (proposal / "fragments").mkdir()
    (proposal / "fragments/fragments.jsonl").write_bytes(fragment_bytes)
    record = {
        "schemaVersion": "0.1",
        "proposalId": PROPOSAL_ID,
        "sourceId": SOURCE_ID,
        "snapshotHash": SNAPSHOT_HASH,
        "artifactSha256": fragment["processor"]["artifactSha256"],
        "processor": fragment["processor"],
        "selectedCell": fragment["sourceAnchor"],
    }
    (proposal / "snapshot/ooxml-record.json").write_bytes(canonical_json(record))
    workspace = {
        "schemaVersion": "0.1",
        "proposalId": PROPOSAL_ID,
        "worldId": "management",
        "capsuleId": "management.role-boundaries",
        "sourceId": SOURCE_ID,
        "stage": "fragmented",
        "artifacts": {
            "snapshot": {
                "metadataPath": "snapshot/ooxml-record.json",
                "hash": SNAPSHOT_HASH,
                "retentionPolicy": "selected-evidence-only",
            },
            "fragments": {
                "path": "fragments/fragments.jsonl",
                "count": 1,
                "hash": sha256(fragment_bytes),
            },
        },
    }
    write_workspace(proposal, workspace, schemas)
    candidate_path = temporary / "candidate.json"
    review_path = temporary / "review.json"
    write_json(candidate_path, _candidate())
    write_json(review_path, _review())
    return world, proposal, candidate_path, review_path, fragment


def _configure_world(world: Path) -> None:
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
            "services/document-evidence/tests/fixtures/"
            "engdoc-confirmed-package-checklist.xlsx"
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


def _candidate() -> dict[str, Any]:
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


def _review() -> dict[str, Any]:
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
                "evidenceQuotes": [
                    {"fragmentId": FRAGMENT_ID, "quote": "Confirmed"}
                ],
                "note": "The selected worksheet cell directly records the decision.",
            }
        ],
    }
