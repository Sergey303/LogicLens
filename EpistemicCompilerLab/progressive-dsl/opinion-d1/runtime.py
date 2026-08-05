#!/usr/bin/env python3
"""Exact-rational DSL-D1 boundary runtime with optional SWI-Prolog cross-check."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from fractions import Fraction
from pathlib import Path
from typing import Any

getcontext().prec = 80
UTF8 = "utf-8"


class RuntimeErrorD1(RuntimeError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ) + "\n").encode(UTF8)


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def fraction_from_object(value: dict[str, Any]) -> Fraction:
    if not isinstance(value, dict):
        raise RuntimeErrorD1("fraction object expected")
    numerator = value.get("numerator")
    denominator = value.get("denominator")
    if not isinstance(numerator, int) or not isinstance(denominator, int):
        raise RuntimeErrorD1("fraction numerator/denominator must be integers")
    if denominator <= 0 or numerator < 0:
        raise RuntimeErrorD1("fraction must be non-negative with positive denominator")
    return Fraction(numerator, denominator)


def fraction_object(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def decimal_text(value: Fraction, precision: int) -> str:
    quantum = Decimal(1).scaleb(-precision)
    decimal = Decimal(value.numerator) / Decimal(value.denominator)
    return format(decimal.quantize(quantum, rounding=ROUND_HALF_EVEN), f".{precision}f")


def fraction_from_decimal(value: str) -> Fraction:
    try:
        return Fraction(Decimal(value))
    except Exception as exc:
        raise RuntimeErrorD1(f"invalid decimal value: {value!r}") from exc


def apply_policy(
    belief: Fraction,
    disbelief: Fraction,
    uncertainty: Fraction,
    base_rate: Fraction,
    conflict: Fraction,
) -> tuple[str, str, bool, Fraction]:
    projected = belief + base_rate * uncertainty
    if conflict >= Fraction(1, 2):
        return "report_conflict", "report_conflict", True, projected
    if uncertainty >= Fraction(1, 2):
        return "abstain_high_uncertainty", "abstain", True, projected
    if (
        projected >= Fraction(3, 4)
        and belief >= Fraction(1, 2)
        and uncertainty <= Fraction(1, 4)
    ):
        return (
            "assert_with_evidence",
            "answer_with_epistemic_profile",
            False,
            projected,
        )
    if (
        projected <= Fraction(1, 4)
        and disbelief >= Fraction(1, 2)
        and uncertainty <= Fraction(1, 4)
    ):
        return (
            "qualified_refutation",
            "explain_refutation_with_profile",
            False,
            projected,
        )
    if (
        projected >= Fraction(13, 20)
        and belief < Fraction(1, 2)
        and uncertainty < Fraction(1, 2)
    ):
        return (
            "qualify_prior_sensitive",
            "answer_with_prior_warning",
            False,
            projected,
        )
    return "qualified_uncertain", "answer_with_uncertainty", True, projected


def exact_values(fixture: dict[str, Any]) -> tuple[Fraction, Fraction, Fraction, Fraction, Fraction] | None:
    opinion = fixture.get("exactOpinion")
    conflict = fixture.get("exactConflictIndex")
    if opinion is None or conflict is None:
        return None
    if not isinstance(opinion, dict):
        raise RuntimeErrorD1("exactOpinion must be object or null")
    return (
        fraction_from_object(opinion["belief"]),
        fraction_from_object(opinion["disbelief"]),
        fraction_from_object(opinion["uncertainty"]),
        fraction_from_object(opinion["baseRate"]),
        fraction_from_object(conflict),
    )


def rounded_values(fixture: dict[str, Any]) -> tuple[Fraction, Fraction, Fraction, Fraction, Fraction]:
    opinion = fixture.get("roundedOpinion")
    if not isinstance(opinion, dict):
        raise RuntimeErrorD1("roundedOpinion must be object")
    return (
        fraction_from_decimal(opinion["belief"]),
        fraction_from_decimal(opinion["disbelief"]),
        fraction_from_decimal(opinion["uncertainty"]),
        fraction_from_decimal(opinion["baseRate"]),
        fraction_from_decimal(fixture["roundedConflictIndex"]),
    )


PROLOG = r"""
ge(N1,D1,N2,D2) :- N1 * D2 >= N2 * D1.
gt(N1,D1,N2,D2) :- N1 * D2 > N2 * D1.
le(N1,D1,N2,D2) :- N1 * D2 =< N2 * D1.
lt(N1,D1,N2,D2) :- N1 * D2 < N2 * D1.

projected(BN,BD,UN,UD,AN,AD,PN,PD) :-
    PN is BN * AD * UD + AN * UN * BD,
    PD is BD * AD * UD.

valid_opinion(BN,BD,DN,DD,UN,UD) :-
    BN * DD * UD + DN * BD * UD + UN * BD * DD =:= BD * DD * UD.

