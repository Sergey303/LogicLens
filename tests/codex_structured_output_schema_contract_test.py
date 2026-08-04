#!/usr/bin/env python3
"""Fail closed when a Codex output schema leaves the supported strict subset."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts" / "progressive-management-codex-response-v0.schema.json"

ALLOWED_KEYS = {
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "enum",
    "const",
    "description",
}
PRIMITIVE_TYPES = {"string", "boolean", "integer", "number", "null"}


def fail(message: str) -> None:
    raise AssertionError(message)


def validate_node(node: Any, path: str) -> None:
    if not isinstance(node, dict):
        fail(f"{path}: schema node must be an object")

    unsupported = sorted(set(node) - ALLOWED_KEYS)
    if unsupported:
        fail(f"{path}: unsupported strict-output keywords: {unsupported}")

    declared_type = node.get("type")
    if not isinstance(declared_type, str):
        fail(f"{path}: every schema node must declare an explicit type")

    if declared_type == "object":
        properties = node.get("properties")
        required = node.get("required")
        if not isinstance(properties, dict):
            fail(f"{path}: object must declare properties")
        if node.get("additionalProperties") is not False:
            fail(f"{path}: object must set additionalProperties=false")
        if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
            fail(f"{path}: object must declare a string required list")
        if set(required) != set(properties):
            fail(f"{path}: every property must be required in strict output schemas")
        for name, child in properties.items():
            validate_node(child, f"{path}.properties.{name}")
        return

    if declared_type == "array":
        if "items" not in node:
            fail(f"{path}: array must declare items")
        validate_node(node["items"], f"{path}.items")
        return

    if declared_type not in PRIMITIVE_TYPES:
        fail(f"{path}: unsupported type {declared_type!r}")

    enum = node.get("enum")
    if enum is not None:
        if not isinstance(enum, list) or not enum:
            fail(f"{path}: enum must be a non-empty array")
        if any(not isinstance(value, str) for value in enum):
            fail(f"{path}: this response contract only permits string enums")

    if "const" in node and not isinstance(node["const"], str):
        fail(f"{path}: this response contract only permits string const values")


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validate_node(schema, "root")

    expected = {
        "schemaVersion",
        "answer",
        "epistemicStatus",
        "action",
        "conclusionStrength",
        "abstain",
        "usedVerifiedFrame",
        "evidenceIds",
        "proofNodeIds",
        "warnings",
        "scopeStatement",
    }
    actual = set(schema["properties"])
    if actual != expected:
        fail(f"response field set changed: expected {sorted(expected)}, got {sorted(actual)}")

    print("Codex structured-output schema contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
