#!/usr/bin/env python3
"""Diagnostic Ollama adapter with grammar-safe schema and retained HTTP errors."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import run_builder_ollama as base

RAW_ROOT: Path | None = None
HTTP_ERROR_BODY_LIMIT = 64 * 1024


def grammar_safe_response_schema(expected_paths: list[str]) -> dict[str, Any]:
    if len(expected_paths) != 3 or len(set(expected_paths)) != 3:
        raise base.OllamaAdapterError(
            "structured response requires three distinct file paths"
        )
    return {
        "type": "object",
        "properties": {
            "notes": {"type": "string"},
            "files": {
                "type": "object",
                "properties": {path: {"type": "string"} for path in expected_paths},
                "required": expected_paths,
                "additionalProperties": False,
            },
        },
        "required": ["files"],
        "additionalProperties": False,
    }


def raw_root_from_argv(argv: list[str]) -> Path:
    try:
        index = argv.index("--output")
        value = argv[index + 1]
    except (ValueError, IndexError) as exc:
        raise base.OllamaAdapterError("diagnostic adapter requires --output") from exc
    root = Path(value).resolve() / "raw"
    root.mkdir(parents=True, exist_ok=True)
    return root


def call_ollama_with_http_diagnostics(
    endpoint: str,
    payload: bytes,
    timeout: float,
) -> bytes:
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read(base.MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        body = exc.read(HTTP_ERROR_BODY_LIMIT + 1)
        truncated = len(body) > HTTP_ERROR_BODY_LIMIT
        if truncated:
            body = body[:HTTP_ERROR_BODY_LIMIT]
        decoded = body.decode("utf-8", errors="replace")
        message = decoded
        try:
            parsed = json.loads(decoded)
            if isinstance(parsed, dict) and isinstance(parsed.get("error"), str):
                message = parsed["error"]
        except json.JSONDecodeError:
            pass
        diagnostic = {
            "schemaVersion": "0.1",
            "status": "http-error",
            "statusCode": exc.code,
            "reason": str(exc.reason),
            "contentType": exc.headers.get("Content-Type") if exc.headers else None,
            "bodyBytes": len(body),
            "bodyTruncated": truncated,
            "error": message,
            "body": decoded,
        }
        if RAW_ROOT is not None:
            (RAW_ROOT / "provider-error.json").write_bytes(
                base.canonical_json_bytes(diagnostic)
            )
            (RAW_ROOT / "adapter-result.json").write_bytes(
                base.canonical_json_bytes(diagnostic)
            )
        raise base.OllamaAdapterError(
            f"Ollama HTTP {exc.code}: {message[:1000]}"
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise base.OllamaAdapterError(f"Ollama request failed: {exc}") from exc
    if len(content) > base.MAX_RESPONSE_BYTES:
        raise base.OllamaAdapterError("Ollama response exceeds the reviewed size limit")
    return content


def main() -> int:
    global RAW_ROOT
    RAW_ROOT = raw_root_from_argv(sys.argv[1:])
    base.build_response_schema = grammar_safe_response_schema
    base.call_ollama = call_ollama_with_http_diagnostics
    return base.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (base.OllamaAdapterError, OSError, json.JSONDecodeError) as exc:
        print(f"Ollama compatibility adapter failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
