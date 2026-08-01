#!/usr/bin/env python3
from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Iterator

from strict_epistemic_benchmark_core import assertion_record, oracle_frame, primary_case
from strict_epistemic_benchmark_data import (
    CLARIFICATION_TEMPLATES,
    SEED,
    SPLITS,
    entity_pairs,
    status_plan,
)


def clarification_context(
    case_id: str,
    field: str,
    family: int,
    pairs: Iterator[tuple[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, str], str, str, str, str]:
    first = next(pairs)
    second = next(pairs)
    third = next(pairs)
    fourth = next(pairs)
    if field == "revision":
        material = first[1]
        specs = [
            (first[0], material, "positive"),
            (second[0], material, "negative"),
            (*third, "positive"),
            (*fourth, "negative"),
        ]
        revision = "missing"
    else:
        revision = first[0]
        specs = [
            (revision, first[1], "positive"),
            (revision, second[1], "negative"),
            (*third, "positive"),
            (*fourth, "negative"),
        ]
        material = "missing"
    random.Random(SEED + sum(ord(ch) for ch in case_id)).shuffle(specs)
    catalog = [
        assertion_record(case_id, i, rev, mat, polarity, family)
        for i, (rev, mat, polarity) in enumerate(specs)
    ]
    aliases = {
        item["canonicalId"]: f"ev-{case_id.split('-', 1)[1]}-{i + 1}"
        for i, item in enumerate(catalog)
    }
    context = [
        {"id": aliases[item["canonicalId"]], "source": item["source"], "textRu": item["textRu"]}
        for item in catalog
    ]
    return context, catalog, aliases, revision, material, first[0], first[1]


def clarification_case(
    split: str,
    split_index: int,
    field: str,
    pairs: Iterator[tuple[str, str]],
    swipl: str,
    lab: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    family = 2
    case_id = f"se-{split}-missing-{field}"
    context, catalog, aliases, revision, material, query_revision, query_material = (
        clarification_context(case_id, field, family, pairs)
    )
    template_index = 0 if field == "revision" else 1
    question = CLARIFICATION_TEMPLATES[split][template_index].format(
        r=query_revision, m=query_material
    )
    frame = oracle_frame(swipl, lab, revision, material, [], [])
    case = {
        "schemaVersion": 2, "id": case_id, "split": split,
        "caseKind": "clarification", "questionRu": question, "sourceContext": context,
        "expected": frame,
        "annotation": {
            "revision": revision, "material": material, "statusClass": None,
            "paraphraseFamily": 0, "evidenceAliasMap": aliases,
            "uniqueProposition": None,
        },
    }
    return case, catalog


def build_benchmark(swipl: str, lab: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    pairs = iter(entity_pairs())
    cases: list[dict[str, Any]] = []
    catalog: list[dict[str, str]] = []
    for split_index, split in enumerate(SPLITS):
        for ordinal, status in enumerate(status_plan(split_index)):
            case, records = primary_case(
                split, split_index, ordinal, status, next(pairs), pairs, swipl, lab
            )
            cases.append(case)
            catalog.extend(records)
        for field in ("revision", "material"):
            case, records = clarification_case(
                split, split_index, field, pairs, swipl, lab
            )
            cases.append(case)
            catalog.extend(records)
    return cases, catalog
