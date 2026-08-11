#!/usr/bin/env python3
"""Fail-closed validation for the append-only WP-003 Q15 freshness remediation."""
from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parent
RESEARCH = PACKET.parents[1]
BASE_VALIDATOR = PACKET / "validate_wp003_semantics.py"
BASE_MATRIX = RESEARCH / "RELATED_WORK_MATRIX.csv"
SUPPLEMENT = PACKET / "Q15_RELATED_WORK_SUPPLEMENT.csv"
SCREENING = PACKET / "Q15_SCREENING_LEDGER_2026-08-11.csv"
DIMENSIONS_FILE = PACKET / "Q15_DIMENSION_LEDGER_2026-08-11.csv"
SATURATION = PACKET / "Q15_SATURATION_ROUND_2026-08-11.csv"
BOUNDARY_ADDENDUM = RESEARCH / "NOVELTY_BOUNDARY_Q15_ADDENDUM.md"
SEARCH_ADDENDUM = RESEARCH / "RELATED_WORK_SEARCH_LOG_Q15_ADDENDUM.md"

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
MANDATORY = {
    "RW-059": "ToolGate: Contract-Grounded and Verified Tool Execution for LLMs",
    "RW-060": "Text2Mem: A Unified Memory Operation Language for Memory Operating System",
    "RW-061": "LatentGate: Low-Latency Semantic Routing via Frozen-Backbone Probing of Small Language Models",
    "RW-062": "Rethinking Scale: Deployment Trade-offs of Small Language Models under Agent Paradigms",
    "RW-063": "Guidelines as Environments: A World Model Approach to Rule Following",
    "RW-064": "Don't Offer What Can't Be Done: Deterministic Executability Gating for LLM Skill Selection at Scale",
}
EXPECTED_CANDIDATES = {f"C-{number:03d}" for number in range(59, 65)}
EXPECTED_SOURCES = set(MANDATORY)
PROHIBITED_POSITIVE = [
    re.compile(r"\bwe\s+(?:are|introduce|present)\s+(?:the\s+)?first\b", re.I),
    re.compile(r"\bour\s+(?:method|approach|architecture)\s+is\s+unique\b", re.I),
    re.compile(r"\bunprecedented\b", re.I),
]


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def rows(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing required file: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        result = list(csv.DictReader(handle))
    require(bool(result), f"empty CSV: {path}")
    return result


def validate_base_snapshot() -> int:
    require(BASE_VALIDATOR.is_file(), "base WP-003 validator missing")
    completed = subprocess.run(
        [sys.executable, str(BASE_VALIDATOR)],
        cwd=str(RESEARCH.parent),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ContractError(
            "base WP-003 snapshot no longer validates before Q15 overlay:\n"
            + completed.stdout
            + completed.stderr
        )
    base = rows(BASE_MATRIX)
    require(len(base) == 58, f"Q15 expected frozen 58-source base snapshot, got {len(base)}")
    return len(base)


def validate_supplement(base_count: int) -> None:
    base = rows(BASE_MATRIX)
    supplement = rows(SUPPLEMENT)
    require(len(supplement) == 6, f"Q15 supplement must contain exactly 6 sources, got {len(supplement)}")

    base_ids = {row["source_id"] for row in base}
    base_urls = {row["primary_url"] for row in base}
    ids = [row.get("source_id", "").strip() for row in supplement]
    urls = [row.get("primary_url", "").strip() for row in supplement]
    require(set(ids) == EXPECTED_SOURCES, f"Q15 source IDs drift: {ids}")
    require(len(ids) == len(set(ids)), "duplicate Q15 source ID")
    require(len(urls) == len(set(urls)), "duplicate Q15 primary URL")
    require(not (set(ids) & base_ids), "Q15 source ID already exists in frozen base matrix")
    require(not (set(urls) & base_urls), "Q15 URL already exists in frozen base matrix")
    require(base_count + len(supplement) == 64, "combined matrix count must be 64")

    required = [
        "source_id", "title", "year", "venue", "family", "primary_url",
        "peer_reviewed", "weights_updated", "external_runtime_or_tool", "model_role",
        "occupied_claim", "distinction_from_flagship", "nearest_neighbor", "inclusion_reason",
    ]
    by_id = {row["source_id"]: row for row in supplement}
    for source_id, expected_title in MANDATORY.items():
        row = by_id[source_id]
        require(row["title"] == expected_title, f"{source_id}: title drift")
        for field in required:
            require(row.get(field, "").strip(), f"{source_id}: missing field {field}")
        require(row["year"] == "2026", f"{source_id}: year drift")
        require(row["primary_url"].startswith("https://"), f"{source_id}: non-HTTPS primary URL")


def validate_screening_and_dimensions() -> None:
    screening = rows(SCREENING)
    dimensions = rows(DIMENSIONS_FILE)
    require(len(screening) == 6, "Q15 screening must contain exactly 6 candidates")
    require(len(dimensions) == 6, "Q15 dimension ledger must contain exactly 6 sources")

    candidate_ids = {row.get("candidate_id", "").strip() for row in screening}
    source_ids = {row.get("source_id", "").strip() for row in screening}
    dimension_ids = {row.get("source_id", "").strip() for row in dimensions}
    require(candidate_ids == EXPECTED_CANDIDATES, f"Q15 candidate IDs drift: {sorted(candidate_ids)}")
    require(source_ids == EXPECTED_SOURCES, f"Q15 screening source IDs drift: {sorted(source_ids)}")
    require(dimension_ids == EXPECTED_SOURCES, f"Q15 dimension source IDs drift: {sorted(dimension_ids)}")

    dim_by_source = {row["source_id"]: row for row in dimensions}
    for row in screening:
        source_id = row["source_id"]
        require(row.get("retrieved_on", "") == "2026-08-11", f"{source_id}: retrieval date drift")
        require(row.get("disposition", "").startswith("include_"), f"{source_id}: Q15 mandatory source excluded")
        require(row.get("primary_url", "").startswith("https://"), f"{source_id}: missing primary URL")
        require(row.get("evidence_locator", "").strip(), f"{source_id}: missing evidence locator")
        drow = dim_by_source[source_id]
        strict_yes = 0
        for field in DIMENSIONS:
            svalue = row.get(field, "").strip().lower()
            dvalue = drow.get(field, "").strip().lower()
            require(svalue in SCORES, f"{source_id}: invalid screening {field}={svalue}")
            require(dvalue in SCORES, f"{source_id}: invalid dimension {field}={dvalue}")
            require(svalue == dvalue, f"{source_id}: screening/dimension drift for {field}: {svalue}!={dvalue}")
            strict_yes += dvalue == "yes"
        require(drow.get("strict_yes_count", "") == str(strict_yes), f"{source_id}: strict YES count mismatch")
        require(strict_yes < 5, f"{source_id}: Q15 exact-threshold match found; saturation=0 is false")
        require(drow.get("evidence_locator", "").strip(), f"{source_id}: dimension evidence locator missing")


def validate_saturation() -> None:
    sat = rows(SATURATION)
    require(len(sat) == 1, "Q15 saturation file must contain exactly one round")
    row = sat[0]
    require(row.get("round_id") == "Q15", "latest round must be Q15")
    require(row.get("date") == "2026-08-11", "Q15 date drift")
    require(row.get("saturation_usable", "").lower() == "yes", "Q15 must be marked usable")
    require(row.get("threshold_matches") == "0", "Q15 threshold match count must be zero")
    require(int(row.get("retrieved_unique_primary_candidates", "0")) == 6, "Q15 retrieval count must be six")
    screened = {item for item in row.get("screened_candidate_ids", "").split(";") if item}
    added = {item for item in row.get("added_source_ids", "").split(";") if item}
    require(screened == EXPECTED_CANDIDATES, f"Q15 saturation screened IDs drift: {sorted(screened)}")
    require(added == EXPECTED_SOURCES, f"Q15 saturation source IDs drift: {sorted(added)}")
    require("5 of 7" in row.get("exact_threshold_rule", ""), "Q15 threshold rule missing")
    require(row.get("queries", "").strip(), "Q15 queries missing")
    require("supersedes Q13/Q14" in row.get("limitation", ""), "Q15 latest-round supersession not explicit")


def validate_addenda() -> None:
    for path in (BOUNDARY_ADDENDUM, SEARCH_ADDENDUM):
        require(path.is_file(), f"missing Q15 addendum: {path}")
    boundary = BOUNDARY_ADDENDUM.read_text(encoding="utf-8")
    search = SEARCH_ADDENDUM.read_text(encoding="utf-8")

    boundary_tokens = [
        "ToolGate", "Text2Mem", "LatentGate", "Rethinking Scale",
        "Guidelines as Environments", "Don't Offer What Can't Be Done",
        "authoritative semantic-result placement", "supported/refuted/unknown/conflicting",
        "Q15", "independent", "not a priority claim",
    ]
    for token in boundary_tokens:
        require(token.lower() in boundary.lower(), f"Q15 novelty addendum missing token: {token}")

    search_tokens = [
        "Q15", "latest usable", "ACL Anthology", "arXiv", "0 / 6",
        "C-059", "C-064", "RW-059", "RW-064", "five strict `YES`",
    ]
    for token in search_tokens:
        require(token.lower() in search.lower(), f"Q15 search addendum missing token: {token}")

    for number, line in enumerate(boundary.splitlines(), 1):
        lower = line.lower()
        negative = any(token in lower for token in (
            "not a priority", "may not claim", "cannot", "not support", "does not", "no exact", "not novel",
        ))
        if negative:
            continue
        for pattern in PROHIBITED_POSITIVE:
            require(not pattern.search(line), f"prohibited priority wording in Q15 boundary:{number}: {line.strip()}")


def main() -> int:
    base_count = validate_base_snapshot()
    validate_supplement(base_count)
    validate_screening_and_dimensions()
    validate_saturation()
    validate_addenda()
    print("WP-003 Q15 semantic contract passed")
    print(f"Combined related-work corpus: {base_count} frozen base + 6 Q15 = {base_count + 6} primary sources")
    print("Q15 latest usable saturation: 6 screened, 0 five-of-seven strict-YES matches")
    print("Q13/Q14 remain reproducible historical snapshots; Q15 supersedes them only for freshness")
    print("Producer validation is not independent novelty acceptance and does not approve GATE-001")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, OSError, ValueError, csv.Error) as exc:
        print(f"WP-003 Q15 semantic contract failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc