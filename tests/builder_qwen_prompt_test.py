#!/usr/bin/env python3
"""Verify the frozen Builder prompt is explicit enough for local Qwen 7B."""
from __future__ import annotations

import importlib.util
import json
import sys
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


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    task_root = (
        repository / "experiments" / "builder" / "eng-26-researcher-at-iis"
    )
    task = json.loads((task_root / "task.json").read_text(encoding="utf-8"))
    prompt = (task_root / "prompt.md").read_text(encoding="utf-8")
    adapter = load_adapter(repository)
    request = adapter.build_request(
        "qwen2.5-coder:7b",
        task,
        prompt,
        [{"name": "public-evidence.json", "content": {"response": {}}}],
        16_384,
        2_048,
    )
    rendered = "\n".join(
        message["content"] for message in request["messages"]
    )

    required = (
        "Every file whose name ends in `.pl` is **SWI-Prolog source**, never Perl.",
        "#!/usr/bin/perl",
        "use strict",
        "epoch_data:fact(FactIdA, Subject, PredicateIriA, iri(ResourceIri))",
        "epoch_data:fact(FactId, Subject, Predicate, Object)",
        "epoch_data:fact(FParticipant, Participation,",
        "'http://fogid.net/o/participant', iri(Person))",
        "epoch_data:fact(FOrganization, Participation,",
        "'http://fogid.net/o/in-org', iri('urn:logiclens:org:iis'))",
        "epoch_data:fact(FRole, Participation,",
        "literal('исследователь', lang('ru'))",
        "Do not reverse these edges.",
        "Do not put `Person` or `urn:logiclens:org:iis` in the Subject position",
        "literal(\"text\", lang('ru'))",
        ":- begin_tests(ModuleName).",
        "test(test_name) :-",
        "At least one `test(...)` clause must appear after `begin_tests/use_module`",
        "Closing the suite before the test creates an empty invalid suite.",
        "Never write `:- test(...)`.",
        '"schemaVersion": "0.1"',
        '"bindings"',
        "# Exact JSON response schema",
        "# Final mandatory constraints — apply these after reading all evidence",
        "Every `.pl` file is SWI-Prolog source, never Perl.",
        "A test case is an ordinary clause: `test(name) :- Goal.`",
        "Escape every newline, tab, quote, and backslash",
        "Interpret epoch_data:fact/4 exactly as fact(FactId, Subject, Predicate, Object)",
        "Place at least one ordinary test(...) clause after begin_tests/use_module and before end_tests",
    )
    missing = [text for text in required if text not in rendered]
    if missing:
        raise VerificationError(f"Qwen prompt is missing required boundaries: {missing}")
    if ":- test(test_name)" in rendered:
        raise VerificationError("Qwen prompt demonstrates a plunit test as a directive")
    if "oracle" in rendered.lower():
        raise VerificationError("trusted oracle leaked into Qwen prompt")
    if request.get("model") != "qwen2.5-coder:7b":
        raise VerificationError("Qwen model identity was not retained")

    if rendered.count("fact(FactId, Subject, Predicate, Object)") < 2:
        raise VerificationError("fact tuple direction is not repeated across prompt and task")
    if rendered.count("Participation") < 6:
        raise VerificationError("shared participation subject is not explicit enough")

    prompt_begin = rendered.find(":- begin_tests(ModuleName).")
    prompt_test = rendered.find("test(test_name) :-", prompt_begin)
    prompt_end = rendered.find(":- end_tests(ModuleName).", prompt_test)
    if min(prompt_begin, prompt_test, prompt_end) < 0 or not (
        prompt_begin < prompt_test < prompt_end
    ):
        raise VerificationError("prompt does not place a test inside the PlUnit suite")

    response_schema = request.get("format")
    if not isinstance(response_schema, dict):
        raise VerificationError("Ollama request does not use a JSON Schema")
    if response_schema.get("type") != "object":
        raise VerificationError("structured response schema is not an object")
    if response_schema.get("additionalProperties") is not False:
        raise VerificationError("structured response schema allows extra top-level fields")
    files_schema = response_schema.get("properties", {}).get("files")
    if not isinstance(files_schema, dict):
        raise VerificationError("structured response schema has no files object")
    expected_paths = [
        task["candidate"]["rulePath"],
        task["candidate"]["testPath"],
        task["candidate"]["uiPath"],
    ]
    if files_schema.get("required") != expected_paths:
        raise VerificationError("structured response schema lost exact file keys")
    if files_schema.get("additionalProperties") is not False:
        raise VerificationError("structured response schema allows extra files")
    properties = files_schema.get("properties")
    if not isinstance(properties, dict) or set(properties) != set(expected_paths):
        raise VerificationError("structured response schema file properties are incorrect")
    if any(item.get("type") != "string" for item in properties.values()):
        raise VerificationError("structured response schema file values are not strings")

    options = request.get("options", {})
    if options.get("temperature") != 0:
        raise VerificationError("Qwen request is not deterministic")
    if options.get("num_ctx") != 16_384:
        raise VerificationError("Qwen request lost the reviewed context window")
    if options.get("num_predict") != 2_048:
        raise VerificationError("Qwen request lost the reviewed output budget")

    evidence_position = rendered.find("# Frozen evidence")
    schema_position = rendered.find("# Exact JSON response schema")
    final_position = rendered.find("# Final mandatory constraints")
    test_clause_position = rendered.rfind("Never write `:- test(...)`.")
    if evidence_position < 0 or schema_position <= evidence_position:
        raise VerificationError("exact JSON schema does not follow evidence")
    if final_position <= schema_position:
        raise VerificationError("final mandatory constraints do not follow the JSON schema")
    if test_clause_position <= final_position:
        raise VerificationError("late constraints lost the plunit test-clause boundary")

    print("ok 1 - Qwen prompt fixes SWI-Prolog versus Perl boundary")
    print("ok 2 - exact fact tuple direction and shared subject are explicit")
    print("ok 3 - task-specific participant, in-org and role patterns are present")
    print("ok 4 - PlUnit example keeps a non-empty test inside suite boundaries")
    print("ok 5 - exact structured-output schema follows public evidence")
    print("ok 6 - final constraints follow the response schema")
    print("ok 7 - reviewed context and output budgets are explicit")
    print("ok 8 - hidden oracle remains excluded")
    print("1..8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
