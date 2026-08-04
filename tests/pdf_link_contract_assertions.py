"""Assertions for selected-evidence-only PDF proposal packages."""

from __future__ import annotations

from typing import Any

SELECTED_EVIDENCE_MISSING = "selected evidence was not retained"


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
        message = f"no-source-retention violated: {sorted(leaked)}"
        raise AssertionError(message)
    if "evidence/selected-fragments.jsonl" not in paths:
        raise AssertionError(SELECTED_EVIDENCE_MISSING)
