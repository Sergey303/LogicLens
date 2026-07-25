from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from .contract import CLI_SCHEMA, DATA_PROJECT, ONTOLOGY_PROJECT, SOURCE_EPOCH
from .generation import run_compilers
from .hashing import BuildError
from .package import (
    build_manifest,
    collect_package_files,
    verify_generated_manifest,
    write_package,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a deterministic portable LogicLens active epoch package."
    )
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--engine-commit", required=True)
    parser.add_argument("--data-compiler-commit")
    parser.add_argument("--ontology-compiler-commit")
    parser.add_argument("--epoch", type=int, default=0)
    parser.add_argument("--revision", type=int, default=0)
    parser.add_argument("--no-build", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.epoch != 0 or args.revision != 0:
        raise BuildError("the v0 active package builder supports only epoch 0, revision 0")

    root = (
        args.repository_root.resolve()
        if args.repository_root is not None
        else find_repository_root()
    )
    output = args.output.resolve()
    source_epoch = (root / SOURCE_EPOCH).resolve()
    require_repository(root)
    require_clean_output(output, source_epoch)

    data_commit = args.data_compiler_commit or args.engine_commit
    ontology_commit = args.ontology_compiler_commit or args.engine_commit
    require_nonempty("engine commit", args.engine_commit)
    require_nonempty("data compiler commit", data_commit)
    require_nonempty("ontology compiler commit", ontology_commit)

    with tempfile.TemporaryDirectory(prefix="logiclens-active-epoch-") as temporary:
        staging = Path(temporary)
        data_output = staging / "data-generated"
        ontology_output = staging / "ontology-generated"
        run_compilers(
            root,
            data_output,
            ontology_output,
            args.epoch,
            data_commit,
            ontology_commit,
            args.no_build,
        )
        files, data_manifest, ontology_manifest = collect_package_files(
            root,
            source_epoch,
            data_output,
            ontology_output,
        )
        verify_generated_manifest(
            data_manifest,
            data_output,
            expected_stage="data-generated",
            expected_commit=data_commit,
            expected_epoch=args.epoch,
        )
        verify_generated_manifest(
            ontology_manifest,
            ontology_output,
            expected_stage="ontology-generated",
            expected_commit=ontology_commit,
        )

    manifest = build_manifest(
        args.epoch,
        args.revision,
        args.engine_commit,
        data_commit,
        ontology_commit,
        data_manifest,
        ontology_manifest,
        files,
    )
    write_package(output, files, manifest)

    print(f"Built active epoch {args.epoch}, revision {args.revision}.")
    print(f"Files: {len(files)}")
    print(f"Package hash: {manifest['packageHash']}")
    print(f"Output: {output}")
    return 0


def find_repository_root() -> Path:
    for start in (Path.cwd(), Path(__file__).resolve().parent):
        for candidate in (start, *start.parents):
            if (candidate / "README.md").is_file() and (
                candidate / SOURCE_EPOCH / "entry.pl"
            ).is_file():
                return candidate
    raise BuildError(
        "Could not locate repository root; pass --repository-root explicitly."
    )


def require_repository(root: Path) -> None:
    required = (
        root / "README.md",
        root / DATA_PROJECT,
        root / ONTOLOGY_PROJECT,
        root / CLI_SCHEMA,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise BuildError(f"repository inputs are missing: {missing}")


def require_clean_output(output: Path, source_epoch: Path) -> None:
    if output == source_epoch or source_epoch in output.parents:
        raise BuildError(
            "output cannot be the reviewed source epoch directory or one of its children"
        )
    if output.exists():
        if not output.is_dir():
            raise BuildError(f"output exists and is not a directory: {output}")
        if any(output.iterdir()):
            raise BuildError(f"output directory must be empty: {output}")
    else:
        output.mkdir(parents=True)


def require_nonempty(name: str, value: str) -> None:
    if not value.strip():
        raise BuildError(f"{name} cannot be empty")


def run_entry() -> int:
    try:
        return main()
    except (BuildError, OSError, subprocess.SubprocessError) as exc:
        print(f"Active epoch build failed: {exc}", file=__import__("sys").stderr)
        return 1
