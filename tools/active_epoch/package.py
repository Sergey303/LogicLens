from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any

from .contract import CLI_SCHEMA, RUNTIME_FILES, SMOKE_REQUESTS
from .hashing import (
    BuildError,
    aggregate_hash,
    canonical_json_bytes,
    read_json,
    required_string,
    sha256,
)


def collect_package_files(
    repository_root: Path,
    source_epoch: Path,
    data_output: Path,
    ontology_output: Path,
) -> tuple[dict[PurePosixPath, bytes], dict[str, Any], dict[str, Any]]:
    data_manifest = read_json(data_output / "manifest.json")
    ontology_manifest = read_json(ontology_output / "manifest.json")
    files: dict[PurePosixPath, bytes] = {}

    add_file(
        files,
        PurePosixPath("data/facts.generated.pl"),
        data_output / "data/facts.generated.pl",
    )
    add_file(
        files,
        PurePosixPath("data/origins.generated.pl"),
        data_output / "data/origins.generated.pl",
    )
    add_file(
        files,
        PurePosixPath("ontology/ontology.generated.pl"),
        ontology_output / "ontology.generated.pl",
    )
    add_bytes(
        files,
        PurePosixPath("metadata/data.manifest.json"),
        canonical_json_bytes(data_manifest),
    )
    add_bytes(
        files,
        PurePosixPath("metadata/ontology.manifest.json"),
        canonical_json_bytes(ontology_manifest),
    )

    for relative_path in RUNTIME_FILES:
        add_file(files, relative_path, source_epoch / relative_path)

    add_file(
        files,
        PurePosixPath("contracts/prolog-cli-v0.schema.json"),
        repository_root / CLI_SCHEMA,
    )
    for filename, request in SMOKE_REQUESTS:
        add_bytes(
            files,
            PurePosixPath("smoke") / filename,
            canonical_json_bytes(request),
        )

    return (
        dict(sorted(files.items(), key=lambda item: str(item[0]))),
        data_manifest,
        ontology_manifest,
    )


def verify_generated_manifest(
    manifest: dict[str, Any],
    output: Path,
    *,
    expected_stage: str,
    expected_commit: str,
    expected_epoch: int | None = None,
) -> None:
    if manifest.get("stage") != expected_stage:
        raise BuildError(
            f"generated manifest stage mismatch: expected {expected_stage!r}, "
            f"actual {manifest.get('stage')!r}"
        )
    if manifest.get("compilerCommit") != expected_commit:
        raise BuildError("generated manifest compilerCommit does not match request")
    if expected_epoch is not None and manifest.get("epoch") != expected_epoch:
        raise BuildError("generated data manifest epoch does not match request")

    declared_files = manifest.get("files")
    if not isinstance(declared_files, dict) or not declared_files:
        raise BuildError("generated manifest files map is missing or empty")
    for relative_path, expected_hash in declared_files.items():
        if not isinstance(relative_path, str) or not isinstance(expected_hash, str):
            raise BuildError("generated manifest contains an invalid file hash entry")
        source = output / Path(*PurePosixPath(relative_path).parts)
        if not source.is_file():
            raise BuildError(f"generated manifest file is missing: {source}")
        actual_hash = sha256(source.read_bytes())
        if actual_hash != expected_hash:
            raise BuildError(
                f"generated manifest hash mismatch for {relative_path}: "
                f"expected {expected_hash}, actual {actual_hash}"
            )


def build_manifest(
    epoch: int,
    revision: int,
    engine_commit: str,
    data_commit: str,
    ontology_commit: str,
    data_manifest: dict[str, Any],
    ontology_manifest: dict[str, Any],
    files: dict[PurePosixPath, bytes],
) -> dict[str, Any]:
    rules_hash = aggregate_hash(
        b"LogicLensRules\0",
        1,
        ((path, files[path]) for path in RUNTIME_FILES),
    )
    package_hash = aggregate_hash(
        b"LogicLensActiveEpoch\0",
        1,
        files.items(),
    )
    return {
        "epoch": epoch,
        "parentEpoch": None,
        "baseRevision": revision,
        "stage": "active",
        "engineCommit": engine_commit,
        "uiContractVersion": "0.1",
        "cliProtocolVersion": "0.1",
        "factContractVersion": "1",
        "factIdEncodingVersion": 1,
        "prologDataContractVersion": "1",
        "ontologyLabelContractVersion": "1",
        "occurrenceIdEncodingVersion": 1,
        "dataCompilerCommit": data_commit,
        "ontologyCompilerCommit": ontology_commit,
        "dataHash": required_string(data_manifest, "dataHash"),
        "ontologyHash": required_string(ontology_manifest, "packageHash"),
        "rulesHash": rules_hash,
        "packageHash": package_hash,
        "files": {str(path): sha256(content) for path, content in files.items()},
    }


def write_package(
    output: Path,
    files: dict[PurePosixPath, bytes],
    manifest: dict[str, Any],
) -> None:
    for relative_path, content in files.items():
        destination = safe_destination(output, relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    (output / "manifest.json").write_bytes(canonical_json_bytes(manifest))


def add_file(
    files: dict[PurePosixPath, bytes],
    path: PurePosixPath,
    source: Path,
) -> None:
    if not source.is_file():
        raise BuildError(f"package source file is missing: {source}")
    add_bytes(files, path, source.read_bytes())


def add_bytes(
    files: dict[PurePosixPath, bytes],
    path: PurePosixPath,
    content: bytes,
) -> None:
    validate_relative_path(path)
    if path in files:
        raise BuildError(f"duplicate package path: {path}")
    files[path] = content


def validate_relative_path(path: PurePosixPath) -> None:
    if (
        path.is_absolute()
        or not path.parts
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise BuildError(f"unsafe package path: {path}")


def safe_destination(root: Path, relative_path: PurePosixPath) -> Path:
    destination = (root / Path(*relative_path.parts)).resolve()
    if root != destination and root not in destination.parents:
        raise BuildError(f"package path escaped output directory: {relative_path}")
    return destination
