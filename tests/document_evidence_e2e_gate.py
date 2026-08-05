#!/usr/bin/env python3
# Copyright (c) 2026 Sergey Leshtaev
"""CLI for the ENG-148 client-selected PDF evidence gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from document_evidence_e2e_gate_runtime import run


def arguments() -> argparse.Namespace:
    """Parse explicit service and output artifact paths."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--fragment", type=Path, required=True)
    parser.add_argument("--service-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    """Run the deterministic proposal and SWI-Prolog gate."""
    args = arguments()
    run(args.fragment, args.service_receipt, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
