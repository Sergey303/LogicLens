#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from teacher_loop_runtime import run_split, write_json


def finish_run(
    output: Path,
    cases: list[dict[str, Any]],
    args: Any,
    baseline_prompt: str,
    baseline_prolog: str,
    best: dict[str, Any],
    epochs: list[dict[str, Any]],
    commit: str,
) -> None:
    baseline_root = output / "holdout-baseline"
    baseline_root.mkdir()
    (baseline_root / "student-prompt.md").write_text(
        baseline_prompt, encoding="utf-8"
    )
    (baseline_root / "knowledge.pl").write_text(
        baseline_prolog, encoding="utf-8"
    )
    baseline_holdout = run_split(
        baseline_root, "holdout", cases, args,
        baseline_prompt, baseline_prolog,
    )

    if best["epoch"] == 0:
        selected_holdout = baseline_holdout
    else:
        selected_root = output / "holdout-selected"
        selected_root.mkdir()
        (selected_root / "student-prompt.md").write_text(
            best["prompt"], encoding="utf-8"
        )
        (selected_root / "knowledge.pl").write_text(
            best["prolog"], encoding="utf-8"
        )
        selected_holdout = run_split(
            selected_root, "holdout", cases, args,
            best["prompt"], best["prolog"],
        )

    baseline_passed = int(
        baseline_holdout["metrics"]["passedCases"]
    )
    selected_passed = int(
        selected_holdout["metrics"]["passedCases"]
    )
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
        "baselineHoldout": baseline_holdout["metrics"],
        "selectedHoldout": selected_holdout["metrics"],
        "holdoutDeltaCases": selected_passed - baseline_passed,
        "generalizationGapCases": (
            int(best["train"]["metrics"]["passedCases"])
            - selected_passed
        ),
        "epochs": epochs,
        "methodologyLimit": (
            "18-case engineering pilot; not publication-grade "
            "without the declared extension."
        ),
    }
    write_json(output / "summary.json", summary)
    _write_epochs_csv(output / "epochs.csv", epochs)
    shutil.make_archive(str(output), "zip", root_dir=output)
    print(json.dumps({
        "bestEpoch": best["epoch"],
        "train": best["train"]["metrics"]["passedCases"],
        "dev": best["dev"]["metrics"]["passedCases"],
        "baselineHoldout": baseline_passed,
        "selectedHoldout": selected_passed,
        "holdoutDelta": selected_passed - baseline_passed,
        "artifact": str(output) + ".zip",
    }, ensure_ascii=False))
    print("[CGR_ARTIFACT_TITLE] Codex-Qwen teacher loop pilot")
    print(f"[CGR_ARTIFACT] {output}.zip")


def _write_epochs_csv(
    path: Path,
    epochs: list[dict[str, Any]],
) -> None:
    fields = [
        "epoch", "status", "changeType", "trainPassed",
        "devPassed", "promptBytes", "prologBytes", "fixed",
        "regressed", "unchangedFail", "hypothesis",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in epochs:
            counts = item.get("trainEffectCounts") or {}
            writer.writerow({
                "epoch": item["epoch"],
                "status": item["status"],
                "changeType": item["changeType"],
                "trainPassed": _passed(item.get("train")),
                "devPassed": _passed(item.get("dev")),
                "promptBytes": item["promptBytes"],
                "prologBytes": item["prologBytes"],
                "fixed": counts.get("fixed"),
                "regressed": counts.get("regressed"),
                "unchangedFail": counts.get("unchangedFail"),
                "hypothesis": item["hypothesis"],
            })


def _passed(metrics: dict[str, Any] | None) -> int | None:
    return None if metrics is None else metrics["passedCases"]
