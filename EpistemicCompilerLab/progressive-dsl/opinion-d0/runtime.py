#!/usr/bin/env python3
"""Deterministic DSL-D0 binomial-opinion runtime.

This pilot keeps four quantities distinct:
belief, disbelief, uncertainty and base rate. Projected probability is derived
as p = b + a*u. Conflict is a separate value and is never folded into u.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

UTF8 = "utf-8"
QUERY_DOMAIN = b"LogicLensOpinionD0Query\0"


class OpinionError(RuntimeError):
    pass


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opinions", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--timeout-seconds", type=int, default=15)
    parser.add_argument("--skip-prolog", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode(UTF8)


def sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding=UTF8).splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise OpinionError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise OpinionError(f"JSON object expected at {path}:{line_number}")
        rows.append(value)
    return rows


def as_fraction(value: Any, label: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise OpinionError(f"{label} must be a decimal string or integer")
    try:
        result = Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise OpinionError(f"invalid rational value for {label}: {value!r}") from exc
    return result


def bounded(value: Fraction, label: str) -> None:
    if value < 0 or value > 1:
        raise OpinionError(f"{label} must be in [0,1]")


def decimal_string(value: Fraction | None, places: int = 6) -> str:
    if value is None:
        return ""
    scale = 10**places
    numerator = value.numerator * scale
    quotient, remainder = divmod(abs(numerator), value.denominator)
    if remainder * 2 >= value.denominator:
        quotient += 1
    if numerator < 0:
        quotient = -quotient
    whole, fraction = divmod(abs(quotient), scale)
    sign = "-" if quotient < 0 else ""
    if fraction == 0:
        return f"{sign}{whole}"
    return f"{sign}{whole}.{fraction:0{places}d}".rstrip("0")


def rational_frame(value: Fraction | None) -> dict[str, int] | None:
    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def compute_opinion(record: dict[str, Any]) -> tuple[Fraction, Fraction, Fraction, Fraction, Fraction] | None:
    mode = record.get("sourceMode")
    if mode == "missing":
        return None
    if mode == "direct-opinion":
        opinion = record.get("opinion")
        if not isinstance(opinion, dict):
            raise OpinionError("direct-opinion record requires opinion")
        b = as_fraction(opinion.get("belief"), "belief")
        d = as_fraction(opinion.get("disbelief"), "disbelief")
        u = as_fraction(opinion.get("uncertainty"), "uncertainty")
        a = as_fraction(opinion.get("baseRate"), "baseRate")
        conflict = as_fraction(record.get("conflictIndex"), "conflictIndex")
    elif mode == "evidence-counts":
        evidence = record.get("evidenceCounts")
        if not isinstance(evidence, dict):
            raise OpinionError("evidence-counts record requires evidenceCounts")
        positive = as_fraction(evidence.get("positive"), "positive")
        negative = as_fraction(evidence.get("negative"), "negative")
        prior_weight = as_fraction(evidence.get("priorWeight"), "priorWeight")
        if positive < 0 or negative < 0 or prior_weight <= 0:
            raise OpinionError("evidence counts must be non-negative and priorWeight positive")
        total = positive + negative + prior_weight
        b = positive / total
        d = negative / total
        u = prior_weight / total
        a = as_fraction(evidence.get("baseRate"), "baseRate")
        evidence_total = positive + negative
        conflict = (
            Fraction(0)
            if evidence_total == 0
            else 2 * min(positive, negative) / evidence_total
        )
    else:
        raise OpinionError(f"unsupported sourceMode: {mode!r}")

    for value, label in ((b, "belief"), (d, "disbelief"), (u, "uncertainty"),
                         (a, "baseRate"), (conflict, "conflictIndex")):
        bounded(value, label)
    if b + d + u != 1:
        raise OpinionError("belief + disbelief + uncertainty must equal 1 exactly")
    return b, d, u, a, conflict


def choose_conclusion(
    b: Fraction,
    d: Fraction,
    u: Fraction,
    a: Fraction,
    conflict: Fraction,
) -> tuple[str, str]:
    projected = b + a * u
    if conflict >= Fraction(1, 2):
        return "report_conflict", "report_conflict"
    if u >= Fraction(1, 2):
        return "abstain_high_uncertainty", "abstain"
    if (
        projected >= Fraction(3, 4)
        and b >= Fraction(1, 2)
        and u <= Fraction(1, 4)
    ):
        return "assert_with_evidence", "answer_with_epistemic_profile"
    if (
        projected <= Fraction(1, 4)
        and d >= Fraction(1, 2)
        and u <= Fraction(1, 4)
    ):
        return "qualified_refutation", "explain_refutation_with_profile"
    if (
        projected >= Fraction(13, 20)
        and b < Fraction(1, 2)
        and u < Fraction(1, 2)
    ):
        return "qualify_prior_sensitive", "answer_with_prior_warning"
    return "qualified_uncertain", "answer_with_uncertainty"


def build_warnings(
    record: dict[str, Any],
    u: Fraction,
    a: Fraction,
    conflict: Fraction,
) -> list[str]:
    warnings = ["local-only", "projected-probability-not-confidence"]
    if u >= Fraction(1, 2):
        warnings.append("high-uncertainty")
    if a * u >= Fraction(1, 5):
        warnings.append("base-rate-material")
    if conflict >= Fraction(1, 2):
        warnings.append("conflict-high")
    if record.get("sourceMode") == "evidence-counts":
        warnings.append("evidence-count-derived")
    if record.get("level") == "answer":
        warnings.extend(["answer-level-opinion", "aggregation-policy-declared"])
    return sorted(warnings)


def query_hash(case_id: str, opinions_hash: str) -> str:
    return sha256(
        QUERY_DOMAIN
        + canonical_json({"schemaVersion": "0.1", "caseId": case_id, "opinionsHash": opinions_hash})
    )


def prolog_fraction(value: Fraction) -> str:
    return f"({value.numerator} rdiv {value.denominator})"


def run_prolog(
    *,
    computed: tuple[Fraction, Fraction, Fraction, Fraction, Fraction] | None,
    expected_conclusion: str,
    swipl: str,
    timeout_seconds: int,
) -> None:
    if computed is None:
        body = "main :- write(request_opinion), halt."
    else:
        b, d, u, a, conflict = computed
        projected = b + a * u
        body = f"""
