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

    assertion_relative = prepared_assertion_path(capsule_manifest)
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
    require_empty_output(output)
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
        activation["activationHash"] = compute_activation_hash(activation)
        activation_schema = load_activation_schema(contracts_root)
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


def finalize_activation(
    *,
    source_world_root: Path,
    staged_world_root: Path,
    output_world_root: Path,
    activation_id: str,
    expected_activation_hash: str,
    approve_provisional: bool,
    contracts_root: Path,
) -> dict[str, Any]:
    source_root = source_world_root.resolve()
    staged_root = staged_world_root.resolve()
    output = output_world_root.resolve()
    reject_overlapping_paths(source_root, output)
    reject_overlapping_paths(staged_root, output)
    require_empty_output(output)

    source_world = validate_world(source_root, contracts_root)
    staged_world = validate_world(staged_root, contracts_root)
    if source_world["manifest"]["worldId"] != staged_world["manifest"]["worldId"]:
        raise SourcePipelineError("source and staged worlds do not match")

    capsule_id, activation_relative, activation = find_activation_record(
        staged_world,
        activation_id,
        contracts_root,
    )
    verify_activation_hash(activation)
    if activation["status"] != "staged":
        raise SourcePipelineError("activation record is not staged")
    if activation["activationHash"] != expected_activation_hash:
        raise SourcePipelineError("staged activation hash mismatch")
    if activation["reviewClass"] == "provisional" and not approve_provisional:
        raise SourcePipelineError(
            "provisional activation finalization requires "
            "explicit --approve-provisional"
        )
    if activation["worldId"] != source_world["manifest"]["worldId"]:
        raise SourcePipelineError("activation world identity mismatch")
    if activation["capsuleId"] != capsule_id:
        raise SourcePipelineError("activation capsule identity mismatch")

    compare_staged_derivation(
        source_world=source_world,
        staged_world=staged_world,
        activation=activation,
        activation_relative=activation_relative,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=output.name + ".tmp-", dir=output.parent)
    )
    try:
        shutil.copytree(staged_root, temporary, dirs_exist_ok=True, symlinks=True)
        capsule_item = next(
            item
            for item in staged_world["manifest"]["capsules"]
            if item["id"] == capsule_id
        )
        record_path = temporary / capsule_item["path"] / activation_relative
        activated = deepcopy(activation)
        activated["status"] = "activated"
        activated["activationHash"] = compute_activation_hash(activated)
        schema_check(
            activated,
            load_activation_schema(contracts_root),
            "activated source proposal record",
        )
        record_path.write_bytes(canonical_json(activated))
        validate_world(temporary, contracts_root)
        if output.exists():
            output.rmdir()
        temporary.replace(output)
        return activated
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def compare_staged_derivation(
    *,
    source_world: dict[str, Any],
    staged_world: dict[str, Any],
    activation: dict[str, Any],
    activation_relative: str,
) -> None:
    source_root: Path = source_world["root"]
    staged_root: Path = staged_world["root"]
    capsule_id = activation["capsuleId"]
    source_capsule = source_world["capsules"].get(capsule_id)
    staged_capsule = staged_world["capsules"].get(capsule_id)
    if source_capsule is None or staged_capsule is None:
        raise SourcePipelineError("activation capsule is missing")

    source_manifest = source_capsule["manifest"]
    staged_manifest = staged_capsule["manifest"]
    if source_manifest["version"] != activation["oldCapsuleVersion"]:
        raise SourcePipelineError("source capsule version changed after staging")
    if staged_manifest["version"] != activation["newCapsuleVersion"]:
        raise SourcePipelineError("staged capsule version mismatch")

    assertion_relative = prepared_assertion_path(source_manifest)
    if prepared_assertion_path(staged_manifest) != assertion_relative:
        raise SourcePipelineError("prepared assertions path changed during staging")

    capsule_item = next(
        item
        for item in source_world["manifest"]["capsules"]
        if item["id"] == capsule_id
    )
    capsule_manifest_relative = (
        Path(capsule_item["path"]) / "capsule.json"
    ).as_posix()
    assertion_world_relative = (
        Path(capsule_item["path"]) / assertion_relative
    ).as_posix()
    activation_world_relative = (
        Path(capsule_item["path"]) / activation_relative
    ).as_posix()

    expected_capsule_manifest = deepcopy(source_manifest)
    expected_capsule_manifest["version"] = activation["newCapsuleVersion"]
    expected_entry = {
        "path": activation_relative,
        "kind": "other",
        "description": (
            "Source proposal activation record for "
            f"{activation['proposalId']}."
        ),
    }
    expected_capsule_manifest["preparedFiles"].append(expected_entry)
    if staged_manifest != expected_capsule_manifest:
        raise SourcePipelineError(
            "staged capsule manifest contains changes outside activation"
        )

    source_assertions = json_lines(
        declared_file(
            source_capsule["root"],
            assertion_relative,
            "source prepared assertions",
        ),
        "source prepared assertions",
    )
    staged_assertions = json_lines(
        declared_file(
            staged_capsule["root"],
            assertion_relative,
            "staged prepared assertions",
        ),
        "staged prepared assertions",
    )
    if staged_assertions[: len(source_assertions)] != source_assertions:
        raise SourcePipelineError("existing assertions changed during staging")
    added = staged_assertions[len(source_assertions) :]
    added_ids = [item["assertionId"] for item in added]
    if added_ids != activation["assertionIds"]:
        raise SourcePipelineError("staged assertion set does not match activation")
    if len({item["assertionId"] for item in staged_assertions}) != len(
        staged_assertions
    ):
        raise SourcePipelineError("staged assertions contain duplicate IDs")

    allowed = {
        capsule_manifest_relative,
        assertion_world_relative,
        activation_world_relative,
    }
    module_updates = {
        item["moduleId"]: item for item in activation["modules"]
    }
    if len(module_updates) != len(activation["modules"]):
        raise SourcePipelineError("activation contains duplicate module IDs")
    source_modules = {
        item["id"]: item for item in source_world["manifest"]["modules"]
    }
    staged_modules = {
        item["id"]: item for item in staged_world["manifest"]["modules"]
    }
    if source_modules != staged_modules:
        raise SourcePipelineError("world module registry changed during staging")

    for module_id, module_item in source_modules.items():
        relative = (Path(module_item["path"]) / "module.json").as_posix()
        source_module = json_object(
            source_root / relative,
            f"source module {module_id}",
        )
        staged_module = json_object(
            staged_root / relative,
            f"staged module {module_id}",
        )
        expected_module = deepcopy(source_module)
        update = module_updates.get(module_id)
        matching = [
            item
            for item in expected_module["usesCapsules"]
            if item["id"] == capsule_id
        ]
        if update is None:
            if matching:
                raise SourcePipelineError(
                    f"activation omits dependent module {module_id}"
                )
        else:
            if (
                update["oldVersion"] != source_module["version"]
                or update["newVersion"] != staged_module["version"]
            ):
                raise SourcePipelineError(
                    f"activation module version mismatch: {module_id}"
                )
            expected_module["version"] = update["newVersion"]
            if not matching:
                raise SourcePipelineError(
                    f"activation lists unrelated module {module_id}"
                )
            for dependency in matching:
                if dependency["version"] != activation["oldCapsuleVersion"]:
                    raise SourcePipelineError(
                        f"source module dependency mismatch: {module_id}"
                    )
                dependency["version"] = activation["newCapsuleVersion"]
        if staged_module != expected_module:
            raise SourcePipelineError(
                f"staged module contains unrelated changes: {module_id}"
            )
        if update is not None:
            allowed.add(relative)

    compare_world_file_sets(
        source_root=source_root,
        staged_root=staged_root,
        allowed_changes=allowed,
        required_added={activation_world_relative},
    )


