#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

CHECKS = (
    "actionCorrect",
    "statusCorrect",
    "materialCorrect",
    "askFieldCorrect",
)


def _outcome(before_passed: bool, after_passed: bool) -> str:
    if before_passed and after_passed:
        return "unchanged_pass"
    if before_passed and not after_passed:
        return "regressed"
    if not before_passed and after_passed:
        return "fixed"
    return "unchanged_fail"


def build_train_effects(
    reference: dict[str, Any],
    candidate: dict[str, Any],
) -> list[dict[str, Any]]:
    before_by_id = {
        record["caseId"]: record
        for record in reference.get("records", [])
    }
    effects: list[dict[str, Any]] = []
    for after in candidate.get("records", []):
        case_id = after["caseId"]
        before = before_by_id.get(case_id)
        if before is None:
            raise ValueError(f"candidate TRAIN record has no reference: {case_id}")
        before_checks = before["checks"]
        after_checks = after["checks"]
        changed = [
            {
                "check": name,
                "before": bool(before_checks.get(name)),
                "after": bool(after_checks.get(name)),
            }
            for name in CHECKS
            if bool(before_checks.get(name)) != bool(after_checks.get(name))
        ]
        effects.append({
            "caseId": case_id,
            "outcome": _outcome(
                bool(before_checks.get("passed")),
                bool(after_checks.get("passed")),
            ),
            "changedChecks": changed,
            "beforeResponse": before.get("response"),
            "candidateResponse": after.get("response"),
        })
    return effects


def summarize_train_effects(effects: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "fixed": 0,
        "regressed": 0,
        "unchangedPass": 0,
        "unchangedFail": 0,
    }
    mapping = {
        "fixed": "fixed",
        "regressed": "regressed",
        "unchanged_pass": "unchangedPass",
        "unchanged_fail": "unchangedFail",
    }
    for effect in effects:
        counts[mapping[effect["outcome"]]] += 1
    return counts
