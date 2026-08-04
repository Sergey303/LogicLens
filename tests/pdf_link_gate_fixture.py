"""Run the PDF source proposal review and selected-evidence package gate."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import source_proposal

if TYPE_CHECKING:
    from pathlib import Path


def run_proposal_gate(
    world: Path,
    proposal: Path,
    resolved: Path,
    root: Path,
    schemas: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Review, execute, and verify selected-evidence-only packaging."""
    source_proposal.prepare_extraction(
        world_root=world,
        proposal_root=proposal,
        prompt_path=root.parents[1] / "prompts/generic/source-assertion-proposer.md",
        schemas=schemas,
        contracts_root=root.parents[1] / "contracts",
    )
    source_proposal.import_assertion_proposal(
        world_root=world,
        proposal_root=proposal,
        candidate_path=resolved / "assertion-candidate.json",
        schemas=schemas,
        contracts_root=root.parents[1] / "contracts",
    )
    source_proposal.import_grounding_review(
        proposal_root=proposal,
        review_path=resolved / "grounding-review.json",
        schemas=schemas,
    )
    package_root = root / "package"
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
    return package
