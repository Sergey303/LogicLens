#!/usr/bin/env python3
from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path
from typing import Any, Iterator

from strict_epistemic_benchmark_data import (
    NEGATIVE_TEXTS,
    POSITIVE_TEXTS,
    QUESTION_TEMPLATES,
    SEED,
)


def oracle_frame(
    swipl: str,
    lab: Path,
    revision: str,
    material: str,
    positive: list[str],
    negative: list[str],
) -> dict[str, Any]:
    csv = lambda values: ",".join(values) if values else "none"
    cmd = [
        swipl, "-q", "-s", str(lab / "prolog" / "strict_epistemic_case_entry.pl"),
        "--", "case-frame", revision, material, csv(positive), csv(negative),
    ]
    completed = subprocess.run(
        cmd, text=True, encoding="utf-8", errors="strict",
        capture_output=True, check=False, timeout=60,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "case oracle failed")
    return json.loads(completed.stdout)


def assertion_record(
    case_id: str,
    index: int,
    revision: str,
    material: str,
    polarity: str,
    family: int,
) -> dict[str, str]:
    canonical = f"src-{case_id}-{index + 1}"
    source = f"DOC-{case_id.upper()}-{index + 1}"
    templates = POSITIVE_TEXTS if polarity == "positive" else NEGATIVE_TEXTS
    return {
        "canonicalId": canonical,
        "revision": revision,
        "material": material,
        "polarity": polarity,
        "source": source,
        "textRu": templates[family % 3].format(s=source, r=revision, m=material),
    }


def context_for(
    case_id: str,
    family: int,
    target: tuple[str, str],
    status: str,
    pairs: Iterator[tuple[str, str]],
    rng: random.Random,
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, str], list[str], list[str]]:
    target_polarities = {
        "supported": ("positive",),
        "refuted": ("negative",),
        "unknown": (),
        "conflicting": ("positive", "negative"),
    }[status]
    specs = [(target[0], target[1], polarity) for polarity in target_polarities]
    positive_needed = 2 - sum(p == "positive" for _, _, p in specs)
    negative_needed = 2 - sum(p == "negative" for _, _, p in specs)
    specs += [(*next(pairs), "positive") for _ in range(positive_needed)]
    specs += [(*next(pairs), "negative") for _ in range(negative_needed)]
    rng.shuffle(specs)

    catalog = [
        assertion_record(case_id, i, revision, material, polarity, family)
        for i, (revision, material, polarity) in enumerate(specs)
    ]
    rename = not (case_id.startswith("se-train") and family == 0)
    aliases = {
        item["canonicalId"]: (
            f"ev-{case_id.split('-', 1)[1]}-{i + 1}" if rename else item["canonicalId"]
        )
        for i, item in enumerate(catalog)
    }
    context = [
        {"id": aliases[item["canonicalId"]], "source": item["source"], "textRu": item["textRu"]}
        for item in catalog
    ]
    positive = [
        item["canonicalId"] for item in catalog
        if item["revision"] == target[0] and item["material"] == target[1]
        and item["polarity"] == "positive"
    ]
    negative = [
        item["canonicalId"] for item in catalog
        if item["revision"] == target[0] and item["material"] == target[1]
        and item["polarity"] == "negative"
    ]
    return context, catalog, aliases, positive, negative


def primary_case(
    split: str,
    split_index: int,
    ordinal: int,
    status: str,
    target: tuple[str, str],
    pairs: Iterator[tuple[str, str]],
    swipl: str,
    lab: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    family = ordinal % 3
    case_id = f"se-{split}-{ordinal + 1:02d}"
    rng = random.Random(SEED + split_index * 100 + ordinal)
    context, catalog, aliases, positive, negative = context_for(
        case_id, family, target, status, pairs, rng
    )
    frame = oracle_frame(swipl, lab, target[0], target[1], positive, negative)
    evidence = sorted(aliases[item] for item in frame["evidence"])
    question = QUESTION_TEMPLATES[split][family].format(r=target[0], m=target[1])
    case = {
        "schemaVersion": 2, "id": case_id, "split": split, "caseKind": "epistemic",
        "questionRu": question, "sourceContext": context,
        "expected": {**frame, "evidence": evidence},
        "annotation": {
            "revision": target[0], "material": target[1], "statusClass": status,
            "paraphraseFamily": family + 1, "evidenceAliasMap": aliases,
            "uniqueProposition": f"{target[0]}::{target[1]}",
        },
    }
    return case, catalog
