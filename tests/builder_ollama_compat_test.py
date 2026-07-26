#!/usr/bin/env python3
"""Offline checks for ENG-61 grammar-safe schema and HTTP error retention."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class VerificationError(AssertionError):
    pass


def load_module(path: Path, name: str):
    tools = path.parent
    sys.path.insert(0, str(tools))
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise VerificationError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(tools))


def contains_length_keyword(value) -> bool:
    if isinstance(value, dict):
        return any(
            key in {"minLength", "maxLength"} or contains_length_keyword(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(contains_length_keyword(item) for item in value)
    return False


class ErrorHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = b'{"error":"invalid grammar: diagnostic body retained"}'
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    compat = load_module(
        repository / "tools" / "run_builder_ollama_compat.py",
        "run_builder_ollama_compat",
    )
    paths = ["rules/a.pl", "tests/a_tests.pl", "ui/a.json"]
    schema = compat.grammar_safe_response_schema(paths)
    if contains_length_keyword(schema):
        raise VerificationError("grammar-safe schema retained length bounds")
    files = schema["properties"]["files"]
    if files.get("required") != paths or files.get("additionalProperties") is not False:
        raise VerificationError("exact file contract was weakened")

    with tempfile.TemporaryDirectory(prefix="logiclens-ollama-preflight-") as temporary:
        output = Path(temporary) / "provider"
        raw = compat.raw_root_from_argv(["--output", str(output)])
        if raw != output.resolve() / "raw":
            raise VerificationError("diagnostic raw path was computed incorrectly")
        if output.exists():
            raise VerificationError("diagnostic preflight created the provider output")

    server = ThreadingHTTPServer(("127.0.0.1", 0), ErrorHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="logiclens-ollama-http-") as temporary:
            compat.RAW_ROOT = Path(temporary) / "raw"
            endpoint = f"http://127.0.0.1:{server.server_port}/api/chat"
            try:
                compat.call_ollama_with_http_diagnostics(endpoint, b"{}", 5.0)
            except compat.base.OllamaAdapterError as exc:
                if "diagnostic body retained" not in str(exc):
                    raise VerificationError("HTTP error body missing from exception") from exc
            else:
                raise VerificationError("HTTP 400 unexpectedly succeeded")
            result = json.loads(
                (compat.RAW_ROOT / "adapter-result.json").read_text(encoding="utf-8")
            )
            if result.get("status") != "http-error" or result.get("statusCode") != 400:
                raise VerificationError(f"unexpected diagnostic: {result}")
            if result.get("error") != "invalid grammar: diagnostic body retained":
                raise VerificationError("structured Ollama error was not retained")
            if not (compat.RAW_ROOT / "provider-error.json").is_file():
                raise VerificationError("provider-error.json was not written")
    finally:
        server.shutdown()
        server.server_close()

    qwen_wrapper = (repository / "tools" / "run_builder_qwen_only_compat.py").read_text(
        encoding="utf-8"
    )
    if "run_builder_ollama_compat.py" not in qwen_wrapper:
        raise VerificationError("Qwen wrapper does not select compatibility adapter")
    if "codex" in qwen_wrapper.lower():
        raise VerificationError("compatibility wrapper references Codex")

    print("ok 1 - grammar-safe schema keeps exact paths without length bounds")
    print("ok 2 - diagnostic preflight leaves provider output absent")
    print("ok 3 - HTTP 400 body and status are retained")
    print("ok 4 - Qwen-only wrapper selects diagnostic adapter without Codex")
    print("1..4")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
