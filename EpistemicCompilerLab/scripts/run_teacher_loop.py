#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from teacher_loop_eval import evaluate, load_cases, write_jsonl
from teacher_loop_teacher import invoke_teacher, validate_candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--student-model", required=True)
    parser.add_argument("--track", choices=["prompt", "prolog", "combined"], default="combined")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ollama-uri", default="http://127.0.0.1:11434")
    parser.add_argument("--swipl", required=True)
    parser.add_argument("--codex-model")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    return parser.parse_args()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def run_split(
    root: Path,
    split: str,
    cases: list[dict[str, Any]],
    args: argparse.Namespace,
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


def score_key(train: dict[str, Any], dev: dict[str, Any], size: int) -> tuple[int, int, int]:
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
    train_diagnostics = [
        {
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
        }
        for record in train["records"]
    ]
    payload = {
        "epoch": epoch,
        "track": track,
        "editBudget": "one smallest coherent reusable change",
        "sourceEvidence": source,
        "currentStudentPrompt": current_prompt,
        "currentPrologKnowledge": current_prolog,
        "trainDiagnostics": train_diagnostics,
        "devAggregateOnly": dev_metrics,
        "previousEpochs": history[-3:],
    }
    return contract + "\n\nTeacher input:\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def epoch_summary(
    epoch: int,
    status: str,
    prompt: str,
    prolog: str,
    train: dict[str, Any] | None,
    dev: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
    validation_errors: list[str],
) -> dict[str, Any]:
    return {
        "epoch": epoch,
        "status": status,
        "changeType": None if candidate is None else candidate.get("changeType"),
        "hypothesis": None if candidate is None else candidate.get("hypothesis"),
        "expectedEffect": None if candidate is None else candidate.get("expectedEffect"),
        "risk": None if candidate is None else candidate.get("risk"),
        "promptHash": sha256_text(prompt),
        "prologHash": sha256_text(prolog),
        "promptBytes": len(prompt.encode("utf-8")),
        "prologBytes": len(prolog.encode("utf-8")),
        "validationErrors": validation_errors,
        "train": None if train is None else train["metrics"],
        "dev": None if dev is None else dev["metrics"],
    }


