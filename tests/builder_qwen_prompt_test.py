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
    )
    rendered = "\n".join(
        message["content"] for message in request["messages"]
    )

    required = (
        "Every file whose name ends in `.pl` is **SWI-Prolog source**, never Perl.",
        "#!/usr/bin/perl",
        "use strict",
        "epoch_data:fact(FactIdA, Subject, PredicateIriA, iri(ResourceIri))",
        'literal("text", lang(\'ru\'))',
        ":- begin_tests(ModuleName).",
        "test(test_name) :-",
        "Never write `:- test(...)`.",
        '"schemaVersion": "0.1"',
        '"bindings"',
        "# Final mandatory constraints — apply these after reading all evidence",
        "Every `.pl` file is SWI-Prolog source, never Perl.",
        "A test case is an ordinary clause: `test(name) :- Goal.`",
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
    if request.get("format") != "json":
        raise VerificationError("Ollama JSON response mode changed unexpectedly")
    options = request.get("options", {})
    if options.get("temperature") != 0:
        raise VerificationError("Qwen request is not deterministic")
    if options.get("num_ctx") != 16_384:
        raise VerificationError("Qwen request lost the reviewed context window")

    evidence_position = rendered.find("# Frozen evidence")
    final_position = rendered.find("# Final mandatory constraints")
    test_clause_position = rendered.rfind("Never write `:- test(...)`.")
    if evidence_position < 0 or final_position <= evidence_position:
        raise VerificationError("final mandatory constraints do not follow evidence")
    if test_clause_position <= final_position:
        raise VerificationError("late constraints lost the plunit test-clause boundary")

    print("ok 1 - Qwen prompt fixes SWI-Prolog versus Perl boundary")
    print("ok 2 - Qwen prompt carries fact, plunit and UI contracts")
    print("ok 3 - final constraints follow public evidence")
    print("ok 4 - plunit test cases remain clauses, never directives")
    print("ok 5 - reviewed Ollama context window is explicit")
    print("ok 6 - hidden oracle remains excluded")
    print("1..6")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
