#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from teacher_loop_eval import evaluate, write_jsonl
from teacher_loop_feedback import build_train_effects, summarize_train_effects


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_split(
    root: Path,
    split: str,
    cases: list[dict[str, Any]],
    args: Any,
    prompt: str,
    prolog: str,
) -> dict[str, Any]:
    records, metrics = evaluate(
        cases,
        split,
        args.student_model,
        prompt,
        prolog,
        args.seed,
        args.ollama_uri,
        args.timeout_seconds,
    )
    write_jsonl(root / f"{split}.jsonl", records)
    write_json(root / f"{split}.metrics.json", metrics)
    return {"records": records, "metrics": metrics}


def candidate_size(prompt: str, prolog: str) -> int:
    return len(prompt.encode("utf-8")) + len(prolog.encode("utf-8"))


def score_key(
    train: dict[str, Any],
    dev: dict[str, Any],
    size: int,
) -> tuple[int, int, int]:
    return (
        int(dev["metrics"]["passedCases"]),
        int(train["metrics"]["passedCases"]),
        -size,
    )


def build_teacher_prompt(
    contract: str,
    source: str,
    track: str,
    current_prompt: str,
    current_prolog: str,
    train: dict[str, Any],
    dev_metrics: dict[str, Any],
    epoch: int,
    history: list[dict[str, Any]],
) -> str:
    diagnostics = []
    for record in train["records"]:
        diagnostics.append({
            "caseId": record["caseId"],
            "question": record["questionRu"],
            "expected": record["expected"],
            "studentResponse": record["response"],
            "runnerError": record["runnerError"],
            "failedChecks": [
                name
                for name, passed in record["checks"].items()
                if name != "runnerOk" and not passed
            ],
        })
    payload = {
        "epoch": epoch,
        "track": track,
        "editBudget": "one smallest coherent reusable change",
        "sourceEvidence": source,
        "currentStudentPrompt": current_prompt,
        "currentPrologKnowledge": current_prolog,
        "trainDiagnostics": diagnostics,
        "devAggregateOnly": dev_metrics,
        "previousEpochs": history[-3:],
    }
    return (
        contract
        + "\n\nTeacher input:\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def epoch_summary(
    epoch: int,
    status: str,
    prompt: str,
    prolog: str,
    train: dict[str, Any] | None,
    dev: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
    validation_errors: list[str],
    reference_train: dict[str, Any] | None = None,
) -> dict[str, Any]:
    effects = (
        build_train_effects(reference_train, train)
        if reference_train is not None and train is not None
        else []
    )
    return {
        "epoch": epoch,
        "status": status,
        "changeType": None if candidate is None else candidate.get("changeType"),
        "hypothesis": None if candidate is None else candidate.get("hypothesis"),
        "expectedEffect": None if candidate is None else candidate.get("expectedEffect"),
        "risk": None if candidate is None else candidate.get("risk"),
        "promptHash": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prologHash": hashlib.sha256(prolog.encode("utf-8")).hexdigest(),
        "promptBytes": len(prompt.encode("utf-8")),
        "prologBytes": len(prolog.encode("utf-8")),
        "validationErrors": validation_errors,
        "train": None if train is None else train["metrics"],
        "dev": None if dev is None else dev["metrics"],
        "trainEffectCounts": (
            summarize_train_effects(effects)
            if effects
            else None
        ),
        "trainCaseEffects": effects,
    }
