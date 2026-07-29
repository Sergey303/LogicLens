#!/usr/bin/env python3
"""Exercise the portable durable-copy helpers without SWI-Prolog."""
from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(
        "apply_builder_activation_transaction_portable",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    portable = load_module(
        repository
        / "tools"
        / "apply_builder_activation_transaction_portable.py"
    )

    if portable.core.copy_file_durable is portable.copy_file_durable:
        raise RuntimeError("portable helpers were installed before run_entry")

    with tempfile.TemporaryDirectory(
        prefix="logiclens-windows-fsync-"
    ) as temporary:
        root = Path(temporary)
        source = root / "source"
        target = root / "target"
        source.mkdir()
        target.mkdir()

        payloads = {
            "entry.pl": b":- initialization(main, main).\nmain :- halt.\n",
            "rules/example.pl": b"example(ok).\n",
            "metadata/example.json": b'{"ok":true}\n',
        }

        for relative, payload in payloads.items():
            path = source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

        for relative in sorted(payloads):
            source_path = source / relative
            target_path = target / relative
            target_path.parent.mkdir(parents=True, exist_ok=True)
            copied = portable.copy_file_durable(
                str(source_path),
                str(target_path),
            )
            if Path(copied).read_bytes() != payloads[relative]:
                raise RuntimeError(f"copied bytes differ: {relative}")

        portable.fsync_tree(target)

        for relative, payload in payloads.items():
            if (target / relative).read_bytes() != payload:
                raise RuntimeError(f"tree bytes differ: {relative}")

        portable.install_portable_sync()
        if portable.core.copy_file_durable is not portable.copy_file_durable:
            raise RuntimeError("portable copy helper was not installed")
        if portable.core.fsync_tree is not portable.fsync_tree:
            raise RuntimeError("portable tree helper was not installed")

        descriptor_modes: list[int] = []
        original_open = portable.os.open

        def recording_open(path, flags, *args, **kwargs):
            descriptor_modes.append(flags)
            return original_open(path, flags, *args, **kwargs)

        portable.os.open = recording_open
        try:
            portable.fsync_file(target / "entry.pl")
        finally:
            portable.os.open = original_open

        if not descriptor_modes:
            raise RuntimeError("fsync_file did not open a descriptor")
        if not all(flags & os.O_WRONLY for flags in descriptor_modes):
            raise RuntimeError(
                "fsync_file did not request writable access"
            )

    print(
        "Portable activation durable-copy helpers passed on "
        f"{os.name}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
