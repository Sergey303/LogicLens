#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import source_proposal as sp
from capsule import json_lines
from source_proposal import gate as gate_module


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def write_minimal_module(world: Path) -> None:
    module = world / "modules" / "fixture"
    write_json(
        module / "module.json",
        {
            "schemaVersion": "0.1",
            "moduleId": "management.module.fixture",
            "version": "0.1.0",
            "worldId": "management",
            "title": "Source proposal fixture module",
            "usesCapsules": [
                {"id": "management.role-boundaries", "version": "0.1.0"}
            ],
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


def build_fixture(root: Path) -> tuple[Path, Path]:
    repo = root / "repo"
    world = repo / "worlds" / "management"
    capsule = world / "capsules" / "role-boundaries"

    (repo / "curriculum").mkdir(parents=True)
    (repo / "curriculum" / "00-learning-model.md").write_text(
        "# Роли в сценариях\n\n"
        "Team Lead задаёт локальное техническое направление и управляет техническими рисками.\n\n"
        "Engineering Manager отвечает за развитие сотрудников и здоровье команды.\n\n"
        "# Ограничение\n\n"
        "Отсутствие сведений не считается опровержением.\n",
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
            "capsules": [
                {
                    "id": "management.role-boundaries",
                    "path": "capsules/role-boundaries",
                }
            ],
            "modules": [
                {
                    "id": "management.module.fixture",
                    "path": "modules/fixture",
                }
            ],
            "tracks": [
                {
                    "id": "fixture-track",
                    "title": "Fixture",
                    "moduleIds": ["management.module.fixture"],
                }
            ],
        },
    )
    write_json(
        world / "semantic" / "vocabulary.json",
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
        world / "semantic" / "predicates.json",
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
        world / "semantic" / "roles.json",
        {
            "schemaVersion": "0.1",
            "roles": [
                {"id": "role.team_lead", "title": "Team Lead"},
                {
                    "id": "role.engineering_manager",
                    "title": "Engineering Manager",
                },
            ],
        },
    )
    write_json(
        world / "semantic" / "competencies.json",
        {"schemaVersion": "0.1", "competencies": []},
    )
    write_json(
        capsule / "capsule.json",
        {
            "schemaVersion": "0.1",
            "capsuleId": "management.role-boundaries",
            "version": "0.1.0",
            "worldId": "management",
            "title": "Role boundaries",
            "description": "fixture",
            "languages": ["ru"],
            "status": "draft",
            "sourceManifest": "sources/manifest.json",
            "preparedFiles": [],
            "ruleFiles": [],
            "learningFiles": [],
            "testFiles": [],
            "exports": {"predicates": [], "profiles": []},
            "requires": {"capsuleContract": "0.1", "epistemicDsl": "0.1"},
        },
    )
    write_json(
        capsule / "sources" / "manifest.json",
        {
            "schemaVersion": "0.1",
            "capsuleId": "management.role-boundaries",
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
    write_minimal_module(world)
    return repo, world


def main() -> int:
    schemas = sp.load_schemas(ROOT / "contracts")
    with tempfile.TemporaryDirectory(prefix="source-pipeline-test-") as td:
        root = Path(td)
        repo, world = build_fixture(root)
        workspace = root / "proposal"
        ws = sp.snapshot_source(
            world_root=world,
            capsule_id="management.role-boundaries",
            source_id="internal-learning-model",
            proposal_id="internal-learning-model-v0",
            output=workspace,
            repository_root=repo,
            allow_network=False,
            max_bytes=100000,
            schemas=schemas,
            contracts_root=ROOT / "contracts",
        )
        assert ws["stage"] == "snapshot"
        ws = sp.fragment_workspace(workspace, schemas)
        assert ws["artifacts"]["fragments"]["count"] == 2
        ws = sp.prepare_extraction(
            world_root=world,
            proposal_root=workspace,
            prompt_path=ROOT / "prompts/generic/source-assertion-proposer.md",
            schemas=schemas,
            contracts_root=ROOT / "contracts",
        )
        fragments = json_lines(
            workspace / "fragments" / "fragments.jsonl",
            "fragments",
        )
        fragment_id = fragments[0]["fragmentId"]
        candidate = {
            "schemaVersion": "0.1",
            "proposalId": "internal-learning-model-v0",
            "sourceId": "internal-learning-model",
            "provider": {"kind": "fixture", "name": "contract-test"},
            "assertions": [
                {
                    "assertionId": "rb.tl.contributes.direction",
                    "target": {
                        "predicate": "contributes_to",
                        "arguments": [
                            "role.team_lead",
                            "outcome.technical_direction",
                        ],
                    },
                    "stance": "support",
                    "grounding": [fragment_id],
                    "dependencyGroup": "internal.learning_model.roles",
                    "generalisability": "context-dependent",
                },
                {
                    "assertionId": "rb.em.contributes.people",
                    "target": {
                        "predicate": "contributes_to",
                        "arguments": [
                            "role.engineering_manager",
                            "outcome.people_development",
                        ],
                    },
                    "stance": "support",
                    "grounding": [fragment_id],
                    "dependencyGroup": "internal.learning_model.roles",
                    "generalisability": "context-dependent",
                },
            ],
            "abstentions": [],
        }
        candidate_path = root / "candidate.json"
        write_json(candidate_path, candidate)
        ws = sp.import_assertion_proposal(
            world_root=world,
            proposal_root=workspace,
            candidate_path=candidate_path,
            schemas=schemas,
            contracts_root=ROOT / "contracts",
        )
        review = {
            "schemaVersion": "0.1",
            "reviewId": "review-001",
            "proposalId": "internal-learning-model-v0",
            "reviewer": {"kind": "agent", "id": "contract-test"},
            "decisions": [
                {
                    "assertionId": "rb.tl.contributes.direction",
                    "decision": "accept",
                    "grounding": "paraphrase",
                    "evidenceQuotes": [
                        {
                            "fragmentId": fragment_id,
                            "quote": (
                                "Team Lead задаёт локальное техническое "
                                "направление"
                            ),
                        }
                    ],
                    "note": (
                        "The source directly names the role and technical "
                        "direction."
                    ),
                },
                {
                    "assertionId": "rb.em.contributes.people",
                    "decision": "accept",
                    "grounding": "direct",
                    "evidenceQuotes": [
                        {
                            "fragmentId": fragment_id,
                            "quote": (
                                "Engineering Manager отвечает за развитие "
                                "сотрудников"
                            ),
                        }
                    ],
                    "note": "The source explicitly names people development.",
                },
            ],
        }
        review_path = root / "review.json"
        write_json(review_path, review)
        ws = sp.import_grounding_review(
            proposal_root=workspace,
            review_path=review_path,
            schemas=schemas,
        )
        assert ws["artifacts"]["review"]["class"] == "provisional"

        swipl = shutil.which("swipl")
        original = gate_module.run_swipl_gate
        if not swipl:
            gate_module.run_swipl_gate = lambda *args, **kwargs: None
            swipl = "contract-test-stub"
        try:
            package = sp.execute_gate(
                proposal_root=workspace,
                output=root / "package",
                swipl=swipl,
                timeout_seconds=20,
                schemas=schemas,
            )
            assert package["activation"] == "not-performed"
            assert package["reviewClass"] == "provisional"
            sp.verify_package(
                package_root=root / "package",
                swipl=swipl if shutil.which("swipl") else None,
                timeout_seconds=20,
                schemas=schemas,
            )
        finally:
            gate_module.run_swipl_gate = original

        generated = root / "package/files/generated/source_proposal.pl"
        text = generated.read_text(encoding="utf-8")
        assert "claim_status" in text and "contributes_to" in text
        generated.write_text(text + "% tampered\n", encoding="utf-8")
        try:
            sp.verify_package(
                package_root=root / "package",
                swipl=None,
                timeout_seconds=5,
                schemas=schemas,
            )
        except sp.SourcePipelineError:
            pass
        else:
            raise AssertionError("tampered package verified")

        try:
            sp.snapshot_source(
                world_root=world,
                capsule_id="management.role-boundaries",
                source_id="link-only",
                proposal_id="link-only-v0",
                output=root / "link",
                repository_root=repo,
                allow_network=False,
                max_bytes=100000,
                schemas=schemas,
                contracts_root=ROOT / "contracts",
            )
        except sp.SourcePipelineError:
            pass
        else:
            raise AssertionError("link-only source was snapshotted")

    print("Source proposal pipeline contract verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
