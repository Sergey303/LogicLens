#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _post_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {body}") from exc


def _same(actual: Any, expected: Any) -> bool:
    if actual is None or expected is None:
        return actual is expected
    return str(actual).lower() == str(expected).lower()


def score_case(case: dict[str, Any], parsed: dict[str, Any] | None, error: str | None) -> dict[str, Any]:
    expected = case["expected"]
    runner_ok = error is None and isinstance(parsed, dict)
    action_ok = runner_ok and _same(parsed.get("action"), expected["action"])
    status_ok = runner_ok and _same(parsed.get("status"), expected["status"])
    material_ok = runner_ok and _same(parsed.get("material"), expected["material"])
    ask_ok = runner_ok and _same(parsed.get("askField"), expected["askField"])
    return {
        "passed": bool(runner_ok and action_ok and status_ok and material_ok and ask_ok),
        "runnerOk": runner_ok,
        "actionCorrect": bool(action_ok),
        "statusCorrect": bool(status_ok),
        "materialCorrect": bool(material_ok),
        "askFieldCorrect": bool(ask_ok),
    }


def evaluate(
    cases: list[dict[str, Any]],
    split: str,
    model: str,
    student_prompt: str,
    prolog_text: str,
    seed: int,
    ollama_uri: str,
    timeout: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    endpoint = ollama_uri.rstrip("/") + "/api/chat"
    selected = [case for case in cases if case["split"] == split]
    for case in selected:
        user_prompt = (
            "Approved Prolog knowledge representation:\n"
            "---BEGIN PROLOG---\n"
            f"{prolog_text}\n"
            "---END PROLOG---\n\n"
            f"User question:\n{case['questionRu']}"
        )
        payload = {
            "model": model,
            "stream": False,
            "format": "json",
            "keep_alive": "10m",
            "messages": [
                {"role": "system", "content": student_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0, "seed": seed, "num_predict": 256},
        }
        started = time.perf_counter()
        parsed = None
        raw = None
        error = None
        usage: dict[str, Any] = {}
        try:
            response = _post_json(endpoint, payload, timeout)
            raw = str(response["message"]["content"])
            parsed = json.loads(raw)
            usage = {
                "promptEvalCount": response.get("prompt_eval_count"),
                "evalCount": response.get("eval_count"),
                "totalDurationNs": response.get("total_duration"),
            }
        except Exception as exc:
            error = str(exc)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        checks = score_case(case, parsed, error)
        records.append({
            "caseId": case["id"],
            "split": split,
            "questionRu": case["questionRu"],
            "expected": case["expected"],
            "response": parsed,
            "raw": raw,
            "runnerError": error,
            "elapsedMs": elapsed_ms,
            "usage": usage,
            "checks": checks,
        })

    def count(name: str) -> int:
        return sum(1 for record in records if record["checks"][name])

    metrics = {
        "split": split,
        "totalCases": len(records),
        "passedCases": count("passed"),
        "actionCorrect": count("actionCorrect"),
        "statusCorrect": count("statusCorrect"),
        "materialCorrect": count("materialCorrect"),
        "askFieldCorrect": count("askFieldCorrect"),
        "runnerErrors": sum(1 for r in records if r["runnerError"]),
        "elapsedMs": sum(r["elapsedMs"] for r in records),
        "promptEvalCount": sum(int(r["usage"].get("promptEvalCount") or 0) for r in records),
        "evalCount": sum(int(r["usage"].get("evalCount") or 0) for r in records),
    }
    return records, metrics


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in records),
        encoding="utf-8",
    )
