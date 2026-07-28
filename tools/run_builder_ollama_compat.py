#!/usr/bin/env python3
"""Structured Ollama adapter with deterministic candidate rendering and diagnostics."""
from __future__ import annotations

import json
import posixpath
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

import run_builder_ollama as base

RAW_ROOT: Path | None = None
HTTP_ERROR_BODY_LIMIT = 64 * 1024
SUPPORTED_TASK_ID = "eng-26-researcher-at-iis-v0"
PARTICIPANT_PREDICATE = "http://fogid.net/o/participant"
ORGANIZATION_PREDICATE = "http://fogid.net/o/in-org"
ROLE_PREDICATE = "http://fogid.net/o/role"
SELECTION_KEYS = (
    "participantFactId",
    "organizationFactId",
    "roleFactId",
)
PUBLIC_FACTS: dict[str, dict[str, Any]] = {}
_ORIGINAL_BUILD_REQUEST = base.build_request


def grammar_safe_response_schema(expected_paths: list[str]) -> dict[str, Any]:
    """Ask Qwen for semantic evidence selection, never free-form source files."""
    if len(expected_paths) != 3 or len(set(expected_paths)) != 3:
        raise base.OllamaAdapterError(
            "structured response requires three distinct file paths"
        )
    selection_properties = {name: {"type": "string"} for name in SELECTION_KEYS}
    return {
        "type": "object",
        "properties": {
            "notes": {"type": "string"},
            "selection": {
                "type": "object",
                "properties": selection_properties,
                "required": list(SELECTION_KEYS),
                "additionalProperties": False,
            },
        },
        "required": ["selection"],
        "additionalProperties": False,
    }


def final_constraints_with_task_acceptance(
    task: dict[str, Any],
    expected_paths: list[str],
) -> str:
    """Repeat the public task while limiting Qwen to three evidence identifiers."""
    if len(expected_paths) != 3 or len(set(expected_paths)) != 3:
        raise base.OllamaAdapterError(
            "structured response requires three distinct file paths"
        )
    acceptance = task.get("acceptance")
    if (
        not isinstance(acceptance, list)
        or not acceptance
        or any(not isinstance(item, str) or not item.strip() for item in acceptance)
    ):
        raise base.OllamaAdapterError(
            "frozen task acceptance must be a non-empty list of strings"
        )
    reminders = "\n".join(f"- {item}" for item in acceptance)
    selection_json = json.dumps(list(SELECTION_KEYS), ensure_ascii=False)
    return (
        "# Final mandatory constraints — apply these after reading all evidence\n"
        "1. Return only a semantic evidence selection. Do not write Prolog or UI source "
        "and do not return a `files` object.\n"
        f"2. The `selection` object has exactly these string keys: {selection_json}.\n"
        "3. Copy each FactId exactly from the public evidence. Select the participant, "
        "in-org and Russian language role facts required by the task.\n"
        "4. The three selected facts must be distinct and must use one identical Subject "
        "participation resource.\n"
        "5. `participantFactId` must name a fact whose predicate is "
        f"`{PARTICIPANT_PREDICATE}` and whose Object is the person IRI.\n"
        "6. `organizationFactId` must name a fact whose predicate is "
        f"`{ORGANIZATION_PREDICATE}` and whose Object is the required organization IRI.\n"
        "7. `roleFactId` must name a fact whose predicate is "
        f"`{ROLE_PREDICATE}` and whose Object is the required Russian language literal.\n"
        "8. Return exactly one JSON object matching the schema above, with no Markdown "
        "fences and no extra top-level fields. The trusted adapter will render the three "
        "task-declared files deterministically from the selected public facts.\n\n"
        "# Task acceptance reminders — apply literally after evidence\n"
        + reminders
    )


