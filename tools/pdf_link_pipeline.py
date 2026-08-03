#!/usr/bin/env python3
"""Ephemerally read public PDF links into a LogicLens source proposal workspace."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from capsule import CapsuleError
from source_proposal import SourcePipelineError, load_schemas
from source_proposal.pdf_link import ingest_pdf_link, load_pdf_schemas, resolve_pdf_seed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contracts-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "contracts",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    ingest = commands.add_parser("ingest")
    ingest.add_argument("--world-root", required=True, type=Path)
    ingest.add_argument("--capsule", required=True)
    ingest.add_argument("--source", required=True)
    ingest.add_argument("--proposal-id", required=True)
    ingest.add_argument("--output", required=True, type=Path)
    ingest.add_argument("--max-bytes", type=int, default=32 * 1024 * 1024)
    ingest.add_argument("--poppler-prefix")

    seed = commands.add_parser("resolve-seed")
    seed.add_argument("--proposal", required=True, type=Path)
    seed.add_argument("--seed", required=True, type=Path)
    seed.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schemas = load_schemas(args.contracts_root)
    pdf_schemas = load_pdf_schemas(args.contracts_root)
    if args.command == "ingest":
        workspace = ingest_pdf_link(
            world_root=args.world_root,
            capsule_id=args.capsule,
            source_id=args.source,
            proposal_id=args.proposal_id,
            output=args.output,
            max_bytes=args.max_bytes,
            poppler_prefix=args.poppler_prefix,
            schemas=schemas,
            pdf_schemas=pdf_schemas,
            contracts_root=args.contracts_root,
        )
        snapshot = workspace["artifacts"]["snapshot"]
        print(f"Read PDF ephemerally: {workspace['sourceId']}")
        print(f"Fragments: {workspace['artifacts']['fragments']['count']}")
        print(f"Snapshot hash: {snapshot['hash']}")
        print("Original PDF retained: no")
        return 0

    candidate, review = resolve_pdf_seed(
        proposal_root=args.proposal,
        seed_path=args.seed,
        output=args.output,
        schemas=schemas,
        pdf_schemas=pdf_schemas,
    )
    print(f"Resolved PDF seed: {len(candidate['assertions'])} assertions")
    print(f"Review decisions: {len(review['decisions'])}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SourcePipelineError, CapsuleError, OSError, ValueError) as exc:
        print(f"PDF link pipeline failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
