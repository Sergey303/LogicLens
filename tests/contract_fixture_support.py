"""Shared builders for schema-valid executable contract fixtures."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

CAPSULE_FILES = {
    "preparedFiles": [{"path": "prepared/assertions.json", "kind": "assertions"}],
    "ruleFiles": [{"path": "rules/policy.pl", "kind": "rules"}],
    "learningFiles": [{"path": "learning/overview.md", "kind": "overview"}],
    "testFiles": [{"path": "tests/test-cases.json", "kind": "test-cases"}],
}


def write_json(path: Path, value: object) -> None:
    """Write deterministic compact UTF-8 JSON with a trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def write_capsule_support_files(capsule: Path) -> None:
    """Create every file required by the minimal capsule manifest."""
    write_json(capsule / "prepared/assertions.json", {"schemaVersion": "0.1"})
    write_json(capsule / "tests/test-cases.json", {"schemaVersion": "0.1"})
    rules = capsule / "rules/policy.pl"
    rules.parent.mkdir(parents=True, exist_ok=True)
    rules.write_text("% fixture policy\n", encoding="utf-8")
    overview = capsule / "learning/overview.md"
    overview.parent.mkdir(parents=True, exist_ok=True)
    overview.write_text("# Fixture overview\n", encoding="utf-8")


def write_minimal_module(world: Path, capsule_id: str) -> None:
    """Create one referenced module and all of its declared files."""
    module = world / "modules/fixture"
    write_json(
        module / "module.json",
        {
            "schemaVersion": "0.1",
            "moduleId": "management.fixture",
            "version": "0.1.0",
            "worldId": "management",
            "title": "Fixture module",
            "usesCapsules": [{"id": capsule_id, "version": "0.1.0"}],
            "supportedTracks": ["fixture-track"],
            "entry": "entry.md",
            "sequence": ["sequence.json"],
            "scenarios": ["scenario.json"],
            "rubrics": ["rubric.json"],
            "completionPolicy": {
                "requiresCorrectionCycle": True,
                "allMandatoryCriteria": True,
                "minimumScore": 75,
            },
        },
    )
    (module / "entry.md").write_text("# Fixture\n", encoding="utf-8")
    for name in ("sequence", "scenario", "rubric"):
        write_json(module / f"{name}.json", {"schemaVersion": "0.1"})