def compare_world_file_sets(
    *,
    source_root: Path,
    staged_root: Path,
    allowed_changes: set[str],
    required_added: set[str],
) -> None:
    source_files = {
        path.relative_to(source_root).as_posix(): path
        for path in source_root.rglob("*")
        if path.is_file()
    }
    staged_files = {
        path.relative_to(staged_root).as_posix(): path
        for path in staged_root.rglob("*")
        if path.is_file()
    }
    added = set(staged_files) - set(source_files)
    removed = set(source_files) - set(staged_files)
    if added != required_added or removed:
        raise SourcePipelineError(
            "staged world file set mismatch; "
            f"added={sorted(added)}, removed={sorted(removed)}"
        )
    for relative in sorted(set(source_files).intersection(staged_files)):
        if relative in allowed_changes:
            continue
        if source_files[relative].read_bytes() != staged_files[relative].read_bytes():
            raise SourcePipelineError(
                f"unrelated staged file changed: {relative}"
            )


def find_activation_record(
    staged_world: dict[str, Any],
    activation_id: str,
    contracts_root: Path,
) -> tuple[str, str, dict[str, Any]]:
    relative = f"activations/{activation_id}.json"
    matches: list[tuple[str, str, dict[str, Any]]] = []
    schema = load_activation_schema(contracts_root)
    for capsule_id, capsule in staged_world["capsules"].items():
        declared = {
            item["path"] for item in capsule["manifest"]["preparedFiles"]
        }
        if relative not in declared:
            continue
        record = json_object(
            declared_file(capsule["root"], relative, "activation record"),
            "activation record",
        )
        schema_check(record, schema, "source proposal activation record")
        matches.append((capsule_id, relative, record))
    if len(matches) != 1:
        raise SourcePipelineError(
            f"expected exactly one activation record {activation_id}, "
            f"found {len(matches)}"
        )
    return matches[0]


def prepared_assertion_path(capsule_manifest: dict[str, Any]) -> str:
    entries = [
        item
        for item in capsule_manifest["preparedFiles"]
        if item["kind"] == "assertions"
    ]
    if len(entries) != 1:
        raise SourcePipelineError(
            "activation requires exactly one prepared assertions file"
        )
    return entries[0]["path"]


def load_activation_schema(contracts_root: Path) -> dict[str, Any]:
    return json_object(
        contracts_root / "source-proposal-activation-record-v0.schema.json",
        "source proposal activation schema",
    )


def compute_activation_hash(activation: dict[str, Any]) -> str:
    payload = deepcopy(activation)
    payload.pop("activationHash", None)
    return domain_hash(ACTIVATION_DOMAIN, payload)


def verify_activation_hash(activation: dict[str, Any]) -> None:
    supplied = activation.get("activationHash")
    if supplied != compute_activation_hash(activation):
        raise SourcePipelineError("source proposal activation hash mismatch")


def require_empty_output(output: Path) -> None:
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise SourcePipelineError(
            f"activation output must be absent or empty: {output}"
        )


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
