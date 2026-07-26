#!/usr/bin/env python3
"""Produce an epoch-candidate proposal from a frozen workspace via Codex CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from active_epoch.hashing import canonical_json_bytes
from run_builder_ollama import (
    MAX_RESPONSE_BYTES,
    UTF8,
    build_request,
    normalize_text,
    read_json,
    require_clean_output,
    validate_generated_files,
    validate_identifier,
)


MAX_EVENT_BYTES = 10 * 1024 * 1024


class CodexAdapterError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--timeout-seconds", type=float, default=900.0)
    parser.add_argument(
        "--response-file",
        type=Path,
        help="offline deterministic final Codex response used only for verification",
    )
    parser.add_argument(
        "--elapsed-ms",
        type=float,
        help="fixed elapsed value allowed only together with --response-file",
    )
    parser.add_argument("--manual-fixes", type=int, default=0)
    parser.add_argument("--cost-usd", type=float)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_identifier(args.run_id, "run ID")
    if not args.model or len(args.model) > 256:
        raise CodexAdapterError("model must be a non-empty string up to 256 characters")
    if args.timeout_seconds <= 0 or args.timeout_seconds > 3600:
        raise CodexAdapterError("timeout-seconds must be between 0 and 3600")
    if args.manual_fixes < 0:
        raise CodexAdapterError("manual-fixes cannot be negative")
    if args.cost_usd is not None and args.cost_usd < 0:
        raise CodexAdapterError("cost-usd cannot be negative")
    if args.elapsed_ms is not None and args.response_file is None:
        raise CodexAdapterError("elapsed-ms override requires response-file")
    if args.elapsed_ms is not None and args.elapsed_ms < 0:
        raise CodexAdapterError("elapsed-ms cannot be negative")

    workspace = args.workspace.resolve()
    output = args.output.resolve()
    if not workspace.is_dir():
        raise CodexAdapterError(f"workspace does not exist: {workspace}")
    if output == workspace or workspace in output.parents or output in workspace.parents:
        raise CodexAdapterError("output must not overlap the frozen workspace")
    require_clean_output(output)

    manifest = read_json(workspace / "workspace-manifest.json", "workspace manifest")
    task = read_json(workspace / "task.json", "task")
    if manifest.get("stage") != "builder-workspace":
        raise CodexAdapterError("input is not a frozen Builder workspace")
    if manifest.get("taskId") != task.get("taskId"):
        raise CodexAdapterError("workspace task identity mismatch")

    prompt = (workspace / "prompt.md").read_text(encoding=UTF8)
    evidence = [
        {
            "name": path.name,
            "content": read_json(path, f"evidence {path.name}"),
        }
        for path in sorted((workspace / "evidence").glob("*.json"))
    ]
    if not evidence:
        raise CodexAdapterError("workspace contains no evidence")

    provider_request = build_request(args.model, task, prompt, evidence)
    system_text = provider_request["messages"][0]["content"]
    user_text = provider_request["messages"][1]["content"]
    codex_prompt = (
        "# System constraints\n"
        + system_text
        + "\n\n# Provider task\n"
        + user_text
        + "\n\nDo not inspect any files or invoke any tools. "
        "Return only the JSON object required by the response schema."
    )
    response_schema = build_response_schema(task)
    workspace_before = hash_tree(workspace)

    raw_root = output / "raw"
    raw_root.mkdir(parents=True)
    (raw_root / "request.json").write_bytes(
        canonical_json_bytes(
            {
                "provider": "codex-cli",
                "model": args.model,
                "system": system_text,
                "prompt": user_text,
                "responseSchema": response_schema,
            }
        )
    )
    (raw_root / "response-schema.json").write_bytes(
        canonical_json_bytes(response_schema)
    )

    started = time.monotonic()
    if args.response_file is not None:
        response_path = args.response_file.resolve()
        if not response_path.is_file():
            raise CodexAdapterError(f"response-file does not exist: {response_path}")
        raw_response = response_path.read_bytes()
        event_bytes = b""
        cli_calls = 0
    else:
        raw_response, event_bytes, cli_calls = call_codex(
            args.codex,
            args.model,
            workspace,
            raw_root / "response-schema.json",
            raw_root / "last-message.json",
            codex_prompt,
            args.timeout_seconds,
        )
    measured_elapsed_ms = (time.monotonic() - started) * 1000.0
    elapsed_ms = args.elapsed_ms if args.elapsed_ms is not None else measured_elapsed_ms

    if len(raw_response) > MAX_RESPONSE_BYTES:
        raise CodexAdapterError("Codex final response exceeds the reviewed size limit")
    generated = decode_json(raw_response, "Codex final response")
    files = validate_generated_files(generated, task)
    if hash_tree(workspace) != workspace_before:
        raise CodexAdapterError("Codex changed the frozen workspace")

    proposal_root = output / "proposal"
    files_root = proposal_root / "files"
    for relative_path, content in files.items():
        destination = (files_root / relative_path).resolve()
        if files_root.resolve() not in destination.parents:
            raise CodexAdapterError(f"generated path escaped proposal: {relative_path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(normalize_text(content), encoding=UTF8, newline="\n")

    metrics: dict[str, int | float] = {
        "cliCalls": cli_calls,
        "manualFixes": args.manual_fixes,
        "elapsedMs": round(elapsed_ms, 3),
    }
    if args.cost_usd is not None:
        metrics["costUsd"] = args.cost_usd
    proposal = {
        "schemaVersion": "0.1",
        "candidateId": f"{args.run_id}-candidate",
        "taskId": task["taskId"],
        "base": task["base"],
        "provider": {
            "kind": "codex",
            "name": "codex-cli",
            "model": args.model,
            "runId": args.run_id,
        },
        "uiContractVersion": task["contracts"]["ui"],
        "cliProtocolVersion": task["contracts"]["cli"],
        "metrics": metrics,
        "files": [
            {"path": task["candidate"]["rulePath"], "kind": "rule"},
            {"path": task["candidate"]["testPath"], "kind": "test"},
            {"path": task["candidate"]["uiPath"], "kind": "ui"},
        ],
        "notes": generated.get("notes", ""),
    }
    (proposal_root / "proposal.json").write_bytes(canonical_json_bytes(proposal))
    (raw_root / "provider-output.json").write_bytes(raw_response)
    if event_bytes:
        (raw_root / "events.jsonl").write_bytes(event_bytes)

    print(f"Codex proposal prepared: {args.run_id}")
    print(f"Model: {args.model}")
    print(f"Files: {len(files)}")
    print(f"CLI calls: {cli_calls}")
    print(f"Elapsed ms: {proposal['metrics']['elapsedMs']}")
    print(f"Proposal: {proposal_root}")
    print(f"Raw output: {raw_root / 'provider-output.json'}")
    return 0


def build_response_schema(task: dict[str, Any]) -> dict[str, Any]:
    paths = [
        task["candidate"]["rulePath"],
        task["candidate"]["testPath"],
        task["candidate"]["uiPath"],
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["files"],
        "properties": {
            "notes": {"type": "string"},
            "files": {
                "type": "object",
                "additionalProperties": False,
                "required": paths,
                "properties": {
                    path: {"type": "string", "minLength": 1, "maxLength": 262144}
                    for path in paths
                },
            },
        },
    }


def call_codex(
    executable: str,
    model: str,
    workspace: Path,
    schema_path: Path,
    final_path: Path,
    prompt: str,
    timeout_seconds: float,
) -> tuple[bytes, bytes, int]:
    resolved = shutil.which(executable)
    if resolved is None:
        raise CodexAdapterError(
            f"Codex CLI executable was not found: {executable!r}; "
            "install it and complete `codex login` first"
        )
    command = [
        resolved,
        "exec",
        "--ephemeral",
        "--json",
        "--sandbox",
        "read-only",
        "--ask-for-approval",
        "never",
        "--ignore-user-config",
        "--ignore-rules",
        "--model",
        model,
        "--cd",
        str(workspace),
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(final_path),
    ]
    try:
        completed = subprocess.run(
            command,
            input=prompt.encode(UTF8),
            capture_output=True,
            cwd=workspace,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise CodexAdapterError("Codex CLI exceeded the reviewed timeout") from exc

    event_bytes = completed.stdout or b""
    error_bytes = completed.stderr or b""
    if not isinstance(event_bytes, bytes) or not isinstance(error_bytes, bytes):
        raise CodexAdapterError("Codex CLI returned non-binary process output")
    if len(event_bytes) + len(error_bytes) > MAX_EVENT_BYTES:
        raise CodexAdapterError("Codex CLI output exceeds the reviewed size limit")
    try:
        events = event_bytes.decode(UTF8)
        errors = error_bytes.decode(UTF8)
    except UnicodeDecodeError as exc:
        raise CodexAdapterError("Codex CLI output is not valid UTF-8") from exc
    if completed.returncode != 0:
        raise CodexAdapterError(
            f"Codex CLI failed with exit {completed.returncode}: "
            f"{errors[-2000:]}"
        )
    if not final_path.is_file():
        raise CodexAdapterError("Codex CLI did not write the final response")
    tool_calls = count_tool_calls(events)
    if tool_calls:
        raise CodexAdapterError(
            "Codex invoked tools even though the frozen provider run forbids them"
        )
    return final_path.read_bytes(), event_bytes, 0


def count_tool_calls(events: str) -> int:
    count = 0
    forbidden_item_types = {
        "command_execution",
        "file_change",
        "mcp_tool_call",
        "web_search",
    }
    for line in events.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexAdapterError("Codex --json output is not valid JSONL") from exc
        if not isinstance(event, dict):
            raise CodexAdapterError("Codex --json event must be a JSON object")
        item = event.get("item")
        if (
            event.get("type") in {"item.started", "item.completed"}
            and isinstance(item, dict)
            and item.get("type") in forbidden_item_types
        ):
            count += 1
    return count


def hash_tree(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise CodexAdapterError(f"symlink is forbidden in workspace: {path}")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def decode_json(content: bytes, context: str) -> dict[str, Any]:
    try:
        value = json.loads(content.decode(UTF8))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexAdapterError(f"{context} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise CodexAdapterError(f"{context} must be a JSON object")
    return value


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CodexAdapterError, OSError, json.JSONDecodeError) as exc:
        print(f"Codex Builder adapter failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
