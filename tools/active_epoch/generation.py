from __future__ import annotations

import subprocess
from pathlib import Path

from .contract import DATA_PROJECT, ONTOLOGY_PROJECT
from .hashing import BuildError


def run_compilers(
    repository_root: Path,
    data_output: Path,
    ontology_output: Path,
    epoch: int,
    data_commit: str,
    ontology_commit: str,
    no_build: bool,
) -> None:
    run_data_compiler(
        repository_root,
        data_output,
        epoch,
        data_commit,
        no_build,
    )
    run_ontology_compiler(
        repository_root,
        ontology_output,
        ontology_commit,
        no_build,
    )


def run_data_compiler(
    repository_root: Path,
    output: Path,
    epoch: int,
    compiler_commit: str,
    no_build: bool,
) -> None:
    command = dotnet_run_prefix(no_build) + [
        "--project",
        str(repository_root / DATA_PROJECT),
        "--configuration",
        "Release",
        "--",
        "--repository-root",
        str(repository_root),
        "--output",
        str(output),
        "--compiler-commit",
        compiler_commit,
        "--epoch",
        str(epoch),
    ]
    run(command, repository_root, "data compiler")


def run_ontology_compiler(
    repository_root: Path,
    output: Path,
    compiler_commit: str,
    no_build: bool,
) -> None:
    command = dotnet_run_prefix(no_build) + [
        "--project",
        str(repository_root / ONTOLOGY_PROJECT),
        "--configuration",
        "Release",
        "--",
        "--repository-root",
        str(repository_root),
        "--output",
        str(output),
        "--compiler-commit",
        compiler_commit,
    ]
    run(command, repository_root, "ontology compiler")


def dotnet_run_prefix(no_build: bool) -> list[str]:
    result = ["dotnet", "run"]
    if no_build:
        result.append("--no-build")
    return result


def run(command: list[str], cwd: Path, name: str) -> None:
    try:
        completed = subprocess.run(command, cwd=cwd, check=False)
    except OSError as exc:
        raise BuildError(f"could not start {name}: {exc}") from exc
    if completed.returncode != 0:
        raise BuildError(f"{name} failed with exit code {completed.returncode}")
