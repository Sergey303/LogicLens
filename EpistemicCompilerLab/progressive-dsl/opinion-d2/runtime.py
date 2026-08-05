#!/usr/bin/env python3
"""Exact dependency-aware fusion runtime for DSL-D2."""
from __future__ import annotations

import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any


class FusionError(RuntimeError):
    pass


def fraction(value: dict[str, Any]) -> Fraction:
    result = Fraction(int(value["numerator"]), int(value["denominator"]))
    if result < 0:
        raise FusionError("negative evidence is forbidden")
    return result


def text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def atom(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def policy(
    b: Fraction,
    d: Fraction,
    u: Fraction,
    p: Fraction,
    c: Fraction,
) -> tuple[str, str, bool]:
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


def blocked_frame(bundle: dict[str, Any], kind: str) -> dict[str, Any]:
    missing = kind == "missing_dependency_metadata"
    return {
        "schemaVersion": "0.1",
        "dslLevel": "DSL-D2",
        "fusionId": bundle["fusionId"],
        "proposition": bundle["proposition"],
        "opinionSubjectLevel": bundle["opinionSubjectLevel"],
        "operatorPlan": (
            "blocked_missing_dependency"
            if missing
            else "blocked_incompatible_base_rate"
        ),
        "sourceReportCount": len(bundle["reports"]),
        "dependencyGroupCount": 0,
        "effectiveGroupCount": 0,
        "exactPositiveEvidence": None,
        "exactNegativeEvidence": None,
        "exactOpinion": None,
        "exactProjectedProbability": None,
        "exactConflictIndex": None,
        "conclusion": (
            "request_dependency_metadata"
            if missing
            else "request_compatible_base_rates"
        ),
        "action": (
            "abstain_and_request_dependency_metadata"
            if missing
            else "abstain_and_request_compatible_base_rates"
        ),
        "withholdsAssertiveDecision": True,
        "dependencyMetadataComplete": not missing,
        "compatibleBaseRates": missing,
        "implicitFusionPerformed": False,
        "dependencyGroups": [],
        "provenance": sorted(
            {item for report in bundle["reports"] for item in report["provenance"]}
        ),
        "scope": {"kind": "local-pilot", "snapshot": "D2-2026.08"},
        "warnings": [
            (
                "dependency-metadata-missing"
                if missing
                else "incompatible-base-rates"
            ),
            "no-implicit-fusion",
            "pilot-only",
        ],
    }


def compute(
    bundle: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Fraction] | None]:
    reports = bundle["reports"]
    if not reports:
        raise FusionError("at least one report is required")

    rates = [fraction(report["baseRate"]) for report in reports]
    if len(set(rates)) != 1:
        return blocked_frame(bundle, "incompatible_base_rates"), None
    if any(not report.get("dependencyGroup") for report in reports):
        return blocked_frame(bundle, "missing_dependency_metadata"), None

    prior_weight = fraction(bundle["priorWeight"])
    if prior_weight <= 0:
        raise FusionError("prior weight must be positive")

    groups: dict[str, list[dict[str, Any]]] = {}
    for report in reports:
        groups.setdefault(report["dependencyGroup"], []).append(report)

    if len(reports) == 1:
        plan = "single_source"
    elif len(groups) == 1:
        plan = "average_within_group"
    elif all(len(rows) == 1 for rows in groups.values()):
        plan = "cumulative_across_groups"
    else:
        plan = "average_then_cumulative"

    positive = Fraction(0)
    negative = Fraction(0)
    group_frames: list[dict[str, Any]] = []
    for group_id in sorted(groups):
        rows = groups[group_id]
        group_positive = sum(
            (fraction(report["positiveEvidence"]) for report in rows),
            Fraction(0),
        ) / len(rows)
        group_negative = sum(
            (fraction(report["negativeEvidence"]) for report in rows),
            Fraction(0),
        ) / len(rows)
        positive += group_positive
        negative += group_negative
        group_frames.append(
            {
                "dependencyGroup": group_id,
                "reportIds": sorted(report["reportId"] for report in rows),
                "sourceReportCount": len(rows),
                "operator": "single" if len(rows) == 1 else "average",
                "exactPositiveEvidence": text(group_positive),
                "exactNegativeEvidence": text(group_negative),
            }
        )

    base_rate = rates[0]
    normalizer = positive + negative + prior_weight
    belief = positive / normalizer
    disbelief = negative / normalizer
    uncertainty = prior_weight / normalizer
    projected = belief + base_rate * uncertainty
    conflict = (
        Fraction(0)
        if positive + negative == 0
        else 2 * min(positive, negative) / (positive + negative)
    )
    conclusion, action, withholds = policy(
        belief,
        disbelief,
        uncertainty,
        projected,
        conflict,
    )

    warnings = ["no-implicit-fusion", "pilot-only"]
    if any(len(rows) > 1 for rows in groups.values()):
        warnings.append("dependent-reports-averaged")
    if len(groups) > 1:
        warnings.append("independent-groups-cumulatively-combined")
    if conflict >= Fraction(1, 2):
        warnings.append("conflict-high")
    if bundle["opinionSubjectLevel"] == "answer":
        warnings.append("answer-level-opinion")

    frame = {
        "schemaVersion": "0.1",
        "dslLevel": "DSL-D2",
        "fusionId": bundle["fusionId"],
        "proposition": bundle["proposition"],
        "opinionSubjectLevel": bundle["opinionSubjectLevel"],
        "operatorPlan": plan,
        "sourceReportCount": len(reports),
        "dependencyGroupCount": len(groups),
        "effectiveGroupCount": len(groups),
        "exactPositiveEvidence": text(positive),
        "exactNegativeEvidence": text(negative),
        "exactOpinion": {
            "belief": text(belief),
            "disbelief": text(disbelief),
            "uncertainty": text(uncertainty),
            "baseRate": text(base_rate),
        },
        "exactProjectedProbability": text(projected),
        "exactConflictIndex": text(conflict),
        "conclusion": conclusion,
        "action": action,
        "withholdsAssertiveDecision": withholds,
        "dependencyMetadataComplete": True,
        "compatibleBaseRates": True,
        "implicitFusionPerformed": False,
        "dependencyGroups": group_frames,
        "provenance": sorted(
            {item for report in reports for item in report["provenance"]}
        ),
        "scope": {"kind": "local-pilot", "snapshot": "D2-2026.08"},
        "warnings": sorted(warnings),
    }
    exact = {
        "positive": positive,
        "negative": negative,
        "belief": belief,
        "disbelief": disbelief,
        "uncertainty": uncertainty,
        "base_rate": base_rate,
        "projected": projected,
        "conflict": conflict,
    }
    return frame, exact


