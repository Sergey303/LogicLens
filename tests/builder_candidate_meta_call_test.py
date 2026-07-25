#!/usr/bin/env python3
"""Reject higher-order attempts to invoke forbidden Prolog predicates."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--fixture", required=True, type=Path)
    return parser.parse_args()


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def digest_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    baseline = args.baseline.resolve()
    before = digest_tree(baseline)

    with tempfile.TemporaryDirectory(prefix="logiclens-builder-meta-call-") as temporary:
        root = Path(temporary)
        proposal = root / "proposal"
        shutil.copytree(args.fixture.resolve(), proposal)
        rule = proposal / "files" / "rules" / "candidate_member.pl"
        rule.write_text(
            ":- module(candidate_member, [candidate_member/1]).\n"
            ":- use_module('../data/epoch_data.pl').\n"
            "candidate_member(_) :- maplist(shell, ['echo forbidden']).\n",
            encoding="utf-8",
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(repository_root() / "tools" / "build_epoch_candidate.py"),
                "--baseline",
                str(baseline),
                "--proposal",
                str(proposal),
                "--schema",
                str(args.schema.resolve()),
                "--output",
                str(root / "candidate"),
                "--report",
                str(root / "comparison.json"),
            ],
            cwd=repository_root(),
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        combined = completed.stdout + completed.stderr
        if completed.returncode == 0:
            raise AssertionError("higher-order forbidden call was accepted")
        if "forbidden call" not in combined or "maplist(" not in combined:
            raise AssertionError(f"unexpected rejection output: {combined!r}")

    if digest_tree(baseline) != before:
        raise AssertionError("meta-call rejection modified the active baseline")

    print("ok 1 - higher-order forbidden call")
    print("1..1")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
