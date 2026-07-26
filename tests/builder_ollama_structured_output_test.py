#!/usr/bin/env python3
"""Focused checks for Ollama structured output and retained diagnostics."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


class VerificationError(AssertionError):
    pass


def load_adapter(repository: Path):
    tools = repository / "tools"
    sys.path.insert(0, str(tools))
    try:
        path = tools / "run_builder_ollama.py"
        spec = importlib.util.spec_from_file_location("run_builder_ollama", path)
        if spec is None or spec.loader is None:
            raise VerificationError(f"cannot load Ollama adapter: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(tools))


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"expected JSON object: {path}")
    return value


def expect_failure(action, text: str) -> None:
    try:
        action()
    except Exception as exc:
        if text not in str(exc):
            raise VerificationError(
                f"failure did not contain {text!r}: {exc!r}"
            ) from exc
        return
    raise VerificationError("operation unexpectedly succeeded")


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    adapter = load_adapter(repository)
    expected_paths = [
        "rules/candidate_researcher_at_iis.pl",
        "tests/candidate_researcher_at_iis_tests.pl",
        "ui/researcher-at-iis.json",
    ]

    schema = adapter.build_response_schema(expected_paths)
    if schema.get("required") != ["files"]:
        raise VerificationError("top-level structured schema does not require files")
    if schema.get("additionalProperties") is not False:
        raise VerificationError("top-level structured schema allows extra fields")
    files = schema.get("properties", {}).get("files")
    if not isinstance(files, dict):
        raise VerificationError("structured schema has no files object")
    if files.get("required") != expected_paths:
        raise VerificationError("structured schema lost exact file paths")
    if files.get("additionalProperties") is not False:
        raise VerificationError("structured schema allows extra file paths")

    with tempfile.TemporaryDirectory(prefix="logiclens-output-limited-") as temporary:
        raw = Path(temporary)
        response = {
            "done": True,
            "done_reason": "length",
            "prompt_eval_count": 7_000,
            "eval_count": 2_048,
        }
        expect_failure(
            lambda: adapter.ensure_generation_complete(response, 2_048, raw),
            "output limit",
        )
        diagnostic = read_json(raw / "adapter-result.json")
        if diagnostic.get("status") != "output-limited":
            raise VerificationError("output-limited status was not retained")
        if diagnostic.get("outputTokens") != 2_048:
            raise VerificationError("output token budget was not retained")
        if diagnostic.get("doneReason") != "length":
            raise VerificationError("done_reason was not retained")
        if diagnostic.get("evalCount") != 2_048:
            raise VerificationError("eval_count was not retained")

    with tempfile.TemporaryDirectory(prefix="logiclens-invalid-json-") as temporary:
        raw = Path(temporary)
        response = {
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 7_000,
            "eval_count": 150,
        }
        malformed = '{"files":{"rules/candidate_researcher_at_iis.pl":"unterminated}'
        expect_failure(
            lambda: adapter.decode_model_json(malformed, response, raw),
            "not valid UTF-8 JSON",
        )
        diagnostic = read_json(raw / "adapter-result.json")
        if diagnostic.get("status") != "invalid-json":
            raise VerificationError("invalid-json status was not retained")
        for key in (
            "contentBytes",
            "jsonError",
            "jsonErrorLine",
            "jsonErrorColumn",
            "jsonErrorPosition",
            "doneReason",
            "promptEvalCount",
            "evalCount",
        ):
            if key not in diagnostic:
                raise VerificationError(f"invalid-json diagnostic is missing {key}")
        if diagnostic.get("doneReason") != "stop":
            raise VerificationError("parse diagnostic lost completion reason")

    with tempfile.TemporaryDirectory(prefix="logiclens-valid-json-") as temporary:
        raw = Path(temporary)
        response = {
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 7_000,
            "eval_count": 180,
        }
        adapter.ensure_generation_complete(response, 2_048, raw)
        value = adapter.decode_model_json(
            json.dumps(
                {
                    "files": {path: "content" for path in expected_paths},
                    "notes": "",
                }
            ),
            response,
            raw,
        )
        if set(value.get("files", {})) != set(expected_paths):
            raise VerificationError("valid structured JSON lost file keys")
        if (raw / "adapter-result.json").exists():
            raise VerificationError("valid response wrote a failure diagnostic")

    print("ok 1 - exact JSON Schema requires three known file paths")
    print("ok 2 - output-limited generation is retained and classified")
    print("ok 3 - malformed JSON retains completion and parse diagnostics")
    print("ok 4 - adapter never repairs malformed model output")
    print("ok 5 - complete structured JSON remains accepted")
    print("1..5")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        VerificationError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
