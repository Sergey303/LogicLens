#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from strict_epistemic_benchmark_core import oracle_frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-root", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--source-catalog", required=True, type=Path)
    parser.add_argument("--swipl", required=True)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def canonical_context(case: dict, catalog: dict[str, dict]) -> list[dict]:
    aliases = case["annotation"].get("evidenceAliasMap") or {}
    reverse = {visible: canonical for canonical, visible in aliases.items()}
    if len(reverse) != len(aliases) or len(reverse) != 4:
        raise AssertionError(f"{case['id']} alias map must contain four unique IDs")
    records = []
    for visible in case["sourceContext"]:
        canonical_id = reverse.get(visible["id"])
        record = catalog.get(canonical_id)
        if not record:
            raise AssertionError(f"{case['id']} missing catalog record: {visible['id']}")
        if visible["source"] != record["source"] or visible["textRu"] != record["textRu"]:
            raise AssertionError(f"{case['id']} visible source differs from catalog")
        records.append(record)
    return records


def main() -> int:
    args = parse_args()
    cases = load_jsonl(args.cases)
    catalog_rows = load_jsonl(args.source_catalog)
    catalog = {item["canonicalId"]: item for item in catalog_rows}
    if len(catalog_rows) != 224 or len(catalog) != 224:
        raise AssertionError("source catalog must contain 224 unique assertions")
    if len(cases) != 56 or len({case["id"] for case in cases}) != 56:
        raise AssertionError("benchmark must contain 56 unique cases")
    if len({case["questionRu"] for case in cases}) != 56:
        raise AssertionError("questions must be unique")

    splits = Counter(case["split"] for case in cases)
    if any(splits[name] != 14 for name in ("train", "dev", "holdout", "replication")):
        raise AssertionError(f"bad split balance: {dict(splits)}")
    primary = [case for case in cases if case["caseKind"] == "epistemic"]
    statuses = Counter(case["expected"]["status"] for case in primary)
    if any(statuses[name] != 12 for name in ("supported", "refuted", "unknown", "conflicting")):
        raise AssertionError(f"bad status balance: {dict(statuses)}")
    propositions = [case["annotation"]["uniqueProposition"] for case in primary]
    if len(primary) != 48 or len(set(propositions)) != 48:
        raise AssertionError("primary cases must contain 48 unique propositions")

    visible = json.dumps(
        [{"questionRu": c["questionRu"], "sourceContext": c["sourceContext"]} for c in cases]
    ).lower()
    if any(token in visible for token in ("supported", "refuted", "unknown", "conflicting")):
        raise AssertionError("status labels leaked into visible inputs")
    if "probab" in visible or "fuzzy" in visible:
        raise AssertionError("probability/fuzzy constructs are forbidden")

    for case in cases:
        if len(case["sourceContext"]) != 4:
            raise AssertionError(f"{case['id']} context size must be four")
        records = canonical_context(case, catalog)
        polarities = Counter(item["polarity"] for item in records)
        if polarities != {"positive": 2, "negative": 2}:
            raise AssertionError(f"{case['id']} context polarity balance changed")
        annotation = case["annotation"]
        revision = annotation["revision"]
        material = annotation["material"]
        positive = [
            item["canonicalId"] for item in records
            if item["revision"] == revision and item["material"] == material
            and item["polarity"] == "positive"
        ]
        negative = [
            item["canonicalId"] for item in records
            if item["revision"] == revision and item["material"] == material
            and item["polarity"] == "negative"
        ]
        frame = oracle_frame(
            args.swipl, args.lab_root, revision, material, positive, negative
        )
        aliases = annotation["evidenceAliasMap"]
        expected_evidence = sorted(aliases[item] for item in frame["evidence"])
        expected = case["expected"]
        for field in ("status", "action", "reason", "askField", "proposition"):
            if expected.get(field) != frame.get(field):
                raise AssertionError(f"{case['id']} {field} mismatch")
        if expected["evidence"] != expected_evidence:
            raise AssertionError(f"{case['id']} evidence mismatch")
        if case["caseKind"] == "epistemic" and expected["status"] != annotation["statusClass"]:
            raise AssertionError(f"{case['id']} status annotation mismatch")
        if case["caseKind"] == "clarification":
            missing = [name for name in ("revision", "material") if annotation[name] == "missing"]
            if len(missing) != 1 or expected["askField"] != missing[0]:
                raise AssertionError(f"{case['id']} clarification mismatch")

    print(json.dumps({
        "cases": len(cases),
        "sourceAssertions": len(catalog),
        "uniquePrimaryPropositions": len(set(propositions)),
        "sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        "sourceSha256": hashlib.sha256(args.source_catalog.read_bytes()).hexdigest(),
        "splits": splits,
        "statuses": statuses,
        "clarificationCases": len(cases) - len(primary),
        "passed": len(cases),
    }, ensure_ascii=False, default=dict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
