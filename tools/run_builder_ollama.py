#!/usr/bin/env python3
"""Produce an epoch-candidate proposal from a frozen workspace via local Ollama."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from active_epoch.hashing import canonical_json_bytes


UTF8 = "utf-8"
MAX_RESPONSE_BYTES = 10 * 1024 * 1024
DEFAULT_CONTEXT_TOKENS = 16_384
MIN_CONTEXT_TOKENS = 4_096
MAX_CONTEXT_TOKENS = 32_768
DEFAULT_OUTPUT_TOKENS = 2_048
MIN_OUTPUT_TOKENS = 256
MAX_OUTPUT_TOKENS = 8_192
REQUIRED_RESPONSE_RESERVE = 512


class OllamaAdapterError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument(
        "--endpoint",
        default="http://127.0.0.1:11434/api/chat",
    )
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument(
        "--context-tokens",
        type=int,
        default=DEFAULT_CONTEXT_TOKENS,
        help="reviewed Ollama context window for the complete frozen request",
    )
    parser.add_argument(
        "--output-tokens",
        type=int,
        default=DEFAULT_OUTPUT_TOKENS,
        help="reviewed maximum number of tokens for the structured response",
    )
    parser.add_argument(
        "--response-file",
        type=Path,
        help="offline deterministic Ollama API response used only for verification",
    )
    parser.add_argument(
        "--elapsed-ms",
        type=float,
        help="fixed elapsed value allowed only together with --response-file",
    )
    parser.add_argument("--manual-fixes", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_identifier(args.run_id, "run ID")
    if not args.model or len(args.model) > 256:
        raise OllamaAdapterError("model must be a non-empty string up to 256 characters")
    if args.timeout_seconds <= 0 or args.timeout_seconds > 1800:
        raise OllamaAdapterError("timeout-seconds must be between 0 and 1800")
    validate_context_tokens(args.context_tokens)
    validate_output_tokens(args.output_tokens)
    if args.manual_fixes < 0:
        raise OllamaAdapterError("manual-fixes cannot be negative")
    if args.elapsed_ms is not None and args.response_file is None:
        raise OllamaAdapterError("elapsed-ms override requires response-file")
    if args.elapsed_ms is not None and args.elapsed_ms < 0:
        raise OllamaAdapterError("elapsed-ms cannot be negative")

    workspace = args.workspace.resolve()
    output = args.output.resolve()
    if not workspace.is_dir():
        raise OllamaAdapterError(f"workspace does not exist: {workspace}")
    if output == workspace or workspace in output.parents or output in workspace.parents:
        raise OllamaAdapterError("output must not overlap the frozen workspace")
    require_clean_output(output)

    manifest = read_json(workspace / "workspace-manifest.json", "workspace manifest")
    task = read_json(workspace / "task.json", "task")
    if manifest.get("stage") != "builder-workspace":
        raise OllamaAdapterError("input is not a frozen Builder workspace")
    if manifest.get("taskId") != task.get("taskId"):
        raise OllamaAdapterError("workspace task identity mismatch")

    prompt = (workspace / "prompt.md").read_text(encoding=UTF8)
    evidence = []
    for path in sorted((workspace / "evidence").glob("*.json")):
        evidence.append(
            {
                "name": path.name,
                "content": read_json(path, f"evidence {path.name}"),
            }
        )
    if not evidence:
        raise OllamaAdapterError("workspace contains no evidence")

    request_payload = build_request(
        args.model,
        task,
        prompt,
        evidence,
        args.context_tokens,
        args.output_tokens,
    )
    raw_root = output / "raw"
    raw_root.mkdir(parents=True)
    (raw_root / "request.json").write_bytes(canonical_json_bytes(request_payload))

    started = time.monotonic()
    if args.response_file is not None:
        response_path = args.response_file.resolve()
        if not response_path.is_file():
            raise OllamaAdapterError(f"response-file does not exist: {response_path}")
        raw_response = response_path.read_bytes()
    else:
        endpoint = validate_loopback_endpoint(args.endpoint)
        raw_response = call_ollama(
            endpoint,
            canonical_compact_bytes(request_payload),
            args.timeout_seconds,
        )
    measured_elapsed_ms = (time.monotonic() - started) * 1000.0
    elapsed_ms = args.elapsed_ms if args.elapsed_ms is not None else measured_elapsed_ms

    if len(raw_response) > MAX_RESPONSE_BYTES:
        raise OllamaAdapterError("Ollama response exceeds the reviewed size limit")
    (raw_root / "provider-output.json").write_bytes(raw_response)

    response = decode_json(raw_response, "Ollama response")
    ensure_prompt_not_context_limited(response, args.context_tokens, raw_root)
    ensure_generation_complete(response, args.output_tokens, raw_root)
    model_content = extract_content(response)
    generated = decode_model_json(model_content, response, raw_root)
    files = validate_generated_files(generated, task)

    proposal_root = output / "proposal"
    files_root = proposal_root / "files"
    for relative_path, content in files.items():
        destination = (files_root / relative_path).resolve()
        if files_root.resolve() not in destination.parents:
            raise OllamaAdapterError(f"generated path escaped proposal: {relative_path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(normalize_text(content), encoding=UTF8, newline="\n")

    proposal = {
        "schemaVersion": "0.1",
        "candidateId": f"{args.run_id}-candidate",
        "taskId": task["taskId"],
        "base": task["base"],
        "provider": {
            "kind": "ollama",
            "name": "ollama",
            "model": args.model,
            "runId": args.run_id,
        },
        "uiContractVersion": task["contracts"]["ui"],
        "cliProtocolVersion": task["contracts"]["cli"],
        "metrics": {
            "cliCalls": 0,
            "manualFixes": args.manual_fixes,
            "elapsedMs": round(elapsed_ms, 3),
            "costUsd": 0,
        },
        "files": [
            {
                "path": task["candidate"]["rulePath"],
                "kind": "rule",
            },
            {
                "path": task["candidate"]["testPath"],
                "kind": "test",
            },
            {
                "path": task["candidate"]["uiPath"],
                "kind": "ui",
            },
        ],
        "notes": generated.get("notes", ""),
    }
    (proposal_root / "proposal.json").write_bytes(canonical_json_bytes(proposal))

    print(f"Ollama proposal prepared: {args.run_id}")
    print(f"Model: {args.model}")
    print(f"Context tokens: {args.context_tokens}")
    print(f"Output tokens: {args.output_tokens}")
    print(f"Files: {len(files)}")
    print(f"Elapsed ms: {proposal['metrics']['elapsedMs']}")
    print(f"Proposal: {proposal_root}")
    print(f"Raw output: {raw_root / 'provider-output.json'}")
    return 0


def build_request(
    model: str,
    task: dict[str, Any],
    prompt: str,
    evidence: list[dict[str, Any]],
    context_tokens: int = DEFAULT_CONTEXT_TOKENS,
    output_tokens: int = DEFAULT_OUTPUT_TOKENS,
) -> dict[str, Any]:
    validate_context_tokens(context_tokens)
    validate_output_tokens(output_tokens)
    expected_paths = [
        task["candidate"]["rulePath"],
        task["candidate"]["testPath"],
        task["candidate"]["uiPath"],
    ]
    response_schema = build_response_schema(expected_paths)
    final_constraints = build_final_constraints(task, expected_paths)
    user_content = (
        prompt
        + "\n\n# Frozen task.json\n"
        + json.dumps(task, ensure_ascii=False, indent=2)
        + "\n\n# Frozen evidence\n"
        + json.dumps(evidence, ensure_ascii=False, indent=2)
        + "\n\n# Exact JSON response schema\n"
        + json.dumps(response_schema, ensure_ascii=False, indent=2)
        + "\n\n"
        + final_constraints
    )
    return {
        "model": model,
        "stream": False,
        "format": response_schema,
        "options": {
            "temperature": 0,
            "num_ctx": context_tokens,
            "num_predict": output_tokens,
        },
        "messages": [
            {
                "role": "system",
                "content": (
                    "You produce untrusted LogicLens candidate files. Follow the frozen "
                    "task and exact JSON schema. Never emit commands, secrets, absolute "
                    "paths, extra files, Markdown fences, or text outside the JSON object."
                ),
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
    }


def build_response_schema(expected_paths: list[str]) -> dict[str, Any]:
    if len(expected_paths) != 3 or len(set(expected_paths)) != 3:
        raise OllamaAdapterError("structured response requires three distinct file paths")
    file_properties = {
        path: {
            "type": "string",
            "minLength": 1,
            "maxLength": 262_144,
        }
        for path in expected_paths
    }
    return {
        "type": "object",
        "properties": {
            "notes": {
                "type": "string",
                "maxLength": 4_096,
            },
            "files": {
                "type": "object",
                "properties": file_properties,
                "required": expected_paths,
                "additionalProperties": False,
            },
        },
        "required": ["files"],
        "additionalProperties": False,
    }


def build_final_constraints(task: dict[str, Any], expected_paths: list[str]) -> str:
    candidate = task["candidate"]
    return (
        "# Final mandatory constraints — apply these after reading all evidence\n"
        "1. Every `.pl` file is SWI-Prolog source, never Perl. Do not emit "
        "`#!/usr/bin/perl`, `use strict`, `use warnings`, `sub`, `my`, or Perl `=>`.\n"
        f"2. Return exactly these file keys: {json.dumps(expected_paths, ensure_ascii=False)}.\n"
        f"3. Export {candidate['module']}:{candidate['predicate']}/{candidate['arity']} "
        "and use `epoch_data:fact/4` with evidence FactIds from the public evidence.\n"
        "4. Tests are executable SWI-Prolog plunit source. Only `begin_tests/1`, "
        "`use_module/1`, and `end_tests/1` are directives in the test file. "
        "A test case is an ordinary clause: `test(name) :- Goal.` Never write "
        "`:- test(...)`.\n"
        f"5. UI JSON uses schemaVersion 0.1 and binds exactly "
        f"{candidate['uiPredicate']} to trusted component {candidate['uiComponent']}.\n"
        "6. Escape every newline, tab, quote, and backslash inside file-content JSON "
        "strings. Complete and close every string, object, and brace.\n"
        "7. Return exactly one JSON object matching the exact schema above, with no "
        "Markdown fences and no extra top-level fields."
    )


def validate_context_tokens(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise OllamaAdapterError("context-tokens must be an integer")
    if value < MIN_CONTEXT_TOKENS or value > MAX_CONTEXT_TOKENS:
        raise OllamaAdapterError(
            f"context-tokens must be between {MIN_CONTEXT_TOKENS} and "
            f"{MAX_CONTEXT_TOKENS}"
        )


def validate_output_tokens(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise OllamaAdapterError("output-tokens must be an integer")
    if value < MIN_OUTPUT_TOKENS or value > MAX_OUTPUT_TOKENS:
        raise OllamaAdapterError(
            f"output-tokens must be between {MIN_OUTPUT_TOKENS} and "
            f"{MAX_OUTPUT_TOKENS}"
        )


def ensure_prompt_not_context_limited(
    response: dict[str, Any],
    context_tokens: int,
    raw_root: Path,
) -> None:
    prompt_eval_count = optional_nonnegative_int(response, "prompt_eval_count")
    if prompt_eval_count is None:
        return
    available_for_response = context_tokens - prompt_eval_count
    if available_for_response >= REQUIRED_RESPONSE_RESERVE:
        return

    diagnostic = {
        "schemaVersion": "0.1",
        "status": "context-limited",
        "contextTokens": context_tokens,
        "promptEvalCount": prompt_eval_count,
        "requiredResponseReserve": REQUIRED_RESPONSE_RESERVE,
        "availableResponseTokens": available_for_response,
    }
    write_adapter_result(raw_root, diagnostic)
    raise OllamaAdapterError(
        "Ollama prompt reached the reviewed context limit; raw response was preserved; "
        f"context-tokens={context_tokens}; prompt-eval-count={prompt_eval_count}; "
        f"required-response-reserve={REQUIRED_RESPONSE_RESERVE}"
    )


def ensure_generation_complete(
    response: dict[str, Any],
    output_tokens: int,
    raw_root: Path,
) -> None:
    done = response.get("done")
    if done is not None and not isinstance(done, bool):
        raise OllamaAdapterError("Ollama done must be a boolean")
    done_reason = response.get("done_reason")
    if done_reason is not None and not isinstance(done_reason, str):
        raise OllamaAdapterError("Ollama done_reason must be a string")
    eval_count = optional_nonnegative_int(response, "eval_count")

    reached_budget = eval_count is not None and eval_count >= output_tokens
    output_limited = done is False or done_reason == "length" or (
        done_reason is None and reached_budget
    )
    if not output_limited:
        return

    diagnostic = response_diagnostic(
        response,
        status="output-limited",
        output_tokens=output_tokens,
    )
    diagnostic["reachedOutputBudget"] = reached_budget
    write_adapter_result(raw_root, diagnostic)
    raise OllamaAdapterError(
        "Ollama generation reached the reviewed output limit; raw response was preserved; "
        f"output-tokens={output_tokens}; eval-count={eval_count}; "
        f"done-reason={done_reason!r}"
    )


def decode_model_json(
    content: str,
    response: dict[str, Any],
    raw_root: Path,
) -> dict[str, Any]:
    try:
        encoded = content.encode(UTF8)
        value = json.loads(content)
    except (UnicodeEncodeError, json.JSONDecodeError) as exc:
        diagnostic = response_diagnostic(response, status="invalid-json")
        diagnostic["contentBytes"] = len(content.encode(UTF8, errors="replace"))
        diagnostic["jsonError"] = str(exc)
        if isinstance(exc, json.JSONDecodeError):
            diagnostic["jsonErrorLine"] = exc.lineno
            diagnostic["jsonErrorColumn"] = exc.colno
            diagnostic["jsonErrorPosition"] = exc.pos
        write_adapter_result(raw_root, diagnostic)
        raise OllamaAdapterError(
            f"Ollama message content is not valid UTF-8 JSON: {exc}"
        ) from exc
    if not isinstance(value, dict):
        diagnostic = response_diagnostic(response, status="invalid-json")
        diagnostic["contentBytes"] = len(encoded)
        diagnostic["jsonError"] = "top-level JSON value is not an object"
        write_adapter_result(raw_root, diagnostic)
        raise OllamaAdapterError("Ollama message content must be a JSON object")
    return value


def response_diagnostic(
    response: dict[str, Any],
    *,
    status: str,
    output_tokens: int | None = None,
) -> dict[str, Any]:
    diagnostic: dict[str, Any] = {
        "schemaVersion": "0.1",
        "status": status,
    }
    for source, target in (
        ("done", "done"),
        ("done_reason", "doneReason"),
        ("prompt_eval_count", "promptEvalCount"),
        ("eval_count", "evalCount"),
    ):
        value = response.get(source)
        if isinstance(value, (bool, int, str)) and not (
            isinstance(value, bool) and source in {"prompt_eval_count", "eval_count"}
        ):
            diagnostic[target] = value
    if output_tokens is not None:
        diagnostic["outputTokens"] = output_tokens
    return diagnostic


def write_adapter_result(raw_root: Path, value: dict[str, Any]) -> None:
    (raw_root / "adapter-result.json").write_bytes(canonical_json_bytes(value))


def optional_nonnegative_int(response: dict[str, Any], name: str) -> int | None:
    value = response.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise OllamaAdapterError(f"Ollama {name} must be an integer")
    if value < 0:
        raise OllamaAdapterError(f"Ollama {name} cannot be negative")
    return value


def validate_loopback_endpoint(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "http":
        raise OllamaAdapterError("Ollama endpoint must use plain HTTP on loopback")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise OllamaAdapterError("Ollama endpoint must be loopback-only")
    if parsed.username is not None or parsed.password is not None:
        raise OllamaAdapterError("Ollama endpoint must not contain credentials")
    if parsed.path != "/api/chat" or parsed.query or parsed.fragment:
        raise OllamaAdapterError("Ollama endpoint must be the exact /api/chat endpoint")
    return value


def call_ollama(endpoint: str, payload: bytes, timeout: float) -> bytes:
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read(MAX_RESPONSE_BYTES + 1)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise OllamaAdapterError(f"Ollama request failed: {exc}") from exc
    if len(content) > MAX_RESPONSE_BYTES:
        raise OllamaAdapterError("Ollama response exceeds the reviewed size limit")
    return content


def extract_content(response: dict[str, Any]) -> str:
    message = response.get("message")
    if not isinstance(message, dict):
        raise OllamaAdapterError("Ollama response is missing message")
    content = message.get("content")
    if not isinstance(content, str) or not content:
        raise OllamaAdapterError("Ollama response message content is empty")
    return content


def validate_generated_files(
    generated: dict[str, Any],
    task: dict[str, Any],
) -> dict[Path, str]:
    if set(generated) - {"notes", "files"}:
        raise OllamaAdapterError("model response contains unknown top-level fields")
    if "files" not in generated or not isinstance(generated["files"], dict):
        raise OllamaAdapterError("model response is missing files object")
    if "notes" in generated and not isinstance(generated["notes"], str):
        raise OllamaAdapterError("model response notes must be a string")

    expected = {
        task["candidate"]["rulePath"],
        task["candidate"]["testPath"],
        task["candidate"]["uiPath"],
    }
    actual = set(generated["files"])
    if actual != expected:
        raise OllamaAdapterError(
            "model response files do not exactly match the frozen task; "
            f"expected={preview_paths(expected)}; actual={preview_paths(actual)}"
        )

    result: dict[Path, str] = {}
    for raw_path, content in generated["files"].items():
        path = Path(raw_path)
        if path.is_absolute() or ".." in path.parts or "\\" in raw_path:
            raise OllamaAdapterError(f"unsafe generated path: {raw_path}")
        if not isinstance(content, str) or not content:
            raise OllamaAdapterError(f"generated file content is empty: {raw_path}")
        if len(content.encode(UTF8)) > 256 * 1024:
            raise OllamaAdapterError(f"generated file is too large: {raw_path}")
        result[path] = content
    return result


def preview_paths(paths: set[str]) -> str:
    ordered = sorted(paths)
    shown = [path[:200] for path in ordered[:20]]
    suffix = f" (+{len(ordered) - len(shown)} more)" if len(ordered) > len(shown) else ""
    return json.dumps(shown, ensure_ascii=False) + suffix


def normalize_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return value if value.endswith("\n") else value + "\n"


def canonical_compact_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode(UTF8)


def read_json(path: Path, context: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding=UTF8))
    except (OSError, json.JSONDecodeError) as exc:
        raise OllamaAdapterError(f"cannot read {context} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OllamaAdapterError(f"{context} must be a JSON object")
    return value


def decode_json(content: bytes, context: str) -> dict[str, Any]:
    try:
        value = json.loads(content.decode(UTF8))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OllamaAdapterError(f"{context} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise OllamaAdapterError(f"{context} must be a JSON object")
    return value


def validate_identifier(value: str, context: str) -> None:
    if (
        not value
        or len(value) > 128
        or not value[0].isalnum()
        or any(
            character
            not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
            for character in value
        )
    ):
        raise OllamaAdapterError(f"{context} is invalid: {value!r}")


def require_clean_output(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise OllamaAdapterError(f"output exists and is not a directory: {path}")
        if any(path.iterdir()):
            raise OllamaAdapterError(f"output directory must be empty: {path}")
    else:
        path.mkdir(parents=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OllamaAdapterError, OSError, json.JSONDecodeError) as exc:
        print(f"Ollama Builder adapter failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
