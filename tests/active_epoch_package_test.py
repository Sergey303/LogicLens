#!/usr/bin/env python3
"""Verify deterministic and portable LogicLens active epoch packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


UTF8 = "utf-8"
RUNTIME_FILES = (
    PurePosixPath("entry.pl"),
    PurePosixPath("data/epoch_data.pl"),
    PurePosixPath("ontology/ontology_data.pl"),
    PurePosixPath("rules/cli_runtime.pl"),
    PurePosixPath("rules/generic_view.pl"),
    PurePosixPath("rules/label_rules.pl"),
    PurePosixPath("rules/subgraph.pl"),
    PurePosixPath("rules/traversal_policy.pl"),
    PurePosixPath("rules/view_policy.pl"),
)
SMOKE_FILES = (
    "health.request.json",
    "entity-view.request.json",
    "subgraph.request.json",
)


class VerificationError(AssertionError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", required=True, type=Path)
    parser.add_argument("--second", required=True, type=Path)
    parser.add_argument("--run-smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    first = args.first.resolve()
    second = args.second.resolve()
    first_files = tree(first)
    second_files = tree(second)
    equal(first_files, second_files, "package trees must be byte-identical")
    manifest = verify_manifest(first, first_files)
    verify_portability_boundary(first_files)
    if args.run_smoke:
        run_portable_smoke(first, manifest)
    print("Active epoch package verification passed.")
    return 0


def tree(root: Path) -> dict[PurePosixPath, bytes]:
    if not root.is_dir():
        raise VerificationError(f"package directory does not exist: {root}")
    result: dict[PurePosixPath, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise VerificationError(f"symlink is not allowed in package: {path}")
        if path.is_file():
            relative = PurePosixPath(path.relative_to(root).as_posix())
            result[relative] = path.read_bytes()
    return result


def verify_manifest(
    root: Path,
    all_files: dict[PurePosixPath, bytes],
) -> dict[str, Any]:
    manifest_path = PurePosixPath("manifest.json")
    if manifest_path not in all_files:
        raise VerificationError("manifest.json is missing")
    manifest = json.loads(all_files[manifest_path].decode(UTF8))
    if not isinstance(manifest, dict):
        raise VerificationError("manifest must be an object")
    equal(manifest.get("stage"), "active", "manifest stage")
    equal(manifest.get("epoch"), 0, "manifest epoch")
    equal(manifest.get("baseRevision"), 0, "manifest revision")
    equal(manifest.get("uiContractVersion"), "0.1", "UI contract version")
    equal(manifest.get("cliProtocolVersion"), "0.1", "CLI protocol version")
    if "manifest.json" in manifest.get("files", {}):
        raise VerificationError("manifest must not hash itself")

    payload = {path: content for path, content in all_files.items() if path != manifest_path}
    expected_hashes = {str(path): sha256(content) for path, content in payload.items()}
    equal(manifest.get("files"), expected_hashes, "per-file hashes")
    equal(
        manifest.get("packageHash"),
        aggregate_hash(b"LogicLensActiveEpoch\0", 1, payload.items()),
        "package hash",
    )
    equal(
        manifest.get("rulesHash"),
        aggregate_hash(
            b"LogicLensRules\0",
            1,
            ((path, payload[path]) for path in RUNTIME_FILES),
        ),
        "rules hash",
    )
    return manifest


def verify_portability_boundary(files: dict[PurePosixPath, bytes]) -> None:
    required = {
        PurePosixPath("entry.pl"),
        PurePosixPath("data/facts.generated.pl"),
        PurePosixPath("data/origins.generated.pl"),
        PurePosixPath("ontology/ontology.generated.pl"),
        PurePosixPath("contracts/prolog-cli-v0.schema.json"),
        *(PurePosixPath("smoke") / name for name in SMOKE_FILES),
        *RUNTIME_FILES,
    }
    missing = sorted(str(path) for path in required if path not in files)
    if missing:
        raise VerificationError(f"portable package files are missing: {missing}")
    forbidden = sorted(
        str(path)
        for path in files
        if path.suffix.lower() in {".fog", ".xml"}
        or any(part in {"archive", "bin", "obj"} for part in path.parts)
    )
    if forbidden:
        raise VerificationError(f"source/build files leaked into package: {forbidden}")


def run_portable_smoke(source: Path, manifest: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory(prefix="logiclens-portable-smoke-") as temporary:
        target = Path(temporary) / "epoch-000"
        shutil.copytree(source, target)
        for filename in SMOKE_FILES:
            request = (target / "smoke" / filename).read_text(encoding=UTF8)
            completed = subprocess.run(
                ["swipl", "-q", "-s", str(target / "entry.pl"), "--"],
                input=request,
                text=True,
                capture_output=True,
                cwd=target,
                check=False,
                timeout=15,
            )
            if completed.returncode != 0:
                raise VerificationError(
                    f"smoke {filename} failed: exit={completed.returncode}, "
                    f"stdout={completed.stdout!r}, stderr={completed.stderr!r}"
                )
            lines = [line for line in completed.stdout.splitlines() if line.strip()]
            if len(lines) != 1:
                raise VerificationError(
                    f"smoke {filename} returned {len(lines)} JSON lines"
                )
            response = json.loads(lines[0])
            equal(response.get("status"), "ok", f"smoke {filename} status")
            equal(response.get("epoch"), manifest["epoch"], f"smoke {filename} epoch")
            equal(
                response.get("revision"),
                manifest["baseRevision"],
                f"smoke {filename} revision",
            )


def sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def aggregate_hash(
    domain: bytes,
    version: int,
    files: Iterable[tuple[PurePosixPath, bytes]],
) -> str:
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(bytes((version,)))
    for path, content in sorted(files, key=lambda item: str(item[0])):
        append_field(digest, str(path).encode(UTF8))
        append_field(digest, content)
    return "sha256:" + digest.hexdigest()


def append_field(digest: Any, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big", signed=False))
    digest.update(value)


def equal(actual: Any, expected: Any, context: str) -> None:
    if actual != expected:
        raise VerificationError(
            f"{context}: expected {expected!r}, actual {actual!r}"
        )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        VerificationError,
        OSError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
