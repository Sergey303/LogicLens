#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def invoke_teacher(
    adapter: Path,
    schema: Path,
    workdir: Path,
    prompt: str,
    timeout: int,
    model: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    output = workdir / "teacher-response.json"
    events = workdir / "teacher-events.jsonl"
    command = [
        "python",
        str(adapter),
        "--working-directory",
        str(workdir),
        "--schema",
        str(schema),
        "--output",
        str(output),
        "--events",
        str(events),
        "--timeout-seconds",
        str(timeout),
    ]
    if model:
        command += ["--model", model]
    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout + 30,
    )
    audit = {
        "exitCode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "eventsPath": str(events),
    }
    if completed.returncode != 0:
        raise RuntimeError(
            f"Codex teacher failed: {completed.stderr.strip()} {completed.stdout.strip()}"
        )
    candidate = json.loads(output.read_text(encoding="utf-8"))
    return candidate, audit


def _contains_memorization(text: str, cases: list[dict[str, Any]]) -> str | None:
    lowered = text.lower()
    for prefix in ("train-", "dev-", "holdout-", "questionru", "passedcases"):
        if prefix in lowered:
            return f"candidate contains benchmark control token '{prefix}'"
    for case in cases:
        question = case["questionRu"].strip().lower()
        if question and question in lowered:
            return f"candidate contains full benchmark question '{case['id']}'"
    return None


def _run_prolog_tests(
    prolog_text: str,
    lab_root: Path,
    swipl: str,
    timeout: int,
) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="epistemic-teacher-") as temporary:
        root = Path(temporary)
        (root / "prolog").mkdir()
        (root / "tests").mkdir()
        (root / "prolog" / "knowledge.pl").write_text(prolog_text, encoding="utf-8")
        shutil.copy2(
            lab_root / "tests" / "knowledge_tests.pl",
            root / "tests" / "knowledge_tests.pl",
        )
        completed = subprocess.run(
            [
                swipl,
                "-q",
                "-s",
                str(root / "tests" / "knowledge_tests.pl"),
                "-g",
                "run_tests,halt",
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        output = (completed.stdout + "\n" + completed.stderr).strip()
        return completed.returncode == 0, output


def validate_candidate(
    candidate: dict[str, Any],
    track: str,
    current_prompt: str,
    current_prolog: str,
    cases: list[dict[str, Any]],
    lab_root: Path,
    swipl: str,
    timeout: int,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    prompt = str(candidate.get("studentPrompt") or "")
    prolog = str(candidate.get("prologKnowledge") or "")
    decision = candidate.get("decision")
    change_type = candidate.get("changeType")

    if decision == "stop" and change_type != "no_change":
        errors.append("stop decision must use no_change")
    if decision == "revise" and change_type == "no_change":
        errors.append("revise decision cannot use no_change")
    allowed = {
        "prompt": {"prompt", "no_change"},
        "prolog": {"prolog", "no_change"},
        "combined": {"prompt", "prolog", "combined", "no_change"},
    }[track]
    if change_type not in allowed:
        errors.append(f"changeType '{change_type}' is forbidden for track '{track}'")
    if track == "prompt" and prolog != current_prolog:
        errors.append("prompt-only candidate changed Prolog")
    if track == "prolog" and prompt != current_prompt:
        errors.append("prolog-only candidate changed prompt")
    if not prompt.strip() or len(prompt) > 10000:
        errors.append("student prompt is empty or too large")
    if not prolog.strip() or len(prolog) > 16000:
        errors.append("Prolog representation is empty or too large")

    memorization = _contains_memorization(prompt + "\n" + prolog, cases)
    if memorization:
        errors.append(memorization)
    if re.search(r"\b2026\b|30\s+июня|1\s+июля|10\s+августа", prompt.lower()):
        errors.append("student prompt contains domain dates; facts must remain in Prolog")
    if re.search(r"(?m)^\s*%|/\*", prolog):
        errors.append("candidate Prolog contains free-form comments")
    if ":- module(epistemic_compiler_knowledge" not in prolog:
        errors.append("Prolog module contract is missing")
    if not errors:
        passed, output = _run_prolog_tests(prolog, lab_root, swipl, timeout)
        if not passed:
            errors.append(f"Prolog regression tests failed: {output[-2000:]}")
    return not errors, errors