def main() -> int:
    args = parse_args()
    if args.epochs < 0 or args.epochs > 10:
        raise ValueError("epochs must be between 0 and 10")
    lab = args.lab_root.resolve()
    output = args.output_root.resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True)

    cases = load_cases(lab / "cases" / "teacher-loop-pilot-v0.jsonl")
    source = (lab / "sources" / "materials.md").read_text(encoding="utf-8")
    baseline_prompt = (lab / "runner" / "prompts" / "direct.md").read_text(encoding="utf-8")
    baseline_prolog = (lab / "prolog" / "knowledge.pl").read_text(encoding="utf-8")
    teacher_contract = (lab / "runner" / "prompts" / "teacher-optimize.md").read_text(encoding="utf-8")
    schema = lab / "runner" / "teacher-candidate.schema.json"
    adapter = lab / "scripts" / "invoke_codex_json.py"
    commit = subprocess.check_output(
        ["git", "-C", str(lab.parent), "rev-parse", "HEAD"],
        text=True,
    ).strip()

    current_prompt, current_prolog = baseline_prompt, baseline_prolog
    epochs: list[dict[str, Any]] = []
    epoch_root = output / "epoch-00"
    epoch_root.mkdir()
    (epoch_root / "student-prompt.md").write_text(current_prompt, encoding="utf-8")
    (epoch_root / "knowledge.pl").write_text(current_prolog, encoding="utf-8")
    train = run_split(epoch_root, "train", cases, args, current_prompt, current_prolog)
    dev = run_split(epoch_root, "dev", cases, args, current_prompt, current_prolog)
    best = {
        "epoch": 0,
        "prompt": current_prompt,
        "prolog": current_prolog,
        "train": train,
        "dev": dev,
    }
    epochs.append(epoch_summary(0, "baseline", current_prompt, current_prolog, train, dev, None, []))
    no_improve = 0

    for epoch in range(1, args.epochs + 1):
        root = output / f"epoch-{epoch:02d}"
        root.mkdir()
        teacher_input = build_teacher_prompt(
            teacher_contract,
            source,
            args.track,
            best["prompt"],
            best["prolog"],
            best["train"],
            best["dev"]["metrics"],
            epoch,
            epochs,
        )
        (root / "teacher-input.txt").write_text(teacher_input, encoding="utf-8")
        try:
            candidate, audit = invoke_teacher(
                adapter,
                schema,
                root,
                teacher_input,
                args.timeout_seconds,
                args.codex_model,
            )
            write_json(root / "teacher-audit.json", audit)
            write_json(root / "candidate.json", candidate)
        except Exception as exc:
            epochs.append(epoch_summary(
                epoch, "teacher_error", best["prompt"], best["prolog"], None, None, None, [str(exc)]
            ))
            continue

        accepted, errors = validate_candidate(
            candidate,
            args.track,
            best["prompt"],
            best["prolog"],
            cases,
            lab,
            args.swipl,
            args.timeout_seconds,
        )
        if not accepted:
            epochs.append(epoch_summary(
                epoch, "rejected", best["prompt"], best["prolog"], None, None, candidate, errors
            ))
            continue
        if candidate["decision"] == "stop":
            epochs.append(epoch_summary(
                epoch, "teacher_stop", best["prompt"], best["prolog"], None, None, candidate, []
            ))
            break

        current_prompt = candidate["studentPrompt"]
        current_prolog = candidate["prologKnowledge"]
        (root / "student-prompt.md").write_text(current_prompt, encoding="utf-8")
        (root / "knowledge.pl").write_text(current_prolog, encoding="utf-8")
        train = run_split(root, "train", cases, args, current_prompt, current_prolog)
        dev = run_split(root, "dev", cases, args, current_prompt, current_prolog)
        summary = epoch_summary(epoch, "accepted", current_prompt, current_prolog, train, dev, candidate, [])
        epochs.append(summary)

        new_key = score_key(train, dev, candidate_size(current_prompt, current_prolog))
        best_key = score_key(best["train"], best["dev"], candidate_size(best["prompt"], best["prolog"]))
        if new_key > best_key:
            best = {
                "epoch": epoch,
                "prompt": current_prompt,
                "prolog": current_prolog,
                "train": train,
                "dev": dev,
            }
            no_improve = 0
        else:
            no_improve += 1
        if no_improve >= 2:
            break

    holdout_root = output / "holdout-final"
    holdout_root.mkdir()
    (holdout_root / "student-prompt.md").write_text(best["prompt"], encoding="utf-8")
    (holdout_root / "knowledge.pl").write_text(best["prolog"], encoding="utf-8")
    holdout = run_split(holdout_root, "holdout", cases, args, best["prompt"], best["prolog"])

    summary = {
        "schemaVersion": 1,
        "kind": "codex-qwen-teacher-loop-pilot",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "track": args.track,
        "studentModel": args.student_model,
        "studentSeed": args.seed,
        "codexModelSelection": args.codex_model or "account-default",
        "epochBudget": args.epochs,
        "bestEpoch": best["epoch"],
        "baseline": epochs[0],
        "bestTrain": best["train"]["metrics"],
        "bestDev": best["dev"]["metrics"],
        "holdout": holdout["metrics"],
        "generalizationGapCases": (
            int(best["train"]["metrics"]["passedCases"])
            - int(holdout["metrics"]["passedCases"])
        ),
        "epochs": epochs,
        "methodologyLimit": "18-case engineering pilot; not publication-grade without the declared extension.",
    }
    write_json(output / "summary.json", summary)
    with (output / "epochs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "epoch", "status", "changeType", "trainPassed", "devPassed",
            "promptBytes", "prologBytes", "hypothesis",
        ])
        writer.writeheader()
        for item in epochs:
            writer.writerow({
                "epoch": item["epoch"],
                "status": item["status"],
                "changeType": item["changeType"],
                "trainPassed": None if item["train"] is None else item["train"]["passedCases"],
                "devPassed": None if item["dev"] is None else item["dev"]["passedCases"],
                "promptBytes": item["promptBytes"],
                "prologBytes": item["prologBytes"],
                "hypothesis": item["hypothesis"],
            })
    shutil.make_archive(str(output), "zip", root_dir=output)
    print(json.dumps({
        "bestEpoch": best["epoch"],
        "train": best["train"]["metrics"]["passedCases"],
        "dev": best["dev"]["metrics"]["passedCases"],
        "holdout": holdout["metrics"]["passedCases"],
        "artifact": str(output) + ".zip",
    }, ensure_ascii=False))
    print("[CGR_ARTIFACT_TITLE] Codex-Qwen teacher loop pilot")
    print(f"[CGR_ARTIFACT] {output}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
