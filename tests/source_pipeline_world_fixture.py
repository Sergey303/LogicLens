"""Schema-valid world fixture used by text source pipeline contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from contract_fixture_support import (
    CAPSULE_FILES,
    write_capsule_support_files,
    write_json,
    write_minimal_module,
)
from source_pipeline_semantic_fixture import write_semantics

if TYPE_CHECKING:
    from pathlib import Path

CAPSULE_ID = "management.role-boundaries"


def build_fixture(root: Path) -> tuple[Path, Path]:
    """Create a repository and world with one internal and one link-only source."""
    repository = root / "repo"
    world = repository / "worlds/management"
    capsule = world / "capsules/role-boundaries"
    curriculum = repository / "curriculum/00-learning-model.md"
    curriculum.parent.mkdir(parents=True)
    curriculum.write_text(
        "# Roles in scenarios\n\n"
        "Team Lead sets local technical direction and manages technical risks.\n\n"
        "Engineering Manager owns employee development and team health.\n\n"
        "# Limitation\n\nMissing information is not contradictory evidence.\n",
        encoding="utf-8",
    )
    write_json(
        world / "world.json",
        {
            "schemaVersion": "0.1",
            "worldId": "management",
            "title": "Management",
            "description": "fixture",
            "languages": ["en"],
            "semantic": {
                "vocabulary": "semantic/vocabulary.json",
                "predicates": "semantic/predicates.json",
                "roles": "semantic/roles.json",
                "competencies": "semantic/competencies.json",
            },
            "capsules": [{"id": CAPSULE_ID, "path": "capsules/role-boundaries"}],
            "modules": [{"id": "management.fixture", "path": "modules/fixture"}],
            "tracks": [
                {
                    "id": "fixture-track",
                    "title": "Fixture",
                    "moduleIds": ["management.fixture"],
                }
            ],
        },
    )
    write_semantics(world)
    write_json(
        capsule / "capsule.json",
        {
            "schemaVersion": "0.1",
            "capsuleId": CAPSULE_ID,
            "version": "0.1.0",
            "worldId": "management",
            "title": "Role boundaries",
            "description": "fixture",
            "languages": ["en"],
            "status": "draft",
            "sourceManifest": "sources/manifest.json",
            **CAPSULE_FILES,
            "exports": {"predicates": [], "profiles": []},
            "requires": {"capsuleContract": "0.1", "epistemicDsl": "0.1"},
        },
    )
    write_json(
        capsule / "sources/manifest.json",
        {
            "schemaVersion": "0.1",
            "capsuleId": CAPSULE_ID,
            "sources": [
                {
                    "id": "internal-learning-model",
                    "kind": "repository-file",
                    "title": "Learning model",
                    "locator": "https://example.invalid/internal",
                    "repositoryPath": "curriculum/00-learning-model.md",
                    "language": "en",
                    "license": {
                        "id": "internal",
                        "status": "internal",
                        "attribution": "fixture",
                    },
                    "snapshotPolicy": "internal-reference",
                },
                {
                    "id": "link-only",
                    "kind": "web-page",
                    "title": "Link only",
                    "locator": "https://example.com",
                    "language": "en",
                    "license": {
                        "id": "CC-BY",
                        "status": "confirmed",
                        "attribution": "example",
                    },
                    "snapshotPolicy": "link-only",
                },
            ],
        },
    )
    write_capsule_support_files(capsule)
    write_minimal_module(world, CAPSULE_ID)
    return repository, world
