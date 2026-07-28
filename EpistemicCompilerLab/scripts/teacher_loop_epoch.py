#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from teacher_loop_runtime import (
    build_teacher_prompt,
    epoch_summary,
    run_split,
    write_json,
)
from teacher_loop_teacher import invoke_teacher, validate_candidate


def run_epoch(
    epoch: int,
    output: Path,
    lab: Path,
    cases: list[dict[str, Any]],
    args: Any,
    source: str,
    contract: str,
    schema: Path,
    adapter: Path,
    best: dict[str, Any],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    root = output / f"epoch-{epoch:02d}"
    root.mkdir()
    teacher_prompt = build_teacher_prompt(
        contract, source, args.track,
        best["prompt"], best["prolog"],
        best["train"], best["dev"]["metrics"],
        epoch, history,
    )
    (root / "teacher-input.txt").write_text(
        teacher_prompt, encoding="utf-8"
    )
    try:
        candidate, audit = invoke_teacher(
            adapter, schema, root, teacher_prompt,
            args.timeout_seconds, args.codex_model,
        )
        write_json(root / "teacher-audit.json", audit)
        write_json(root / "candidate.json", candidate)
    except Exception as exc:
        return empty_result(
            epoch, "teacher_error", best, [str(exc)]
        )

    accepted, errors = validate_candidate(
        candidate, args.track, best["prompt"],
        best["prolog"], cases, lab, args.swipl,
        args.timeout_seconds,
    )
    if not accepted:
        return empty_result(
            epoch, "rejected", best, errors, candidate
        )
    if candidate["decision"] == "stop":
        return empty_result(
            epoch, "teacher_stop", best, [],
            candidate, stop=True,
        )

    prompt = candidate["studentPrompt"]
    prolog = candidate["prologKnowledge"]
    store_candidate(root, prompt, prolog)
    train = run_split(
        root, "train", cases, args, prompt, prolog
    )
    dev = run_split(
        root, "dev", cases, args, prompt, prolog
    )
    return {
        "summary": epoch_summary(
            epoch, "accepted", prompt, prolog,
            train, dev, candidate, [],
            reference_train=best["train"],
        ),
        "candidate": candidate,
        "prompt": prompt,
        "prolog": prolog,
        "train": train,
        "dev": dev,
        "stop": False,
    }


def empty_result(
    epoch: int,
    status: str,
    best: dict[str, Any],
    errors: list[str],
    candidate: dict[str, Any] | None = None,
    stop: bool = False,
) -> dict[str, Any]:
    return {
        "summary": epoch_summary(
            epoch, status, best["prompt"], best["prolog"],
            None, None, candidate, errors,
        ),
        "candidate": None,
        "stop": stop,
    }


def store_candidate(
    root: Path,
    prompt: str,
    prolog: str,
) -> None:
    (root / "student-prompt.md").write_text(
        prompt, encoding="utf-8"
    )
    (root / "knowledge.pl").write_text(
        prolog, encoding="utf-8"
    )
