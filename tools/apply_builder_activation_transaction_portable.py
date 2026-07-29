#!/usr/bin/env python3
"""Cross-platform entry point for the Builder activation transaction.

Windows rejects ``os.fsync`` for descriptors opened read-only. The original
transaction engine uses read-only descriptors while durably copying immutable
packages, which works on POSIX but fails with ``EBADF`` on Windows. This entry
point installs equivalent helpers that open regular files for binary write
access before flushing them, then delegates every command and contract check to
the reviewed transaction engine.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

TOOLS_DIRECTORY = str(Path(__file__).resolve().parent)
if TOOLS_DIRECTORY not in sys.path:
    sys.path.insert(0, TOOLS_DIRECTORY)

import apply_builder_activation_transaction as core


def fsync_file(path: Path) -> None:
    """Flush one existing regular file through a writable descriptor."""

    flags = os.O_WRONLY | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def copy_file_durable(source: str, destination: str) -> str:
    """Copy metadata and bytes, then durably flush the destination."""

    result = shutil.copy2(source, destination)
    fsync_file(Path(result))
    return result


def fsync_tree(root: Path) -> None:
    """Flush every file and, where supported, every directory in a tree."""

    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise core.ActivationTransactionError(
                f"symlink is forbidden: {path}"
            )
        if path.is_file():
            fsync_file(path)

    directories = [path for path in root.rglob("*") if path.is_dir()]
    for path in sorted(directories, reverse=True):
        core.fsync_directory(path)
    core.fsync_directory(root)


def install_portable_sync() -> None:
    core.copy_file_durable = copy_file_durable
    core.fsync_tree = fsync_tree


def run_entry() -> int:
    install_portable_sync()
    return core.run_entry()


if __name__ == "__main__":
    raise SystemExit(run_entry())