choose(B,D,U,A,C,Conclusion) :-
  P is B + A*U,
  ( C >= (1 rdiv 2) -> Conclusion = report_conflict
  ; U >= (1 rdiv 2) -> Conclusion = abstain_high_uncertainty
  ; P >= (3 rdiv 4), B >= (1 rdiv 2), U =< (1 rdiv 4)
      -> Conclusion = assert_with_evidence
  ; P =< (1 rdiv 4), D >= (1 rdiv 2), U =< (1 rdiv 4)
      -> Conclusion = qualified_refutation
  ; P >= (13 rdiv 20), B < (1 rdiv 2), U < (1 rdiv 2)
      -> Conclusion = qualify_prior_sensitive
  ; Conclusion = qualified_uncertain
  ).

main :-
  B is {prolog_fraction(b)},
  D is {prolog_fraction(d)},
  U is {prolog_fraction(u)},
  A is {prolog_fraction(a)},
  C is {prolog_fraction(conflict)},
  ExpectedP is {prolog_fraction(projected)},
  B + D + U =:= 1,
  P is B + A*U,
  P =:= ExpectedP,
  choose(B,D,U,A,C,Conclusion),
  write(Conclusion),
  halt.
"""
    program = f":- set_prolog_flag(prefer_rationals, true).\n:- initialization(main).\n{body}\n"
    with tempfile.TemporaryDirectory(prefix="logiclens-opinion-d0-") as temp:
        script = Path(temp) / "verify.pl"
        script.write_text(program, encoding=UTF8)
        try:
            completed = subprocess.run(
                [swipl, "-q", "-f", "none", "-s", str(script)],
                text=True,
                encoding=UTF8,
                errors="strict",
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise OpinionError("SWI-Prolog opinion kernel timed out") from exc
        if completed.returncode != 0:
            raise OpinionError(
                f"SWI-Prolog opinion kernel failed: {completed.stderr.strip()[-1000:]}"
            )
        actual = completed.stdout.strip()
        if actual != expected_conclusion:
            raise OpinionError(
                f"Python/Prolog conclusion mismatch: expected={expected_conclusion} actual={actual}"
            )


def build_frame(
    record: dict[str, Any],
    *,
    opinions_hash: str,
    swipl: str,
    timeout_seconds: int,
    skip_prolog: bool,
) -> dict[str, Any]:
    case_id = record.get("opinionId")
    if not isinstance(case_id, str):
        raise OpinionError("opinionId is required")
    computed = compute_opinion(record)
    if computed is None:
        conclusion = "request_opinion"
        action = "abstain_and_request_opinion"
        warnings = ["missing-opinion"]
        opinion_frame = None
        projected = None
        conflict = None
    else:
        b, d, u, a, conflict = computed
        projected = b + a * u
        conclusion, action = choose_conclusion(b, d, u, a, conflict)
        warnings = build_warnings(record, u, a, conflict)
        opinion_frame = {
            "belief": decimal_string(b),
            "disbelief": decimal_string(d),
            "uncertainty": decimal_string(u),
            "baseRate": decimal_string(a),
            "exact": {
                "belief": rational_frame(b),
                "disbelief": rational_frame(d),
                "uncertainty": rational_frame(u),
                "baseRate": rational_frame(a),
            },
        }

    if not skip_prolog:
        run_prolog(
            computed=computed,
            expected_conclusion=conclusion,
            swipl=swipl,
            timeout_seconds=timeout_seconds,
        )

    return {
        "schemaVersion": "0.1",
        "dslLevel": "DSL-D",
        "caseId": case_id,
        "queryHash": query_hash(case_id, opinions_hash),
        "target": record.get("target"),
        "level": record.get("level"),
        "sourceMode": record.get("sourceMode"),
        "opinion": opinion_frame,
        "projectedProbability": decimal_string(projected) if projected is not None else None,
        "projectedProbabilityExact": rational_frame(projected),
        "conflictIndex": decimal_string(conflict) if conflict is not None else None,
        "conflictIndexExact": rational_frame(conflict),
        "allowedConclusion": conclusion,
        "action": action,
        "policyId": record.get("policyId"),
        "aggregationPolicyId": record.get("aggregationPolicyId"),
        "scope": record.get("scope"),
        "dependencyGroups": record.get("dependencyGroups", []),
        "provenance": record.get("provenance", []),
        "warnings": warnings,
        "displayProfile": (
            None
            if computed is None
            else {
                "beliefPercent": decimal_string(computed[0] * 100),
                "disbeliefPercent": decimal_string(computed[1] * 100),
                "uncertaintyPercent": decimal_string(computed[2] * 100),
                "baseRatePercent": decimal_string(computed[3] * 100),
                "projectedProbabilityPercent": decimal_string(projected * 100),
                "conflictPercent": decimal_string(conflict * 100),
            }
        ),
        "runtime": {
            "engine": "python+swipl" if not skip_prolog else "python-only-test",
            "semantics": "binomial-opinion-d0",
            "verifiedArithmetic": True,
            "verifiedPolicy": True,
            "verifiedAgainstPrologKernel": not skip_prolog,
            "implicitFusionPerformed": False,
        },
    }


def main() -> int:
    args = arguments()
    if args.timeout_seconds < 1 or args.timeout_seconds > 300:
        raise OpinionError("timeout-seconds must be between 1 and 300")
    rows = load_jsonl(args.opinions.resolve())
    identifiers = [row.get("opinionId") for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise OpinionError("duplicate opinionId")
    selected = next((row for row in rows if row.get("opinionId") == args.case_id), None)
    if selected is None:
        raise OpinionError(f"unknown case ID: {args.case_id}")
    opinions_hash = sha256(args.opinions.read_bytes())
    frame = build_frame(
        selected,
        opinions_hash=opinions_hash,
        swipl=args.swipl,
        timeout_seconds=args.timeout_seconds,
        skip_prolog=args.skip_prolog,
    )
    content = (
        (json.dumps(frame, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(UTF8)
        if args.pretty
        else canonical_json(frame)
    )
    if args.output is None:
        sys.stdout.buffer.write(content)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(content)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OpinionError, OSError, subprocess.SubprocessError) as exc:
        print(f"DSL-D0 opinion runtime failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
