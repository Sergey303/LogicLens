#!/usr/bin/env python3
"""Resolve and invoke the runtime selected by deployment/current.json."""

from transactional_runtime.cli import run_entry


if __name__ == "__main__":
    raise SystemExit(run_entry())
