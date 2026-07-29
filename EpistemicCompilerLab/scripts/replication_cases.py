#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from compiled_frame_core import query_material

DATES = {
    20260630: {
        "words": "30 июня 2026",
        "dotted": "30.06.2026",
        "iso": "2026-06-30",
    },
    20260701: {
        "words": "1 июля 2026",
        "dotted": "01.07.2026",
        "iso": "2026-07-01",
    },
    20260810: {
        "words": "10 августа 2026",
        "dotted": "10.08.2026",
        "iso": "2026-08-10",
    },
}
KINDS = {"success", "unknown", "missing_date", "missing_revision"}


def validate_generated(
    value: dict[str, Any],
    old_questions: set[str],
) -> list[dict[str, Any]]:
    cases = value.get("cases")
    if value.get("schemaVersion") != 1 or not isinstance(cases, list):
        raise ValueError("bad replication response envelope")
    if len(cases) != 24:
        raise ValueError(f"replication generator returned {len(cases)} cases")
    ids = [str(item.get("id") or "") for item in cases]
    questions = [str(item.get("questionRu") or "").strip() for item in cases]
    if len(set(ids)) != 24 or not all(item.startswith("rep-") for item in ids):
        raise ValueError("replication IDs must be unique and start with rep-")
    if len(set(questions)) != 24 or any(question in old_questions for question in questions):
        raise ValueError("replication questions must be new and unique")
    counts = Counter(str(item.get("caseKind")) for item in cases)
    if set(counts) != KINDS or any(counts[kind] != 6 for kind in KINDS):
        raise ValueError(f"replication kind balance is invalid: {dict(counts)}")
    for item, question in zip(cases, questions):
        _validate_case(item, question)
    return cases


def _validate_case(item: dict[str, Any], question: str) -> None:
    kind = str(item["caseKind"])
    revision = str(item["revision"])
    date = int(item["date"])
    style = str(item["dateStyle"])
    lowered = question.lower()
    if not 15 <= len(question) <= 300 or "asd" in lowered:
        raise ValueError(f"bad question content: {item['id']}")
    letters = set(re.findall(r"(?i)(?<![a-zа-я])[abc](?![a-zа-я])", lowered))
    if revision == "missing":
        if letters or kind != "missing_revision":
            raise ValueError(f"revision annotation mismatch: {item['id']}")
    elif revision not in letters:
        raise ValueError(f"revision is not explicit: {item['id']}")
    all_dates = [text for styles in DATES.values() for text in styles.values()]
    found_dates = [text for text in all_dates if text in lowered]
    if date == 0:
        if style != "none" or kind != "missing_date" or found_dates or "2026" in lowered:
            raise ValueError(f"missing-date annotation mismatch: {item['id']}")
    else:
        expected_text = DATES[date][style]
        if expected_text not in lowered or len(found_dates) != 1:
            raise ValueError(f"date annotation mismatch: {item['id']}")
    if kind == "unknown" and revision != "c":
        raise ValueError(f"unknown case must use revision C: {item['id']}")
    if kind == "success" and revision not in {"a", "b"}:
        raise ValueError(f"success case has invalid revision: {item['id']}")


def compile_cases(
    cases: list[dict[str, Any]],
    swipl: str,
    lab_root: Path,
) -> list[dict[str, Any]]:
    return [
        {
            "schemaVersion": 1,
            "id": item["id"],
            "split": "replication",
            "questionRu": item["questionRu"],
            "expected": _expected(item, swipl, lab_root),
            "annotation": {
                "caseKind": item["caseKind"],
                "revision": item["revision"],
                "date": item["date"],
                "dateStyle": item["dateStyle"],
                "hasDistractor": item["hasDistractor"],
            },
        }
        for item in cases
    ]


def _expected(item: dict[str, Any], swipl: str, lab_root: Path) -> dict[str, Any]:
    kind = item["caseKind"]
    if kind == "missing_date":
        return {"action": "ask_user", "status": "need_user", "material": None, "askField": "date"}
    if kind == "missing_revision":
        return {"action": "ask_user", "status": "need_user", "material": None, "askField": "revision"}
    result = query_material(swipl, lab_root, item["revision"], int(item["date"]))
    solutions = result.get("solutions") or []
    material = solutions[0].get("material") if len(solutions) == 1 else None
    status = "success" if material else "unknown"
    return {"action": "answer", "status": status, "material": material, "askField": None}


def write_jsonl(path: Path, cases: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in cases),
        encoding="utf-8",
    )
