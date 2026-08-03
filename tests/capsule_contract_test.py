#!/usr/bin/env python3
"""Contract verification for deterministic LogicLens capsule packages."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPOSITORY_ROOT / "tools" / "capsule.py"
CONTRACTS = REPOSITORY_ROOT / "contracts"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
            for value in values
        ),
        encoding="utf-8",
    )


def build_fixture(root: Path) -> Path:
    world = root / "world"
    capsule = world / "capsules" / "fixture"
    module = world / "modules" / "fixture"
    write_json(
        world / "world.json",
        {
            "schemaVersion": "0.1",
            "worldId": "fixture",
            "title": "Fixture",
            "languages": ["en"],
            "semantic": {
                "vocabulary": "semantic/vocabulary.json",
                "predicates": "semantic/predicates.json",
                "roles": "semantic/roles.json",
                "competencies": "semantic/competencies.json",
            },
            "capsules": [{"id": "fixture.capsule", "path": "capsules/fixture"}],
            "modules": [{"id": "fixture.module", "path": "modules/fixture"}],
            "tracks": [
                {
                    "id": "fixture-track",
                    "title": "Fixture",
                    "moduleIds": ["fixture.module"],
                }
            ],
        },
    )
    for name in ("vocabulary", "predicates", "roles", "competencies"):
        write_json(world / "semantic" / f"{name}.json", {"schemaVersion": "0.1", name: []})

    write_json(
        capsule / "capsule.json",
        {
            "schemaVersion": "0.1",
            "capsuleId": "fixture.capsule",
            "version": "0.1.0",
            "worldId": "fixture",
            "title": "Fixture capsule",
            "languages": ["en"],
            "status": "draft",
            "sourceManifest": "sources/manifest.json",
            "preparedFiles": [{"path": "prepared/assertions.jsonl", "kind": "assertions"}],
            "ruleFiles": [{"path": "rules/rules.pl", "kind": "rules"}],
            "learningFiles": [{"path": "learning/overview.md", "kind": "overview"}],
            "testFiles": [{"path": "tests/cases.jsonl", "kind": "test-cases"}],
            "exports": {"predicates": ["claim_status/2"], "profiles": []},
            "requires": {"capsuleContract": "0.1", "epistemicDsl": "0.1"},
        },
    )
    write_json(
        capsule / "sources" / "manifest.json",
        {
            "schemaVersion": "0.1",
            "capsuleId": "fixture.capsule",
            "sources": [
                {
                    "id": "fixture-source",
                    "kind": "local-file",
                    "title": "Fixture",
                    "locator": "fixture",
                    "license": {
                        "id": "internal",
                        "status": "internal",
                        "attribution": "LogicLens test",
                    },
                    "snapshotPolicy": "internal-reference",
                }
            ],
        },
    )
    write_jsonl(
        capsule / "prepared" / "assertions.jsonl",
        [
            {
                "assertionId": "fixture.assertion",
                "target": {"predicate": "owns", "arguments": ["role.a", "outcome.a"]},
                "stance": "support",
                "provenance": ["fixture-source#claim"],
                "dependencyGroup": "fixture.group",
                "generalisability": "local",
            }
        ],
    )
    (capsule / "rules").mkdir(parents=True, exist_ok=True)
    (capsule / "rules" / "rules.pl").write_text(
        ":- module(fixture_rules, [fixture_rule/1]).\nfixture_rule(ok).\n",
        encoding="utf-8",
    )
    (capsule / "learning").mkdir(parents=True, exist_ok=True)
    (capsule / "learning" / "overview.md").write_text("# Fixture\n", encoding="utf-8")
    write_jsonl(capsule / "tests" / "cases.jsonl", [{"id": "case-1"}])

    write_json(
        module / "module.json",
        {
            "schemaVersion": "0.1",
            "moduleId": "fixture.module",
            "version": "0.1.0",
            "worldId": "fixture",
            "title": "Fixture module",
            "usesCapsules": [{"id": "fixture.capsule", "version": "0.1.0"}],
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
    (module / "entry.md").write_text("# Fixture module\n", encoding="utf-8")
    for name in ("sequence", "scenario", "rubric"):
        write_json(module / f"{name}.json", {"schemaVersion": "0.1"})
    return world


def run(*arguments: str, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--contracts-root", str(CONTRACTS), *arguments],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if expect_success and result.returncode != 0:
        raise AssertionError(result.stderr)
    if not expect_success and result.returncode == 0:
        raise AssertionError("command unexpectedly succeeded")
    return result


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="logiclens-capsule-test-") as temporary:
        root = Path(temporary)
        world = build_fixture(root)
        package_a = root / "package-a"
        package_b = root / "package-b"

        run("validate", "--world-root", str(world))
        run(
            "compile",
            "--world-root",
            str(world),
            "--capsule",
            "fixture.capsule",
            "--output",
            str(package_a),
        )
        run(
            "compile",
            "--world-root",
            str(world),
            "--capsule",
            "fixture.capsule",
            "--output",
            str(package_b),
        )
        if (package_a / "capsule-package.json").read_bytes() != (
            package_b / "capsule-package.json"
        ).read_bytes():
            raise AssertionError("capsule manifests are not deterministic")
        if (package_a / "capsule.lock.json").read_bytes() != (
            package_b / "capsule.lock.json"
        ).read_bytes():
            raise AssertionError("capsule locks are not deterministic")

        run("verify", "--package", str(package_a))
        generated = package_a / "files" / "generated" / "assertions.pl"
        generated.write_text(generated.read_text(encoding="utf-8") + "% tampered\n", encoding="utf-8")
        run("verify", "--package", str(package_a), expect_success=False)

    print("Capsule contract verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
