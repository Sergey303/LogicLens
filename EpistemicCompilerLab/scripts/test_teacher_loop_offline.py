#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-root", required=True, type=Path)
    parser.add_argument("--swipl", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lab = args.lab_root.resolve()
    sys.path.insert(0, str(lab / "scripts"))
    from teacher_loop_teacher import validate_candidate

    prompt = (lab / "runner" / "prompts" / "direct.md").read_text(encoding="utf-8")
    prolog = (lab / "prolog" / "knowledge.pl").read_text(encoding="utf-8")
    cases = [
        json.loads(line)
        for line in (lab / "cases" / "teacher-loop-pilot-v0.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    def validate(candidate: dict, track: str) -> tuple[bool, list[str]]:
        return validate_candidate(
            candidate,
            track,
            prompt,
            prolog,
            cases,
            lab,
            args.swipl,
            60,
        )

    stop = {
        "decision": "stop",
        "changeType": "no_change",
        "hypothesis": "No safe reusable change is required.",
        "studentPrompt": prompt,
        "prologKnowledge": prolog,
        "expectedEffect": "Keep the baseline.",
        "risk": "None.",
    }
    passed, errors = validate(stop, "combined")
    if not passed:
        raise AssertionError(f"valid stop was rejected: {errors}")

    prompt_change = dict(stop)
    prompt_change.update({
        "decision": "revise",
        "changeType": "prompt",
        "studentPrompt": prompt + "\nParse explicit calendar dates before deciding whether date is missing.\n",
    })
    passed, errors = validate(prompt_change, "prompt")
    if not passed:
        raise AssertionError(f"generic prompt edit was rejected: {errors}")

    false_declaration = dict(prompt_change)
    false_declaration["changeType"] = "no_change"
    passed, errors = validate(false_declaration, "combined")
    if passed or not any("does not match observed" in error for error in errors):
        raise AssertionError("false changeType was not rejected")

    memorized = dict(prompt_change)
    memorized["studentPrompt"] += "\n" + cases[0]["questionRu"]
    passed, errors = validate(memorized, "prompt")
    if passed or not any("full benchmark question" in error for error in errors):
        raise AssertionError("memorized benchmark question was not rejected")

    semantic_change = dict(stop)
    semantic_change.update({
        "decision": "revise",
        "changeType": "prolog",
        "prologKnowledge": prolog.replace("Date < 20260701", "Date < 20260630", 1),
    })
    passed, errors = validate(semantic_change, "prolog")
    if passed or not any(
        "semantics or provenance" in error or "regression tests" in error
        for error in errors
    ):
        raise AssertionError("semantic Prolog change was not rejected")

    print("ok 1 - unchanged validated stop is accepted")
    print("ok 2 - generic prompt-only edit is accepted")
    print("ok 3 - declared change type must match actual files")
    print("ok 4 - benchmark-question memorization is rejected")
    print("ok 5 - Prolog semantic changes are rejected")
    print("1..5")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