policy(BN,BD,_DN,_DD,_UN,_UD,_AN,_AD,CN,CD,
       report_conflict,report_conflict,true,PN,PD) :-
    ge(CN,CD,1,2), !,
    projected(BN,BD,_UN,_UD,_AN,_AD,PN,PD).
policy(BN,BD,_DN,_DD,UN,UD,AN,AD,_CN,_CD,
       abstain_high_uncertainty,abstain,true,PN,PD) :-
    ge(UN,UD,1,2), !,
    projected(BN,BD,UN,UD,AN,AD,PN,PD).
policy(BN,BD,_DN,_DD,UN,UD,AN,AD,_CN,_CD,
       assert_with_evidence,answer_with_epistemic_profile,false,PN,PD) :-
    projected(BN,BD,UN,UD,AN,AD,PN,PD),
    ge(PN,PD,3,4), ge(BN,BD,1,2), le(UN,UD,1,4), !.
policy(BN,BD,DN,DD,UN,UD,AN,AD,_CN,_CD,
       qualified_refutation,explain_refutation_with_profile,false,PN,PD) :-
    projected(BN,BD,UN,UD,AN,AD,PN,PD),
    le(PN,PD,1,4), ge(DN,DD,1,2), le(UN,UD,1,4), !.
policy(BN,BD,_DN,_DD,UN,UD,AN,AD,_CN,_CD,
       qualify_prior_sensitive,answer_with_prior_warning,false,PN,PD) :-
    projected(BN,BD,UN,UD,AN,AD,PN,PD),
    ge(PN,PD,13,20), lt(BN,BD,1,2), lt(UN,UD,1,2), !.
policy(BN,BD,_DN,_DD,UN,UD,AN,AD,_CN,_CD,
       qualified_uncertain,answer_with_uncertainty,true,PN,PD) :-
    projected(BN,BD,UN,UD,AN,AD,PN,PD).

opinion_valid(BN,BD,DN,DD,UN,UD,true) :-
    valid_opinion(BN,BD,DN,DD,UN,UD), !.
opinion_valid(_BN,_BD,_DN,_DD,_UN,_UD,false).

run(BN,BD,DN,DD,UN,UD,AN,AD,CN,CD) :-
    opinion_valid(BN,BD,DN,DD,UN,UD,V),
    policy(BN,BD,DN,DD,UN,UD,AN,AD,CN,CD,C,A,W,PN,PD),
    format('~w|~w|~w|~w|~w|~w', [C,A,W,PN,PD,V]).
