"""Build a generic source-proposal workspace from selected XLSX evidence."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from capsule import canonical_json, schema_check, sha256
from document_evidence_xlsx_bridge_data import (
    PROPOSAL_ID,
    SOURCE_ID,
    candidate,
    configure_world,
    review,
)
from pdf_link_world_fixture import build_world, write_json
from source_proposal.common import write_workspace

if TYPE_CHECKING:
    from pathlib import Path

SNAPSHOT_HASH = "sha256:" + "f" * 64


def build_workspace(
    *,
    root: Path,
    temporary: Path,
    schemas: dict[str, dict[str, Any]],
) -> tuple[Path, Path, Path, Path, dict[str, Any]]:
    """Create a fragmented local-file workspace and deterministic review inputs."""
    fragment_path = (
        root / "services/document-evidence/tests/fixtures/xlsx-source-proposal-fragment-v1.jsonl"
    )
    fragment_bytes = fragment_path.read_bytes()
    fragment = json.loads(fragment_bytes)
    schema_check(fragment, schemas["fragment"], "Document Evidence XLSX fragment")

    world = build_world(temporary)
    configure_world(world)
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
    candidate_path = temporary / "candidate.json"
    review_path = temporary / "review.json"
    write_json(candidate_path, candidate())
    write_json(review_path, review())
    return world, proposal, candidate_path, review_path, fragment
