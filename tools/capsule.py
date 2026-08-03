#!/usr/bin/env python3
"""Validate, compile and verify LogicLens knowledge capsules."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

UTF8 = "utf-8"
SHA = "sha256:"
PACKAGE_DOMAIN = b"LogicLensCapsulePackage\0"
GROUP_DOMAIN = b"LogicLensCapsuleGroup\0"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SCHEMAS = {
    "world": "knowledge-world-v0.schema.json",
    "capsule": "capsule-v0.schema.json",
    "module": "learning-module-v0.schema.json",
    "sources": "source-manifest-v0.schema.json",
    "assertion": "prepared-assertion-v0.schema.json",
}
FORBIDDEN_PROLOG = tuple(
    re.compile(pattern, re.I)
    for pattern in (
        r"\bshell\s*\(", r"\bprocess_create\s*\(", r"\bopen\s*\(",
        r"\bdelete_file\s*\(", r"\brename_file\s*\(", r"\bmake_directory",
        r"\bconsult\s*\(", r"\bload_files\s*\(", r"\bassert(?:a|z)?\s*\(",
        r"\bretract(?:all)?\s*\(", r"\babolish\s*\(", r"\bhttp_open\s*\(",
        r"\btcp_connect\s*\(",
    )
)


class CapsuleError(RuntimeError):
    pass


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contracts-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "contracts",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--world-root", required=True, type=Path)
    compile_command = commands.add_parser("compile")
    compile_command.add_argument("--world-root", required=True, type=Path)
    compile_command.add_argument("--capsule", required=True)
    compile_command.add_argument("--output", required=True, type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--package", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = arguments()
    if args.command == "verify":
        package = verify_package(args.package)
        print(f"Verified capsule package: {package['capsule']['id']}")
        print(f"Package hash: {package['packageHash']}")
        return 0

    world = validate_world(args.world_root, args.contracts_root)
    if args.command == "validate":
        print(f"Validated world: {world['manifest']['worldId']}")
        print(f"Capsules: {len(world['capsules'])}")
        print(f"Modules: {len(world['modules'])}")
        return 0

    package = compile_capsule(world, args.capsule, args.output)
    print(f"Compiled capsule: {package['capsule']['id']}")
    print(f"Package hash: {package['packageHash']}")
    print(f"Output: {args.output.resolve()}")
    return 0


def validate_world(world_root: Path, contracts_root: Path) -> dict[str, Any]:
    root = world_root.resolve()
    if not root.is_dir():
        raise CapsuleError(f"world root does not exist: {root}")
    schemas = {
        name: json_object(contracts_root / filename, f"{name} schema")
        for name, filename in SCHEMAS.items()
    }
    manifest = json_object(root / "world.json", "world manifest")
    schema_check(manifest, schemas["world"], "world manifest")
    if not SAFE_ID.fullmatch(manifest["worldId"]):
        raise CapsuleError("unsafe world ID")
    for relative in manifest["semantic"].values():
        json_value(declared_file(root, relative, "semantic file"), relative)

    capsules: dict[str, dict[str, Any]] = {}
    for item in manifest["capsules"]:
        capsule_id = item["id"]
        if capsule_id in capsules:
            raise CapsuleError(f"duplicate capsule ID: {capsule_id}")
        capsule_root = declared_directory(root, item["path"], "capsule")
        capsule = json_object(capsule_root / "capsule.json", capsule_id)
        schema_check(capsule, schemas["capsule"], capsule_id)
        if capsule["capsuleId"] != capsule_id or capsule["worldId"] != manifest["worldId"]:
            raise CapsuleError(f"capsule identity mismatch: {capsule_id}")
        source_path = declared_file(capsule_root, capsule["sourceManifest"], "source manifest")
        sources = json_object(source_path, "source manifest")
        schema_check(sources, schemas["sources"], "source manifest")
        if sources["capsuleId"] != capsule_id:
            raise CapsuleError("source manifest capsule mismatch")
        source_ids = [item["id"] for item in sources["sources"]]
        if len(source_ids) != len(set(source_ids)):
            raise CapsuleError(f"duplicate source ID in {capsule_id}")
        validate_capsule_files(capsule_root, capsule, set(source_ids), schemas["assertion"])
        capsules[capsule_id] = {"root": capsule_root, "manifest": capsule, "sources": sources}

    modules: dict[str, dict[str, Any]] = {}
    for item in manifest["modules"]:
        module_id = item["id"]
        module_root = declared_directory(root, item["path"], "module")
        module = json_object(module_root / "module.json", module_id)
        schema_check(module, schemas["module"], module_id)
        if module["moduleId"] != module_id or module["worldId"] != manifest["worldId"]:
            raise CapsuleError(f"module identity mismatch: {module_id}")
        for dependency in module["usesCapsules"]:
            referenced = capsules.get(dependency["id"])
            if referenced is None:
                raise CapsuleError(f"{module_id} references unknown capsule {dependency['id']}")
            if referenced["manifest"]["version"] != dependency["version"]:
                raise CapsuleError(f"{module_id} capsule version mismatch")
        for relative in (
            [module["entry"]] + module["sequence"] + module["scenarios"] + module["rubrics"]
        ):
            declared_file(module_root, relative, f"module file in {module_id}")
        modules[module_id] = module
    known_modules = set(modules)
    for track in manifest["tracks"]:
        unknown = set(track["moduleIds"]) - known_modules
        if unknown:
            raise CapsuleError(f"track {track['id']} has unknown modules: {sorted(unknown)}")
    return {
        "root": root,
        "manifest": manifest,
        "capsules": capsules,
        "modules": modules,
        "schemas": schemas,
    }


def validate_capsule_files(
    root: Path,
    capsule: dict[str, Any],
    source_ids: set[str],
    assertion_schema: dict[str, Any],
) -> None:
    seen = {"capsule.json", capsule["sourceManifest"]}
    for group in ("preparedFiles", "ruleFiles", "learningFiles", "testFiles"):
        for entry in capsule[group]:
            relative = entry["path"]
            if relative in seen:
                raise CapsuleError(f"duplicate capsule path: {relative}")
            seen.add(relative)
            path = declared_file(root, relative, group)
            suffix = path.suffix.lower()
            if suffix == ".json":
                json_value(path, relative)
            elif suffix == ".jsonl":
                rows = json_lines(path, relative)
                if entry["kind"] == "assertions":
                    for index, row in enumerate(rows, 1):
                        schema_check(row, assertion_schema, f"{relative}:{index}")
                        for provenance in row["provenance"]:
                            source_id = provenance.split("#", 1)[0]
                            if source_id not in source_ids:
                                raise CapsuleError(
                                    f"{relative}:{index} unknown source {source_id}"
                                )
            elif suffix == ".pl":
                text = text_value(path, relative)
                for forbidden in FORBIDDEN_PROLOG:
                    if forbidden.search(text):
                        raise CapsuleError(
                            f"{relative} contains forbidden Prolog: {forbidden.pattern}"
                        )
            elif suffix not in {".md", ".txt"}:
                raise CapsuleError(f"unsupported capsule file type: {relative}")


def compile_capsule(world: dict[str, Any], capsule_id: str, output_path: Path) -> dict[str, Any]:
    capsule = world["capsules"].get(capsule_id)
    if capsule is None:
        raise CapsuleError(f"unknown capsule: {capsule_id}")
    output = output_path.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise CapsuleError(f"output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    files_root = output / "files"
    files: list[dict[str, str]] = []
    groups: dict[str, list[tuple[str, str]]] = {
        name: [] for name in (
            "sources", "prepared", "semantic", "rules", "learning",
            "tests", "manifests", "generated"
        )
    }

    world_paths = ["world.json", *world["manifest"]["semantic"].values()]
    for relative in world_paths:
        category = "manifests" if relative == "world.json" else "semantic"
        add_file(
            world["root"] / relative,
            files_root / "world" / relative,
            f"world/{relative}",
            category,
            files,
            groups,
        )

    capsule_paths: list[tuple[str, str]] = [
        ("capsule.json", "manifests"),
        (capsule["manifest"]["sourceManifest"], "sources"),
    ]
    for key, category in (
        ("preparedFiles", "prepared"),
        ("ruleFiles", "rules"),
        ("learningFiles", "learning"),
        ("testFiles", "tests"),
    ):
        capsule_paths.extend((entry["path"], category) for entry in capsule["manifest"][key])
    for relative, category in capsule_paths:
        add_file(
            capsule["root"] / relative,
            files_root / "capsule" / relative,
            f"capsule/{relative}",
            category,
            files,
            groups,
        )

    generated_relative = "generated/assertions.pl"
    generated_content = normalized_text(generate_assertions(capsule))
    generated_path = files_root / generated_relative
    generated_path.parent.mkdir(parents=True, exist_ok=True)
    generated_path.write_bytes(generated_content)
    generated_hash = sha256(generated_content)
    files.append({"path": generated_relative, "sha256": generated_hash})
    groups["generated"].append((generated_relative, generated_hash))

    files.sort(key=lambda item: item["path"])
    package: dict[str, Any] = {
        "schemaVersion": "0.1",
        "world": {"id": world["manifest"]["worldId"], "title": world["manifest"]["title"]},
        "capsule": {
            "id": capsule_id,
            "version": capsule["manifest"]["version"],
            "title": capsule["manifest"]["title"],
        },
        "files": files,
    }
    package["packageHash"] = domain_hash(PACKAGE_DOMAIN, package)
    lock = {
        "schemaVersion": "0.1",
        "worldId": world["manifest"]["worldId"],
        "capsuleId": capsule_id,
        "capsuleVersion": capsule["manifest"]["version"],
        "sourceManifestHash": group_hash(groups["sources"]),
        "preparedDataHash": group_hash(groups["prepared"]),
        "semanticModelHash": group_hash(groups["semantic"]),
        "rulesHash": group_hash(groups["rules"]),
        "learningHash": group_hash(groups["learning"]),
        "testsHash": group_hash(groups["tests"]),
        "generatedHash": group_hash(groups["generated"]),
        "packageHash": package["packageHash"],
    }
    (output / "capsule-package.json").write_bytes(canonical_json(package))
    (output / "capsule.lock.json").write_bytes(canonical_json(lock))
    return package


def add_file(
    source: Path,
    destination: Path,
    package_relative: str,
    category: str,
    files: list[dict[str, str]],
    groups: dict[str, list[tuple[str, str]]],
) -> None:
    if not source.is_file():
        raise CapsuleError(f"declared package file is missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() == ".json":
        content = canonical_json(json_value(source, str(source)))
    elif source.suffix.lower() == ".jsonl":
        content = b"".join(canonical_json(row) for row in json_lines(source, str(source)))
    else:
        content = normalized_text(text_value(source, str(source)))
    destination.write_bytes(content)
    file_hash = sha256(content)
    files.append({"path": package_relative, "sha256": file_hash})
    groups[category].append((package_relative, file_hash))


def verify_package(package_root: Path) -> dict[str, Any]:
    root = package_root.resolve()
    package = json_object(root / "capsule-package.json", "capsule package")
    lock = json_object(root / "capsule.lock.json", "capsule lock")
    supplied = package.get("packageHash")
    payload = dict(package)
    payload.pop("packageHash", None)
    if supplied != domain_hash(PACKAGE_DOMAIN, payload):
        raise CapsuleError("package hash mismatch")
    if lock.get("packageHash") != supplied:
        raise CapsuleError("lock package hash mismatch")
    files_root = root / "files"
    expected: set[str] = set()
    for record in package.get("files", []):
        relative = record.get("path")
        if not isinstance(relative, str) or relative in expected:
            raise CapsuleError(f"invalid package file record: {relative!r}")
        expected.add(relative)
        path = declared_file(files_root, relative, "package file")
        if sha256(path.read_bytes()) != record.get("sha256"):
            raise CapsuleError(f"package file hash mismatch: {relative}")
    actual = {
        path.relative_to(files_root).as_posix()
        for path in files_root.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        raise CapsuleError(
            f"package file set mismatch; extra={sorted(actual-expected)}, "
            f"missing={sorted(expected-actual)}"
        )
    return package


def generate_assertions(capsule: dict[str, Any]) -> str:
    rows: list[dict[str, Any]] = []
    for entry in capsule["manifest"]["preparedFiles"]:
        if entry["kind"] == "assertions":
            rows.extend(json_lines(capsule["root"] / entry["path"], entry["path"]))
    lines = [
        ":- module(capsule_assertions, [prepared_assertion/6]).",
        "",
        "% Generated from prepared assertion JSONL.",
        "% Absence is not negative evidence.",
        "",
    ]
    for row in sorted(rows, key=lambda item: item["assertionId"]):
        target = row["target"]
        term = (
            atom(target["predicate"]) + "("
            + ", ".join(prolog_value(value) for value in target["arguments"])
            + ")"
        )
        provenance = "[" + ", ".join(atom(value) for value in row["provenance"]) + "]"
        lines.append(
            "prepared_assertion("
            + ", ".join(
                (
                    atom(row["assertionId"]),
                    term,
                    atom(row["stance"]),
                    atom(row["dependencyGroup"]),
                    provenance,
                    atom(row["generalisability"]),
                )
            )
            + ")."
        )
    return "\n".join(lines) + "\n"


def prolog_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return atom(value)
    raise CapsuleError(f"unsupported Prolog value: {value!r}")


def atom(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def group_hash(records: list[tuple[str, str]]) -> str:
    digest = hashlib.sha256(GROUP_DOMAIN)
    for path, file_hash in sorted(records):
        digest.update(path.encode(UTF8) + b"\0" + file_hash.encode("ascii") + b"\0")
    return SHA + digest.hexdigest()


def domain_hash(domain: bytes, payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(domain + bytes((1,)) + canonical_json(payload))
    return SHA + digest.hexdigest()


def sha256(content: bytes) -> str:
    return SHA + hashlib.sha256(content).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode(UTF8)


def normalized_text(value: str) -> bytes:
    return (value.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n").encode(UTF8)


def schema_check(value: Any, schema: dict[str, Any], context: str) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: list(item.path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors[:10]
        )
        raise CapsuleError(f"{context} schema validation failed: {details}")


def relative_path(value: str, context: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise CapsuleError(f"{context} must be a POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CapsuleError(f"unsafe {context}: {value!r}")
    return path


def declared_file(root: Path, relative: str, context: str) -> Path:
    path = root.joinpath(*relative_path(relative, context).parts).resolve()
    within(root, path, context)
    if not path.is_file():
        raise CapsuleError(f"{context} does not exist: {path}")
    return path


def declared_directory(root: Path, relative: str, context: str) -> Path:
    path = root.joinpath(*relative_path(relative, context).parts).resolve()
    within(root, path, context)
    if not path.is_dir():
        raise CapsuleError(f"{context} does not exist: {path}")
    return path


def within(root: Path, path: Path, context: str) -> None:
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise CapsuleError(f"{context} escapes its root: {path}") from exc


def json_value(path: Path, context: str) -> Any:
    try:
        return json.loads(path.read_text(encoding=UTF8))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapsuleError(f"cannot read {context}: {exc}") from exc


def json_object(path: Path, context: str) -> dict[str, Any]:
    value = json_value(path, context)
    if not isinstance(value, dict):
        raise CapsuleError(f"{context} must be an object")
    return value


def json_lines(path: Path, context: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        for number, line in enumerate(path.read_text(encoding=UTF8).splitlines(), 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise CapsuleError(f"{context}:{number} must be an object")
            rows.append(value)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapsuleError(f"cannot read {context}: {exc}") from exc
    return rows


def text_value(path: Path, context: str) -> str:
    try:
        return path.read_text(encoding=UTF8)
    except (OSError, UnicodeDecodeError) as exc:
        raise CapsuleError(f"cannot read {context}: {exc}") from exc


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CapsuleError, OSError, ValueError) as exc:
        print(f"Capsule operation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
