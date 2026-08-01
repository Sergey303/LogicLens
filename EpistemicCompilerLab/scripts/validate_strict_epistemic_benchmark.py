#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from strict_epistemic_benchmark_core import oracle_frame
SPLITS = ("train", "dev", "holdout", "replication")
STATUSES = ("supported", "refuted", "unknown", "conflicting")
def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-root", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--source-catalog", required=True, type=Path)
    parser.add_argument("--swipl", required=True)
    return parser.parse_args()
def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
def canonical_context(case: dict, catalog: dict[str, dict]) -> list[dict]:
    aliases = case["annotation"].get("evidenceAliasMap") or {}
    reverse = {visible: canonical for canonical, visible in aliases.items()}
    if len(reverse) != 4 or len(aliases) != 4:
        raise AssertionError(f"{case['id']} alias map must contain four unique IDs")
    if any(canonical == visible for canonical, visible in aliases.items()):
        raise AssertionError(f"{case['id']} canonical IDs must be hidden")
    records = []
    for visible in case["sourceContext"]:
        canonical_id = reverse.get(visible["id"])
        record = catalog.get(canonical_id)
        if not record:
            raise AssertionError(f"{case['id']} missing catalog record")
        if visible["source"] != record["source"] or visible["textRu"] != record["textRu"]:
            raise AssertionError(f"{case['id']} visible source differs from catalog")
        records.append(record)
    return records
def main() -> int:
    cfg = args()
    cases = load_jsonl(cfg.cases)
    rows = load_jsonl(cfg.source_catalog)
    catalog = {item["canonicalId"]: item for item in rows}
    if len(rows) != 224 or len(catalog) != 224:
        raise AssertionError("source catalog must contain 224 unique assertions")
    if len(cases) != 56 or len({case["id"] for case in cases}) != 56:
        raise AssertionError("benchmark must contain 56 unique cases")
    if len({case["questionRu"] for case in cases}) != 56:
        raise AssertionError("questions must be unique")
    if any(case.get("schemaVersion") != 3 for case in cases):
        raise AssertionError("all cases must use schemaVersion 3")
    splits = Counter(case["split"] for case in cases)
    if any(splits[name] != 14 for name in SPLITS):
        raise AssertionError(f"bad split balance: {dict(splits)}")
    primary = [case for case in cases if case["caseKind"] == "epistemic"]
    statuses = Counter(case["expected"]["status"] for case in primary)
    if any(statuses[name] != 12 for name in STATUSES):
        raise AssertionError(f"bad status balance: {dict(statuses)}")
    family_status = Counter(
        (case["split"], case["annotation"]["paraphraseFamily"], case["expected"]["status"])
        for case in primary
    )
    if any(family_status[(split, family, status)] != 1
           for split in SPLITS for family in (1, 2, 3) for status in STATUSES):
        raise AssertionError("each question family must contain every status once")
    propositions = [case["annotation"]["uniqueProposition"] for case in primary]
    revisions = [case["annotation"]["revision"] for case in primary]
    materials = [case["annotation"]["material"] for case in primary]
    if len(primary) != 48 or len(set(propositions)) != 48:
        raise AssertionError("primary cases must contain 48 unique propositions")
    if len(set(revisions)) != 48 or len(set(materials)) != 48:
        raise AssertionError("primary entity tokens must be unique")
    if any(not re.fullmatch(r"RX-[0-9A-F]{8}", value) for value in revisions):
        raise AssertionError("revision tokens are not opaque")
    if any(not re.fullmatch(r"MX-[0-9A-F]{8}", value) for value in materials):
        raise AssertionError("material tokens are not opaque")
    if any(rev[3:] == mat[3:] for rev, mat in zip(revisions, materials)):
        raise AssertionError("revision/material token relation leaked")
    visible = json.dumps(
        [{"questionRu": c["questionRu"], "sourceContext": c["sourceContext"]} for c in cases]
    ).lower()
    if any(token in visible for token in (*STATUSES, *SPLITS)):
        raise AssertionError("status or split labels leaked into visible inputs")
    if "probab" in visible or "fuzzy" in visible:
        raise AssertionError("probability/fuzzy constructs are forbidden")
    used_canonical: list[str] = []
    for case in cases:
        if not re.fullmatch(r"se-[0-9A-F]{12}", case["id"]):
            raise AssertionError(f"{case['id']} case ID is not opaque")
        if len(case["sourceContext"]) != 4:
            raise AssertionError(f"{case['id']} context size must be four")
        if any(not re.fullmatch(r"ev-[0-9A-F]{12}", item["id"])
               or not re.fullmatch(r"DOC-[0-9A-F]{12}", item["source"])
               for item in case["sourceContext"]):
            raise AssertionError(f"{case['id']} visible IDs are not opaque")
        records = canonical_context(case, catalog)
        used_canonical.extend(item["canonicalId"] for item in records)
        if Counter(item["polarity"] for item in records) != {"positive": 2, "negative": 2}:
            raise AssertionError(f"{case['id']} context polarity balance changed")
        ann = case["annotation"]
        positive = [item["canonicalId"] for item in records
                    if item["revision"] == ann["revision"] and item["material"] == ann["material"]
                    and item["polarity"] == "positive"]
        negative = [item["canonicalId"] for item in records
                    if item["revision"] == ann["revision"] and item["material"] == ann["material"]
                    and item["polarity"] == "negative"]
        frame = oracle_frame(cfg.swipl, cfg.lab_root, ann["revision"], ann["material"], positive, negative)
        aliases = ann["evidenceAliasMap"]
        expected = case["expected"]
        if expected["evidence"] != sorted(aliases[item] for item in frame["evidence"]):
            raise AssertionError(f"{case['id']} evidence mismatch")
        if any(expected.get(field) != frame.get(field)
               for field in ("status", "action", "reason", "askField", "proposition")):
            raise AssertionError(f"{case['id']} oracle frame mismatch")
        if case["caseKind"] == "epistemic" and expected["status"] != ann["statusClass"]:
            raise AssertionError(f"{case['id']} status annotation mismatch")
        if case["caseKind"] == "clarification":
            missing = [name for name in ("revision", "material") if ann[name] == "missing"]
            if len(missing) != 1 or expected["askField"] != missing[0]:
                raise AssertionError(f"{case['id']} clarification mismatch")
            values = {item[missing[0]] for item in records}
            if len(values) < 2:
                raise AssertionError(f"{case['id']} missing field is inferable")
    if len(used_canonical) != 224 or set(used_canonical) != set(catalog):
        raise AssertionError("source assertions must be case-local and used exactly once")
    print(json.dumps({
        "cases": len(cases), "sourceAssertions": len(catalog),
        "uniquePrimaryPropositions": len(set(propositions)),
        "sha256": hashlib.sha256(cfg.cases.read_bytes()).hexdigest(),
        "sourceSha256": hashlib.sha256(cfg.source_catalog.read_bytes()).hexdigest(),
        "splits": splits, "statuses": statuses,
        "clarificationCases": len(cases) - len(primary), "passed": len(cases),
    }, ensure_ascii=False, default=dict))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
