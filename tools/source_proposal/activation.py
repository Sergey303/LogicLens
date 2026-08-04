from __future__ import annotations

import re
import shutil
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

from capsule import (
    canonical_json,
    declared_file,
    domain_hash,
    json_lines,
    json_object,
    schema_check,
    sha256,
    validate_world,
)
from .common import SAFE_DEPENDENCY, SourcePipelineError, load_semantics
from .gate import verify_package

ACTIVATION_DOMAIN = b"LogicLensSourceProposalActivation\0"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def stage_activation(
    *,
    package_root: Path,
    world_root: Path,
    output_world_root: Path,
    expected_current_version: str,
    new_version: str,
    allow_provisional: bool,
    swipl: str | None,
    timeout_seconds: int,
    schemas: dict[str, dict[str, Any]],
    contracts_root: Path,
) -> dict[str, Any]:
    package = verify_package(
        package_root=package_root,
        swipl=swipl,
        timeout_seconds=timeout_seconds,
        schemas=schemas,
    )
    if package["reviewClass"] == "provisional" and not allow_provisional:
        raise SourcePipelineError(
            "provisional source proposal requires explicit --allow-provisional"
        )

    world = validate_world(world_root, contracts_root)
    manifest = world["manifest"]
    if package["worldId"] != manifest["worldId"]:
        raise SourcePipelineError("source proposal package world mismatch")
    capsule_id = package["capsuleId"]
    capsule = world["capsules"].get(capsule_id)
    if capsule is None:
        raise SourcePipelineError(f"unknown activation capsule: {capsule_id}")
    if package["sourceId"] not in {
        item["id"] for item in capsule["sources"]["sources"]
    }:
        raise SourcePipelineError("source proposal package source is not declared")

    capsule_manifest = capsule["manifest"]
    old_version = capsule_manifest["version"]
    if old_version != expected_current_version:
        raise SourcePipelineError(
            "activation current capsule version mismatch: "
            f"expected {expected_current_version}, got {old_version}"
        )
    require_newer_version(old_version, new_version)

    assertion_entries = [
        item
        for item in capsule_manifest["preparedFiles"]
        if item["kind"] == "assertions"
    ]
    if len(assertion_entries) != 1:
        raise SourcePipelineError(
            "activation requires exactly one prepared assertions file"
        )
    assertion_relative = assertion_entries[0]["path"]
    existing = json_lines(
        declared_file(capsule["root"], assertion_relative, "prepared assertions"),
        "prepared assertions",
    )

    approved_relative = "generated/approved-assertions.jsonl"
    approved = json_lines(
        declared_file(
            package_root.resolve() / "files",
            approved_relative,
            "approved assertions",
        ),
        "approved assertions",
    )
    if len(approved) != package["gate"]["acceptedAssertions"]:
        raise SourcePipelineError(
            "approved assertion count does not match gate report"
        )

    existing_ids = {item["assertionId"] for item in existing}
    validate_approved_assertions(approved, load_semantics(world))
    verify_source_manifest_binding(package_root, package, capsule)

    approved_ids = [item["assertionId"] for item in approved]
    if len(approved_ids) != len(set(approved_ids)):
        raise SourcePipelineError("approved assertions contain duplicate IDs")
    duplicates = existing_ids.intersection(approved_ids)
    if duplicates:
        raise SourcePipelineError(
            f"activation assertion IDs already exist: {sorted(duplicates)}"
        )

    root = world_root.resolve()
    output = output_world_root.resolve()
    reject_overlapping_paths(root, output)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise SourcePipelineError(
            f"activation output must be absent or empty: {output}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)

    capsule_item = next(
        item for item in manifest["capsules"] if item["id"] == capsule_id
    )
    temporary = Path(
        tempfile.mkdtemp(prefix=output.name + ".tmp-", dir=output.parent)
    )
    try:
        shutil.copytree(root, temporary, dirs_exist_ok=True, symlinks=True)
        staged_capsule_root = temporary / capsule_item["path"]
        staged_assertions = staged_capsule_root / assertion_relative
        staged_assertions.write_bytes(
            b"".join(canonical_json(item) for item in [*existing, *approved])
        )

        staged_capsule_manifest = deepcopy(capsule_manifest)
        staged_capsule_manifest["version"] = new_version

        activation_relative = (
            f"activations/{package['proposalId']}-{new_version}.json"
        )
        declared_paths = {
            item["path"] for item in staged_capsule_manifest["preparedFiles"]
        }
        if activation_relative in declared_paths:
            raise SourcePipelineError(
                f"activation record already declared: {activation_relative}"
            )

        module_updates: list[dict[str, str]] = []
        for module_item in manifest["modules"]:
            module_path = temporary / module_item["path"] / "module.json"
            module = json_object(module_path, module_item["id"])
            matching = [
                item
                for item in module["usesCapsules"]
                if item["id"] == capsule_id
            ]
            if not matching:
                continue
            for dependency in matching:
                if dependency["version"] != old_version:
                    raise SourcePipelineError(
                        f"{module['moduleId']} does not reference current "
                        "capsule version"
                    )
                dependency["version"] = new_version
            old_module_version = module["version"]
            new_module_version = bump_patch(old_module_version)
            module["version"] = new_module_version
            module_path.write_bytes(canonical_json(module))
            module_updates.append(
                {
                    "moduleId": module["moduleId"],
                    "oldVersion": old_module_version,
                    "newVersion": new_module_version,
                }
            )

        activation: dict[str, Any] = {
            "schemaVersion": "0.1",
            "activationId": f"{package['proposalId']}-{new_version}",
            "status": "staged",
            "proposalId": package["proposalId"],
            "packageHash": package["packageHash"],
            "worldId": package["worldId"],
            "capsuleId": capsule_id,
            "sourceId": package["sourceId"],
            "reviewClass": package["reviewClass"],
            "approvalMode": (
                "human-reviewed"
                if package["reviewClass"] == "human-reviewed"
                else "provisional-override"
            ),
            "oldCapsuleVersion": old_version,
            "newCapsuleVersion": new_version,
            "assertionIds": approved_ids,
            "modules": module_updates,
        }
        activation["activationHash"] = domain_hash(
            ACTIVATION_DOMAIN,
            activation,
        )
        activation_schema = json_object(
            contracts_root / "source-proposal-activation-record-v0.schema.json",
            "source proposal activation schema",
        )
        schema_check(
            activation,
            activation_schema,
            "source proposal activation record",
        )
        activation_path = staged_capsule_root / activation_relative
        activation_path.parent.mkdir(parents=True, exist_ok=True)
        activation_path.write_bytes(canonical_json(activation))
        staged_capsule_manifest["preparedFiles"].append(
            {
                "path": activation_relative,
                "kind": "other",
                "description": (
                    "Source proposal activation record for "
                    f"{package['proposalId']}."
                ),
            }
        )
        (staged_capsule_root / "capsule.json").write_bytes(
            canonical_json(staged_capsule_manifest)
        )

        validate_world(temporary, contracts_root)
        if output.exists():
            output.rmdir()
        temporary.replace(output)
        return activation
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def require_newer_version(old_version: str, new_version: str) -> None:
    old = parse_version(old_version)
    new = parse_version(new_version)
    if new <= old:
        raise SourcePipelineError(
            f"activation version must increase: {old_version} -> {new_version}"
        )


def parse_version(value: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(value)
    if not match:
        raise SourcePipelineError(f"invalid semantic version: {value}")
    return tuple(int(part) for part in match.groups())


def bump_patch(value: str) -> str:
    major, minor, patch = parse_version(value)
    return f"{major}.{minor}.{patch + 1}"


def reject_overlapping_paths(world_root: Path, output: Path) -> None:
    if (
        output == world_root
        or output.is_relative_to(world_root)
        or world_root.is_relative_to(output)
    ):
        raise SourcePipelineError(
            "activation output must not overlap the source world"
        )


def validate_approved_assertions(
    assertions: list[dict[str, Any]],
    semantics: dict[str, Any],
) -> None:
    predicates = {item["id"]: item for item in semantics["predicates"]}
    typed_ids = semantics["typedIds"]
    for assertion in assertions:
        target = assertion["target"]
        predicate = predicates.get(target["predicate"])
        if predicate is None:
            raise SourcePipelineError(
                f"{assertion['assertionId']} uses unknown predicate "
                f"{target['predicate']}"
            )
        arguments = target["arguments"]
        if len(arguments) != len(predicate["arguments"]):
            raise SourcePipelineError(
                f"{assertion['assertionId']} argument count mismatch"
            )
        for value, declaration in zip(
            arguments,
            predicate["arguments"],
            strict=True,
        ):
            if value not in typed_ids.get(declaration["type"], set()):
                raise SourcePipelineError(
                    f"{assertion['assertionId']} unknown "
                    f"{declaration['type']} ID: {value}"
                )
        if not SAFE_DEPENDENCY.fullmatch(assertion["dependencyGroup"]):
            raise SourcePipelineError(
                f"{assertion['assertionId']} has unsafe dependency group"
            )


def verify_source_manifest_binding(
    package_root: Path,
    package: dict[str, Any],
    capsule: dict[str, Any],
) -> None:
    candidates: list[str] = []
    files_root = package_root.resolve() / "files"
    for record in package["files"]:
        relative = record["path"]
        if not relative.startswith("snapshot/") or not relative.endswith(".json"):
            continue
        value = json_object(
            declared_file(files_root, relative, "snapshot metadata"),
            "snapshot metadata",
        )
        manifest_hash = value.get("sourceManifestHash")
        if isinstance(manifest_hash, str):
            candidates.append(manifest_hash)
    if len(candidates) != 1:
        raise SourcePipelineError(
            "source proposal package must contain exactly one source "
            "manifest binding"
        )
    current_hash = sha256(canonical_json(capsule["sources"]))
    if candidates[0] != current_hash:
        raise SourcePipelineError(
            "source proposal package was built from a different source manifest"
        )
