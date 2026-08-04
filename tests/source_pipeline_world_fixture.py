"""Schema-valid world fixture used by text source pipeline contracts."""

from __future__ import annotations

from pathlib import Path

from contract_fixture_support import (
    CAPSULE_FILES,
    write_capsule_support_files,
    write_json,
    write_minimal_module,
)

CAPSULE_ID = "management.role-boundaries"


def build_fixture(root: Path) -> tuple[Path, Path]:
    """Create a repository and world with one internal and one link-only source."""
    repository = root / "repo"
    world = repository / "worlds/management"
    capsule = world / "capsules/role-boundaries"
    curriculum = repository / "curriculum/00-learning-model.md"
    curriculum.parent.mkdir(parents=True)
    curriculum.write_text(
        "# Роли в сценариях\n\n"
        "Team Lead задаёт локальное техническое направление и управляет техническими рисками.\n\n"
        "Engineering Manager отвечает за развитие сотрудников и здоровье команды.\n\n"
        "# Ограничение\n\nОтсутствие сведений не считается опровержением.\n",
        encoding="utf-8",
    )
    write_json(
        world / "world.json",
        {
            "schemaVersion": "0.1",
            "worldId": "management",
            "title": "Management",
            "description": "fixture",
            "languages": ["ru"],
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
    write_json(
        world / "semantic/vocabulary.json",
        {
            "schemaVersion": "0.1",
            "concepts": [
                {
                    "id": "outcome.technical_direction",
                    "kind": "management_outcome",
                    "labels": {"ru": "техническое направление"},
                },
                {
                    "id": "outcome.people_development",
                    "kind": "management_outcome",
                    "labels": {"ru": "развитие сотрудников"},
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
    write_json(
        capsule / "capsule.json",
        {
            "schemaVersion": "0.1",
            "capsuleId": CAPSULE_ID,
            "version": "0.1.0",
            "worldId": "management",
            "title": "Role boundaries",
            "description": "fixture",
            "languages": ["ru"],
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
                    "language": "ru",
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