def prolog_program(
    bundle: dict[str, Any],
    frame: dict[str, Any],
    exact: dict[str, Fraction] | None,
) -> str:
    facts: list[str] = []
    for report in bundle["reports"]:
        group = report.get("dependencyGroup", "__missing__")
        positive = fraction(report["positiveEvidence"])
        negative = fraction(report["negativeEvidence"])
        base_rate = fraction(report["baseRate"])
        facts.append(
            "report("
            f"{atom(group)},"
            f"{positive.numerator} rdiv {positive.denominator},"
            f"{negative.numerator} rdiv {negative.denominator},"
            f"{base_rate.numerator} rdiv {base_rate.denominator}"
            ")."
        )

    prior_weight = fraction(bundle["priorWeight"])
    expected_plan = atom(frame["operatorPlan"])
    expected_conclusion = atom(frame["conclusion"])
    checks = f"Plan == {expected_plan}, Conclusion == {expected_conclusion}"
    if exact:
        numeric_checks = [
            f"R =:= {exact['positive'].numerator} rdiv {exact['positive'].denominator}",
            f"S =:= {exact['negative'].numerator} rdiv {exact['negative'].denominator}",
            f"B =:= {exact['belief'].numerator} rdiv {exact['belief'].denominator}",
            f"D =:= {exact['disbelief'].numerator} rdiv {exact['disbelief'].denominator}",
            f"U =:= {exact['uncertainty'].numerator} rdiv {exact['uncertainty'].denominator}",
            f"A =:= {exact['base_rate'].numerator} rdiv {exact['base_rate'].denominator}",
            f"P =:= {exact['projected'].numerator} rdiv {exact['projected'].denominator}",
            f"C =:= {exact['conflict'].numerator} rdiv {exact['conflict'].denominator}",
        ]
        checks = ", ".join([checks, *numeric_checks])

    return rf""":- set_prolog_flag(prefer_rationals,true).
:- use_module(library(lists)).
{chr(10).join(facts)}
prior_weight({prior_weight.numerator} rdiv {prior_weight.denominator}).
missing_dependency :- report('__missing__',_,_,_).
compatible_base_rate(A) :-
    findall(X,report(_,_,_,X),Xs),
    sort(Xs,[A]).
group_average(G,R,S) :-
    findall(X,report(G,X,_,_),Rs),
    sum_list(Rs,TR),
    length(Rs,N),
    R is TR/N,
    findall(Y,report(G,_,Y,_),Ss),
    sum_list(Ss,TS),
    S is TS/N.
sum_groups([],0,0).
sum_groups([G|Gs],R,S) :-
    group_average(G,R0,S0),
    sum_groups(Gs,R1,S1),
    R is R0+R1,
    S is S0+S1.
all_singleton_groups([]).
all_singleton_groups([G|Gs]) :-
    findall(1,report(G,_,_,_),Rows),
    length(Rows,1),
    all_singleton_groups(Gs).
plan(Gs,N,P) :-
    length(Gs,C),
    ( N =:= 1 ->
        P = single_source
    ; C =:= 1 ->
        P = average_within_group
    ; all_singleton_groups(Gs) ->
        P = cumulative_across_groups
    ; P = average_then_cumulative
    ).
policy(B,D,U,P,C,O) :-
    ( C >= 1 rdiv 2 ->
        O = report_conflict
    ; U >= 1 rdiv 2 ->
        O = abstain_high_uncertainty
    ; P >= 3 rdiv 4,
      B >= 1 rdiv 2,
      U =< 1 rdiv 4 ->
        O = assert_with_evidence
    ; P =< 1 rdiv 4,
      D >= 1 rdiv 2,
      U =< 1 rdiv 4 ->
        O = qualified_refutation
    ; P >= 13 rdiv 20,
      B < 1 rdiv 2,
      U < 1 rdiv 2 ->
        O = qualify_prior_sensitive
    ; O = qualified_uncertain
    ).
compute(Plan,R,S,B,D,U,A,P,C,O) :-
    ( missing_dependency ->
        Plan = blocked_missing_dependency,
        O = request_dependency_metadata,
        R = 0, S = 0, B = 0, D = 0, U = 0, A = 0, P = 0, C = 0
    ; \+ compatible_base_rate(_) ->
        Plan = blocked_incompatible_base_rate,
        O = request_compatible_base_rates,
        R = 0, S = 0, B = 0, D = 0, U = 0, A = 0, P = 0, C = 0
    ; compatible_base_rate(A),
      findall(G,report(G,_,_,_),All),
      sort(All,Gs),
      length(All,N),
      plan(Gs,N,Plan),
      sum_groups(Gs,R,S),
      prior_weight(W),
      Z is R+S+W,
      B is R/Z,
      D is S/Z,
      U is W/Z,
      P is B+A*U,
      ( R+S =:= 0 ->
          C = 0
      ; C is 2*min(R,S)/(R+S)
      ),
      policy(B,D,U,P,C,O)
    ).
main :-
    compute(Plan,R,S,B,D,U,A,P,C,Conclusion),
    {checks},
    writeln(ok),
    halt(0).
main :-
    halt(1).
"""


