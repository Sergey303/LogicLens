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
    cases_path = lab / "cases" / "compiled-frame-replication-v0.jsonl"
    manifest_path = lab / "cases" / "compiled-frame-replication-v0.manifest.json"
    cases = load_cases(cases_path)
    frozen = json.loads(manifest_path.read_text(encoding="utf-8"))
    renderer = (
        lab / "runner" / "prompts" / "compiled-frame-renderer.md"
    ).read_text(encoding="utf-8")
    records, metrics = evaluate_split(cases, "replication", args, renderer)
    write_jsonl(output / "replication.jsonl", records)
    (output / "replication.metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    commit = subprocess.check_output(
        ["git", "-C", str(lab.parent), "rev-parse", "HEAD"],
        text=True,
        encoding="utf-8",
    ).strip()
    result = {
        "schemaVersion": 1,
        "kind": "compiled-decision-frame-replication-v0",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "studentModel": args.student_model,
        "studentSeed": args.seed,
        "frozenCasesSha256": frozen["casesSha256"],
        "frozenParserSha256": frozen["parserSha256"],
        "metrics": metrics,
    }
    (output / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    shutil.make_archive(str(output), "zip", root_dir=output)
    print(json.dumps(result, ensure_ascii=False))
    print("[CGR_ARTIFACT_TITLE] Compiled-frame frozen replication v0")
    print(f"[CGR_ARTIFACT] {output}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
