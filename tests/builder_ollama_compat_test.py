#!/usr/bin/env python3
"""Offline checks for structured selection, deterministic rendering and HTTP diagnostics."""
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


def public_evidence(compat):
    facts = [
        {
            "factId": "f:participant",
            "subject": "urn:logiclens:participation:work",
            "predicate": compat.PARTICIPANT_PREDICATE,
            "object": {"kind": "iri", "value": "urn:logiclens:person:alex"},
        },
        {
            "factId": "f:organization",
            "subject": "urn:logiclens:participation:work",
            "predicate": compat.ORGANIZATION_PREDICATE,
            "object": {"kind": "iri", "value": "urn:logiclens:org:iis"},
        },
        {
            "factId": "f:role",
            "subject": "urn:logiclens:participation:work",
            "predicate": compat.ROLE_PREDICATE,
            "object": {
                "kind": "literal",
                "literalKind": "language",
                "lexical": "исследователь",
                "language": "ru",
            },
        },
    ]
    return [{"name": "public.json", "content": {"response": {"result": {"facts": facts}}}}]


def expect_adapter_error(compat, action, text: str):
    try:
        action()
    except compat.base.OllamaAdapterError as exc:
        if text not in str(exc):
            raise VerificationError(f"unexpected adapter error: {exc}") from exc
    else:
        raise VerificationError(f"expected adapter error containing {text!r}")


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
    if "files" in schema.get("properties", {}):
        raise VerificationError("structured schema still asks Qwen for free-form files")
    selection_schema = schema.get("properties", {}).get("selection")
    if not isinstance(selection_schema, dict):
        raise VerificationError("structured schema has no selection object")
    if selection_schema.get("required") != list(compat.SELECTION_KEYS):
        raise VerificationError("structured schema lost exact selection keys")
    if selection_schema.get("additionalProperties") is not False:
        raise VerificationError("structured schema allows extra selection fields")

    task_root = (
        repository
        / "experiments"
        / "builder"
        / "eng-26-researcher-at-iis"
    )
    task = json.loads((task_root / "task.json").read_text(encoding="utf-8"))
    prompt = (task_root / "prompt.md").read_text(encoding="utf-8")
    for expected in (
        "When that schema asks for a `selection` object",
        "Do not write the Prolog, PlUnit or UI files yourself",
        "one identical participation Subject",
    ):
        if expected not in prompt:
            raise VerificationError(f"frozen prompt is missing {expected!r}")

    constraints = compat.final_constraints_with_task_acceptance(task, paths)
    required_constraints = (
        "Do not write Prolog or UI source",
        "do not return a `files` object",
        "participantFactId",
        "organizationFactId",
        "roleFactId",
        "Copy each FactId exactly from the public evidence",
        "one identical Subject participation resource",
        "trusted adapter will render the three task-declared files deterministically",
        "# Task acceptance reminders — apply literally after evidence",
    )
    missing = [item for item in required_constraints if item not in constraints]
    if missing:
        raise VerificationError(f"structured final constraints are incomplete: {missing}")

    compat.PUBLIC_FACTS = compat.collect_public_facts(public_evidence(compat))
    generated = {
        "notes": "selected from public evidence",
        "selection": {
            "participantFactId": "f:participant",
            "organizationFactId": "f:organization",
            "roleFactId": "f:role",
        },
    }
    with tempfile.TemporaryDirectory(prefix="logiclens-structured-render-") as temporary:
        compat.RAW_ROOT = Path(temporary) / "raw"
        files = compat.compile_structured_candidate_files(generated, task)
        rule_path = Path(task["candidate"]["rulePath"])
        test_path = Path(task["candidate"]["testPath"])
        ui_path = Path(task["candidate"]["uiPath"])
        if set(files) != {rule_path, test_path, ui_path}:
            raise VerificationError("renderer did not produce exactly the task-declared files")

        rule = files[rule_path]
        for expected in (
            "epoch_data:fact(FParticipant, Participation",
            "'http://fogid.net/o/participant', iri(Person))",
            "'http://fogid.net/o/in-org', iri('urn:logiclens:org:iis'))",
            "literal('исследователь', lang('ru'))",
            "sort([FParticipant, FOrganization, FRole], EvidenceFactIds)",
        ):
            if expected not in rule:
                raise VerificationError(f"rendered rule is missing {expected!r}")

        test = files[test_path]
        begin = test.find(":- begin_tests(")
        ordinary_test = test.find("test(selected_public_evidence) :-")
        end = test.find(":- end_tests(")
        if min(begin, ordinary_test, end) < 0 or not begin < ordinary_test < end:
            raise VerificationError("renderer placed the PlUnit test outside the suite")
        if ":- test(" in test:
            raise VerificationError("renderer emitted a test directive")
        if "researcher_at_iis('urn:logiclens:person:alex', EvidenceFactIds)" not in test:
            raise VerificationError("renderer lost the selected public person")

        ui = json.loads(files[ui_path])
        if ui != {
            "schemaVersion": "0.1",
            "bindings": [
                {
                    "predicate": task["candidate"]["uiPredicate"],
                    "component": task["candidate"]["uiComponent"],
                }
            ],
        }:
            raise VerificationError("renderer produced an invalid UI binding")
        diagnostic = json.loads(
            (compat.RAW_ROOT / "semantic-selection.json").read_text(encoding="utf-8")
        )
        if diagnostic.get("selection") != generated["selection"]:
            raise VerificationError("semantic selection was not retained")

    expect_adapter_error(
        compat,
        lambda: compat.compile_structured_candidate_files(
            {
                "selection": {
                    "participantFactId": "f:missing",
                    "organizationFactId": "f:organization",
                    "roleFactId": "f:role",
                }
            },
            task,
        ),
        "absent from public evidence",
    )
    expect_adapter_error(
        compat,
        lambda: compat.compile_structured_candidate_files(
            {
                "selection": {
                    "participantFactId": "f:participant",
                    "organizationFactId": "f:participant",
                    "roleFactId": "f:role",
                }
            },
            task,
        ),
        "must be distinct",
    )

    mismatched = public_evidence(compat)
    mismatched[0]["content"]["response"]["result"]["facts"][2]["subject"] = (
        "urn:logiclens:participation:other"
    )
    compat.PUBLIC_FACTS = compat.collect_public_facts(mismatched)
    expect_adapter_error(
        compat,
        lambda: compat.compile_structured_candidate_files(generated, task),
        "do not share one subject",
    )

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
            expect_adapter_error(
                compat,
                lambda: compat.call_ollama_with_http_diagnostics(endpoint, b"{}", 5.0),
                "diagnostic body retained",
            )
            result = json.loads(
                (compat.RAW_ROOT / "adapter-result.json").read_text(encoding="utf-8")
            )
            if result.get("status") != "http-error" or result.get("statusCode") != 400:
                raise VerificationError(f"unexpected diagnostic: {result}")
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

    print("ok 1 - Qwen returns three semantic FactIds instead of source files")
    print("ok 2 - selected FactIds are checked against public evidence")
    print("ok 3 - deterministic renderer creates valid rule, PlUnit and UI files")
    print("ok 4 - unknown, duplicate and cross-subject selections are rejected")
    print("ok 5 - selected semantic values are retained for audit")
    print("ok 6 - HTTP error body and status are retained")
    print("ok 7 - Qwen-only wrapper remains free of Codex")
    print("1..7")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
