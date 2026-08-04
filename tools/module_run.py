#!/usr/bin/env python3
"""Issue deterministic Markdown/JSON learning runs from LogicLens modules."""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from capsule import (
    CapsuleError,
    canonical_json,
    compile_capsule,
    json_lines,
    json_object,
    json_value,
    normalized_text,
    schema_check,
    validate_world,
)

UTF8 = "utf-8"
RUN_DOMAIN = b"LogicLensLearningRun\0"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ModuleRunError(RuntimeError):
    pass


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contracts-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "contracts",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    issue = commands.add_parser("issue")
    issue.add_argument("--world-root", required=True, type=Path)
    issue.add_argument("--module", required=True)
    issue.add_argument("--track", required=True)
    issue.add_argument("--run-id", required=True)
    issue.add_argument("--output", required=True, type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = arguments()
    if args.command == "verify":
        record = verify_run(args.run, args.contracts_root)
        print(f"Verified learning run: {record['runId']}")
        print(f"Run hash: {record['runHash']}")
        return 0

    record = issue_run(
        world_root=args.world_root,
        contracts_root=args.contracts_root,
        module_id=args.module,
        track_id=args.track,
        run_id=args.run_id,
        output=args.output,
    )
    print(f"Issued learning run: {record['runId']}")
    print(f"Module: {record['module']['id']}")
    print(f"Track: {record['track']['id']}")
    print(f"Run hash: {record['runHash']}")
    print(f"Output: {args.output.resolve()}")
    return 0


def issue_run(
    *,
    world_root: Path,
    contracts_root: Path,
    module_id: str,
    track_id: str,
    run_id: str,
    output: Path,
) -> dict[str, Any]:
    world = validate_world(world_root, contracts_root)
    if not safe_id(run_id):
        raise ModuleRunError("run ID is not a safe identifier")
    module = world["modules"].get(module_id)
    if module is None:
        raise ModuleRunError(f"unknown module: {module_id}")
    if track_id not in module["supportedTracks"]:
        raise ModuleRunError(f"module {module_id} does not support track {track_id}")
    track = next(
        (
            item
            for item in world["manifest"]["tracks"]
            if item["id"] == track_id
        ),
        None,
    )
    if track is None or module_id not in track["moduleIds"]:
        raise ModuleRunError(f"track {track_id} does not include module {module_id}")

    module_root = next(
        world["root"] / item["path"]
        for item in world["manifest"]["modules"]
        if item["id"] == module_id
    )
    entry = (module_root / module["entry"]).read_text(encoding=UTF8)
    sequence_path = module_root / module["sequence"][0]
    scenario_path = module_root / module["scenarios"][0]
    rubric_path = module_root / module["rubrics"][0]
    sequence = json_object(sequence_path, "learning sequence")
    scenario = json_object(scenario_path, "learning scenario")
    rubric = json_object(rubric_path, "learning rubric")
    variants = scenario.get("roleVariants")
    if not isinstance(variants, dict) or track_id not in variants:
        raise ModuleRunError(f"scenario does not define track {track_id}")
    role_variant = variants[track_id]

    destination = output.resolve()
    if destination.exists() and (
        not destination.is_dir() or any(destination.iterdir())
    ):
        raise ModuleRunError(f"output must be absent or empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    capsule_packages: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(
        prefix="logiclens-module-capsules-"
    ) as temporary:
        temp = Path(temporary)
        for dependency in module["usesCapsules"]:
            package = compile_capsule(
                world,
                dependency["id"],
                temp / dependency["id"],
            )
            capsule_packages.append(
                {
                    "id": dependency["id"],
                    "version": dependency["version"],
                    "packageHash": package["packageHash"],
                }
            )

    stage_files = build_stage_input_files(
        world=world,
        module=module,
        track_id=track_id,
        role_variant=role_variant,
        run_id=run_id,
    )
    stage_inputs = {
        stage_id: {
            "path": relative,
            "sha256": content_hash(content),
        }
        for stage_id, (relative, content) in stage_files.items()
    }

    public_scenario = {
        key: value
        for key, value in scenario.items()
        if key not in {"hiddenTensions", "roleVariants"}
    }
    public_scenario["roleTask"] = role_variant.get("task")
    public_scenario["primaryOutcomes"] = role_variant.get(
        "primaryOutcomes",
        [],
    )
    public_scenario["mustEscalate"] = role_variant.get(
        "mustEscalate",
        [],
    )

    source_hashes = {
        "moduleManifest": canonical_source_hash(module_root / "module.json"),
        "entry": canonical_source_hash(module_root / module["entry"]),
        "sequence": canonical_source_hash(sequence_path),
        "scenario": canonical_source_hash(scenario_path),
        "rubric": canonical_source_hash(rubric_path),
    }
    record: dict[str, Any] = {
        "schemaVersion": "0.1",
        "runId": run_id,
        "status": "issued",
        "world": {
            "id": world["manifest"]["worldId"],
            "title": world["manifest"]["title"],
        },
        "module": {
            "id": module_id,
            "version": module["version"],
            "title": module["title"],
        },
        "track": {"id": track_id, "title": track["title"]},
        "capsules": sorted(
            capsule_packages,
            key=lambda item: item["id"],
        ),
        "scenario": public_scenario,
        "sequence": sequence,
        "stageInputs": stage_inputs,
        "completionPolicy": module["completionPolicy"],
        "requiredOutputs": [
            stage["output"]
            for stage in sequence.get("stages", [])
            if isinstance(stage, dict)
            and isinstance(stage.get("output"), str)
        ],
        "sourceHashes": source_hashes,
    }
    record["runHash"] = run_hash(record)
    run_schema = json_object(
        contracts_root / "learning-run-v0.schema.json",
        "learning run schema",
    )
    schema_check(record, run_schema, "learning run")
    evaluator = {
        "schemaVersion": "0.1",
        "runId": run_id,
        "runHash": record["runHash"],
        "hiddenTensions": scenario.get("hiddenTensions", []),
        "roleVariant": role_variant,
        "rubric": rubric,
    }

    (destination / "run.json").write_bytes(canonical_json(record))
    (destination / "evaluator-frame.json").write_bytes(
        canonical_json(evaluator)
    )
    (destination / "briefing.md").write_text(
        render_briefing(record, entry),
        encoding=UTF8,
        newline="\n",
    )
    (destination / "response-template.md").write_text(
        response_template(record),
        encoding=UTF8,
        newline="\n",
    )
    for _, (relative, content) in stage_files.items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    write_manifest(destination)
    return record


def build_stage_input_files(
    *,
    world: dict[str, Any],
    module: dict[str, Any],
    track_id: str,
    role_variant: dict[str, Any],
    run_id: str,
) -> dict[str, tuple[str, bytes]]:
    baseline = role_variant.get("baselineQuestion")
    if not isinstance(baseline, str) or not baseline.strip():
        baseline = baseline_from_capsules(world, module, track_id)

    challenge = role_variant.get("stakeholderChallenge")
    if not isinstance(challenge, str) or not challenge.strip():
        raise ModuleRunError(
            f"scenario role variant {track_id} lacks stakeholderChallenge"
        )

    counterexample = role_variant.get("nearbyCounterexample")
    if not isinstance(counterexample, str) or not counterexample.strip():
        raise ModuleRunError(
            f"scenario role variant {track_id} lacks nearbyCounterexample"
        )

    learning = learning_material_from_capsules(world, module)

    return {
        "baseline": (
            "baseline-question.md",
            normalized_text(
                "# Baseline-вопрос\n\n"
                f"Run ID: `{run_id}`\n\n"
                "Ответьте до изучения учебного материала. "
                "Зафиксируйте исходную модель роли и не пытайтесь "
                "угадать формулировку рубрики.\n\n"
                f"{baseline.strip()}\n"
            ),
        ),
        "learn": (
            "learning-material.md",
            normalized_text(learning),
        ),
        "challenge": (
            "stakeholder-challenge.md",
            normalized_text(
                "# Возражение стейкхолдера\n\n"
                f"Run ID: `{run_id}`\n\n"
                f"{challenge.strip()}\n\n"
                "Ответьте так, чтобы сохранить границы роли, "
                "показать факты и альтернативы, назвать владельца "
                "решения и срок.\n"
            ),
        ),
        "exam": (
            "exam-counterexample.md",
            normalized_text(
                "# Финальный nearby counterexample\n\n"
                f"Run ID: `{run_id}`\n\n"
                f"{counterexample.strip()}\n\n"
                "Примените ту же ролевую модель к изменённому "
                "контексту. Отдельно укажите, что изменилось, "
                "а что осталось неизвестным.\n"
            ),
        ),
    }


def baseline_from_capsules(
    world: dict[str, Any],
    module: dict[str, Any],
    track_id: str,
) -> str:
    matches: list[str] = []
    for dependency in module["usesCapsules"]:
        capsule = world["capsules"].get(dependency["id"])
        if capsule is None:
            raise ModuleRunError(
                f"module references unknown capsule {dependency['id']}"
            )
        for item in capsule["manifest"].get("learningFiles", []):
            if item.get("kind") != "questions":
                continue
            path = capsule["root"] / item["path"]
            for row in json_lines(path, f"learning questions:{path}"):
                if row.get("track") == track_id:
                    prompt = row.get("prompt")
                    if isinstance(prompt, str) and prompt.strip():
                        matches.append(prompt.strip())
    if len(matches) != 1:
        raise ModuleRunError(
            f"track {track_id} must resolve exactly one baseline question; "
            f"found {len(matches)}"
        )
    return matches[0]


def learning_material_from_capsules(
    world: dict[str, Any],
    module: dict[str, Any],
) -> str:
    sections = ["# Учебный материал капсул", ""]
    count = 0
    for dependency in module["usesCapsules"]:
        capsule = world["capsules"].get(dependency["id"])
        if capsule is None:
            raise ModuleRunError(
                f"module references unknown capsule {dependency['id']}"
            )
        overview_files = [
            item
            for item in capsule["manifest"].get("learningFiles", [])
            if item.get("kind") == "overview"
        ]
        if len(overview_files) != 1:
            raise ModuleRunError(
                f"capsule {dependency['id']} must declare exactly one overview"
            )
        overview = overview_files[0]
        content = (
            capsule["root"] / overview["path"]
        ).read_text(encoding=UTF8).strip()
        sections.extend(
            [
                f"## {capsule['manifest']['title']}",
                "",
                f"Капсула: `{dependency['id']}` "
                f"`{dependency['version']}`",
                "",
                content,
                "",
            ]
        )
        count += 1
    if count == 0:
        raise ModuleRunError("module has no learning capsule overview")
    return "\n".join(sections).rstrip() + "\n"


def verify_run(
    run_root: Path,
    contracts_root: Path,
) -> dict[str, Any]:
    root = run_root.resolve()
    manifest = json_object(
        root / "run-files.json",
        "run files manifest",
    )
    expected: set[str] = set()
    for item in manifest.get("files", []):
        relative = item.get("path")
        if not isinstance(relative, str) or relative in expected:
            raise ModuleRunError("invalid run file manifest")
        expected.add(relative)
        path = root / relative
        if not path.is_file() or file_hash(path) != item.get("sha256"):
            raise ModuleRunError(f"run file hash mismatch: {relative}")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "run-files.json"
    }
    if actual != expected:
        raise ModuleRunError("run file set mismatch")

    record = json_object(root / "run.json", "learning run")
    run_schema = json_object(
        contracts_root / "learning-run-v0.schema.json",
        "learning run schema",
    )
    schema_check(record, run_schema, "learning run")
    supplied = record.get("runHash")
    payload = dict(record)
    payload.pop("runHash", None)
    if supplied != run_hash(payload):
        raise ModuleRunError("learning run hash mismatch")

    evaluator = json_object(
        root / "evaluator-frame.json",
        "evaluator frame",
    )
    if (
        evaluator.get("runId") != record.get("runId")
        or evaluator.get("runHash") != supplied
    ):
        raise ModuleRunError(
            "evaluator frame is not bound to the learning run"
        )

    stage_inputs = record.get("stageInputs")
    if isinstance(stage_inputs, dict):
        required = {"baseline", "learn", "challenge", "exam"}
        if set(stage_inputs) != required:
            raise ModuleRunError(
                "learning run stage input set is incomplete"
            )
        for stage_id, item in stage_inputs.items():
            relative = item.get("path")
            expected_hash = item.get("sha256")
            if not isinstance(relative, str):
                raise ModuleRunError(
                    f"invalid stage input path: {stage_id}"
                )
            path = root / relative
            if (
                not path.is_file()
                or file_hash(path) != expected_hash
            ):
                raise ModuleRunError(
                    f"stage input hash mismatch: {stage_id}"
                )
    return record


def write_manifest(destination: Path) -> None:
    files = []
    for path in sorted(destination.rglob("*")):
        if path.is_file() and path.name != "run-files.json":
            files.append(
                {
                    "path": path.relative_to(destination).as_posix(),
                    "sha256": file_hash(path),
                }
            )
    (destination / "run-files.json").write_bytes(
        canonical_json(
            {
                "schemaVersion": "0.1",
                "files": files,
            }
        )
    )


def render_briefing(
    record: dict[str, Any],
    entry: str,
) -> str:
    facts = record["scenario"].get("sharedFacts", {})
    fact_lines = "\n".join(
        f"- `{key}`: `{value}`"
        for key, value in facts.items()
    )
    outcomes = "\n".join(
        f"- `{value}`"
        for value in record["scenario"].get(
            "primaryOutcomes",
            [],
        )
    )
    escalations = "\n".join(
        f"- {value}"
        for value in record["scenario"].get(
            "mustEscalate",
            [],
        )
    )
    inputs = record.get("stageInputs", {})
    input_lines = "\n".join(
        f"- `{stage}`: `{item['path']}`"
        for stage, item in inputs.items()
    )
    return (
        f"# {record['module']['title']}\n\n"
        f"**Трек:** {record['track']['title']}  \n"
        f"**Run ID:** `{record['runId']}`  \n"
        f"**Run hash:** `{record['runHash']}`\n\n"
        f"## Ситуация\n\n{record['scenario']['title']}\n\n"
        f"## Данные\n\n{fact_lines}\n\n"
        f"## Задача роли\n\n"
        f"{record['scenario'].get('roleTask', '')}\n\n"
        f"## Основные outcomes роли\n\n{outcomes}\n\n"
        f"## Обязательная эскалация\n\n{escalations}\n\n"
        f"## Входы стадий\n\n{input_lines}\n\n"
        f"---\n\n{entry.strip()}\n"
    )


