#!/usr/bin/env python3
"""Compare Direct, Raw observation and verified DSL-C Codex answers."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from jsonschema import Draft202012Validator

UTF8 = "utf-8"
CONDITIONS = ("direct", "raw", "gold-c")


class ExperimentError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logiclens-root", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--dsl-c-package", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--response-schema", type=Path)
    parser.add_argument("--prompt-template", type=Path)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--model")
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument(
        "--conditions",
        nargs="+",
        choices=CONDITIONS,
        default=list(CONDITIONS),
    )
    return parser.parse_args()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode(UTF8)


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding=UTF8))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"cannot read {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExperimentError(f"{label} must be an object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding=UTF8).splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ExperimentError(f"invalid JSONL {path}:{number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ExperimentError(f"JSONL record is not an object: {path}:{number}")
        rows.append(value)
    if not rows:
        raise ExperimentError(f"JSONL file is empty: {path}")
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


def schema_errors(value: Any, schema: dict[str, Any]) -> list[str]:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: list(item.path),
    )
    return [
        f"{'/'.join(str(part) for part in error.path) or '<root>'}: "
        f"{error.message}"
        for error in errors
    ]


def run_command(
    command: list[str],
    *,
    stdin: str | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        input=stdin,
        text=True,
        encoding=UTF8,
        errors="strict",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise ExperimentError(
            "command failed: "
            + " ".join(command)
            + f"\nstdout:\n{completed.stdout[-4000:]}"
            + f"\nstderr:\n{completed.stderr[-4000:]}"
        )
    return completed


def verify_package(logiclens: Path, package: Path) -> dict[str, Any]:
    tool = logiclens / "tools" / "capsule.py"
    contracts = logiclens / "contracts"
    run_command(
        [
            sys.executable,
            str(tool),
            "--contracts-root",
            str(contracts),
            "verify",
            "--package",
            str(package),
        ]
    )
    return load_json(package / "capsule-package.json", "capsule package")


def target_key(target: dict[str, Any]) -> str:
    return json.dumps(
        target,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def load_packaged_observations(package: Path) -> dict[str, dict[str, Any]]:
    files = package / "files"
    capsule = load_json(files / "capsule" / "capsule.json", "packaged capsule")
    result: dict[str, dict[str, Any]] = {}
    for entry in capsule.get("preparedFiles", []):
        if not isinstance(entry, dict) or entry.get("kind") != "observations":
            continue
        relative = entry.get("path")
        if not isinstance(relative, str):
            raise ExperimentError("invalid observation path in packaged capsule")
        for row in load_jsonl(files / "capsule" / relative):
            key = target_key(row["target"])
            if key in result:
                raise ExperimentError(f"duplicate packaged observation target: {key}")
            result[key] = row
    if not result:
        raise ExperimentError("package contains no raw observations")
    return result


def query_request(case: dict[str, Any]) -> dict[str, Any]:
    queries = case.get("goldQueries")
    if not isinstance(queries, list) or len(queries) != 1:
        raise ExperimentError(
            f"{case.get('caseId')}: exactly one gold query is required"
        )
    query = queries[0]
    request = {
        "schemaVersion": "0.1",
        "dslLevel": "DSL-C",
        "operation": query["operation"],
        "target": query["target"],
    }
    if query["operation"] == "numeric-comparison":
        request["comparison"] = query["comparison"]
    return request


def create_frame(
    *,
    logiclens: Path,
    package: Path,
    case: dict[str, Any],
    output_root: Path,
    swipl: str,
) -> dict[str, Any]:
    identifier = case["caseId"]
    request = query_request(case)
    frame_dir = output_root / "frames" / "dsl-c"
    request_path = frame_dir / f"{identifier}.request.json"
    result_path = frame_dir / f"{identifier}.result.json"
    write_json(request_path, request)
    run_command(
        [
            sys.executable,
            str(logiclens / "tools" / "capsule_query_dsl_c.py"),
            "--contracts-root",
            str(logiclens / "contracts"),
            "--package",
            str(package),
            "--request",
            str(request_path),
            "--swipl",
            swipl,
            "--pretty",
            "--output",
            str(result_path),
        ]
    )
    return load_json(result_path, "verified DSL-C frame")


def build_prompt(
    template: str,
    *,
    case: dict[str, Any],
    condition: str,
    raw_observation: dict[str, Any] | None,
    frame: dict[str, Any] | None,
    repetition: int,
) -> str:
    payload = {
        "schemaVersion": "0.1",
        "caseId": case["caseId"],
        "condition": condition,
        "repetition": repetition,
        "question": case["question"],
        "publicContext": case.get("publicContext", {}),
        "comparisonRequest": query_request(case),
        "rawObservation": raw_observation,
        "verifiedFrame": frame,
    }
    return (
        template.rstrip()
        + "\n\nBEGIN_EXPERIMENT_INPUT_JSON\n"
        + json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
        + "\nEND_EXPERIMENT_INPUT_JSON\n"
    )


def invoke_codex(
    *,
    adapter: Path,
    logiclens: Path,
    schema: Path,
    prompt: str,
    output: Path,
    events: Path,
    codex: str,
    model: str | None,
    timeout_seconds: float,
) -> tuple[dict[str, Any], float]:
    command = [
        sys.executable,
        str(adapter),
        "--working-directory",
        str(logiclens),
        "--schema",
        str(schema),
        "--output",
        str(output),
        "--events",
        str(events),
        "--codex",
        codex,
        "--timeout-seconds",
        str(timeout_seconds),
    ]
    if model:
        command.extend(["--model", model])
    started = time.perf_counter()
    run_command(command, stdin=prompt, timeout=timeout_seconds + 30)
    latency_ms = (time.perf_counter() - started) * 1000.0
    return load_json(output, "Codex numeric response"), latency_ms


def empty_numeric() -> dict[str, str]:
    return {
        "normalizedPoint": "",
        "normalizedLower": "",
        "normalizedUpper": "",
        "normalizedMean": "",
        "normalizedStandardDeviation": "",
        "normalizedThresholdValue": "",
        "normalizedThresholdLower": "",
        "normalizedThresholdUpper": "",
    }


def expected_numeric(frame: dict[str, Any]) -> dict[str, Any]:
    observation = frame.get("observation")
    comparison = frame.get("comparison")
    values: dict[str, Any] = {
        **empty_numeric(),
        "observationId": "",
        "modelKind": "missing",
        "baseUnit": "none",
        "comparisonOperator": frame["query"]["comparison"]["operator"],
        "preservedInterval": False,
        "preservedDistribution": False,
        "introducedProbabilityPolicy": False,
    }
    if isinstance(observation, dict):
        values["observationId"] = observation["observationId"]
        model_kind = observation["model"]["kind"]
        values["modelKind"] = model_kind
        normalized = frame["normalized"]
        values["baseUnit"] = normalized["baseUnit"]
        if model_kind == "point":
            values["normalizedPoint"] = normalized["value"]
        elif model_kind == "bounded":
            values["normalizedLower"] = normalized["lower"]
            values["normalizedUpper"] = normalized["upper"]
            values["preservedInterval"] = True
        elif model_kind == "normal":
            values["normalizedMean"] = normalized["mean"]
            values["normalizedStandardDeviation"] = normalized["standardDeviation"]
            values["preservedDistribution"] = True
    if isinstance(comparison, dict):
        threshold = comparison["normalizedThreshold"]
        if "value" in threshold:
            values["normalizedThresholdValue"] = threshold["value"]
        if "lower" in threshold:
            values["normalizedThresholdLower"] = threshold["lower"]
        if "upper" in threshold:
            values["normalizedThresholdUpper"] = threshold["upper"]
    return values


def expected_flags(frame: dict[str, Any]) -> list[str]:
    observation = frame.get("observation")
    warnings = set(frame.get("warnings", []))
    flags: set[str] = set()
    if "local-only" in warnings:
        flags.add("local-snapshot-only")
    if "unit-conversion-applied" in warnings:
        flags.add("unit-conversion-required")
    if observation is None:
        flags.add("missing-observation")
        return sorted(flags)

    kind = observation["model"]["kind"]
    status = frame["status"]
    if kind == "point":
        flags.add("point-comparison")
    elif kind == "bounded":
        if status == "supported":
            flags.add("whole-interval-satisfies")
        elif status == "refuted":
            flags.add("whole-interval-violates")
        else:
            flags.add("interval-crosses-threshold")
    elif kind == "normal":
        flags.add("distribution-not-strict-bound")
        flags.add("probability-policy-missing")

    comparison = frame["query"].get("comparison")
    if (
        isinstance(comparison, dict)
        and comparison.get("operator") == "between"
        and comparison.get("lowerInclusive") is True
        and comparison.get("upperInclusive") is True
    ):
        flags.add("inclusive-range")
    return sorted(flags)


def exact_string_list(value: Any) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return []
    return sorted(set(value))


def score_response(
    *,
    case: dict[str, Any],
    condition: str,
    raw_observation: dict[str, Any] | None,
    frame: dict[str, Any],
    response: dict[str, Any],
    latency_ms: float,
    output_bytes: int,
    event_bytes: int,
) -> dict[str, Any]:
    task_status = frame["status"]
    task_action = frame["action"]
    direct = condition == "direct"
    condition_status = "unknown" if direct else task_status
    condition_action = (
        "abstain_on_numeric_decision" if direct else task_action
    )
    condition_abstain = condition_status == "unknown"

    expected = expected_numeric(frame)
    if direct:
        expected = {
            **empty_numeric(),
            "observationId": "",
            "modelKind": "missing",
            "baseUnit": "none",
            "comparisonOperator": query_request(case)["comparison"]["operator"],
            "preservedInterval": False,
            "preservedDistribution": False,
            "introducedProbabilityPolicy": False,
        }

    expected_warnings = [] if direct else sorted(frame["warnings"])
    expected_interpretation = [] if direct else expected_flags(frame)
    expected_used_frame = condition == "gold-c"
    expected_used_raw = condition == "raw" and raw_observation is not None

    numeric_keys = list(empty_numeric())
    numeric_exact = all(
        response[key] == expected[key]
        for key in numeric_keys
    )
    structure_exact = all(
        response[key] == expected[key]
        for key in (
            "observationId",
            "modelKind",
            "baseUnit",
            "comparisonOperator",
            "preservedInterval",
            "preservedDistribution",
            "introducedProbabilityPolicy",
        )
    )

    return {
        "taskStatusCorrect": response["epistemicStatus"] == task_status,
        "taskActionCorrect": response["action"] == task_action,
        "conditionStatusCorrect": (
            response["epistemicStatus"] == condition_status
        ),
        "conditionActionCorrect": response["action"] == condition_action,
        "conditionAbstentionCorrect": response["abstain"] == condition_abstain,
        "usedFrameCorrect": (
            response["usedVerifiedFrame"] == expected_used_frame
        ),
        "usedRawObservationCorrect": (
            response["usedRawObservation"] == expected_used_raw
        ),
        "observationStructureExact": structure_exact,
        "normalizedValuesExact": numeric_exact,
        "interpretationFlagsExact": (
            exact_string_list(response["interpretationFlags"])
            == expected_interpretation
        ),
        "warningsExact": (
            exact_string_list(response["warnings"]) == expected_warnings
        ),
        "scopeQualificationCorrect": (
            True if direct else bool(response["scopeStatement"].strip())
        ),
        "probabilityPolicySafety": (
            response["introducedProbabilityPolicy"] is False
        ),
        "latencyMs": round(latency_ms, 3),
        "outputBytes": output_bytes,
        "eventBytes": event_bytes,
        "expected": {
            "conditionStatus": condition_status,
            "conditionAction": condition_action,
            "conditionAbstain": condition_abstain,
            "numeric": expected,
            "warnings": expected_warnings,
            "interpretationFlags": expected_interpretation,
        },
    }


def ratio(values: list[bool]) -> float | None:
    return None if not values else sum(1 for value in values if value) / len(values)


def numeric_mean(values: list[float]) -> float | None:
    return None if not values else mean(values)


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(
        0,
        min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1),
    )
    return ordered[index]


def aggregate(records: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    selected = [record for record in records if record["condition"] == condition]
    scores = [record["score"] for record in selected]

    def booleans(key: str) -> list[bool]:
        return [
            score[key]
            for score in scores
            if isinstance(score.get(key), bool)
        ]

    def numbers(key: str) -> list[float]:
        return [
            float(score[key])
            for score in scores
            if isinstance(score.get(key), (int, float))
            and not isinstance(score.get(key), bool)
        ]

    latencies = numbers("latencyMs")
    return {
        "condition": condition,
        "records": len(selected),
        "taskStatusAccuracy": ratio(booleans("taskStatusCorrect")),
        "taskActionAccuracy": ratio(booleans("taskActionCorrect")),
        "conditionStatusAccuracy": ratio(
            booleans("conditionStatusCorrect")
        ),
        "conditionActionAccuracy": ratio(
            booleans("conditionActionCorrect")
        ),
        "conditionAbstentionAccuracy": ratio(
            booleans("conditionAbstentionCorrect")
        ),
        "usedFrameAccuracy": ratio(booleans("usedFrameCorrect")),
        "usedRawObservationAccuracy": ratio(
            booleans("usedRawObservationCorrect")
        ),
        "observationStructureExactRate": ratio(
            booleans("observationStructureExact")
        ),
        "normalizedValuesExactRate": ratio(
            booleans("normalizedValuesExact")
        ),
        "interpretationFlagsExactRate": ratio(
            booleans("interpretationFlagsExact")
        ),
        "warningsExactRate": ratio(booleans("warningsExact")),
        "scopeQualificationAccuracy": ratio(
            booleans("scopeQualificationCorrect")
        ),
        "probabilityPolicySafetyRate": ratio(
            booleans("probabilityPolicySafety")
        ),
        "latencyMeanMs": numeric_mean(latencies),
        "latencyP95Ms": percentile(latencies, 0.95),
        "outputBytesMean": numeric_mean(numbers("outputBytes")),
        "eventBytesMean": numeric_mean(numbers("eventBytes")),
    }


def main() -> int:
    args = parse_args()
    logiclens = args.logiclens_root.resolve()
    cases_path = args.cases.resolve()
    package = args.dsl_c_package.resolve()
    output = args.output_root.resolve()
    if output.exists():
        raise ExperimentError(f"output already exists: {output}")
    if args.repetitions < 1 or args.repetitions > 20:
        raise ExperimentError("repetitions must be between 1 and 20")
    if args.timeout_seconds <= 0 or args.timeout_seconds > 3600:
        raise ExperimentError("timeout-seconds must be between 0 and 3600")

    adapter = (
        args.adapter.resolve()
        if args.adapter
        else logiclens
        / "EpistemicCompilerLab"
        / "scripts"
        / "invoke_codex_json.py"
    )
    response_schema_path = (
        args.response_schema.resolve()
        if args.response_schema
        else logiclens
        / "contracts"
        / "progressive-management-numeric-codex-response-v0.schema.json"
    )
    prompt_path = (
        args.prompt_template.resolve()
        if args.prompt_template
        else logiclens
        / "EpistemicCompilerLab"
        / "progressive-dsl"
        / "management-course"
        / "prompts"
        / "codex-numeric-frame-use-v0.md"
    )
    for path, label in (
        (logiclens, "LogicLens root"),
        (cases_path, "cases"),
        (package, "DSL-C package"),
        (adapter, "Codex adapter"),
        (response_schema_path, "response schema"),
        (prompt_path, "prompt template"),
    ):
        if not path.exists():
            raise ExperimentError(f"{label} does not exist: {path}")

    cases = load_jsonl(cases_path)
    package_record = verify_package(logiclens, package)
    observations = load_packaged_observations(package)
    response_schema = load_json(response_schema_path, "numeric response schema")
    prompt_template = prompt_path.read_text(encoding=UTF8)
    output.mkdir(parents=True)

    frames: dict[str, dict[str, Any]] = {}
    raw_by_case: dict[str, dict[str, Any] | None] = {}
    for case in cases:
        identifier = case["caseId"]
        frame = create_frame(
            logiclens=logiclens,
            package=package,
            case=case,
            output_root=output,
            swipl=args.swipl,
        )
        frames[identifier] = frame
        raw_by_case[identifier] = observations.get(
            target_key(query_request(case)["target"])
        )

    records: list[dict[str, Any]] = []
    for condition in args.conditions:
        for repetition in range(1, args.repetitions + 1):
            for case in cases:
                identifier = case["caseId"]
                raw_observation = (
                    raw_by_case[identifier] if condition == "raw" else None
                )
                frame = frames[identifier] if condition == "gold-c" else None
                prompt = build_prompt(
                    prompt_template,
                    case=case,
                    condition=condition,
                    raw_observation=raw_observation,
                    frame=frame,
                    repetition=repetition,
                )
                run_dir = (
                    output
                    / "runs"
                    / condition
                    / identifier
                    / f"r{repetition:02d}"
                )
                run_dir.mkdir(parents=True, exist_ok=False)
                prompt_file = run_dir / "prompt.txt"
                response_file = run_dir / "response.json"
                events_file = run_dir / "events.jsonl"
                prompt_file.write_text(
                    prompt,
                    encoding=UTF8,
                    newline="\n",
                )
                response, latency_ms = invoke_codex(
                    adapter=adapter,
                    logiclens=logiclens,
                    schema=response_schema_path,
                    prompt=prompt,
                    output=response_file,
                    events=events_file,
                    codex=args.codex,
                    model=args.model,
                    timeout_seconds=args.timeout_seconds,
                )
                errors = schema_errors(response, response_schema)
                if errors:
                    raise ExperimentError(
                        f"response schema failure {condition}/{identifier}: "
                        + "; ".join(errors[:10])
                    )
                score = score_response(
                    case=case,
                    condition=condition,
                    raw_observation=raw_observation,
                    frame=frames[identifier],
                    response=response,
                    latency_ms=latency_ms,
                    output_bytes=response_file.stat().st_size,
                    event_bytes=events_file.stat().st_size,
                )
                record = {
                    "schemaVersion": "0.1",
                    "caseId": identifier,
                    "condition": condition,
                    "repetition": repetition,
                    "question": case["question"],
                    "rawObservationHash": (
                        None
                        if raw_observation is None
                        else sha256_bytes(canonical_json(raw_observation))
                    ),
                    "frameHash": (
                        None
                        if frame is None
                        else sha256_bytes(canonical_json(frame))
                    ),
                    "response": response,
                    "score": score,
                }
                write_json(run_dir / "record.json", record)
                records.append(record)
                print(
                    f"{condition} {identifier} r{repetition}: "
                    f"task={score['taskStatusCorrect']} "
                    f"condition={score['conditionStatusCorrect']} "
                    f"numeric={score['normalizedValuesExact']} "
                    f"semantics={score['interpretationFlagsExact']} "
                    f"latencyMs={score['latencyMs']}"
                )

    records_path = output / "records.jsonl"
    records_path.write_text(
        "".join(
            canonical_json(record).decode(UTF8)
            for record in records
        ),
        encoding=UTF8,
        newline="\n",
    )
    summary = {
        "schemaVersion": "0.1",
        "kind": "progressive-management-codex-dsl-c-ablation-v0",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "conditions": list(args.conditions),
        "repetitions": args.repetitions,
        "caseCount": len(cases),
        "callCount": len(records),
        "modelSelection": args.model or "account-default",
        "hashes": {
            "cases": sha256_file(cases_path),
            "prompt": sha256_file(prompt_path),
            "responseSchema": sha256_file(response_schema_path),
            "dslCPackage": package_record["packageHash"],
        },
        "metrics": [
            aggregate(records, condition)
            for condition in args.conditions
        ],
    }
    write_json(output / "summary.json", summary)
    archive = shutil.make_archive(str(output), "zip", root_dir=output)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    print("[CGR_ARTIFACT_TITLE] Progressive management numeric DSL-C ablation")
    print(f"[CGR_ARTIFACT] {archive}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ExperimentError, OSError, subprocess.SubprocessError) as exc:
        print(f"Progressive management DSL-C ablation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
