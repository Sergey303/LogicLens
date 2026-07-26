#!/usr/bin/env python3
"""Invoke Codex CLI as a no-tools, schema-constrained JSON provider."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

FORBIDDEN = {"command_execution", "file_change", "mcp_tool_call", "web_search"}
MAX_EVENTS = 10 * 1024 * 1024


class AdapterError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model")
    parser.add_argument("--working-directory", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    return parser.parse_args()


def parse_events(events: str) -> list[dict]:
    parsed: list[dict] = []
    for line in events.splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AdapterError("Codex --json output is not valid JSONL") from exc
        if not isinstance(value, dict):
            raise AdapterError("Codex event must be a JSON object")
        parsed.append(value)
    return parsed


def count_tool_calls(events: str) -> int:
    count = 0
    for event in parse_events(events):
        item = event.get("item")
        if (
            event.get("type") in {"item.started", "item.completed"}
            and isinstance(item, dict)
            and item.get("type") in FORBIDDEN
        ):
            count += 1
    return count


def failure_details(events: str) -> str:
    details: list[str] = []
    try:
        parsed = parse_events(events)
    except AdapterError:
        tail = events.strip()[-2000:]
        return f"non-JSONL stdout tail: {tail}" if tail else "no stdout diagnostics"
    for event in parsed:
        kind = event.get("type")
        item = event.get("item")
        if kind in {"turn.failed", "thread.error", "error"}:
            details.append(json.dumps(event.get("error") or event.get("message") or event, ensure_ascii=False))
        elif kind in {"item.started", "item.completed"} and isinstance(item, dict) and item.get("type") == "error":
            details.append(json.dumps(item.get("message") or item.get("error") or item, ensure_ascii=False))
    if details:
        return " | ".join(details[-5:])
    tail = events.strip()[-2000:]
    return f"JSONL tail: {tail}" if tail else "no JSONL diagnostic events"


def main() -> int:
    args = parse_args()
    executable = shutil.which(args.codex)
    if executable is None:
        raise AdapterError("Codex CLI not found; install it and complete `codex login`")
    workdir = args.working_directory.resolve()
    schema = args.schema.resolve()
    output = args.output.resolve()
    events = args.events.resolve()
    if not workdir.is_dir() or not schema.is_file():
        raise AdapterError("working directory or output schema is missing")
    if args.timeout_seconds <= 0 or args.timeout_seconds > 3600:
        raise AdapterError("timeout-seconds must be between 0 and 3600")
    output.parent.mkdir(parents=True, exist_ok=True)
    events.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or events.exists():
        raise AdapterError("output and events paths must be new")
    command = [
        executable, "exec", "--ephemeral", "--json", "--sandbox", "read-only",
        "--ignore-user-config", "--ignore-rules",
    ]
    if args.model:
        command.extend(["--model", args.model])
    command.extend([
        "--cd", str(workdir), "--output-schema", str(schema),
        "--output-last-message", str(output),
    ])
    prompt = sys.stdin.read()
    if not prompt.strip():
        raise AdapterError("provider prompt is empty")
    try:
        completed = subprocess.run(
            command, input=prompt, text=True, capture_output=True,
            cwd=workdir, check=False, timeout=args.timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise AdapterError("Codex CLI exceeded the timeout") from exc
    event_bytes = completed.stdout.encode("utf-8")
    error_bytes = completed.stderr.encode("utf-8")
    if len(event_bytes) + len(error_bytes) > MAX_EVENTS:
        raise AdapterError("Codex CLI output exceeded the audit limit")
    events.write_bytes(event_bytes)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "no stderr"
        raise AdapterError(
            f"Codex CLI failed with exit {completed.returncode}; "
            f"structured={failure_details(completed.stdout)}; stderr={stderr[-2000:]}"
        )
    if not output.is_file():
        raise AdapterError("Codex CLI did not write the final response")
    if count_tool_calls(completed.stdout):
        raise AdapterError("Codex invoked a forbidden tool")
    try:
        value = json.loads(output.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AdapterError("Codex final response is not valid JSON") from exc
    if not isinstance(value, dict):
        raise AdapterError("Codex final response must be a JSON object")
    print(f"Codex JSON response: {output}")
    print(f"Codex events: {events}")
    print(f"Codex model selection: {args.model or 'account default'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AdapterError, OSError, subprocess.SubprocessError) as exc:
        print(f"Codex JSON adapter failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
