"""Workspace alignment helpers for the ENG-148 service fragment."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


def align_snapshot(
    proposal: Path,
    fragment: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
    canonical_json: Any,
) -> None:
    """Replace the legacy fixture hash with the service revision snapshot hash."""
    snapshot_hash = fragment["snapshotHash"]
    record_path = proposal / "snapshot/pdf-link-record.json"
    record = json.loads(record_path.read_bytes())
    record["snapshotHash"] = snapshot_hash
    record_path.write_bytes(canonical_json(record))

    proposal_path = proposal / "proposal.json"
    workspace = json.loads(proposal_path.read_bytes())
    workspace["artifacts"]["snapshot"]["hash"] = snapshot_hash
    common = importlib.import_module("source_proposal.common")
    common.write_workspace(proposal, workspace, schemas)