def iter_public_fact_records(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if all(key in value for key in ("factId", "subject", "predicate", "object")):
            yield value
        for child in value.values():
            yield from iter_public_fact_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_public_fact_records(child)


def collect_public_facts(evidence: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    facts: dict[str, dict[str, Any]] = {}
    for item in evidence:
        if not isinstance(item, dict) or "content" not in item:
            raise base.OllamaAdapterError("public evidence item is malformed")
        for fact in iter_public_fact_records(item["content"]):
            fact_id = fact.get("factId")
            if not isinstance(fact_id, str) or not fact_id:
                raise base.OllamaAdapterError("public evidence factId must be a string")
            normalized = {
                "factId": fact_id,
                "subject": fact.get("subject"),
                "predicate": fact.get("predicate"),
                "object": fact.get("object"),
            }
            existing = facts.get(fact_id)
            if existing is not None and existing != normalized:
                raise base.OllamaAdapterError(
                    f"public evidence contains conflicting records for {fact_id}"
                )
            facts[fact_id] = normalized
    if not facts:
        raise base.OllamaAdapterError("public evidence contains no fact records")
    return facts


def build_request_with_public_evidence(
    model: str,
    task: dict[str, Any],
    prompt: str,
    evidence: list[dict[str, Any]],
    context_tokens: int = base.DEFAULT_CONTEXT_TOKENS,
    output_tokens: int = base.DEFAULT_OUTPUT_TOKENS,
) -> dict[str, Any]:
    global PUBLIC_FACTS
    PUBLIC_FACTS = collect_public_facts(evidence)
    return _ORIGINAL_BUILD_REQUEST(
        model,
        task,
        prompt,
        evidence,
        context_tokens,
        output_tokens,
    )


def require_nonempty_string(value: Any, context: str, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise base.OllamaAdapterError(
            f"{context} must be a non-empty string up to {maximum} characters"
        )
    return value


def require_task_contract(task: dict[str, Any]) -> dict[str, Any]:
    if task.get("taskId") != SUPPORTED_TASK_ID:
        raise base.OllamaAdapterError(
            f"structured renderer does not support task {task.get('taskId')!r}"
        )
    candidate = task.get("candidate")
    if not isinstance(candidate, dict):
        raise base.OllamaAdapterError("task candidate contract is missing")
    module = require_nonempty_string(candidate.get("module"), "candidate module")
    predicate = require_nonempty_string(
        candidate.get("predicate"), "candidate predicate"
    )
    if not re.fullmatch(r"[a-z][A-Za-z0-9_]*", module):
        raise base.OllamaAdapterError("candidate module is not a safe Prolog identifier")
    if not re.fullmatch(r"[a-z][A-Za-z0-9_]*", predicate):
        raise base.OllamaAdapterError("candidate predicate is not a safe Prolog identifier")
    if candidate.get("arity") != 2:
        raise base.OllamaAdapterError("structured renderer requires predicate arity 2")
    for key in ("rulePath", "testPath", "uiPath", "uiPredicate", "uiComponent"):
        require_nonempty_string(candidate.get(key), f"candidate {key}", 1024)
    return candidate


def require_relative_path(value: str, context: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        raise base.OllamaAdapterError(f"unsafe {context}: {value}")
    return path


def require_iri_object(fact: dict[str, Any], context: str) -> str:
    obj = fact.get("object")
    if not isinstance(obj, dict) or obj.get("kind") != "iri":
        raise base.OllamaAdapterError(f"{context} must have an IRI object")
    return require_nonempty_string(obj.get("value"), f"{context} IRI", 4096)


def require_language_literal(fact: dict[str, Any], context: str) -> tuple[str, str]:
    obj = fact.get("object")
    if (
        not isinstance(obj, dict)
        or obj.get("kind") != "literal"
        or obj.get("literalKind") != "language"
    ):
        raise base.OllamaAdapterError(f"{context} must have a language literal object")
    lexical = require_nonempty_string(obj.get("lexical"), f"{context} lexical", 4096)
    language = require_nonempty_string(obj.get("language"), f"{context} language", 64)
    return lexical, language


def prolog_atom(value: str) -> str:
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise base.OllamaAdapterError("public evidence contains a control character")
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def relative_import(source_file: PurePosixPath, target_file: PurePosixPath) -> str:
    start = source_file.parent.as_posix() or "."
    return posixpath.relpath(target_file.as_posix(), start=start)


def compile_structured_candidate_files(
    generated: dict[str, Any],
    task: dict[str, Any],
) -> dict[Path, str]:
    candidate = require_task_contract(task)
    if set(generated) - {"notes", "selection"}:
        raise base.OllamaAdapterError("model response contains unknown top-level fields")
    if "notes" in generated and not isinstance(generated["notes"], str):
        raise base.OllamaAdapterError("model response notes must be a string")
    selection = generated.get("selection")
    if not isinstance(selection, dict):
        raise base.OllamaAdapterError("model response is missing selection object")
    if set(selection) != set(SELECTION_KEYS):
        raise base.OllamaAdapterError(
            "model selection keys do not exactly match the structured contract"
        )

    selected_ids = {
        key: require_nonempty_string(selection.get(key), f"selection {key}", 256)
        for key in SELECTION_KEYS
    }
    if len(set(selected_ids.values())) != len(SELECTION_KEYS):
        raise base.OllamaAdapterError("selected FactIds must be distinct")
    if not PUBLIC_FACTS:
        raise base.OllamaAdapterError("public evidence facts were not captured")

    try:
        participant_fact = PUBLIC_FACTS[selected_ids["participantFactId"]]
        organization_fact = PUBLIC_FACTS[selected_ids["organizationFactId"]]
        role_fact = PUBLIC_FACTS[selected_ids["roleFactId"]]
    except KeyError as exc:
        raise base.OllamaAdapterError(
            f"selected FactId is absent from public evidence: {exc.args[0]}"
        ) from exc

    expected_predicates = (
        (participant_fact, PARTICIPANT_PREDICATE, "participant fact"),
        (organization_fact, ORGANIZATION_PREDICATE, "organization fact"),
        (role_fact, ROLE_PREDICATE, "role fact"),
    )
    for fact, expected_predicate, context in expected_predicates:
        if fact.get("predicate") != expected_predicate:
            raise base.OllamaAdapterError(
                f"{context} has unexpected predicate {fact.get('predicate')!r}"
            )

    subjects = [
        require_nonempty_string(fact.get("subject"), "selected fact subject", 4096)
        for fact, _, _ in expected_predicates
    ]
    if len(set(subjects)) != 1:
        raise base.OllamaAdapterError(
            "selected participant, organization and role facts do not share one subject"
        )

    person_iri = require_iri_object(participant_fact, "participant fact")
    organization_iri = require_iri_object(organization_fact, "organization fact")
    role_lexical, role_language = require_language_literal(role_fact, "role fact")

    rule_path = require_relative_path(candidate["rulePath"], "rule path")
    test_path = require_relative_path(candidate["testPath"], "test path")
    ui_path = require_relative_path(candidate["uiPath"], "UI path")
    module = candidate["module"]
    predicate = candidate["predicate"]
    data_import = relative_import(rule_path, PurePosixPath("data/epoch_data.pl"))
    rule_import = relative_import(test_path, rule_path)

    rule_source = (
        f":- module({module}, [{predicate}/2]).\n"
        f":- use_module({prolog_atom(data_import)}).\n\n"
        f"{predicate}(Person, EvidenceFactIds) :-\n"
        "    epoch_data:fact(FParticipant, Participation, "
        f"{prolog_atom(PARTICIPANT_PREDICATE)}, iri(Person)),\n"
        "    epoch_data:fact(FOrganization, Participation, "
        f"{prolog_atom(ORGANIZATION_PREDICATE)}, iri({prolog_atom(organization_iri)})),\n"
        "    epoch_data:fact(FRole, Participation, "
        f"{prolog_atom(ROLE_PREDICATE)}, "
        f"literal({prolog_atom(role_lexical)}, lang({prolog_atom(role_language)}))),\n"
        "    sort([FParticipant, FOrganization, FRole], EvidenceFactIds).\n"
    )

    fact_id_atoms = ", ".join(
        prolog_atom(selected_ids[key]) for key in SELECTION_KEYS
    )
    test_source = (
        f":- begin_tests({module}).\n"
        f":- use_module({prolog_atom(rule_import)}).\n\n"
        "test(selected_public_evidence) :-\n"
        f"    {predicate}({prolog_atom(person_iri)}, EvidenceFactIds),\n"
        f"    sort([{fact_id_atoms}], ExpectedFactIds),\n"
        "    assertion(EvidenceFactIds == ExpectedFactIds).\n\n"
        f":- end_tests({module}).\n"
    )

    ui_source = json.dumps(
        {
            "schemaVersion": "0.1",
            "bindings": [
                {
                    "predicate": candidate["uiPredicate"],
                    "component": candidate["uiComponent"],
                }
            ],
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"

    if RAW_ROOT is not None:
        RAW_ROOT.mkdir(parents=True, exist_ok=True)
        (RAW_ROOT / "semantic-selection.json").write_bytes(
            base.canonical_json_bytes(
                {
                    "schemaVersion": "0.1",
                    "taskId": task["taskId"],
                    "selection": selected_ids,
                    "derivedPublicValues": {
                        "participationSubject": subjects[0],
                        "personIri": person_iri,
                        "organizationIri": organization_iri,
                        "roleLexical": role_lexical,
                        "roleLanguage": role_language,
                    },
                }
            )
        )

    return {
        Path(rule_path.as_posix()): rule_source,
        Path(test_path.as_posix()): test_source,
        Path(ui_path.as_posix()): ui_source,
    }


def raw_root_from_argv(argv: list[str]) -> Path:
    try:
        index = argv.index("--output")
        value = argv[index + 1]
    except (ValueError, IndexError) as exc:
        raise base.OllamaAdapterError("diagnostic adapter requires --output") from exc
    return Path(value).resolve() / "raw"


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
            RAW_ROOT.mkdir(parents=True, exist_ok=True)
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
    base.build_final_constraints = final_constraints_with_task_acceptance
    base.build_request = build_request_with_public_evidence
    base.validate_generated_files = compile_structured_candidate_files
    base.call_ollama = call_ollama_with_http_diagnostics
    return base.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (base.OllamaAdapterError, OSError, json.JSONDecodeError) as exc:
        print(f"Ollama compatibility adapter failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
