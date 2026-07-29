#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import time
from typing import Any

from compiled_frame_core import compile_frame
from teacher_loop_eval import STUDENT_SCHEMA, _post_json, score_case

CYRILLIC = re.compile(r"[А-Яа-яЁё]")


def evaluate_split(
    cases: list[dict[str, Any]],
    split: str,
    args: Any,
    renderer: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    endpoint = args.ollama_uri.rstrip("/") + "/api/chat"
    for case in (item for item in cases if item["split"] == split):
        records.append(evaluate_case(case, split, args, renderer, endpoint))
    return records, metrics(split, records)


def evaluate_case(
    case: dict[str, Any],
    split: str,
    args: Any,
    renderer: str,
    endpoint: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    frame_error = None
    response_error = None
    response = None
    raw = None
    usage: dict[str, Any] = {}
    try:
        frame = compile_frame(case["questionRu"], args.swipl, args.lab_root)
    except Exception as exc:
        frame_error = str(exc)
        frame = {"decision": {}}
    frame_checks = score_case(case, frame.get("decision"), frame_error)
    if frame_error is None:
        try:
            result = _post_json(
                endpoint,
                _payload(args, renderer, frame),
                args.timeout_seconds,
            )
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
    language = answer_checks(response)
    return {
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
        "answerChecks": language,
    }


def answer_checks(response: dict[str, Any] | None) -> dict[str, bool]:
    answer = "" if response is None else str(response.get("answerRu") or "").strip()
    return {
        "nonEmpty": bool(answer),
        "hasCyrillic": bool(CYRILLIC.search(answer)),
    }


def _payload(args: Any, renderer: str, frame: dict[str, Any]) -> dict[str, Any]:
    return {
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


def metrics(split: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    count = lambda key: sum(1 for item in records if item["checks"][key])
    answer_count = lambda key: sum(
        1 for item in records if item["answerChecks"][key]
    )
    return {
        "split": split,
        "totalCases": len(records),
        "framePassedCases": sum(1 for item in records if item["frameChecks"]["passed"]),
        "renderedPassedCases": count("passed"),
        "actionCorrect": count("actionCorrect"),
        "statusCorrect": count("statusCorrect"),
        "materialCorrect": count("materialCorrect"),
        "askFieldCorrect": count("askFieldCorrect"),
        "answerRuNonEmpty": answer_count("nonEmpty"),
        "answerRuHasCyrillic": answer_count("hasCyrillic"),
        "frameErrors": sum(1 for item in records if item["frameError"]),
        "runnerErrors": sum(1 for item in records if item["runnerError"]),
        "elapsedMs": sum(item["elapsedMs"] for item in records),
        "promptEvalCount": sum(
            int(item["usage"].get("promptEvalCount") or 0) for item in records
        ),
        "evalCount": sum(int(item["usage"].get("evalCount") or 0) for item in records),
    }
