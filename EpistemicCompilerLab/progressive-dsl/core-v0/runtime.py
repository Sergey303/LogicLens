#!/usr/bin/env python3
"""Deterministic synthetic semantic kernel for isolated Epistemic DSL smoke tests.

This module is intentionally not a package verifier. Production/research consumer tests
must load verified LogicLens capsule packages through the existing DSL-A/B/C query tools.
"""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any

UTF8 = "utf-8"
KERNEL_DOMAIN = b"LogicLensSyntheticSemanticKernelV0\0"
_NON_NEGATIVE_RATIONAL = re.compile(r"^(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?$")
_POSITIVE_RATIONAL = re.compile(r"^(?:[1-9][0-9]*)(?:/[1-9][0-9]*)?$")
_UNIT_INTERVAL_DECIMAL = re.compile(r"^(?:0(?:\.[0-9]+)?|1(?:\.0+)?)$")


class CoreError(RuntimeError):
    """Fail-closed contract error for the synthetic kernel."""


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode(UTF8)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(KERNEL_DOMAIN + canonical_json(value)).hexdigest()


def _non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise CoreError(f"{label} must be a non-empty string")
    return value


def _provenance(value: Any, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise CoreError(f"{label} must be a non-empty list of source references")
    if len(value) != len(set(value)):
        raise CoreError(f"{label} contains duplicates")
    return sorted(value)


def _evidence_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise CoreError(f"{label} must be an array")
    result: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise CoreError(f"{label}[{index}] must be an object")
        evidence_id = _non_empty_string(item.get("evidenceId"), f"{label}[{index}].evidenceId")
        if evidence_id in ids:
            raise CoreError(f"{label} contains duplicate evidenceId: {evidence_id}")
        ids.add(evidence_id)
        result.append(
            {
                "evidenceId": evidence_id,
                "dependencyGroup": _non_empty_string(
                    item.get("dependencyGroup"), f"{label}[{index}].dependencyGroup"
                ),
                "provenance": _provenance(
                    item.get("provenance"), f"{label}[{index}].provenance"
                ),
            }
        )
    return sorted(result, key=lambda row: row["evidenceId"])


def _unique_cross_stance(
    support: list[dict[str, Any]], oppose: list[dict[str, Any]], label: str
) -> None:
    support_ids = {item["evidenceId"] for item in support}
    oppose_ids = {item["evidenceId"] for item in oppose}
    overlap = sorted(support_ids & oppose_ids)
    if overlap:
        raise CoreError(f"{label} reuses evidence IDs across stances: {overlap}")


def strict_status(support: list[dict[str, Any]], oppose: list[dict[str, Any]]) -> str:
    if support and oppose:
        return "conflicting"
    if support:
        return "supported"
    if oppose:
        return "refuted"
    return "unknown"


def _source_frame(*evidence_sets: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    provenance = sorted(
        {
            reference
            for evidence in evidence_sets
            for record in evidence
            for reference in record["provenance"]
        }
    )
    dependency_groups = sorted(
        {record["dependencyGroup"] for evidence in evidence_sets for record in evidence}
    )
    return provenance, dependency_groups


def strict_frame(case: dict[str, Any]) -> dict[str, Any]:
    support = _evidence_list(case.get("supportEvidence", []), "supportEvidence")
    oppose = _evidence_list(case.get("opposeEvidence", []), "opposeEvidence")
    _unique_cross_stance(support, oppose, "strict claim")
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
    provenance, dependency_groups = _source_frame(support, oppose)
    return {
        "status": status,
        "action": action,
        "withholdsAssertiveDecision": withholds,
        "evidence": {"support": support, "oppose": oppose},
        "provenance": provenance,
        "dependencyGroups": dependency_groups,
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
    premise_ids: set[str] = set()
    all_evidence: list[list[dict[str, Any]]] = []
    for index, premise in enumerate(premises):
        if not isinstance(premise, dict):
            raise CoreError(f"premises[{index}] must be an object")
        premise_id = _non_empty_string(premise.get("premiseId"), f"premises[{index}].premiseId")
        if premise_id in premise_ids:
            raise CoreError(f"duplicate premiseId: {premise_id}")
        premise_ids.add(premise_id)
        support = _evidence_list(
            premise.get("supportEvidence", []), f"premises[{index}].supportEvidence"
        )
        oppose = _evidence_list(
            premise.get("opposeEvidence", []), f"premises[{index}].opposeEvidence"
        )
        _unique_cross_stance(support, oppose, f"premise {premise_id}")
        all_evidence.extend([support, oppose])
        premise_frames.append(
            {
                "premiseId": premise_id,
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
    rule_id = _non_empty_string(case.get("ruleId"), "ruleId")
    derived_support = [{"evidenceId": f"rule:{rule_id}", "dependencyGroup": f"rule:{rule_id}", "provenance": [f"synthetic-rule://{rule_id}"]}] if satisfied and head_stance == "support" else []
    derived_oppose = [{"evidenceId": f"rule:{rule_id}", "dependencyGroup": f"rule:{rule_id}", "provenance": [f"synthetic-rule://{rule_id}"]}] if satisfied and head_stance == "oppose" else []
    status = strict_status(derived_support, derived_oppose)
    provenance, dependency_groups = _source_frame(*all_evidence)
    return {
        "status": status,
        "action": "answer_with_proof" if satisfied else "abstain_and_request_missing_premises",
        "withholdsAssertiveDecision": not satisfied,
        "proof": {
            "ruleId": rule_id,
            "operator": operator,
            "headStance": head_stance,
            "satisfied": satisfied,
            "premises": premise_frames,
        },
        "provenance": provenance,
        "dependencyGroups": dependency_groups,
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
    observation = case.get("observation")
    threshold = case.get("threshold")
    if not isinstance(observation, dict) or not isinstance(threshold, dict):
        raise CoreError("numeric case requires observation and threshold")
    model = observation.get("model")
    if not isinstance(model, dict):
        raise CoreError("numeric observation requires model")
    provenance = _provenance(observation.get("provenance"), "observation.provenance")
    dependency_group = _non_empty_string(
        observation.get("dependencyGroup"), "observation.dependencyGroup"
    )
    observation_id = _non_empty_string(observation.get("observationId"), "observation.observationId")

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
        "observation": {
            "observationId": observation_id,
            "dependencyGroup": dependency_group,
            "provenance": provenance,
        },
        "normalized": {
            "dimension": dimension,
            "lower": format(lower, "f"),
            "upper": format(upper, "f"),
            "threshold": format(boundary, "f"),
            "operator": operator,
        },
        "provenance": provenance,
        "dependencyGroups": [dependency_group],
        "warnings": ["threshold-crosses-observation-bounds"] if status == "unknown" else [],
    }


def _fraction(value: Any, label: str, *, positive: bool = False) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise CoreError(f"{label} must be a canonical rational string or integer")
    if isinstance(value, int):
        if value < (1 if positive else 0):
            raise CoreError(f"{label} is outside its allowed domain")
        return Fraction(value, 1)
    pattern = _POSITIVE_RATIONAL if positive else _NON_NEGATIVE_RATIONAL
    if not pattern.fullmatch(value):
        raise CoreError(f"{label} must be a canonical rational")
    result = Fraction(value)
    if result < (1 if positive else 0):
        raise CoreError(f"{label} is outside its allowed domain")
    return result


def _base_rate(value: Any, label: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise CoreError(f"{label} must be a unit-interval decimal string or 0/1 integer")
    if isinstance(value, int):
        if value not in {0, 1}:
            raise CoreError(f"{label} must be in [0,1]")
        return Fraction(value, 1)
    if not _UNIT_INTERVAL_DECIMAL.fullmatch(value):
        raise CoreError(f"{label} must be a canonical decimal in [0,1]")
    return Fraction(value)


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
    report_ids: set[str] = set()
    normalized_reports: list[dict[str, Any]] = []
    for index, report in enumerate(reports):
        if not isinstance(report, dict):
            raise CoreError(f"reports[{index}] must be an object")
        report_id = _non_empty_string(report.get("reportId"), f"reports[{index}].reportId")
        if report_id in report_ids:
            raise CoreError(f"duplicate reportId: {report_id}")
        report_ids.add(report_id)
        normalized_reports.append(
            {
                "reportId": report_id,
                "dependencyGroup": _non_empty_string(
                    report.get("dependencyGroup"), f"reports[{index}].dependencyGroup"
                ),
                "positive": _fraction(
                    report.get("positiveEvidence"), f"reports[{index}].positiveEvidence"
                ),
                "negative": _fraction(
                    report.get("negativeEvidence"), f"reports[{index}].negativeEvidence"
                ),
                "baseRate": _base_rate(report.get("baseRate"), f"reports[{index}].baseRate"),
                "provenance": _provenance(
                    report.get("provenance"), f"reports[{index}].provenance"
                ),
            }
        )

    base_rates = {report["baseRate"] for report in normalized_reports}
    all_provenance = sorted(
        {reference for report in normalized_reports for reference in report["provenance"]}
    )
    if len(base_rates) != 1:
        return {
            "opinionSubjectLevel": case["opinionSubjectLevel"],
            "conclusion": "request_compatible_base_rates",
            "action": "abstain_and_request_compatible_base_rates",
            "withholdsAssertiveDecision": True,
            "operatorPlan": "blocked_incompatible_base_rate",
            "implicitFusionPerformed": False,
            "provenance": all_provenance,
            "dependencyGroups": [],
            "warnings": ["incompatible-base-rates", "no-implicit-fusion"],
        }

    prior_weight = _fraction(case.get("priorWeight"), "priorWeight", positive=True)
    groups: dict[str, list[dict[str, Any]]] = {}
    for report in normalized_reports:
        groups.setdefault(report["dependencyGroup"], []).append(report)

    positive = Fraction(0)
    negative = Fraction(0)
    group_frames: list[dict[str, Any]] = []
    for group_id in sorted(groups):
        rows = groups[group_id]
        group_positive = sum((row["positive"] for row in rows), Fraction(0)) / len(rows)
        group_negative = sum((row["negative"] for row in rows), Fraction(0)) / len(rows)
        positive += group_positive
        negative += group_negative
        group_frames.append(
            {
                "dependencyGroup": group_id,
                "reportIds": sorted(row["reportId"] for row in rows),
                "reportCount": len(rows),
                "operator": "single" if len(rows) == 1 else "average",
                "positiveEvidence": _fraction_text(group_positive),
                "negativeEvidence": _fraction_text(group_negative),
            }
        )

    base_rate = next(iter(base_rates))
    total = positive + negative + prior_weight
    belief = positive / total
    disbelief = negative / total
    uncertainty = prior_weight / total
    projected = belief + base_rate * uncertainty
    conflict = Fraction(0) if positive + negative == 0 else 2 * min(positive, negative) / (positive + negative)
    conclusion, action, withholds = _opinion_policy(belief, disbelief, uncertainty, projected, conflict)
    if len(normalized_reports) == 1:
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
    if case["opinionSubjectLevel"] == "answer":
        warnings.append("answer-level-opinion")
    return {
        "opinionSubjectLevel": case["opinionSubjectLevel"],
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
        "provenance": all_provenance,
        "warnings": sorted(warnings),
    }


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    case_id = _non_empty_string(case.get("caseId"), "caseId")
    kind = case.get("kind")
    if kind == "strict-claim":
        dsl_level = "DSL-A-semantics"
        frame = strict_frame(case)
    elif kind == "logical-rule":
        dsl_level = "DSL-B-semantics"
        frame = logical_frame(case)
    elif kind == "numeric-comparison":
        dsl_level = "DSL-C-semantics"
        frame = numeric_frame(case)
    elif kind == "opinion-fusion":
        dsl_level = "DSL-D2-semantics"
        frame = opinion_frame(case)
    else:
        raise CoreError(f"unsupported case kind: {kind!r}")
    return {
        "schemaVersion": "0.2",
        "kernelVersion": "synthetic-semantic-kernel-v0",
        "caseId": case_id,
        "kind": kind,
        "dslLevel": dsl_level,
        "inputHash": digest(case),
        **frame,
        "runtime": {
            "engine": "python-exact-synthetic",
            "syntheticKernel": True,
            "trustedPackageVerified": False,
            "weakModelPerformsArithmetic": False,
            "unknownIsFalse": False,
            "conflictCollapsed": False,
        },
    }
