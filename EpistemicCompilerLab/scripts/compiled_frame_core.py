#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def parse_revision(question: str) -> str | None:
    patterns = (
        r"(?:ревизи(?:я|и|ю)|верси(?:я|и|ю))\s+([abc])\b",
        r"\b(?:для|в)\s+([abc])\b",
        r"\b([abc])\s+(?:с|начиная)\b",
    )
    lowered = question.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    return None


def parse_date(question: str) -> int | None:
    iso = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", question)
    if iso:
        return _date_int(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
    dotted = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(20\d{2})\b", question)
    if dotted:
        return _date_int(int(dotted.group(3)), int(dotted.group(2)), int(dotted.group(1)))
    names = "|".join(MONTHS)
    words = re.search(rf"\b(\d{{1,2}})\s+({names})\s+(20\d{{2}})\b", question.lower())
    if words:
        return _date_int(int(words.group(3)), MONTHS[words.group(2)], int(words.group(1)))
    return None


def _date_int(year: int, month: int, day: int) -> int:
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        raise ValueError(f"invalid calendar date: {year}-{month}-{day}")
    return year * 10000 + month * 100 + day


def query_material(swipl: str, lab_root: Path, revision: str, date: int) -> dict[str, Any]:
    completed = subprocess.run(
        [
            swipl,
            "-q",
            "-s",
            str(lab_root / "prolog" / "entry.pl"),
            "--",
            "current-material",
            revision,
            str(date),
        ],
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "SWI-Prolog query failed")
    return json.loads(completed.stdout)


def compile_frame(question: str, swipl: str, lab_root: Path) -> dict[str, Any]:
    revision = parse_revision(question)
    date = parse_date(question)
    inputs = {
        "revision": {"state": "present" if revision else "absent", "value": revision},
        "date": {"state": "present" if date else "absent", "value": date},
    }
    if revision is None or date is None:
        ask_field = "revision" if revision is None else "date"
        decision = {
            "action": "ask_user",
            "status": "need_user",
            "material": None,
            "askField": ask_field,
            "proof": [f"compiler:missing_{ask_field}"],
        }
    else:
        result = query_material(swipl, lab_root, revision, date)
        solutions = result.get("solutions") or []
        if result.get("status") == "success" and len(solutions) == 1:
            solution = solutions[0]
            decision = {
                "action": "answer",
                "status": "success",
                "material": solution.get("material"),
                "askField": None,
                "proof": solution.get("proof") or [],
            }
        else:
            decision = {
                "action": "answer",
                "status": "unknown",
                "material": None,
                "askField": None,
                "proof": ["compiler:no_verified_solution"],
            }
    return {
        "schemaVersion": 1,
        "compiler": "trusted-question-plus-prolog-v1",
        "inputs": inputs,
        "decision": decision,
    }
