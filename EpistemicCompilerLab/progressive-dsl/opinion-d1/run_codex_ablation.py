#!/usr/bin/env python3
"""Run Scalar/Rounded/Exact/Verified Codex ablation for DSL-D1."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from statistics import mean
from typing import Any

from jsonschema import Draft202012Validator

UTF8 = "utf-8"


class ExperimentError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--model")
    parser.add_argument("--timeout-seconds", type=float, default=300)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument(
        "--conditions",
        nargs="+",
        choices=["scalar", "rounded", "exact", "verified"],
        default=["scalar", "rounded", "exact", "verified"],
    )
    parser.add_argument("--fake-provider", action="store_true")
    parser.add_argument("--skip-prolog", action="store_true")
    return parser.parse_args()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ) + "\n").encode(UTF8)


def digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding=UTF8))
    if not isinstance(value, dict):
        raise ExperimentError(f"JSON object expected: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(path.read_text(encoding=UTF8).splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ExperimentError(f"JSON object expected: {path}:{number}")
        rows.append(value)
    return rows


def load_runtime(root: Path):
    spec = importlib.util.spec_from_file_location("dsl_d1_runtime", root / "runtime.py")
    if spec is None or spec.loader is None:
        raise ExperimentError("cannot load DSL-D1 runtime")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fraction_text(value: dict[str, int] | None) -> str:
    if value is None:
        return ""
    return f"{value['numerator']}/{value['denominator']}"


def numeric_equal(left: str, right: str) -> bool:
    if left == "" or right == "":
        return left == right
    try:
        return Decimal(left) == Decimal(right)
    except Exception:
        return False


def exact_equal(left: str, right: str) -> bool:
    if left == "" or right == "":
        return left == right
    try:
        return Fraction(left) == Fraction(right)
    except Exception:
        return False


def decimal_values(frame: dict[str, Any]) -> dict[str, str]:
    opinion = frame["roundedOpinion"]
    return {
        "belief": opinion["belief"],
        "disbelief": opinion["disbelief"],
        "uncertainty": opinion["uncertainty"],
        "baseRate": opinion["baseRate"],
        "projectedProbability": frame["roundedProjectedProbability"],
        "conflictIndex": frame["roundedConflictIndex"],
    }


def exact_values(frame: dict[str, Any]) -> dict[str, str]:
    opinion = frame["exactOpinion"]
    if opinion is None:
        return {
            "exactBelief": "",
            "exactDisbelief": "",
            "exactUncertainty": "",
            "exactBaseRate": "",
            "exactProjectedProbability": "",
            "exactConflictIndex": "",
        }
    return {
        "exactBelief": fraction_text(opinion["belief"]),
        "exactDisbelief": fraction_text(opinion["disbelief"]),
        "exactUncertainty": fraction_text(opinion["uncertainty"]),
        "exactBaseRate": fraction_text(opinion["baseRate"]),
        "exactProjectedProbability": fraction_text(frame["exactProjectedProbability"]),
        "exactConflictIndex": fraction_text(frame["exactConflictIndex"]),
    }


def blank_decimals() -> dict[str, str]:
    return {
        "belief": "",
        "disbelief": "",
        "uncertainty": "",
        "baseRate": "",
        "projectedProbability": "",
        "conflictIndex": "",
    }


def blank_exacts() -> dict[str, str]:
    return {
        "exactBelief": "",
        "exactDisbelief": "",
        "exactUncertainty": "",
        "exactBaseRate": "",
        "exactProjectedProbability": "",
        "exactConflictIndex": "",
    }


def payload(case: dict[str, Any], frame: dict[str, Any], condition: str) -> dict[str, Any]:
    result = {
        "schemaVersion": "0.1",
        "condition": condition,
        "question": case["question"],
        "scope": frame["scope"],
        "precision": frame["precision"],
        "roundingMode": frame["roundingMode"],
    }
    if condition == "scalar":
        result["projectedProbability"] = frame["roundedProjectedProbability"]
    elif condition == "rounded":
        result["roundedOpinion"] = frame["roundedOpinion"]
        result["roundedConflictIndex"] = frame["roundedConflictIndex"]
    elif condition == "exact":
        result["exactOpinion"] = frame["exactOpinion"]
        result["exactConflictIndex"] = frame["exactConflictIndex"]
    elif condition == "verified":
        result["verifiedFrame"] = frame
    return result


def prompt(base: str, data: dict[str, Any]) -> str:
    return (
        base.rstrip()
        + "\n\n--- BEGIN EXPERIMENT INPUT ---\n"
        + json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
        + "\n--- END EXPERIMENT INPUT ---\n"
    )


def expected(frame: dict[str, Any], condition: str) -> tuple[str, str, bool]:
    if condition == "scalar":
        return "scalar_insufficient", "abstain_on_scalar", True
    if condition == "rounded":
        return (
            frame["roundedConclusion"],
            frame["roundedAction"],
            frame["roundedWithholdsAssertiveDecision"],
        )
    return (
        frame["exactConclusion"],
        frame["exactAction"],
        frame["exactWithholdsAssertiveDecision"],
    )


def fake_response(frame: dict[str, Any], condition: str) -> dict[str, Any]:
    decimals = blank_decimals()
    exacts = blank_exacts()
    conclusion, action, withholds = expected(frame, condition)
    used_scalar = condition == "scalar"
    used_rounded = condition == "rounded"
    used_exact = condition == "exact"
    used_verified = condition == "verified"
    computed_rounded = condition == "rounded"
    computed_exact = condition == "exact" and frame["exactOpinion"] is not None

    if condition == "scalar":
        decimals["projectedProbability"] = frame["roundedProjectedProbability"]
        answer = "Один округлённый scalar не позволяет восстановить exact opinion или policy outcome."
        warnings = ["scalar-compression-insufficient"]
    elif condition == "rounded":
        decimals = decimal_values(frame)
        answer = "Вывод вычислен только по объявленным округлённым десятичным значениям."
        warnings = ["rounded-opinion-used"]
    elif condition == "exact":
        if frame["exactOpinion"] is not None:
            exacts = exact_values(frame)
            decimals = decimal_values(frame)
            answer = "Вывод вычислен в точной рациональной арифметике."
            warnings = ["exact-rational-opinion-used"]
        else:
            answer = "Точные дроби отсутствуют; требуется exact opinion."
            warnings = ["exact-opinion-missing"]
    else:
        decimals = decimal_values(frame)
        exacts = exact_values(frame)
        answer = "Перенесён авторитетный exact-rational verified frame."
        warnings = list(frame["warnings"])

    exact_available = frame["exactOpinion"] is not None and condition in {"exact", "verified"}
    rounded_available = condition in {"rounded", "verified"}
    return {
        "schemaVersion": "0.1",
        "condition": condition,
        "conclusion": conclusion,
        "action": action,
        "withholdsAssertiveDecision": withholds,
        **decimals,
        **exacts,
        "usedScalar": used_scalar,
        "usedRoundedOpinion": used_rounded,
        "usedExactOpinion": used_exact,
        "usedVerifiedFrame": used_verified,
        "computedFromRounded": computed_rounded,
        "computedFromExact": computed_exact,
        "recognizedRoundingCollision": (
            frame["roundingCollision"] if condition == "verified" else False
        ),
        "roundedInvariantPreserved": (
            frame["roundedInvariantPreserved"] if rounded_available else False
        ),
        "exactInvariantPreserved": (
            frame["exactInvariantPreserved"] if exact_available else False
        ),
        "baseRateIsPrior": condition != "scalar",
        "uncertaintyIsErrorProbability": False,
        "conflictSeparateFromUncertainty": condition != "scalar",
        "introducedFusion": False,
        "answerLevelProfile": frame["level"] == "answer",
        "scopeStatement": json.dumps(frame["scope"], ensure_ascii=False, sort_keys=True),
        "answer": answer,
        "warnings": warnings,
    }


def parse_usage(events_path: Path) -> dict[str, int]:
    usage = {
        "inputTokens": 0,
        "cachedInputTokens": 0,
        "outputTokens": 0,
        "reasoningOutputTokens": 0,
    }
    if not events_path.is_file():
        return usage
    for line in events_path.read_text(encoding=UTF8).splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if value.get("type") != "turn.completed":
            continue
        item = value.get("usage")
        if not isinstance(item, dict):
            continue
        usage = {
            "inputTokens": int(item.get("input_tokens", 0)),
            "cachedInputTokens": int(item.get("cached_input_tokens", 0)),
            "outputTokens": int(item.get("output_tokens", 0)),
            "reasoningOutputTokens": int(item.get("reasoning_output_tokens", 0)),
        }
    return usage


def invoke(
    root: Path,
    output_root: Path,
    schema: Path,
    text: str,
    condition: str,
    case_id: str,
    repetition: int,
    cfg: argparse.Namespace,
    frame: dict[str, Any],
) -> tuple[dict[str, Any], float, int, int, dict[str, int]]:
    run_root = output_root / "runs" / condition / case_id / f"r{repetition:02d}"
    run_root.mkdir(parents=True, exist_ok=False)
    prompt_path = run_root / "prompt.txt"
    response_path = run_root / "response.json"
    events_path = run_root / "events.jsonl"
    prompt_path.write_text(text, encoding=UTF8)
    start = time.perf_counter()
    if cfg.fake_provider:
        response = fake_response(frame, condition)
        response_path.write_bytes(canonical_json(response))
        events_path.write_text("", encoding=UTF8)
    else:
        adapter = root.parents[1] / "scripts" / "invoke_codex_json.py"
        command = [
            sys.executable,
            str(adapter),
            "--working-directory",
            str(root),
            "--schema",
            str(schema),
            "--output",
            str(response_path),
            "--events",
            str(events_path),
            "--codex",
            cfg.codex,
            "--timeout-seconds",
            str(cfg.timeout_seconds),
        ]
        if cfg.model:
            command += ["--model", cfg.model]
        completed = subprocess.run(
            command,
            input=text,
            text=True,
            encoding=UTF8,
            errors="strict",
            capture_output=True,
            timeout=cfg.timeout_seconds + 30,
        )
        if completed.returncode != 0:
            raise ExperimentError(
                f"provider failed {condition}/{case_id}: {completed.stderr[-2000:]}"
            )
        response = read_json(response_path)
    latency = (time.perf_counter() - start) * 1000
    return (
        response,
        latency,
        response_path.stat().st_size,
        events_path.stat().st_size,
        parse_usage(events_path),
    )


def score(
    case: dict[str, Any],
    frame: dict[str, Any],
    condition: str,
    response: dict[str, Any],
    latency: float,
    output_bytes: int,
    event_bytes: int,
    usage: dict[str, int],
) -> dict[str, Any]:
    wanted_conclusion, wanted_action, wanted_withholds = expected(frame, condition)

    decimal_expected = blank_decimals()
    exact_expected = blank_exacts()
    if condition == "scalar":
        decimal_expected["projectedProbability"] = frame["roundedProjectedProbability"]
    elif condition == "rounded":
        decimal_expected = decimal_values(frame)
    elif condition == "exact":
        exact_expected = exact_values(frame)
    elif condition == "verified":
        decimal_expected = decimal_values(frame)
        exact_expected = exact_values(frame)

    supplied_decimal_keys = [
        key for key, value in decimal_expected.items() if value != ""
    ]
    supplied_exact_keys = [key for key, value in exact_expected.items() if value != ""]

    numeric_transport = all(
        numeric_equal(response[key], decimal_expected[key])
        for key in supplied_decimal_keys
    ) and all(
        exact_equal(response[key], exact_expected[key])
        for key in supplied_exact_keys
    )
    lexical_transport = all(
        response[key] == decimal_expected[key] for key in supplied_decimal_keys
    ) and all(
        response[key] == exact_expected[key] for key in supplied_exact_keys
    )
    exact_fraction_transport = (
        None
        if not supplied_exact_keys
        else all(exact_equal(response[key], exact_expected[key]) for key in supplied_exact_keys)
    )

    if condition in {"rounded", "verified"}:
        projection_correct = numeric_equal(
            response["projectedProbability"], frame["roundedProjectedProbability"]
        )
    elif condition == "exact":
        projection_correct = exact_equal(
            response["exactProjectedProbability"],
            fraction_text(frame["exactProjectedProbability"]),
        )
    else:
        projection_correct = numeric_equal(
            response["projectedProbability"], frame["roundedProjectedProbability"]
        )

    rounded_invariant_expected = (
        frame["roundedInvariantPreserved"] if condition in {"rounded", "verified"} else False
    )
    exact_invariant_expected = (
        frame["exactInvariantPreserved"]
        if condition in {"exact", "verified"} and frame["exactOpinion"] is not None
        else False
    )
    invariant_correct = (
        response["roundedInvariantPreserved"] == rounded_invariant_expected
        and response["exactInvariantPreserved"] == exact_invariant_expected
    )

    semantic = (
        response["introducedFusion"] is False
        and response["uncertaintyIsErrorProbability"] is False
        and response["answerLevelProfile"] == (frame["level"] == "answer")
    )
    if condition != "scalar":
        semantic = (
            semantic
            and response["baseRateIsPrior"] is True
            and response["conflictSeparateFromUncertainty"] is True
        )

    required_warning_subset = None
    if condition == "verified":
        required_warning_subset = set(frame["warnings"]).issubset(response["warnings"])

    boundary_case = case["contrastGroup"] in {
        "p-boundary",
        "uncertainty-boundary",
        "conflict-boundary",
        "belief-boundary",
        "missing-exactness",
    }

    return {
        "taskConclusionCorrect": response["conclusion"] == frame["exactConclusion"],
        "conditionConclusionCorrect": response["conclusion"] == wanted_conclusion,
        "conditionActionCorrect": response["action"] == wanted_action,
        "conditionWithholdingCorrect": (
            response["withholdsAssertiveDecision"] == wanted_withholds
        ),
        "boundaryCase": boundary_case,
        "exactBoundaryPreserved": (
            response["conclusion"] == frame["exactConclusion"] if boundary_case else None
        ),
        "suppliedNumberNumericEquality": numeric_transport,
        "canonicalLexicalExact": lexical_transport,
        "exactFractionTransportExact": exact_fraction_transport,
        "projectionArithmeticCorrect": projection_correct,
        "invariantInterpretationCorrect": invariant_correct,
        "semanticObligationsSatisfied": semantic,
        "requiredWarningSubset": required_warning_subset,
        "probabilitySemanticsSafe": (
            response["uncertaintyIsErrorProbability"] is False
            and response["introducedFusion"] is False
        ),
        "collisionRecognitionCorrect": (
            response["recognizedRoundingCollision"] == frame["roundingCollision"]
            if condition == "verified"
            else response["recognizedRoundingCollision"] is False
        ),
        "latencyMs": latency,
        "outputBytes": output_bytes,
        "eventBytes": event_bytes,
        **usage,
    }


def rate(values: list[bool]) -> float | None:
    return None if not values else sum(values) / len(values)


def aggregate(records: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    scores = [row["score"] for row in records if row["condition"] == condition]
    boundary = [
        row["exactBoundaryPreserved"]
        for row in scores
        if isinstance(row["exactBoundaryPreserved"], bool)
    ]
    fraction = [
        row["exactFractionTransportExact"]
        for row in scores
        if isinstance(row["exactFractionTransportExact"], bool)
    ]
    warnings = [
        row["requiredWarningSubset"]
        for row in scores
        if isinstance(row["requiredWarningSubset"], bool)
    ]
    return {
        "condition": condition,
        "records": len(scores),
        "taskConclusionAccuracy": rate([row["taskConclusionCorrect"] for row in scores]),
        "conditionConclusionAccuracy": rate(
            [row["conditionConclusionCorrect"] for row in scores]
        ),
        "conditionActionAccuracy": rate([row["conditionActionCorrect"] for row in scores]),
        "conditionWithholdingAccuracy": rate(
            [row["conditionWithholdingCorrect"] for row in scores]
        ),
        "exactBoundaryPreservationRate": rate(boundary),
        "suppliedNumberNumericEqualityRate": rate(
            [row["suppliedNumberNumericEquality"] for row in scores]
        ),
        "canonicalLexicalExactRate": rate(
            [row["canonicalLexicalExact"] for row in scores]
        ),
        "exactFractionTransportExactRate": rate(fraction),
        "projectionArithmeticCorrectRate": rate(
            [row["projectionArithmeticCorrect"] for row in scores]
        ),
        "invariantInterpretationCorrectRate": rate(
            [row["invariantInterpretationCorrect"] for row in scores]
        ),
        "semanticObligationsRate": rate(
            [row["semanticObligationsSatisfied"] for row in scores]
        ),
        "requiredWarningSubsetRate": rate(warnings),
        "probabilitySemanticsSafetyRate": rate(
            [row["probabilitySemanticsSafe"] for row in scores]
        ),
        "collisionRecognitionRate": rate(
            [row["collisionRecognitionCorrect"] for row in scores]
        ),
        "latencyMeanMs": mean(row["latencyMs"] for row in scores),
        "inputTokensMean": mean(row["inputTokens"] for row in scores),
        "outputTokensMean": mean(row["outputTokens"] for row in scores),
        "reasoningOutputTokensMean": mean(
            row["reasoningOutputTokens"] for row in scores
        ),
        "outputBytesMean": mean(row["outputBytes"] for row in scores),
        "eventBytesMean": mean(row["eventBytes"] for row in scores),
    }


def contrasts(records: list[dict[str, Any]]) -> dict[str, Any]:
    index = {
        (row["condition"], row["caseId"]): row["response"]["conclusion"]
        for row in records
    }
    pairs = {
        "pBoundary": ("management.d1.p-below", "management.d1.p-above"),
        "uncertaintyBoundary": ("management.d1.u-below", "management.d1.u-above"),
        "conflictBoundary": (
            "management.d1.conflict-below",
            "management.d1.conflict-above",
        ),
        "beliefBoundary": (
            "management.d1.belief-below",
            "management.d1.belief-above",
        ),
    }
    result = {}
    for condition in sorted({row["condition"] for row in records}):
        result[condition] = {
            name + "Distinguished": index.get((condition, left)) != index.get(
                (condition, right)
            )
            for name, (left, right) in pairs.items()
        }
    return result


def main() -> int:
    cfg = parse_args()
    if not 1 <= cfg.repetitions <= 20:
        raise ExperimentError("repetitions must be in [1,20]")
    root = cfg.root.resolve()
    output_root = cfg.output_root.resolve()
    if output_root.exists() and (
        not output_root.is_dir() or any(output_root.iterdir())
    ):
        raise ExperimentError(f"output root must be absent or empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    cases_path = root / "cases-v0.jsonl"
    opinions_path = root / "opinions-v0.jsonl"
    prompt_path = root / "prompt-v0.md"
    schema_path = root / "codex-response-v0.schema.json"
    cases = read_jsonl(cases_path)
    opinions = read_jsonl(opinions_path)
    base_prompt = prompt_path.read_text(encoding=UTF8)
    schema = read_json(schema_path)
    validator = Draft202012Validator(schema)
    runtime = load_runtime(root)
    opinions_hash = digest(opinions_path.read_bytes())
    by_opinion = {row["opinionId"]: row for row in opinions}

    frames: dict[str, dict[str, Any]] = {}
    (output_root / "frames").mkdir()
    for case in cases:
        frame = runtime.build_frame(
            by_opinion[case["opinionId"]],
            opinions_hash=opinions_hash,
            swipl=cfg.swipl,
            timeout_seconds=min(int(cfg.timeout_seconds), 300),
            skip_prolog=cfg.skip_prolog,
        )
        frames[case["caseId"]] = frame
        (output_root / "frames" / f"{case['caseId']}.json").write_bytes(
            canonical_json(frame)
        )

    records = []
    records_path = output_root / "records.jsonl"
    for condition in cfg.conditions:
        for case in cases:
            frame = frames[case["caseId"]]
            text = prompt(base_prompt, payload(case, frame, condition))
            for repetition in range(1, cfg.repetitions + 1):
                response, latency, output_bytes, event_bytes, usage = invoke(
                    root,
                    output_root,
                    schema_path,
                    text,
                    condition,
                    case["caseId"],
                    repetition,
                    cfg,
                    frame,
                )
                errors = sorted(
                    validator.iter_errors(response), key=lambda error: list(error.path)
                )
                if errors:
                    raise ExperimentError(
                        f"response schema failure {condition}/{case['caseId']}: "
                        f"{errors[0].message}"
                    )
                record = {
                    "schemaVersion": "0.1",
                    "caseId": case["caseId"],
                    "condition": condition,
                    "repetition": repetition,
                    "question": case["question"],
                    "frameHash": digest(canonical_json(frame)),
                    "response": response,
                    "score": score(
                        case,
                        frame,
                        condition,
                        response,
                        latency,
                        output_bytes,
                        event_bytes,
                        usage,
                    ),
                }
                records.append(record)
                with records_path.open("ab") as handle:
                    handle.write(canonical_json(record))
                print(
                    f"{condition} {case['caseId']} r{repetition}: "
                    f"task={record['score']['taskConclusionCorrect']} "
                    f"condition={record['score']['conditionConclusionCorrect']} "
                    f"boundary={record['score']['exactBoundaryPreserved']} "
                    f"numbers={record['score']['suppliedNumberNumericEquality']} "
                    f"latencyMs={latency:.3f}"
                )

    summary = {
        "schemaVersion": "0.1",
        "kind": "progressive-management-codex-dsl-d1-boundary-ablation",
        "linearIssue": "ENG-186",
        "caseCount": len(cases),
        "callCount": len(records),
        "conditions": cfg.conditions,
        "repetitions": cfg.repetitions,
        "modelSelection": cfg.model or "account-default",
        "hashes": {
            "cases": digest(cases_path.read_bytes()),
            "opinions": opinions_hash,
            "prompt": digest(prompt_path.read_bytes()),
            "responseSchema": digest(schema_path.read_bytes()),
        },
        "metrics": [aggregate(records, condition) for condition in cfg.conditions],
        "contrastMetrics": contrasts(records),
    }
    (output_root / "summary.json").write_bytes(canonical_json(summary))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ExperimentError, OSError, subprocess.SubprocessError) as exc:
        print(f"DSL-D1 Codex ablation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