def response_template(record: dict[str, Any]) -> str:
    return (
        f"# Ответ: {record['module']['title']}\n\n"
        f"Run ID: `{record['runId']}`\n\n"
        "## 1. Диагноз\n\n"
        "## 2. Outcome, которым владеет моя роль\n\n"
        "## 3. Во что я вношу вклад, но чем не владею\n\n"
        "## 4. Что и кому делегирую\n\n"
        "## 5. Что, кому и к какому сроку эскалирую\n\n"
        "## 6. Варианты решения и trade-offs\n\n"
        "## 7. Рекомендация\n\n"
        "## 8. Риски, неизвестное и предположения\n\n"
        "## 9. Owners, сроки, gates и дата пересмотра\n"
    )


def run_hash(record: dict[str, Any]) -> str:
    payload = dict(record)
    payload.pop("runHash", None)
    digest = hashlib.sha256(
        RUN_DOMAIN + bytes((1,)) + canonical_json(payload)
    )
    return "sha256:" + digest.hexdigest()


def content_hash(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def file_hash(path: Path) -> str:
    return content_hash(path.read_bytes())


def canonical_source_hash(path: Path) -> str:
    if path.suffix.lower() == ".json":
        content = canonical_json(json_value(path, str(path)))
    else:
        content = normalized_text(path.read_text(encoding=UTF8))
    return "sha256:" + hashlib.sha256(content).hexdigest()


def safe_id(value: str) -> bool:
    return (
        isinstance(value, str)
        and SAFE_ID.fullmatch(value) is not None
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        CapsuleError,
        ModuleRunError,
        OSError,
        ValueError,
    ) as exc:
        print(f"Module run failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
