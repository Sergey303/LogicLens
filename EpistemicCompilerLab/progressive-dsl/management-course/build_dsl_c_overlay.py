#!/usr/bin/env python3
"""Build a temporary management DSL-C typed-observation overlay."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from capsule import (  # noqa: E402
    canonical_json,
    json_lines,
    json_object,
    schema_check,
    validate_world,
)

UTF8 = "utf-8"
OVERLAY_VERSION = "0.3.0"
OBSERVATION_RELATIVE = "prepared/observations-dsl-c-v0.jsonl"
SOURCE_ID = "northstar-kpi-snapshot-c0"

METRICS = (
    ("metric.release_lead_time_p95", "P95 времени выполнения изменения"),
    ("metric.mttr", "время восстановления сервиса"),
    ("metric.change_failure_rate", "доля неуспешных изменений"),
    ("metric.availability", "доступность сервиса"),
    ("metric.budget_variance", "отклонение бюджета"),
    ("metric.deployment_frequency", "частота развёртываний"),
    ("metric.sev1_incident_count", "число инцидентов Sev-1"),
    ("metric.delivery_predictability", "предсказуемость поставки"),
    ("metric.unloaded_control", "контрольная незагруженная метрика"),
)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-world", required=True, type=Path)
    parser.add_argument("--output-world", required=True, type=Path)
    parser.add_argument(
        "--observations",
        type=Path,
        default=Path(__file__).with_name("dsl-c-observations-v0.jsonl"),
    )
    parser.add_argument(
        "--contracts-root",
        type=Path,
        default=ROOT / "contracts",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding=UTF8))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object expected: {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def add_concept(
    concepts: list[dict[str, Any]],
    identifier: str,
    kind: str,
    label_ru: str,
    label_en: str,
) -> None:
    if any(item.get("id") == identifier for item in concepts):
        raise RuntimeError(f"semantic concept already exists: {identifier}")
    concepts.append(
        {
            "id": identifier,
            "kind": kind,
            "labels": {"ru": label_ru, "en": label_en},
        }
    )


def main() -> int:
    args = arguments()
    source = args.source_world.resolve()
    output = args.output_world.resolve()
    observations_path = args.observations.resolve()
    contracts = args.contracts_root.resolve()
    if not source.is_dir():
        raise RuntimeError(f"source world does not exist: {source}")
    if not observations_path.is_file():
        raise RuntimeError(f"observation fixture does not exist: {observations_path}")
    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            raise RuntimeError(f"output world must be absent or empty: {output}")
        output.rmdir()

    observation_schema = json_object(
        contracts / "epistemic-observation-v0.schema.json",
        "typed observation schema",
    )
    observations = json_lines(observations_path, "DSL-C observations")
    observation_ids: set[str] = set()
    targets: set[str] = set()
    for index, row in enumerate(observations, 1):
        schema_check(row, observation_schema, f"DSL-C observation:{index}")
        observation_id = row["observationId"]
        target = json.dumps(
            row["target"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if observation_id in observation_ids:
            raise RuntimeError(f"duplicate observation ID: {observation_id}")
        if target in targets:
            raise RuntimeError(f"duplicate observation target: {target}")
        observation_ids.add(observation_id)
        targets.add(target)

    source_capsule_path = source / "capsules" / "role-boundaries" / "capsule.json"
    source_module_path = source / "modules" / "00-role-boundaries" / "module.json"
    source_capsule = read_json(source_capsule_path)
    source_module = read_json(source_module_path)
    source_capsule_version = source_capsule.get("version")
    source_module_version = source_module.get("version")

    shutil.copytree(source, output)
    capsule_root = output / "capsules" / "role-boundaries"
    capsule_path = capsule_root / "capsule.json"
    module_path = output / "modules" / "00-role-boundaries" / "module.json"
    vocabulary_path = output / "semantic" / "vocabulary.json"
    capsule = read_json(capsule_path)
    module = read_json(module_path)
    vocabulary = read_json(vocabulary_path)

    concepts = vocabulary.get("concepts")
    if not isinstance(concepts, list):
        raise RuntimeError("management vocabulary must contain concepts")
    for identifier, label_ru in METRICS:
        add_concept(
            concepts,
            identifier,
            "management_metric",
            label_ru,
            identifier.removeprefix("metric.").replace("_", " "),
        )
    add_concept(
        concepts,
        "subject.northstar_platform",
        "measurement_subject",
        "платформа Northstar",
        "Northstar platform",
    )
    add_concept(
        concepts,
        "window.2026_q2",
        "time_window",
        "второй квартал 2026 года",
        "2026 Q2",
    )

    prepared_files = capsule.get("preparedFiles")
    if not isinstance(prepared_files, list):
        raise RuntimeError("capsule preparedFiles must be an array")
    if any(
        isinstance(item, dict) and item.get("path") == OBSERVATION_RELATIVE
        for item in prepared_files
    ):
        raise RuntimeError("DSL-C observation overlay is already declared")
    prepared_files.append(
        {
            "path": OBSERVATION_RELATIVE,
            "kind": "observations",
            "description": (
                "Frozen private Northstar KPI observations for typed numerical "
                "comparison experiments."
            ),
        }
    )

    source_manifest_path = capsule_root / str(capsule["sourceManifest"])
    source_manifest = read_json(source_manifest_path)
    sources = source_manifest.get("sources")
    if not isinstance(sources, list):
        raise RuntimeError("capsule source manifest must contain sources")
    if any(item.get("id") == SOURCE_ID for item in sources if isinstance(item, dict)):
        raise RuntimeError(f"source already exists: {SOURCE_ID}")
    sources.append(
        {
            "id": SOURCE_ID,
            "kind": "local-file",
            "title": "Synthetic Northstar KPI snapshot C0",
            "locator": OBSERVATION_RELATIVE,
            "version": "C0-2026.08",
            "language": "ru",
            "license": {
                "id": "internal",
                "status": "internal",
                "attribution": "LogicLens research fixture",
            },
            "snapshotPolicy": "internal-reference",
            "notes": (
                "Synthetic private management measurements used only for the "
                "progressive DSL-C experiment."
            ),
        }
    )

    capsule["version"] = OVERLAY_VERSION
    capsule["description"] = (
        "Experimental DSL-C overlay with typed point, bounded and normal KPI "
        "observations. The source management world remains unchanged."
    )
    uses_capsules = module.get("usesCapsules")
    if not isinstance(uses_capsules, list) or len(uses_capsules) != 1:
        raise RuntimeError("expected exactly one module capsule dependency")
    dependency = uses_capsules[0]
    if not isinstance(dependency, dict):
        raise RuntimeError("invalid module capsule dependency")
    dependency["version"] = OVERLAY_VERSION
    module["version"] = OVERLAY_VERSION

    destination = capsule_root / OBSERVATION_RELATIVE
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(observations_path, destination)
    write_json(capsule_path, capsule)
    write_json(module_path, module)
    write_json(vocabulary_path, vocabulary)
    write_json(source_manifest_path, source_manifest)

    validate_world(output, contracts)
    overlay = {
        "schemaVersion": "0.1",
        "overlayId": "management-progressive-dsl-c-v0",
        "dslLevel": "DSL-C",
        "benchmarkTranche": "C0-private-typed-kpi",
        "sourceWorld": str(source),
        "sourceCapsuleVersion": source_capsule_version,
        "sourceModuleVersion": source_module_version,
        "overlayCapsuleVersion": OVERLAY_VERSION,
        "overlayModuleVersion": OVERLAY_VERSION,
        "observationsPath": OBSERVATION_RELATIVE,
        "observationsHash": file_hash(destination),
        "observationCount": len(observations),
        "sourceWorldModified": False,
    }
    write_json(output / "dsl-c-overlay.json", overlay)
    print("Built and validated management DSL-C overlay")
    print(f"Source capsule: {source_capsule_version}")
    print(f"Overlay capsule: {OVERLAY_VERSION}")
    print(f"Observations: {len(observations)}")
    print(f"Observations hash: {overlay['observationsHash']}")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
