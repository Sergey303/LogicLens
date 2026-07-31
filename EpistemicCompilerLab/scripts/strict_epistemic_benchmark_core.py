#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

SPLITS = ("train", "dev", "holdout", "replication")
TARGETS = (
    ("supported", "revision_a"),
    ("refuted", "revision_b"),
    ("unknown", "revision_c"),
    ("conflicting", "revision_d"),
)
QUESTIONS = {
    "train": (
        "Подтверждают ли загруженные источники, что ревизия {r} использует материал {m}?",
        "Каков эпистемический статус утверждения «ревизия {r} использует {m}»?",
        "Можно ли уверенно утверждать по документам, что для ревизии {r} применяется {m}?",
    ),
    "dev": (
        "Следует ли из доступных свидетельств, что ревизия {r} работает с материалом {m}?",
        "Что говорят загруженные источники об утверждении: ревизия {r} — материал {m}?",
        "Есть ли достаточные основания считать, что ревизия {r} использует {m}?",
    ),
    "holdout": (
        "Установлено ли документами применение материала {m} в ревизии {r}?",
        "Как следует оценить тезис «для ревизии {r} предусмотрен {m}»?",
        "Позволяют ли источники однозначно сказать, что ревизия {r} использует {m}?",
    ),
    "replication": (
        "Доказано ли загруженными данными, что в ревизии {r} применяется {m}?",
        "Как классифицировать утверждение о применении {m} для ревизии {r}?",
        "Можно ли по доступным документам принять тезис: ревизия {r} использует {m}?",
    ),
}
ASSERTIONS = (
    ("ep_a_positive", "Source S-A-positive", "Для ревизии A утверждён материал ASD2."),
    ("ep_b_negative", "Source S-B-negative", "Ревизия B не использует ASD2 как утверждённый материал."),
    ("ep_d_positive", "Source S-D-positive", "Для ревизии D утверждён материал ASD2."),
    ("ep_d_negative", "Source S-D-negative", "Ревизия D не использует ASD2 как утверждённый материал."),
)
IRRELEVANT = (
    ("ep_e_positive", "Source S-E-positive", "Для ревизии E утверждён материал ASD7."),
    ("ep_f_negative", "Source S-F-negative", "Ревизия F не использует ASD9."),
)


def oracle_frame(swipl: str, lab: Path, revision: str, material: str) -> dict[str, Any]:
    completed = subprocess.run(
        [swipl, "-q", "-s", str(lab / "prolog" / "strict_epistemic_entry.pl"),
         "--", "request-frame", revision, material],
        text=True, encoding="utf-8", errors="strict", capture_output=True,
        check=False, timeout=60,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "strict epistemic query failed")
    return json.loads(completed.stdout)


def alias_map(split_index: int, family: int, include_irrelevant: bool) -> dict[str, str]:
    items = ASSERTIONS + (IRRELEVANT if include_irrelevant else ())
    if split_index == 0 and family == 0:
        return {item[0]: item[0] for item in items}
    return {item[0]: f"ev-{split_index + 1}{family + 1}-{i + 1}" for i, item in enumerate(items)}


def visible_context(split_index: int, family: int) -> tuple[list[dict[str, str]], dict[str, str], dict[str, Any]]:
    include_irrelevant = (split_index + family) % 2 == 1
    items = list(ASSERTIONS + (IRRELEVANT if include_irrelevant else ()))
    rotation = (split_index + family) % len(items)
    items = items[rotation:] + items[:rotation]
    aliases = alias_map(split_index, family, include_irrelevant)
    style = ("section", "document", "compact")[family]
    context = [
        {"id": aliases[item_id], "source": source if style != "compact" else source.replace("Source ", ""),
         "textRu": text}
        for item_id, source, text in items
    ]
    meta = {"orderVariant": rotation, "idsRenamed": any(k != v for k, v in aliases.items()),
            "includesIrrelevant": include_irrelevant, "provenanceStyle": style}
    return context, aliases, meta


def remap_evidence(evidence: list[str], aliases: dict[str, str]) -> list[str]:
    return sorted(aliases[item] for item in evidence)


def primary_case(split: str, split_index: int, status: str, revision: str, family: int,
                 swipl: str, lab: Path) -> dict[str, Any]:
    context, aliases, meta = visible_context(split_index, family)
    frame = oracle_frame(swipl, lab, revision, "asd2")
    if frame["status"] != status:
        raise AssertionError(f"oracle status mismatch: {revision} {frame}")
    return {
        "schemaVersion": 1, "id": f"se-{split}-{status}-{family + 1}", "split": split,
        "caseKind": "epistemic", "questionRu": QUESTIONS[split][family].format(
            r=revision[-1].upper(), m="ASD2"),
        "sourceContext": context,
        "expected": {"status": frame["status"], "action": frame["action"],
                     "reason": frame["reason"], "evidence": remap_evidence(frame["evidence"], aliases),
                     "askField": None},
        "annotation": {"revision": revision, "material": "asd2", "statusClass": status,
                       "paraphraseFamily": family + 1, **meta},
    }


def clarification_cases(split: str, split_index: int, swipl: str, lab: Path) -> list[dict[str, Any]]:
    context, _, meta = visible_context(split_index, 2)
    specs = (
        ("revision", "Подтверждается ли применение ASD2 для указанной ревизии?", "missing", "asd2"),
        ("material", "Каков статус утверждения о материале для ревизии A?", "revision_a", "missing"),
    )
    result = []
    for field, question, revision, material in specs:
        frame = oracle_frame(swipl, lab, revision, material)
        result.append({
            "schemaVersion": 1, "id": f"se-{split}-missing-{field}", "split": split,
            "caseKind": "clarification", "questionRu": question, "sourceContext": context,
            "expected": {"status": frame["status"], "action": frame["action"],
                         "reason": frame["reason"], "evidence": [], "askField": frame["askField"]},
            "annotation": {"revision": revision, "material": material, "statusClass": None,
                           "paraphraseFamily": 0, **meta},
        })
    return result
