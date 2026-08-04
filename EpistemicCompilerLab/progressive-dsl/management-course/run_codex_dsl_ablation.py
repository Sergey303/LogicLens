#!/usr/bin/env python3
"""Compare Direct, Gold DSL-A and Gold DSL-B Codex answers on frozen management cases."""
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
CONDITIONS = ("direct", "gold-a", "gold-b")


class ExperimentError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logiclens-root", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--dsl-a-package", required=True, type=Path)
    parser.add_argument("--dsl-b-package", required=True, type=Path)
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


def load_json(path: Path, context: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding=UTF8))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"cannot read {context}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExperimentError(f"{context} must be a JSON object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding=UTF8).splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ExperimentError(f"invalid JSONL {path}:{number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ExperimentError(f"JSONL record is not an object: {path}:{number}")
        records.append(value)
    if not records:
        raise ExperimentError(f"case set is empty: {path}")
    return records


def schema_errors(value: Any, schema: dict[str, Any]) -> list[str]:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: list(item.path),
    )
    return [
        f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


def create_frame(
    *,
    logiclens: Path,
    package: Path,
    case: dict[str, Any],
    level: str,
    output_root: Path,
    swipl: str,
) -> dict[str, Any]:
    query = case["goldQueries"][0]
    target = query["target"]
    request_dir = output_root / "frames" / level.lower()
    request_path = request_dir / f"{case['caseId']}.request.json"
    result_path = request_dir / f"{case['caseId']}.result.json"
    contracts = logiclens / "contracts"
    if level == "DSL-A":
        request = {
            "schemaVersion": "0.1",
            "operation": "strict-claim",
            "target": target,
        }
        tool = logiclens / "tools" / "capsule_query.py"
    elif level == "DSL-B":
        request = {
            "schemaVersion": "0.1",
            "dslLevel": "DSL-B",
            "operation": "derived-strict-claim",
            "target": target,
        }
        tool = logiclens / "tools" / "capsule_query_dsl_b.py"
    else:
        raise ExperimentError(f"unsupported DSL level: {level}")
    write_json(request_path, request)
    run_command(
        [
            sys.executable,
            str(tool),
            "--contracts-root",
            str(contracts),
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
    return load_json(result_path, f"{level} verified frame")


def frame_evidence_ids(frame: dict[str, Any]) -> list[str]:
    evidence = frame.get("evidence")
    if not isinstance(evidence, dict):
        return []
    result: list[str] = []
    for stance in ("support", "oppose"):
        records = evidence.get(stance)
        if not isinstance(records, list):
            continue
        for item in records:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict) and isinstance(item.get("assertionId"), str):
                result.append(item["assertionId"])
    return sorted(set(result))


def frame_proof_node_ids(frame: dict[str, Any]) -> list[str]:
    proof = frame.get("proof")
    if not isinstance(proof, dict):
        return []
    nodes = proof.get("nodes")
    if not isinstance(nodes, list):
        return []
    return sorted(
        {
            item["nodeId"]
            for item in nodes
            if isinstance(item, dict) and isinstance(item.get("nodeId"), str)
        }
    )


def build_prompt(
    template: str,
    *,
    case: dict[str, Any],
    condition: str,
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
    return load_json(output, "Codex response"), latency_ms


def expected_for_condition(case: dict[str, Any], condition: str) -> dict[str, Any]:
    expected = case["expectedByLevel"]
    if condition == "gold-a":
        return expected["DSL-A"]
    return expected["DSL-B"]


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
    task_expected = case["expectedByLevel"]["DSL-B"]
    frame_expected = None if condition == "direct" else expected_for_condition(case, condition)
    response_evidence = sorted(response["evidenceIds"])
    response_proof = sorted(response["proofNodeIds"])
    frame_evidence = frame_evidence_ids(frame or {})
    frame_proof = frame_proof_node_ids(frame or {})
    fabricated_evidence = sorted(set(response_evidence) - set(frame_evidence)) if frame is not None else response_evidence
    fabricated_proof = sorted(set(response_proof) - set(frame_proof)) if frame is not None else response_proof
    expected_abstain = (
        task_expected["status"] == "unknown"
        if frame_expected is None
        else frame_expected["status"] == "unknown"
    )
    scope_warnings = {"local-only", "context-dependent"}
    expected_warnings = (
        task_expected.get("warnings", [])
        if frame_expected is None
        else frame_expected.get("warnings", [])
    )
    scope_required = bool(scope_warnings.intersection(expected_warnings))
    proof_recall: float | None
    if frame_proof:
        proof_recall = len(set(response_proof).intersection(frame_proof)) / len(frame_proof)
    else:
        proof_recall = None
    warning_recall: float | None
    if expected_warnings:
        warning_recall = len(set(response["warnings"]).intersection(expected_warnings)) / len(expected_warnings)
    else:
        warning_recall = None
    return {
        "taskStatusCorrect": response["epistemicStatus"] == task_expected["status"],
        "taskActionCorrect": response["action"] == task_expected["action"],
        "frameStatusCorrect": (
            None
            if frame_expected is None
            else response["epistemicStatus"] == frame_expected["status"]
        ),
        "frameActionCorrect": (
            None
            if frame_expected is None
            else response["action"] == frame_expected["action"]
        ),
        "abstentionCorrect": response["abstain"] == expected_abstain,
        "usedFrameCorrect": response["usedVerifiedFrame"] == (frame is not None),
        "evidenceExact": (
            None if frame is None else response_evidence == frame_evidence
        ),
        "fabricatedEvidenceIds": fabricated_evidence,
        "proofNodeRecall": proof_recall,
        "fabricatedProofNodeIds": fabricated_proof,
        "warningRecall": warning_recall,
        "scopeQualificationCorrect": (
            True if not scope_required else bool(response["scopeStatement"].strip())
        ),
        "latencyMs": round(latency_ms, 3),
        "outputBytes": output_bytes,
        "eventBytes": event_bytes,
    }


def ratio(values: list[bool]) -> float | None:
    return None if not values else sum(1 for value in values if value) / len(values)


def numeric_mean(values: list[float]) -> float | None:
    return None if not values else mean(values)


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def aggregate(records: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    selected = [record for record in records if record["condition"] == condition]
    scores = [record["score"] for record in selected]
    def booleans(key: str) -> list[bool]:
        return [score[key] for score in scores if isinstance(score.get(key), bool)]
    def numbers(key: str) -> list[float]:
        return [float(score[key]) for score in scores if isinstance(score.get(key), (int, float)) and not isinstance(score.get(key), bool)]
    fabricated_evidence_count = sum(len(score["fabricatedEvidenceIds"]) for score in scores)
    fabricated_proof_count = sum(len(score["fabricatedProofNodeIds"]) for score in scores)
    latencies = numbers("latencyMs")
    return {
        "condition": condition,
        "records": len(selected),
        "taskStatusAccuracy": ratio(booleans("taskStatusCorrect")),
        "taskActionAccuracy": ratio(booleans("taskActionCorrect")),
        "frameStatusAccuracy": ratio(booleans("frameStatusCorrect")),
        "frameActionAccuracy": ratio(booleans("frameActionCorrect")),
        "abstentionAccuracy": ratio(booleans("abstentionCorrect")),
        "usedFrameAccuracy": ratio(booleans("usedFrameCorrect")),
        "evidenceExactRate": ratio(booleans("evidenceExact")),
        "meanProofNodeRecall": numeric_mean(numbers("proofNodeRecall")),
        "meanWarningRecall": numeric_mean(numbers("warningRecall")),
        "scopeQualificationAccuracy": ratio(booleans("scopeQualificationCorrect")),
        "fabricatedEvidenceCount": fabricated_evidence_count,
        "fabricatedProofNodeCount": fabricated_proof_count,
        "latencyMeanMs": numeric_mean(latencies),
        "latencyP95Ms": percentile(latencies, 0.95),
        "outputBytesMean": numeric_mean(numbers("outputBytes")),
        "eventBytesMean": numeric_mean(numbers("eventBytes")),
    }


def main() -> int:
    args = parse_args()
    logiclens = args.logiclens_root.resolve()
    cases_path = args.cases.resolve()
    package_a = args.dsl_a_package.resolve()
    package_b = args.dsl_b_package.resolve()
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
        else logiclens / "EpistemicCompilerLab" / "scripts" / "invoke_codex_json.py"
    )
    response_schema_path = (
        args.response_schema.resolve()
        if args.response_schema
        else logiclens / "contracts" / "progressive-management-codex-response-v0.schema.json"
    )
    prompt_path = (
        args.prompt_template.resolve()
        if args.prompt_template
        else logiclens
        / "EpistemicCompilerLab"
        / "progressive-dsl"
        / "management-course"
        / "prompts"
        / "codex-frame-use-v0.md"
    )
    for path, label in (
        (logiclens, "LogicLens root"),
        (cases_path, "cases"),
        (adapter, "provider adapter"),
        (response_schema_path, "response schema"),
        (prompt_path, "prompt template"),
    ):
        if not path.exists():
            raise ExperimentError(f"{label} does not exist: {path}")
    cases = load_jsonl(cases_path)
    for case in cases:
        if "DSL-A" not in case.get("expectedByLevel", {}) or "DSL-B" not in case.get("expectedByLevel", {}):
            raise ExperimentError(f"case is not an A/B case: {case.get('caseId')}")
        if len(case.get("goldQueries", [])) != 1:
            raise ExperimentError(f"case must have exactly one gold query: {case.get('caseId')}")
    package_record_a = verify_package(logiclens, package_a)
    package_record_b = verify_package(logiclens, package_b)
    response_schema = load_json(response_schema_path, "response schema")
    prompt_template = prompt_path.read_text(encoding=UTF8)
    output.mkdir(parents=True)

    frames_a: dict[str, dict[str, Any]] = {}
    frames_b: dict[str, dict[str, Any]] = {}
    for case in cases:
        identifier = case["caseId"]
        frames_a[identifier] = create_frame(
            logiclens=logiclens,
            package=package_a,
            case=case,
            level="DSL-A",
            output_root=output,
            swipl=args.swipl,
        )
        frames_b[identifier] = create_frame(
            logiclens=logiclens,
            package=package_b,
            case=case,
            level="DSL-B",
            output_root=output,
            swipl=args.swipl,
        )

    records: list[dict[str, Any]] = []
    for condition in args.conditions:
        for repetition in range(1, args.repetitions + 1):
            for case in cases:
                identifier = case["caseId"]
                frame = None
                if condition == "gold-a":
                    frame = frames_a[identifier]
                elif condition == "gold-b":
                    frame = frames_b[identifier]
                prompt = build_prompt(
                    prompt_template,
                    case=case,
                    condition=condition,
                    frame=frame,
                    repetition=repetition,
                )
                run_dir = output / "runs" / condition / identifier / f"r{repetition:02d}"
                run_dir.mkdir(parents=True, exist_ok=False)
                prompt_file = run_dir / "prompt.txt"
                response_file = run_dir / "response.json"
                events_file = run_dir / "events.jsonl"
                prompt_file.write_text(prompt, encoding=UTF8, newline="\n")
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
                        f"Codex response failed schema for {condition}/{identifier}: "
                        + "; ".join(errors[:10])
                    )
                score = score_response(
                    case=case,
                    condition=condition,
                    frame=frame,
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
                    "frameHash": None if frame is None else sha256_bytes(canonical_json(frame)),
                    "response": response,
                    "score": score,
                }
                write_json(run_dir / "record.json", record)
                records.append(record)
                print(
                    f"{condition} {identifier} r{repetition}: "
                    f"task={score['taskStatusCorrect']} "
                    f"frame={score['frameStatusCorrect']} "
                    f"latencyMs={score['latencyMs']}"
                )

    records_path = output / "records.jsonl"
    records_path.write_text(
        "".join(canonical_json(record).decode(UTF8) for record in records),
        encoding=UTF8,
        newline="\n",
    )
    summary = {
        "schemaVersion": "0.1",
        "kind": "progressive-management-codex-ablation-v0",
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
            "dslAPackage": package_record_a["packageHash"],
            "dslBPackage": package_record_b["packageHash"],
        },
        "metrics": [aggregate(records, condition) for condition in args.conditions],
    }
    write_json(output / "summary.json", summary)
    archive = shutil.make_archive(str(output), "zip", root_dir=output)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    print("[CGR_ARTIFACT_TITLE] Progressive management Codex DSL A/B ablation")
    print(f"[CGR_ARTIFACT] {archive}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ExperimentError, OSError, subprocess.SubprocessError) as exc:
        print(f"Progressive management Codex ablation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
