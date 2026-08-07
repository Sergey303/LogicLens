#!/usr/bin/env python3
"""Fail-closed semantic validation for WP-003 related-work remediation."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT / "research-execution"
PACKET = Path(__file__).resolve().parent
MATRIX = RESEARCH / "RELATED_WORK_MATRIX.csv"
LOG = RESEARCH / "RELATED_WORK_SEARCH_LOG.yaml"
BOUNDARY = RESEARCH / "NOVELTY_BOUNDARY.md"
NEAREST_MD = RESEARCH / "NEAREST_PRIOR_WORK.md"
LEDGER = PACKET / "DIMENSION_LEDGER_ALL_2026-08-07.csv"
SCREENING = PACKET / "SCREENING_LEDGER_2026-08-07.csv"
ROUNDS = PACKET / "SATURATION_ROUNDS_2026-08-07.csv"
STRUCTURED = PACKET / "NEAREST_WORK_STRUCTURED_2026-08-07.csv"
RANKING_RULE = PACKET / "NEAREST_RANKING_RULE_2026-08-07.md"

SCORES = {"yes", "partial", "no", "unclear"}
DIMENSIONS = [
    "d1_fixed_weight_small_open",
    "d2_matched_interface_contrast",
    "d3_trusted_deterministic_semantics",
    "d4_four_state_epistemic_status",
    "d5_verified_result_renderer",
    "d6_structure_and_copy_controls",
    "d7_independent_layer_oracle",
]
REQUIRED_NEAREST = [
    "rank", "source_id", "title", "exact_task", "model_scale", "weights_updated",
    "runtime", "baselines", "data", "evaluation", "distinction_from_flagship", "evidence",
]
ANCHORS = ["RW-042", "RW-038", "RW-039"]
PROHIBITED_POSITIVE = [
    re.compile(r"\bwe\s+(?:are|introduce|present)\s+(?:the\s+)?first\b", re.I),
    re.compile(r"\bour\s+(?:method|approach|architecture)\s+is\s+unique\b", re.I),
    re.compile(r"\bunprecedented\b", re.I),
]


class ContractError(RuntimeError):
    pass


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        result = list(csv.DictReader(handle))
    if not result:
        raise ContractError(f"empty CSV: {path}")
    return result


def required_files() -> None:
    for path in (MATRIX, LOG, BOUNDARY, NEAREST_MD, LEDGER, SCREENING, ROUNDS, STRUCTURED, RANKING_RULE):
        if not path.is_file():
            raise ContractError(f"missing required artifact: {path}")


def unique(values: list[str], label: str) -> None:
    if any(not value.strip() for value in values):
        raise ContractError(f"{label}: blank value")
    if len(values) != len(set(values)):
        raise ContractError(f"{label}: duplicate value")


def validate_matrix() -> tuple[list[dict[str, str]], set[str]]:
    matrix = rows(MATRIX)
    if len(matrix) < 30:
        raise ContractError(f"matrix has only {len(matrix)} primary sources")
    ids = [row.get("source_id", "") for row in matrix]
    urls = [row.get("primary_url", "") for row in matrix]
    unique(ids, "matrix source_id")
    unique(urls, "matrix primary_url")
    required = [
        "source_id", "title", "year", "family", "primary_url", "weights_updated",
        "external_runtime_or_tool", "occupied_claim", "distinction_from_flagship", "inclusion_reason",
    ]
    for row in matrix:
        for field in required:
            if not row.get(field, "").strip():
                raise ContractError(f"{row.get('source_id')}: missing matrix field {field}")
    return matrix, set(ids)


def validate_dimension_ledger(matrix_ids: set[str]) -> None:
    ledger = rows(LEDGER)
    ids = [row.get("source_id", "") for row in ledger]
    unique(ids, "dimension ledger source_id")
    ledger_ids = set(ids)
    if ledger_ids != matrix_ids:
        missing = sorted(matrix_ids - ledger_ids)
        extra = sorted(ledger_ids - matrix_ids)
        raise ContractError(f"dimension ledger ID mismatch; missing={missing}, extra={extra}")
    for row in ledger:
        yes_count = 0
        for field in DIMENSIONS:
            value = row.get(field, "").strip().lower()
            if value not in SCORES:
                raise ContractError(f"{row['source_id']}: invalid {field}={value!r}")
            yes_count += value == "yes"
        declared = row.get("strict_yes_count", "")
        if declared != str(yes_count):
            raise ContractError(
                f"{row['source_id']}: strict_yes_count={declared!r}, computed={yes_count}"
            )
        if not row.get("evidence_locator", "").strip():
            raise ContractError(f"{row['source_id']}: evidence locator missing")


def validate_nearest(matrix_ids: set[str]) -> set[str]:
    nearest = rows(STRUCTURED)
    if len(nearest) < 8:
        raise ContractError("structured nearest table must contain at least eight comparisons")
    ranks = [int(row["rank"]) for row in nearest]
    if ranks != list(range(1, len(nearest) + 1)):
        raise ContractError(f"nearest ranks are not contiguous: {ranks}")
    ids = [row["source_id"] for row in nearest]
    unique(ids, "structured nearest source_id")
    if ids[:3] != ANCHORS:
        raise ContractError(f"top architecture anchors must be {ANCHORS}, got {ids[:3]}")
    for row in nearest:
        if row["source_id"] not in matrix_ids:
            raise ContractError(f"nearest ID absent from matrix: {row['source_id']}")
        for field in REQUIRED_NEAREST:
            if not row.get(field, "").strip():
                raise ContractError(f"{row['source_id']}: missing nearest field {field}")
    mandated = {"RW-042", "RW-038", "RW-039", "RW-043", "RW-003", "RW-002", "RW-004", "RW-005"}
    missing = mandated - set(ids)
    if missing:
        raise ContractError(f"independent-review comparison set missing: {sorted(missing)}")
    return set(ids)


def validate_screening_and_rounds(matrix_ids: set[str]) -> None:
    screening = rows(SCREENING)
    candidate_ids = [row.get("candidate_id", "") for row in screening]
    unique(candidate_ids, "screening candidate_id")
    screening_ids = set(candidate_ids)
    source_ids = {row.get("source_id", "") for row in screening if row.get("source_id", "").strip()}
    if not source_ids <= matrix_ids:
        raise ContractError(f"screening references unknown source IDs: {sorted(source_ids - matrix_ids)}")
    for row in screening:
        if not row.get("primary_url", "").strip() or not row.get("retrieved_on", "").strip():
            raise ContractError(f"{row['candidate_id']}: missing primary URL or retrieval date")
        disposition = row.get("disposition", "")
        if disposition == "exclude" and not row.get("exclusion_reason", "").strip():
            raise ContractError(f"{row['candidate_id']}: exclusion reason missing")
        for field in DIMENSIONS:
            if row.get(field, "").strip().lower() not in SCORES:
                raise ContractError(f"{row['candidate_id']}: invalid screening dimension {field}")
        if not row.get("evidence_locator", "").strip():
            raise ContractError(f"{row['candidate_id']}: evidence locator missing")

    rounds = rows(ROUNDS)
    if len(rounds) < 2:
        raise ContractError("at least two fresh saturation rounds required")
    latest = rounds[-2:]
    for row in latest:
        if row.get("saturation_usable", "").strip().lower() != "yes":
            raise ContractError(f"{row['round_id']}: not usable for saturation")
        if row.get("threshold_matches", "").strip() != "0":
            raise ContractError(f"{row['round_id']}: threshold matches are nonzero")
        count = int(row.get("retrieved_unique_primary_candidates", "0"))
        screened = [item.strip() for item in row.get("screened_candidate_ids", "").split(";") if item.strip()]
        if count != len(set(screened)):
            raise ContractError(
                f"{row['round_id']}: retrieval count={count}, unique screened={len(set(screened))}"
            )
        missing = set(screened) - screening_ids
        if missing:
            raise ContractError(f"{row['round_id']}: screened candidates absent from ledger: {sorted(missing)}")
        if not row.get("queries", "").strip() or not row.get("exact_threshold_rule", "").strip():
            raise ContractError(f"{row['round_id']}: missing query/threshold audit")


def scalar(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text, re.M)
    if not match:
        raise ContractError(f"search log missing {label}")
    return match.group(1)


def validate_search_log(matrix_count: int, nearest_ids: set[str]) -> None:
    text = LOG.read_text(encoding="utf-8")
    source_count = int(scalar(r"^source_count:\s*(\d+)\s*$", text, "source_count"))
    if source_count != matrix_count:
        raise ContractError(f"search-log source_count={source_count}, matrix={matrix_count}")
    as_of = scalar(r"^as_of:\s*['\"]?([^'\"\n]+)", text, "as_of")
    if as_of.strip() < "2026-08-07":
        raise ContractError(f"search log is stale: as_of={as_of}")
    if "Q11" not in text or "Q12" not in text:
        raise ContractError("search log must record fresh Q11/Q12 replacement rounds")
    if "legacy" not in text.lower() or "Q1-Q10" not in text:
        raise ContractError("search log must state that legacy Q1-Q10 are not reproducible saturation evidence")
    match = re.search(r"^nearest_source_ids:\s*\[([^\]]+)\]", text, re.M)
    if not match:
        raise ContractError("search log nearest_source_ids missing")
    logged = {item.strip() for item in match.group(1).split(",") if item.strip()}
    if not {"RW-042", "RW-038", "RW-039"} <= logged:
        raise ContractError("search log omits mandatory architecture anchors")
    if not logged <= nearest_ids:
        raise ContractError(f"search log nearest IDs absent from structured table: {sorted(logged-nearest_ids)}")


def validate_priority_language() -> None:
    for path in (BOUNDARY, NEAREST_MD):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            lower = line.lower()
            negative_context = any(token in lower for token in (
                "delete", "not support", "may not", "cannot", "no defensible", "not a", "not `first`",
                "without priority", "prohibit", "forbidden", "never", "does not support",
            ))
            if negative_context:
                continue
            for pattern in PROHIBITED_POSITIVE:
                if pattern.search(line):
                    raise ContractError(f"prohibited priority wording in {path.name}:{number}: {line.strip()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    required_files()
    matrix, matrix_ids = validate_matrix()
    validate_dimension_ledger(matrix_ids)
    nearest_ids = validate_nearest(matrix_ids)
    validate_screening_and_rounds(matrix_ids)
    validate_search_log(len(matrix), nearest_ids)
    validate_priority_language()
    print(f"WP-003 semantic contract passed: {len(matrix)} primary sources, {len(nearest_ids)} structured comparisons")
    print("Fresh Q11/Q12 saturation rounds are reproducible and contain zero five-of-seven matches")
    print("This validator does not constitute independent novelty acceptance or GATE-001 approval")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, OSError, ValueError, csv.Error) as exc:
        print(f"WP-003 semantic contract failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
