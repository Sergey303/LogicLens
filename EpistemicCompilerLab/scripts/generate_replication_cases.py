#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from replication_cases import compile_cases, validate_generated, write_jsonl
from teacher_loop_eval import load_cases
from teacher_loop_teacher import invoke_teacher


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--swipl", required=True)
    parser.add_argument("--codex-model")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = parse_args()
    lab = args.lab_root.resolve()
    output = args.output_root.resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True)
    schema = lab / "runner" / "replication-cases.schema.json"
    prompt_path = lab / "runner" / "prompts" / "generate-replication-cases.md"
    parser_path = lab / "scripts" / "compiled_frame_core.py"
    adapter = lab / "scripts" / "invoke_codex_json.py"
    prompt = prompt_path.read_text(encoding="utf-8") + (
        "\n\nThe parser implementation and previous benchmark questions are intentionally "
        "withheld. Generate the dataset without requesting tools or files."
    )
    value, audit = invoke_teacher(
        adapter,
        schema,
        output,
        prompt,
        args.timeout_seconds,
        args.codex_model,
    )
    (output / "generator-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    old_questions = _old_questions(lab)
    generated = validate_generated(value, old_questions)
    compiled = compile_cases(generated, args.swipl, lab)
    case_path = output / "compiled-frame-replication-v0.jsonl"
    write_jsonl(case_path, compiled)
    commit = subprocess.check_output(
        ["git", "-C", str(lab.parent), "rev-parse", "HEAD"],
        text=True,
        encoding="utf-8",
    ).strip()
    manifest = {
        "schemaVersion": 1,
        "kind": "compiled-frame-replication-candidate",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "generator": "codex-cli-account-default" if not args.codex_model else args.codex_model,
        "caseCount": len(compiled),
        "parserSha256": sha256(parser_path),
        "generatorPromptSha256": sha256(prompt_path),
        "casesSha256": sha256(case_path),
        "oldQuestionsWithheld": True,
        "parserSourceWithheld": True,
        "status": "candidate_requires_review_and_freeze",
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    shutil.make_archive(str(output), "zip", root_dir=output)
    print(json.dumps(manifest, ensure_ascii=False))
    print("[CGR_ARTIFACT_TITLE] Compiled-frame replication candidate")
    print(f"[CGR_ARTIFACT] {output}.zip")
    return 0


def _old_questions(lab: Path) -> set[str]:
    paths = [
        lab / "cases" / "teacher-loop-pilot-v0.jsonl",
        lab / "cases" / "benchmark-v0.jsonl",
        lab / "cases" / "benchmark-v1.jsonl",
    ]
    questions: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        for item in load_cases(path):
            question = str(item.get("questionRu") or item.get("question") or "").strip()
            if question:
                questions.add(question)
    return questions


if __name__ == "__main__":
    raise SystemExit(main())
