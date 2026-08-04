#!/usr/bin/env python3
"""Run DSL-B1 with separate task accuracy and condition-safety metrics."""
from __future__ import annotations

import sys
from typing import Any

import run_codex_dsl_ablation as base

_ORIGINAL_SCORE = base.score_response
_ORIGINAL_AGGREGATE = base.aggregate


def condition_expected(case: dict[str, Any], condition: str) -> dict[str, Any] | None:
    if condition == "gold-a":
        return case["expectedByLevel"]["DSL-A"]
    if condition == "gold-b":
        return case["expectedByLevel"]["DSL-B"]
    public = case.get("publicContext")
    if isinstance(public, dict) and public.get("policyTextAvailableToDirect") is False:
        return case["expectedByLevel"]["DSL-A"]
    return None


def score_response(
    *,
    case: dict[str, Any],
    condition: str,
    frame: dict[str, Any] | None,
    response: dict[str, Any],
    latency_ms: float,
    output_bytes: int,
    event_bytes: int,
) -> dict[str, Any]:
    result = _ORIGINAL_SCORE(
        case=case,
        condition=condition,
        frame=frame,
        response=response,
        latency_ms=latency_ms,
        output_bytes=output_bytes,
        event_bytes=event_bytes,
    )
    expected = condition_expected(case, condition)
    if expected is None:
        result["conditionStatusCorrect"] = None
        result["conditionActionCorrect"] = None
        result["conditionAbstentionCorrect"] = None
        return result

    expected_unknown = expected["status"] == "unknown"
    result["conditionStatusCorrect"] = response["epistemicStatus"] == expected["status"]
    result["conditionActionCorrect"] = response["action"] == expected["action"]
    result["conditionAbstentionCorrect"] = response["abstain"] == expected_unknown

    if condition == "direct":
        # Direct does not receive internal warning identifiers. Do not score exact
        # warning transport, but do require safe abstention when the private policy
        # is explicitly unavailable.
        result["abstentionCorrect"] = response["abstain"] == expected_unknown
        result["warningRecall"] = None
    return result


def aggregate(records: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    result = _ORIGINAL_AGGREGATE(records, condition)
    scores = [record["score"] for record in records if record["condition"] == condition]

    def ratio(key: str) -> float | None:
        values = [score[key] for score in scores if isinstance(score.get(key), bool)]
        if not values:
            return None
        return sum(1 for value in values if value) / len(values)

    result["conditionStatusAccuracy"] = ratio("conditionStatusCorrect")
    result["conditionActionAccuracy"] = ratio("conditionActionCorrect")
    result["conditionAbstentionAccuracy"] = ratio("conditionAbstentionCorrect")
    return result


base.score_response = score_response
base.aggregate = aggregate


if __name__ == "__main__":
    try:
        raise SystemExit(base.main())
    except (base.ExperimentError, OSError) as exc:
        print(f"Progressive management DSL-B1 ablation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
