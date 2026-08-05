# Copyright (c) 2026 Sergey Leshtaev
"""Prove that unknown and conflicting ENG-148 grounding fail closed."""

from __future__ import annotations

import importlib
import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

from document_evidence_e2e_workspace import align_snapshot

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "services/document-evidence/tests/fixtures/pdf-source-proposal-fragment-v1.jsonl"


def _build_workspace(
    temporary: Path,
    fragment_bytes: bytes,
    fragment: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
    pdf_schemas: dict[str, dict[str, Any]],
    fixture: Any,
    canonical_json: Any,
) -> tuple[Path, Path]:
    original_loader = fixture.load_fragment
    fixture.load_fragment = lambda _root, _schemas: (fragment_bytes, fragment)
    try:
        _world, proposal, seed_path, expected = fixture.build_workspace(
            root=ROOT,
            temporary=temporary,
            schemas=schemas,
            pdf_schemas=pdf_schemas,
        )
    finally:
        fixture.load_fragment = original_loader
    if expected != fragment:
        message = "Negative workspace did not retain the service fragment."
        raise AssertionError(message)
    align_snapshot(proposal, fragment, schemas, canonical_json)
    return proposal, seed_path


def _expect_rejection(
    label: str,
    mutate: Any,
    modules: dict[str, Any],
    fragment_bytes: bytes,
    fragment: dict[str, Any],
) -> None:
    with tempfile.TemporaryDirectory(prefix=f"eng-148-{label}-") as temp_name:
        temporary = Path(temp_name)
        proposal, seed_path = _build_workspace(
            temporary,
            fragment_bytes,
            fragment,
            modules["schemas"],
            modules["pdf_schemas"],
            modules["fixture"],
            modules["capsule"].canonical_json,
        )
        mutate(proposal, seed_path, fragment, modules)
        output = temporary / "resolved"
        try:
            modules["pdf_link"].resolve_pdf_seed(
                proposal_root=proposal,
                seed_path=seed_path,
                output=output,
                schemas=modules["schemas"],
                pdf_schemas=modules["pdf_schemas"],
            )
        except modules["common"].SourcePipelineError:
            if output.exists():
                message = f"{label} rejection left a trusted output directory."
                raise AssertionError(message)
            return
        message = f"{label} evidence unexpectedly produced a trusted proposal."
        raise AssertionError(message)


def _unknown(
    _proposal: Path,
    seed_path: Path,
    _fragment: dict[str, Any],
    modules: dict[str, Any],
) -> None:
    seed = json.loads(seed_path.read_bytes())
    seed["assertions"][0]["evidence"][0]["quote"] = "Evidence absent from the document."
    seed_path.write_bytes(modules["capsule"].canonical_json(seed))


def _conflict(
    proposal: Path,
    _seed_path: Path,
    fragment: dict[str, Any],
    modules: dict[str, Any],
) -> None:
    duplicate = deepcopy(fragment)
    duplicate["fragmentId"] = fragment["fragmentId"] + "-conflict"
    duplicate["ordinal"] = fragment["ordinal"] + 1
    content = modules["capsule"].canonical_json(fragment) + modules["capsule"].canonical_json(
        duplicate
    )
    (proposal / "fragments/fragments.jsonl").write_bytes(content)
    workspace_path = proposal / "proposal.json"
    workspace = json.loads(workspace_path.read_bytes())
    workspace["artifacts"]["fragments"]["count"] = 2
    workspace["artifacts"]["fragments"]["hash"] = modules["capsule"].sha256(content)
    modules["common"].write_workspace(proposal, workspace, modules["schemas"])


def main() -> int:
    """Run both fail-closed grounding cases."""
    sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
    source_proposal = importlib.import_module("source_proposal")
    pdf_link = importlib.import_module("source_proposal.pdf_link")
    modules = {
        "capsule": importlib.import_module("capsule"),
        "common": importlib.import_module("source_proposal.common"),
        "fixture": importlib.import_module("tests.document_evidence_pdf_bridge_fixture"),
        "pdf_link": pdf_link,
        "schemas": source_proposal.load_schemas(ROOT / "contracts"),
        "pdf_schemas": pdf_link.load_pdf_schemas(ROOT / "contracts"),
    }
    fragment_bytes = FIXTURE.read_bytes()
    fragment = json.loads(fragment_bytes)
    _expect_rejection("unknown", _unknown, modules, fragment_bytes, fragment)
    _expect_rejection("conflict", _conflict, modules, fragment_bytes, fragment)
    sys.stdout.write('{"conflict":"rejected","status":"success","unknown":"rejected"}\n')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
