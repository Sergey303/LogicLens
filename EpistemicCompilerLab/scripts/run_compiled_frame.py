#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from compiled_frame_core import compile_frame
from teacher_loop_eval import (
    STUDENT_SCHEMA,
    _post_json,
    load_cases,
    score_case,
    write_jsonl,
)


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


def evaluate_split(
    cases: list[dict[str, Any]],
    split: str,
    args: argparse.Namespace,
    renderer: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    endpoint = args.ollama_uri.rstrip("/") + "/api/chat"
    for case in (item for item in cases if item["split"] == split):
        frame_error = None
        response_error = None
        response = None
        raw = None
        usage: dict[str, Any] = {}
        started = time.perf_counter()
        try:
            frame = compile_frame(case["questionRu"], args.swipl, args.lab_root)
        except Exception as exc:
            frame_error = str(exc)
            frame = {"decision": {}}
        frame_checks = score_case(case, frame.get("decision"), frame_error)
        if frame_error is None:
            payload = {
                "model": args.student_model,
                "stream": False,
                "format": STUDENT_SCHEMA,
                "keep_alive": "10m",
                "messages": [
                    {"role": "system", "content": renderer},
                    {
                        "role": "user",
                        "content": "Verified decision frame:\n"
                        + json.dumps(frame, ensure_ascii=False, indent=2),
                    },
                ],
                "options": {
                    "temperature": 0,
                    "seed": args.seed,
                    "num_predict": 128,
                },
            }
            try:
                result = _post_json(endpoint, payload, args.timeout_seconds)
                raw = str(result["message"]["content"])
                response = json.loads(raw)
                usage = {
                    "promptEvalCount": result.get("prompt_eval_count"),
                    "evalCount": result.get("eval_count"),
                    "totalDurationNs": result.get("total_duration"),
                    "doneReason": result.get("done_reason"),
                }
                if result.get("done_reason") == "length":
                    raise RuntimeError("Ollama reached the 128-token output limit")
            except Exception as exc:
                response_error = str(exc)
        checks = score_case(case, response, response_error or frame_error)
        records.append({
            "caseId": case["id"],
            "split": split,
            "questionRu": case["questionRu"],
            "expected": case["expected"],
            "frame": frame,
            "frameError": frame_error,
            "frameChecks": frame_checks,
            "response": response,
            "raw": raw,
            "runnerError": response_error,
            "elapsedMs": int((time.perf_counter() - started) * 1000),
            "usage": usage,
            "checks": checks,
        })
    return records, metrics(split, records)


def metrics(split: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    count = lambda key: sum(1 for item in records if item["checks"][key])
    return {
        "split": split,
        "totalCases": len(records),
        "framePassedCases": sum(1 for item in records if item["frameChecks"]["passed"]),
        "renderedPassedCases": count("passed"),
        "actionCorrect": count("actionCorrect"),
        "statusCorrect": count("statusCorrect"),
        "materialCorrect": count("materialCorrect"),
        "askFieldCorrect": count("askFieldCorrect"),
        "frameErrors": sum(1 for item in records if item["frameError"]),
        "runnerErrors": sum(1 for item in records if item["runnerError"]),
        "elapsedMs": sum(item["elapsedMs"] for item in records),
        "promptEvalCount": sum(int(item["usage"].get("promptEvalCount") or 0) for item in records),
        "evalCount": sum(int(item["usage"].get("evalCount") or 0) for item in records),
    }


def main() -> int:
    args = parse_args()
    lab = args.lab_root.resolve()
    output = args.output_root.resolve()
    output.mkdir(parents=True)
    cases = load_cases(lab / "cases" / "teacher-loop-pilot-v0.jsonl")
    renderer = (lab / "runner" / "prompts" / "compiled-frame-renderer.md").read_text(encoding="utf-8")
    summaries = {}
    for split in ("train", "dev", "holdout"):
        records, summary = evaluate_split(cases, split, args, renderer)
        write_jsonl(output / f"{split}.jsonl", records)
        (output / f"{split}.metrics.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summaries[split] = summary
    commit = subprocess.check_output(
        ["git", "-C", str(lab.parent), "rev-parse", "HEAD"],
        text=True, encoding="utf-8",
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
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    shutil.make_archive(str(output), "zip", root_dir=output)
    print(json.dumps(result, ensure_ascii=False))
    print("[CGR_ARTIFACT_TITLE] Compiled decision frame control")
    print(f"[CGR_ARTIFACT] {output}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
