#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from compiled_frame_eval import evaluate_split
from teacher_loop_eval import load_cases, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--student-model", required=True)
    parser.add_argument("--swipl", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ollama-uri", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lab = args.lab_root.resolve()
    output = args.output_root.resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True)
    cases = load_cases(lab / "cases" / "teacher-loop-pilot-v0.jsonl")
    renderer = (
        lab / "runner" / "prompts" / "compiled-frame-renderer.md"
    ).read_text(encoding="utf-8")
    summaries = {}
    for split in ("train", "dev", "holdout"):
        records, summary = evaluate_split(cases, split, args, renderer)
        write_jsonl(output / f"{split}.jsonl", records)
        (output / f"{split}.metrics.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        summaries[split] = summary
    commit = subprocess.check_output(
        ["git", "-C", str(lab.parent), "rev-parse", "HEAD"],
        text=True,
        encoding="utf-8",
    ).strip()
    result = {
        "schemaVersion": 1,
        "kind": "compiled-decision-frame-control",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "studentModel": args.student_model,
        "studentSeed": args.seed,
        "splits": summaries,
    }
    (output / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    shutil.make_archive(str(output), "zip", root_dir=output)
    print(json.dumps(result, ensure_ascii=False))
    print("[CGR_ARTIFACT_TITLE] Compiled decision frame control")
    print(f"[CGR_ARTIFACT] {output}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
