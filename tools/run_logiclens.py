#!/usr/bin/env python3
"""Run LogicLens through the package selected by deployment/current.json."""

from transactional_runtime.stack import run_entry


if __name__ == "__main__":
    raise SystemExit(run_entry())
