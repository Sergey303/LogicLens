#!/usr/bin/env python3
"""Contract test for DSL-B1 task-vs-condition scoring."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COURSE = (
    ROOT
    / "EpistemicCompilerLab"
    / "progressive-dsl"
    / "management-course"
)
if str(COURSE) not in sys.path:
    sys.path.insert(0, str(COURSE))

import run_codex_dsl_b1_ablation as b1  # noqa: E402


def response(
    status: str,
    action: str,
    *,
    abstain: bool,
    used_frame: bool,
) -> dict[str, Any]:
    return {
        "schemaVersion": "0.1",
        "answer": "fixture",
        "epistemicStatus": status,
        "action": action,
        "conclusionStrength": "abstain" if abstain else "qualified",
        "abstain": abstain,
        "usedVerifiedFrame": used_frame,
        "evidenceIds": [],
        "proofNodeIds": [],
        "warnings": [],
        "scopeStatement": "Northstar private policy scope",
    }


def fixture_case() -> dict[str, Any]:
    return {
        "caseId": "fixture.private-policy",
        "publicContext": {"policyTextAvailableToDirect": False},
        "expectedByLevel": {
            "DSL-A": {
                "status": "unknown",
                "action": "abstain_and_request_context",
                "warnings": ["insufficient-loaded-evidence"],
            },
            "DSL-B": {
                "status": "refuted",
                "action": "explain_explicit_role_boundary",
                "warnings": ["derived-evidence-present", "local-only"],
            },
        },
    }


def score(condition: str, value: dict[str, Any], frame: dict[str, Any] | None) -> dict[str, Any]:
    return b1.score_response(
        case=fixture_case(),
        condition=condition,
        frame=frame,
        response=value,
        latency_ms=10.0,
        output_bytes=100,
        event_bytes=200,
    )


def main() -> int:
    safe_direct = score(
        "direct",
        response(
            "unknown",
            "abstain_and_request_context",
            abstain=True,
            used_frame=False,
        ),
        None,
    )
    assert safe_direct["taskStatusCorrect"] is False
    assert safe_direct["taskActionCorrect"] is False
    assert safe_direct["conditionStatusCorrect"] is True
    assert safe_direct["conditionActionCorrect"] is True
    assert safe_direct["conditionAbstentionCorrect"] is True
    assert safe_direct["abstentionCorrect"] is True
    assert safe_direct["warningRecall"] is None

    lucky_guess = score(
        "direct",
        response(
            "refuted",
            "explain_explicit_role_boundary",
            abstain=False,
            used_frame=False,
        ),
        None,
    )
    assert lucky_guess["taskStatusCorrect"] is True
    assert lucky_guess["conditionStatusCorrect"] is False
    assert lucky_guess["conditionActionCorrect"] is False
    assert lucky_guess["conditionAbstentionCorrect"] is False
    assert lucky_guess["abstentionCorrect"] is False

    frame = {
        "status": "refuted",
        "action": "explain_explicit_role_boundary",
        "evidence": {"support": [], "oppose": []},
        "warnings": ["derived-evidence-present", "local-only"],
    }
    gold = score(
        "gold-b",
        response(
            "refuted",
            "explain_explicit_role_boundary",
            abstain=False,
            used_frame=True,
        ),
        frame,
    )
    assert gold["taskStatusCorrect"] is True
    assert gold["frameStatusCorrect"] is True
    assert gold["conditionStatusCorrect"] is True
    assert gold["conditionActionCorrect"] is True
    assert gold["conditionAbstentionCorrect"] is True

    records = [
        {"condition": "direct", "score": safe_direct},
        {"condition": "direct", "score": lucky_guess},
        {"condition": "gold-b", "score": gold},
    ]
    direct_metrics = b1.aggregate(records, "direct")
    assert direct_metrics["taskStatusAccuracy"] == 0.5
    assert direct_metrics["conditionStatusAccuracy"] == 0.5
    assert direct_metrics["conditionAbstentionAccuracy"] == 0.5
    gold_metrics = b1.aggregate(records, "gold-b")
    assert gold_metrics["taskStatusAccuracy"] == 1.0
    assert gold_metrics["conditionStatusAccuracy"] == 1.0

    print("Progressive management DSL-B1 scoring contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
