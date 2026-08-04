"""Semantic vocabulary used by the text source proposal contract."""

from __future__ import annotations

from typing import TYPE_CHECKING

from contract_fixture_support import write_json

if TYPE_CHECKING:
    from pathlib import Path


def write_semantics(world: Path) -> None:
    """Create the minimal roles, outcomes, and predicate used by the fixture."""
    write_json(
        world / "semantic/vocabulary.json",
        {
            "schemaVersion": "0.1",
            "concepts": [
                {
                    "id": "outcome.technical_direction",
                    "kind": "management_outcome",
                    "labels": {"en": "technical direction"},
                },
                {
                    "id": "outcome.people_development",
                    "kind": "management_outcome",
                    "labels": {"en": "people development"},
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
                    "id": "contributes_to",
                    "arguments": [
                        {"name": "role", "type": "role"},
                        {"name": "outcome", "type": "management_outcome"},
                    ],
                    "valueSpace": "strict_claim",
                    "world": "open",
                    "negation": "explicit_evidence",
                }
            ],
        },
    )
    write_json(
        world / "semantic/roles.json",
        {
            "schemaVersion": "0.1",
            "roles": [
                {"id": "role.team_lead", "title": "Team Lead"},
                {"id": "role.engineering_manager", "title": "Engineering Manager"},
            ],
        },
    )
    write_json(
        world / "semantic/competencies.json",
        {"schemaVersion": "0.1", "competencies": []},
    )