"""


def verify_with_prolog(
    values: tuple[Fraction, Fraction, Fraction, Fraction, Fraction],
    expected: tuple[str, str, bool, Fraction],
    swipl: str,
    timeout_seconds: int,
) -> None:
    belief, disbelief, uncertainty, base_rate, conflict = values
    conclusion, action, withholds, projected = expected
    goal = (
        "run("
        f"{belief.numerator},{belief.denominator},"
        f"{disbelief.numerator},{disbelief.denominator},"
        f"{uncertainty.numerator},{uncertainty.denominator},"
        f"{base_rate.numerator},{base_rate.denominator},"
        f"{conflict.numerator},{conflict.denominator}"
        ")"
    )
    with tempfile.TemporaryDirectory(prefix="logiclens-d1-") as temp:
        program = Path(temp) / "kernel.pl"
        program.write_text(PROLOG, encoding=UTF8)
        completed = subprocess.run(
            [swipl, "-q", "-s", str(program), "-g", goal, "-t", "halt"],
            capture_output=True,
            text=True,
            encoding=UTF8,
            errors="strict",
            check=False,
            timeout=timeout_seconds,
        )
    if completed.returncode != 0:
        raise RuntimeErrorD1(
            f"SWI-Prolog failed: {completed.stderr.strip() or completed.stdout.strip()}"
        )
    parts = completed.stdout.strip().split("|")
    if len(parts) != 6:
        raise RuntimeErrorD1(f"unexpected SWI-Prolog output: {completed.stdout!r}")
    got_conclusion, got_action, got_withholds, p_num, p_den, got_valid = parts
    got_projected = Fraction(int(p_num), int(p_den))
    expected_valid = values[0] + values[1] + values[2] == 1
    if (
        got_conclusion != conclusion
        or got_action != action
        or (got_withholds == "true") is not withholds
        or got_projected != projected
        or (got_valid == "true") is not expected_valid
    ):
        raise RuntimeErrorD1(
            "Python/SWI-Prolog disagreement: "
            f"python={(conclusion, action, withholds, projected, expected_valid)} "
            f"prolog={(got_conclusion, got_action, got_withholds, got_projected, got_valid)}"
        )


def build_frame(
    fixture: dict[str, Any],
    *,
    opinions_hash: str,
    swipl: str = "swipl",
    timeout_seconds: int = 60,
    skip_prolog: bool = False,
) -> dict[str, Any]:
    precision = fixture["precision"]
    rounded = rounded_values(fixture)
    rb, rd, ru, ra, rc = rounded
    if rb + rd + ru <= 0:
        raise RuntimeErrorD1("rounded masses are empty")
    rounded_result = apply_policy(rb, rd, ru, ra, rc)
    rounded_conclusion, rounded_action, rounded_withholds, rounded_projected = rounded_result

    exact = exact_values(fixture)
    if exact is None:
        exact_opinion = None
        exact_conflict = None
        exact_projected = None
        exact_conclusion = "request_exact_opinion"
        exact_action = "abstain_and_request_exact_opinion"
        exact_withholds = True
        exact_invariant = False
        exact_verified = True
    else:
        eb, ed, eu, ea, ec = exact
        if eb + ed + eu != 1:
            raise RuntimeErrorD1("exact b+d+u must equal 1")
        if any(value < 0 or value > 1 for value in exact):
            raise RuntimeErrorD1("exact opinion values must be in [0,1]")
        exact_result = apply_policy(eb, ed, eu, ea, ec)
        exact_conclusion, exact_action, exact_withholds, exact_projected = exact_result
        exact_opinion = {
            "belief": fraction_object(eb),
            "disbelief": fraction_object(ed),
            "uncertainty": fraction_object(eu),
            "baseRate": fraction_object(ea),
        }
        exact_conflict = fraction_object(ec)
        exact_invariant = True
        if not skip_prolog:
            verify_with_prolog(exact, exact_result, swipl, timeout_seconds)
        exact_verified = not skip_prolog

    if not skip_prolog:
        verify_with_prolog(rounded, rounded_result, swipl, timeout_seconds)

    rounded_invariant = rb + rd + ru == 1
    rounding_collision = (
        exact is not None
        and (
            exact_conclusion != rounded_conclusion
            or exact_projected != rounded_projected
            or not rounded_invariant
        )
    )
    warnings = ["pilot-only", "no-implicit-fusion"]
    if exact is None:
        warnings.append("exact-opinion-missing")
    if not rounded_invariant:
        warnings.append("rounded-invariant-drift")
    if exact is not None and exact_conclusion != rounded_conclusion:
        warnings.append("rounding-changes-policy-outcome")
    if exact is not None and exact_projected != rounded_projected:
        warnings.append("rounded-projection-differs-from-exact")

    frame = {
        "schemaVersion": "0.1",
        "dslLevel": "DSL-D1",
        "opinionId": fixture["opinionId"],
        "level": fixture["level"],
        "sourceMode": fixture["sourceMode"],
        "precision": precision,
        "roundingMode": fixture["roundingMode"],
        "scope": fixture["scope"],
        "exactOpinion": exact_opinion,
        "exactConflictIndex": exact_conflict,
        "exactProjectedProbability": (
            None if exact_projected is None else fraction_object(exact_projected)
        ),
        "roundedOpinion": fixture["roundedOpinion"],
        "roundedConflictIndex": fixture["roundedConflictIndex"],
        "roundedProjectedProbability": decimal_text(rounded_projected, precision),
        "exactConclusion": exact_conclusion,
        "exactAction": exact_action,
        "exactWithholdsAssertiveDecision": exact_withholds,
        "roundedConclusion": rounded_conclusion,
        "roundedAction": rounded_action,
        "roundedWithholdsAssertiveDecision": rounded_withholds,
        "exactInvariantPreserved": exact_invariant,
        "roundedInvariantPreserved": rounded_invariant,
        "roundingCollision": rounding_collision,
        "provenance": fixture["provenance"],
        "dependencyGroups": fixture["dependencyGroups"],
        "warnings": sorted(warnings),
        "runtime": {
            "engine": "python+swipl" if not skip_prolog else "python",
            "semantics": "exact-rational-opinion-boundary-d1",
            "verifiedExactArithmetic": True,
            "verifiedRoundedArithmetic": True,
            "verifiedPolicy": True,
            "verifiedAgainstPrologKernel": exact_verified and not skip_prolog,
            "implicitFusionPerformed": False,
        },
    }
    frame["queryHash"] = digest_bytes(canonical_json({
        "opinionId": fixture["opinionId"],
        "opinionsHash": opinions_hash,
        "precision": precision,
    }))
    return frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--opinions-hash", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--skip-prolog", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture = json.loads(args.fixture.read_text(encoding=UTF8))
    frame = build_frame(
        fixture,
        opinions_hash=args.opinions_hash,
        swipl=args.swipl,
        timeout_seconds=args.timeout_seconds,
        skip_prolog=args.skip_prolog,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json(frame))
    print(json.dumps(frame, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeErrorD1, OSError, subprocess.SubprocessError) as exc:
        print(f"DSL-D1 runtime failed: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1) from exc
