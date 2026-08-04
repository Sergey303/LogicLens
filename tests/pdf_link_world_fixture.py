"""Schema-valid world fixture used by PDF source contracts."""

from __future__ import annotations

from pathlib import Path

from contract_fixture_support import (
    CAPSULE_FILES,
    write_capsule_support_files,
    write_json,
    write_minimal_module,
)

CAPSULE_ID = "management.role-boundaries"


def build_world(root: Path) -> Path:
    """Create a minimal world with one PDF source, capsule, module, and track."""
    world = root / "world"
    capsule = world / "capsules/role-boundaries"
    write_json(
        world / "world.json",
        {
            "schemaVersion": "0.1",
            "worldId": "management",
            "title": "Management",
            "description": "PDF contract fixture",
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
    write_json(
        world / "semantic/vocabulary.json",
        {
            "schemaVersion": "0.1",
            "concepts": [
                {
                    "id": "outcome.product_value",
                    "kind": "management_outcome",
                    "labels": {"en": "product value"},
                }
            ],
        },
    )
    write_json(
        world / "semantic/predicates.json",
        {
            "schemaVersion": "0.1",
            "predicates": [
                {
                    "id": "owns_outcome",
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
            "roles": [{"id": "role.product_owner", "title": "Product Owner"}],
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
                    "id": "scrum-guide-2020",
                    "kind": "pdf-document",
                    "title": "The Scrum Guide",
                    "locator": "https://example.com/scrum-guide.pdf",
                    "version": "2020-11",
                    "language": "en",
                    "license": {
                        "id": "CC-BY-SA-4.0",
                        "status": "confirmed",
                        "attribution": "Ken Schwaber and Jeff Sutherland",
                    },
                    "snapshotPolicy": "ephemeral-read",
                    "reader": {"kind": "poppler-layout"},
                }
            ],
        },
    )
    write_capsule_support_files(capsule)
    write_minimal_module(world, CAPSULE_ID)
    return world
