#!/usr/bin/env python3
"""Runtime verification for language-literal rendering in Qwen candidates."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
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


def public_evidence(literal_compat):
    compat = literal_compat.compat
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


def write_candidate(root: Path, files: dict[Path, str]) -> None:
    for relative_path, content in files.items():
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    literal_path = repository / "tools" / "run_builder_ollama_literal_compat.py"
    qwen_path = repository / "tools" / "run_builder_qwen_only_compat.py"
    literal_compat = load_module(
        literal_path,
        "run_builder_ollama_literal_compat",
    )
    compat = literal_compat.compat
    task_root = (
        repository
        / "experiments"
        / "builder"
        / "eng-26-researcher-at-iis"
    )
    task = json.loads((task_root / "task.json").read_text(encoding="utf-8"))
    compat.PUBLIC_FACTS = compat.collect_public_facts(public_evidence(literal_compat))
    generated = {
        "selection": {
            "participantFactId": "f:participant",
            "organizationFactId": "f:organization",
            "roleFactId": "f:role",
        }
    }

    files = literal_compat.compile_structured_candidate_files_with_string_literal(
        generated,
        task,
    )
    rule_path = Path(task["candidate"]["rulePath"])
    test_path = Path(task["candidate"]["testPath"])
    rule = files[rule_path]
    if 'literal("исследователь", lang(\'ru\'))' not in rule:
        raise VerificationError("renderer did not emit a SWI-Prolog string literal")
    if "literal('исследователь', lang('ru'))" in rule:
        raise VerificationError("renderer retained the incorrect Prolog atom literal")

    escaped = literal_compat.prolog_string('текст "A" \\ путь')
    if escaped != json.dumps('текст "A" \\ путь', ensure_ascii=False):
        raise VerificationError("Prolog string escaping is not deterministic")

    qwen_source = qwen_path.read_text(encoding="utf-8")
    expected_route = '"run_builder_ollama.py": "run_builder_ollama_literal_compat.py"'
    if expected_route not in qwen_source:
        raise VerificationError("Qwen wrapper does not select the literal renderer")
    if "codex" in (literal_path.read_text(encoding="utf-8") + qwen_source).lower():
        raise VerificationError("literal Qwen route references Codex")

    swipl = shutil.which("swipl")
    if swipl is None:
        raise VerificationError("swipl is required for the literal runtime test")

    with tempfile.TemporaryDirectory(prefix="logiclens-literal-runtime-") as temporary:
        candidate_root = Path(temporary) / "candidate"
        write_candidate(candidate_root, files)
        data_path = candidate_root / "data" / "epoch_data.pl"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(
            ":- module(epoch_data, [fact/4]).\n"
            "fact('f:participant', 'urn:logiclens:participation:work', "
            "'http://fogid.net/o/participant', iri('urn:logiclens:person:alex')).\n"
            "fact('f:organization', 'urn:logiclens:participation:work', "
            "'http://fogid.net/o/in-org', iri('urn:logiclens:org:iis')).\n"
            "fact('f:role', 'urn:logiclens:participation:work', "
            "'http://fogid.net/o/role', literal(\"исследователь\", lang('ru'))).\n",
            encoding="utf-8",
            newline="\n",
        )
        completed = subprocess.run(
            [
                swipl,
                "--quiet",
                "-s",
                str(candidate_root / test_path),
                "-g",
                "run_tests",
                "-t",
                "halt",
            ],
            cwd=candidate_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise VerificationError(
                "rendered candidate failed SWI-Prolog runtime test: "
                f"stdout={completed.stdout!r}; stderr={completed.stderr!r}"
            )

    print("ok 1 - language lexical value is rendered as a Prolog string")
    print("ok 2 - string escaping is deterministic")
    print("ok 3 - Qwen-only wrapper selects the literal renderer without Codex")
    print("ok 4 - rendered rule and PlUnit test pass on SWI-Prolog")
    print("1..4")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        VerificationError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
