"""Run the PDF source proposal review and selected-evidence package gate."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import source_proposal

if TYPE_CHECKING:
    from pathlib import Path as PathType

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def run_proposal_gate(
    world: PathType,
    proposal: PathType,
    resolved: PathType,
    output_root: PathType,
    schemas: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Review, execute, and verify selected-evidence-only packaging."""
    source_proposal.prepare_extraction(
        world_root=world,
        proposal_root=proposal,
        prompt_path=REPOSITORY_ROOT / "prompts/generic/source-assertion-proposer.md",
        schemas=schemas,
        contracts_root=REPOSITORY_ROOT / "contracts",
    )
    source_proposal.import_assertion_proposal(
        world_root=world,
        proposal_root=proposal,
        candidate_path=resolved / "assertion-candidate.json",
        schemas=schemas,
        contracts_root=REPOSITORY_ROOT / "contracts",
    )
    source_proposal.import_grounding_review(
        proposal_root=proposal,
        review_path=resolved / "grounding-review.json",
        schemas=schemas,
    )
    package_root = output_root / "package"
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
