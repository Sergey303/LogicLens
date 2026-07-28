#!/usr/bin/env python3
"""Render selected language literal lexical values as SWI-Prolog strings."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import run_builder_ollama_compat as compat


_ORIGINAL_COMPILE = compat.compile_structured_candidate_files


def prolog_string(value: str) -> str:
    """Return a deterministic SWI-Prolog string literal for public lexical data."""
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise compat.base.OllamaAdapterError(
            "public language literal contains a control character"
        )
    return json.dumps(value, ensure_ascii=False)


def compile_structured_candidate_files_with_string_literal(
    generated: dict[str, Any],
    task: dict[str, Any],
) -> dict[Path, str]:
    """Reuse the reviewed renderer, correcting only lexical literal term type."""
    files = _ORIGINAL_COMPILE(generated, task)
    candidate = compat.require_task_contract(task)
    selection = generated.get("selection")
    if not isinstance(selection, dict):
        raise compat.base.OllamaAdapterError(
            "model response is missing selection object"
        )

    role_fact_id = compat.require_nonempty_string(
        selection.get("roleFactId"),
        "selection roleFactId",
        256,
    )
    try:
        role_fact = compat.PUBLIC_FACTS[role_fact_id]
    except KeyError as exc:
        raise compat.base.OllamaAdapterError(
            f"selected FactId is absent from public evidence: {role_fact_id}"
        ) from exc

    role_lexical, role_language = compat.require_language_literal(
        role_fact,
        "role fact",
    )
    old_term = (
        f"literal({compat.prolog_atom(role_lexical)}, "
        f"lang({compat.prolog_atom(role_language)}))"
    )
    new_term = (
        f"literal({prolog_string(role_lexical)}, "
        f"lang({compat.prolog_atom(role_language)}))"
    )

    rule_path = Path(candidate["rulePath"])
    rule_source = files.get(rule_path)
    if not isinstance(rule_source, str):
        raise compat.base.OllamaAdapterError(
            "structured renderer did not produce the task rule file"
        )
    if rule_source.count(old_term) != 1:
        raise compat.base.OllamaAdapterError(
            "structured renderer language literal boundary changed unexpectedly"
        )
    files[rule_path] = rule_source.replace(old_term, new_term, 1)
    return files


def main() -> int:
    compat.compile_structured_candidate_files = (
        compile_structured_candidate_files_with_string_literal
    )
    return compat.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (compat.base.OllamaAdapterError, OSError, json.JSONDecodeError) as exc:
        print(f"Ollama literal compatibility adapter failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
