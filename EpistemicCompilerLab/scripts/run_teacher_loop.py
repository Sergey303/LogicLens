#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from teacher_loop_epoch import run_epoch
from teacher_loop_eval import load_cases
from teacher_loop_report import finish_run
from teacher_loop_runtime import (
    candidate_size,
    epoch_summary,
    run_split,
    score_key,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--student-model", required=True)
    parser.add_argument(
        "--track",
        choices=["prompt", "prolog", "combined"],
        default="combined",
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ollama-uri", default="http://127.0.0.1:11434")
    parser.add_argument("--swipl", required=True)
    parser.add_argument("--codex-model")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    return parser.parse_args()


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
    prompt = (lab / "runner" / "prompts" / "direct.md").read_text(encoding="utf-8")
    prolog = (lab / "prolog" / "knowledge.pl").read_text(encoding="utf-8")
    contract = (lab / "runner" / "prompts" / "teacher-optimize.md").read_text(encoding="utf-8")
    schema = lab / "runner" / "teacher-candidate.schema.json"
    adapter = lab / "scripts" / "invoke_codex_json.py"
    commit = subprocess.check_output(
        ["git", "-C", str(lab.parent), "rev-parse", "HEAD"],
        text=True,
        encoding="utf-8",
    ).strip()

    baseline_root = output / "epoch-00"
    baseline_root.mkdir()
    (baseline_root / "student-prompt.md").write_text(prompt, encoding="utf-8")
    (baseline_root / "knowledge.pl").write_text(prolog, encoding="utf-8")
    train = run_split(baseline_root, "train", cases, args, prompt, prolog)
    dev = run_split(baseline_root, "dev", cases, args, prompt, prolog)
    best = {
        "epoch": 0,
        "prompt": prompt,
        "prolog": prolog,
        "train": train,
        "dev": dev,
    }
    epochs = [
        epoch_summary(0, "baseline", prompt, prolog, train, dev, None, [])
    ]
    no_improve = 0

    for epoch in range(1, args.epochs + 1):
        result = run_epoch(
            epoch, output, lab, cases, args, source, contract,
            schema, adapter, best, epochs,
        )
        epochs.append(result["summary"])
        if result["stop"]:
            break
        if result["candidate"] is None:
            continue
        new_key = score_key(
            result["train"], result["dev"],
            candidate_size(result["prompt"], result["prolog"]),
        )
        best_key = score_key(
            best["train"], best["dev"],
            candidate_size(best["prompt"], best["prolog"]),
        )
        if new_key > best_key:
            best = {
                "epoch": epoch,
                "prompt": result["prompt"],
                "prolog": result["prolog"],
                "train": result["train"],
                "dev": result["dev"],
            }
            no_improve = 0
        else:
            no_improve += 1
        if no_improve >= 2:
            break

    finish_run(output, cases, args, prompt, prolog, best, epochs, commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