def verify_prolog(
    bundle: dict[str, Any],
    frame: dict[str, Any],
    exact: dict[str, Fraction] | None,
    swipl: str,
    timeout_seconds: int,
) -> None:
    with tempfile.TemporaryDirectory(prefix="dsl-d2-") as temp_dir:
        path = Path(temp_dir) / "verify.pl"
        path.write_text(
            prolog_program(bundle, frame, exact),
            encoding="utf-8",
            newline="\n",
        )
        completed = subprocess.run(
            [swipl, "-q", "-s", str(path), "-g", "main", "-t", "halt"],
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )

    if completed.returncode != 0 or completed.stdout.strip() != "ok":
        raise FusionError(
            "SWI-Prolog mismatch: "
            f"exit={completed.returncode} "
            f"stdout={completed.stdout!r} "
            f"stderr={completed.stderr!r}"
        )


def build_frame(
    bundle: dict[str, Any],
    reports_hash: str,
    swipl: str = "swipl",
    timeout_seconds: int = 60,
    skip_prolog: bool = False,
) -> dict[str, Any]:
    frame, exact = compute(bundle)
    if not skip_prolog:
        verify_prolog(bundle, frame, exact, swipl, timeout_seconds)
    frame["sourceHashes"] = [reports_hash]
    frame["runtime"] = {
        "engine": "python" if skip_prolog else "python+swipl",
        "verifiedArithmetic": exact is not None,
        "verifiedOperatorPlan": True,
        "verifiedPolicy": True,
        "verifiedAgainstPrologKernel": not skip_prolog,
    }
    return frame
