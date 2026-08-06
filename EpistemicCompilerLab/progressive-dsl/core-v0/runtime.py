#!/usr/bin/env python3
"""Deterministic experimental Epistemic DSL core for strict, logical, numeric and opinion frames."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any

UTF8 = "utf-8"
CORE_DOMAIN = b"LogicLensEpistemicCoreV0\0"


class CoreError(RuntimeError):
    pass


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode(UTF8)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(CORE_DOMAIN + canonical_json(value)).hexdigest()


def _identifier_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise CoreError(f"{label} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise CoreError(f"{label} contains duplicates")
    return sorted(value)


def strict_status(support: list[str], oppose: list[str]) -> str:
    if support and oppose:
        return "conflicting"
    if support:
        return "supported"
    if oppose:
        return "refuted"
    return "unknown"


def strict_frame(case: dict[str, Any]) -> dict[str, Any]:
    support = _identifier_list(case.get("supportEvidence", []), "supportEvidence")
    oppose = _identifier_list(case.get("opposeEvidence", []), "opposeEvidence")
    status = strict_status(support, oppose)
    policies = {
        "supported": ("answer_with_source_scope", False),
        "refuted": ("explain_explicit_negative_evidence", False),
        "unknown": ("abstain_and_request_context", True),
        "conflicting": ("report_conflict", True),
    }
    action, withholds = policies[status]
    warnings: list[str] = []
    if status == "unknown":
        warnings.append("insufficient-loaded-evidence")
    if status == "conflicting":
        warnings.append("incompatible-loaded-assertions")
    return {
        "status": status,
        "action": action,
        "withholdsAssertiveDecision": withholds,
        "evidence": {"support": support, "oppose": oppose},
        "warnings": warnings,
    }


def logical_frame(case: dict[str, Any]) -> dict[str, Any]:
    premises = case.get("premises")
    if not isinstance(premises, list) or not premises:
        raise CoreError("logical case requires non-empty premises")
    operator = case.get("operator")
    if operator not in {"all", "any"}:
        raise CoreError("logical operator must be all or any")
    premise_frames: list[dict[str, Any]] = []
    for premise in premises:
        if not isinstance(premise, dict) or not isinstance(premise.get("premiseId"), str):
            raise CoreError("each premise requires premiseId")
        support = _identifier_list(premise.get("supportEvidence", []), "premise supportEvidence")
        oppose = _identifier_list(premise.get("opposeEvidence", []), "premise opposeEvidence")
        premise_frames.append(
            {
                "premiseId": premise["premiseId"],
                "status": strict_status(support, oppose),
                "support": support,
                "oppose": oppose,
            }
        )
    satisfied = (
        all(item["status"] == "supported" for item in premise_frames)
        if operator == "all"
        else any(item["status"] == "supported" for item in premise_frames)
    )
    head_stance = case.get("headStance", "support")
    if head_stance not in {"support", "oppose"}:
        raise CoreError("headStance must be support or oppose")
    derived_support = [case["ruleId"]] if satisfied and head_stance == "support" else []
    derived_oppose = [case["ruleId"]] if satisfied and head_stance == "oppose" else []
    status = strict_status(derived_support, derived_oppose)
    return {
        "status": status,
        "action": "answer_with_proof" if satisfied else "abstain_and_request_missing_premises",
        "withholdsAssertiveDecision": not satisfied,
        "proof": {
            "ruleId": case["ruleId"],
            "operator": operator,
            "headStance": head_stance,
            "satisfied": satisfied,
            "premises": premise_frames,
        },
        "warnings": [] if satisfied else ["logical-premises-not-satisfied"],
    }


_UNIT_FACTORS: dict[str, tuple[str, Decimal]] = {
    "fraction": ("ratio", Decimal("1")),
    "percent": ("ratio", Decimal("0.01")),
    "count": ("count", Decimal("1")),
    "millisecond": ("duration", Decimal("0.001")),
    "second": ("duration", Decimal("1")),
    "minute": ("duration", Decimal("60")),
    "hour": ("duration", Decimal("3600")),
    "day": ("duration", Decimal("86400")),
}


def _decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise CoreError(f"{label} must be a decimal string or integer")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise CoreError(f"invalid decimal for {label}: {value!r}") from exc
    if not result.is_finite():
        raise CoreError(f"{label} must be finite")
    return result


def _normalize(value: Any, unit: Any, label: str) -> tuple[Decimal, str]:
    if not isinstance(unit, str) or unit not in _UNIT_FACTORS:
        raise CoreError(f"unsupported unit for {label}: {unit!r}")
    dimension, factor = _UNIT_FACTORS[unit]
    return _decimal(value, label) * factor, dimension


def numeric_frame(case: dict[str, Any]) -> dict[str, Any]:
    model = case.get("model")
    threshold = case.get("threshold")
    if not isinstance(model, dict) or not isinstance(threshold, dict):
        raise CoreError("numeric case requires model and threshold")
    kind = model.get("kind")
    if kind == "point":
        lower, dimension = _normalize(model.get("value"), model.get("unit"), "point")
        upper = lower
    elif kind == "bounded":
        lower, dimension = _normalize(model.get("lower"), model.get("unit"), "lower")
        upper, upper_dimension = _normalize(model.get("upper"), model.get("unit"), "upper")
        if dimension != upper_dimension or lower > upper:
            raise CoreError("invalid bounded model")
    else:
        raise CoreError("numeric model kind must be point or bounded")
    boundary, boundary_dimension = _normalize(
        threshold.get("value"), threshold.get("unit"), "threshold"
    )
    if dimension != boundary_dimension:
        raise CoreError("numeric dimension mismatch")
    operator = case.get("operator")
    if operator == ">=":
        status = "supported" if lower >= boundary else "refuted" if upper < boundary else "unknown"
    elif operator == "<=":
        status = "supported" if upper <= boundary else "refuted" if lower > boundary else "unknown"
    elif operator == ">":
        status = "supported" if lower > boundary else "refuted" if upper <= boundary else "unknown"
    elif operator == "<":
        status = "supported" if upper < boundary else "refuted" if lower >= boundary else "unknown"
    else:
        raise CoreError("numeric operator must be one of >=, <=, >, <")
    return {
        "status": status,
        "action": "answer_with_measurement_scope" if status != "unknown" else "abstain_on_numeric_decision",
        "withholdsAssertiveDecision": status == "unknown",
        "normalized": {
            "dimension": dimension,
            "lower": format(lower, "f"),
            "upper": format(upper, "f"),
            "threshold": format(boundary, "f"),
            "operator": operator,
        },
        "warnings": ["threshold-crosses-observation-bounds"] if status == "unknown" else [],
    }


def _fraction(value: Any, label: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise CoreError(f"{label} must be a rational string or integer")
    try:
        result = Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise CoreError(f"invalid rational for {label}: {value!r}") from exc
    if result < 0:
        raise CoreError(f"{label} must be non-negative")
    return result


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _opinion_policy(b: Fraction, d: Fraction, u: Fraction, p: Fraction, c: Fraction) -> tuple[str, str, bool]:
    if c >= Fraction(1, 2):
        return "report_conflict", "report_conflict", True
    if u >= Fraction(1, 2):
        return "abstain_high_uncertainty", "abstain", True
    if p >= Fraction(3, 4) and b >= Fraction(1, 2) and u <= Fraction(1, 4):
        return "assert_with_evidence", "answer_with_epistemic_profile", False
    if p <= Fraction(1, 4) and d >= Fraction(1, 2) and u <= Fraction(1, 4):
        return "qualified_refutation", "explain_refutation_with_profile", False
    if p >= Fraction(13, 20) and b < Fraction(1, 2) and u < Fraction(1, 2):
        return "qualify_prior_sensitive", "answer_with_prior_warning", False
    return "qualified_uncertain", "answer_with_uncertainty", True


def opinion_frame(case: dict[str, Any]) -> dict[str, Any]:
    reports = case.get("reports")
    if not isinstance(reports, list) or not reports:
        raise CoreError("opinion case requires reports")
    base_rates = {_fraction(report.get("baseRate"), "baseRate") for report in reports}
    if len(base_rates) != 1:
        return {
            "conclusion": "request_compatible_base_rates",
            "action": "abstain_and_request_compatible_base_rates",
            "withholdsAssertiveDecision": True,
            "implicitFusionPerformed": False,
            "warnings": ["incompatible-base-rates", "no-implicit-fusion"],
        }
    if any(not isinstance(report.get("dependencyGroup"), str) or not report["dependencyGroup"] for report in reports):
        return {
            "conclusion": "request_dependency_metadata",
            "action": "abstain_and_request_dependency_metadata",
            "withholdsAssertiveDecision": True,
            "implicitFusionPerformed": False,
            "warnings": ["dependency-metadata-missing", "no-implicit-fusion"],
        }
    prior_weight = _fraction(case.get("priorWeight"), "priorWeight")
    if prior_weight <= 0:
        raise CoreError("priorWeight must be positive")
    groups: dict[str, list[dict[str, Any]]] = {}
    for report in reports:
        groups.setdefault(report["dependencyGroup"], []).append(report)
    positive = Fraction(0)
    negative = Fraction(0)
    group_frames: list[dict[str, Any]] = []
    for group_id in sorted(groups):
        rows = groups[group_id]
        group_positive = sum((_fraction(row.get("positiveEvidence"), "positiveEvidence") for row in rows), Fraction(0)) / len(rows)
        group_negative = sum((_fraction(row.get("negativeEvidence"), "negativeEvidence") for row in rows), Fraction(0)) / len(rows)
        positive += group_positive
        negative += group_negative
        group_frames.append({
            "dependencyGroup": group_id,
            "reportCount": len(rows),
            "operator": "single" if len(rows) == 1 else "average",
            "positiveEvidence": _fraction_text(group_positive),
            "negativeEvidence": _fraction_text(group_negative),
        })
    base_rate = next(iter(base_rates))
    total = positive + negative + prior_weight
    belief = positive / total
    disbelief = negative / total
    uncertainty = prior_weight / total
    projected = belief + base_rate * uncertainty
    conflict = Fraction(0) if positive + negative == 0 else 2 * min(positive, negative) / (positive + negative)
    conclusion, action, withholds = _opinion_policy(belief, disbelief, uncertainty, projected, conflict)
    if len(reports) == 1:
        plan = "single_source"
    elif len(groups) == 1:
        plan = "average_within_group"
    elif all(len(rows) == 1 for rows in groups.values()):
        plan = "cumulative_across_groups"
    else:
        plan = "average_then_cumulative"
    warnings = ["no-implicit-fusion"]
    if any(len(rows) > 1 for rows in groups.values()):
        warnings.append("dependent-reports-averaged")
    if len(groups) > 1:
        warnings.append("independent-groups-cumulatively-combined")
    if conflict >= Fraction(1, 2):
        warnings.append("conflict-high")
    return {
        "conclusion": conclusion,
        "action": action,
        "withholdsAssertiveDecision": withholds,
        "operatorPlan": plan,
        "implicitFusionPerformed": False,
        "exactPositiveEvidence": _fraction_text(positive),
        "exactNegativeEvidence": _fraction_text(negative),
        "exactOpinion": {
            "belief": _fraction_text(belief),
            "disbelief": _fraction_text(disbelief),
            "uncertainty": _fraction_text(uncertainty),
            "baseRate": _fraction_text(base_rate),
        },
        "exactProjectedProbability": _fraction_text(projected),
        "exactConflictIndex": _fraction_text(conflict),
        "dependencyGroups": group_frames,
        "warnings": sorted(warnings),
    }


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(case.get("caseId"), str) or not case["caseId"]:
        raise CoreError("caseId is required")
    kind = case.get("kind")
    if kind == "strict-claim":
        dsl_level = "DSL-A"
        frame = strict_frame(case)
    elif kind == "logical-rule":
        dsl_level = "DSL-B"
        frame = logical_frame(case)
    elif kind == "numeric-comparison":
        dsl_level = "DSL-C"
        frame = numeric_frame(case)
    elif kind == "opinion-fusion":
        dsl_level = "DSL-D2"
        frame = opinion_frame(case)
    else:
        raise CoreError(f"unsupported case kind: {kind!r}")
    return {
        "schemaVersion": "0.1",
        "coreVersion": "epistemic-core-v0",
        "caseId": case["caseId"],
        "kind": kind,
        "dslLevel": dsl_level,
        "inputHash": digest(case),
        **frame,
        "runtime": {
            "engine": "python-exact-reference",
            "weakModelPerformsArithmetic": False,
            "unknownIsFalse": False,
            "conflictCollapsed": False,
        },
    }
