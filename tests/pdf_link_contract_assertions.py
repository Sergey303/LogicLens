"""Assertions for selected-evidence-only PDF proposal packages."""

from __future__ import annotations

from typing import Any


def assert_selected_retention(package: dict[str, Any]) -> None:
    """Reject packages that retain full PDF processing artifacts."""
    paths = {item["path"] for item in package["files"]}
    forbidden = {
        "document/canonical-document-ir.json",
        "fragments/fragments.jsonl",
        "extraction/extraction-request.json",
    }
    leaked = paths & forbidden
    if leaked or any(path.endswith(".pdf") for path in paths):
        raise AssertionError(f"no-source-retention violated: {sorted(leaked)}")
    if "evidence/selected-fragments.jsonl" not in paths:
        raise AssertionError("selected evidence was not retained")
