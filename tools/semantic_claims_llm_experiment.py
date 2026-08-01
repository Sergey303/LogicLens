#!/usr/bin/env python3
"""Plan and aggregate measured bounded LLM Semantic Claims pilot runs."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from active_epoch.hashing import append_field, canonical_json_bytes
from semantic_claims_artifact import (
    FROZEN_MANIFEST_SHA256,
    SemanticClaimsArtifactError,
    load_case,
)
from semantic_claims_llm import (
    SemanticClaimsLlmError,
    build_request,
    sha256_prefixed,
    verify_candidate,
    verify_evaluation,
)
from semantic_claims_llm_contract import (
    DEFAULT_CONTEXT_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_TOKENS,
)

PLAN_SCHEMA = "semantic-claims-llm-experiment-plan-v0"
REPORT_SCHEMA = "semantic-claims-llm-experiment-report-v0"
PLAN_DOMAIN = b"LogicLensSemanticClaimsLlmExperimentPlan\0"
REPORT_DOMAIN = b"LogicLensSemanticClaimsLlmExperimentReport\0"
HASH_VERSION = bytes((1,))
PILOT_ID = "semantic-claims-gate-a-pilot-v0"
PILOT_CASES = (
    "clear-revision-comparison",
    "opaque-revision-comparison",
    "ambiguous-time-excluded",
    "lookalike-incomparable-records",
    "single-entity-generic-fallback",
)
PILOT_SEEDS = (0, 1, 2)
BASELINE_REFERENCE = {
    "allCases": {"tp": 14, "fp": 0, "fn": 4, "f1": 0.875},
    "opaqueCase": {"tp": 0, "fp": 0, "fn": 3, "f1": 0.0},
}


class SemanticClaimsExperimentError(RuntimeError):
    pass


def domain_hash(domain: bytes, value: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(HASH_VERSION)
    append_field(digest, canonical_json_bytes(value))
    return "sha256:" + digest.hexdigest()


def read_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SemanticClaimsExperimentError(f"cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise SemanticClaimsExperimentError(f"{label} must be a JSON object: {path}")
    return value, raw


def safe_ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def f1_from_counts(tp: int, fp: int, fn: int) -> float:
    precision = safe_ratio(tp, tp + fp)
    recall = safe_ratio(tp, tp + fn)
    return (
        round(2 * precision * recall / (precision + recall), 6)
        if precision + recall
        else 0.0
    )


def load_frozen_case(root: Path, case_id: str):
    try:
        return load_case(root.resolve(), case_id, FROZEN_MANIFEST_SHA256)
    except SemanticClaimsArtifactError as error:
        raise SemanticClaimsExperimentError(f"cannot load frozen case {case_id}: {error}") from error


def build_plan(benchmark_root: Path) -> dict[str, Any]:
    matrix: list[dict[str, Any]] = []
    benchmark: dict[str, Any] | None = None
    for case_id in PILOT_CASES:
        summary, manifest_raw, case_path, case, case_raw = load_frozen_case(
            benchmark_root, case_id
        )
        current_benchmark = {
            "benchmarkId": summary.benchmark_id,
            "manifestSha256": sha256_prefixed(manifest_raw),
        }
        if benchmark is None:
            benchmark = current_benchmark
        elif benchmark != current_benchmark:
            raise SemanticClaimsExperimentError("pilot cases do not share one benchmark manifest")
        for seed in PILOT_SEEDS:
            request = build_request(
                case,
                DEFAULT_MODEL,
                seed,
                DEFAULT_CONTEXT_TOKENS,
                DEFAULT_OUTPUT_TOKENS,
            )
            run_id = f"{case_id}--seed-{seed}"
            matrix.append(
                {
                    "runId": run_id,
                    "caseId": case_id,
                    "casePath": case_path,
                    "caseSha256": sha256_prefixed(case_raw),
                    "seed": seed,
                    "requestSha256": sha256_prefixed(canonical_json_bytes(request)),
                }
            )
    assert benchmark is not None
    payload: dict[str, Any] = {
        "schemaVersion": PLAN_SCHEMA,
        "stage": "measured-llm-semantic-claims-plan",
        "experimentId": PILOT_ID,
        "benchmark": benchmark,
        "producer": {
            "provider": "ollama",
            "model": DEFAULT_MODEL,
            "temperature": 0,
            "numCtx": DEFAULT_CONTEXT_TOKENS,
            "numPredict": DEFAULT_OUTPUT_TOKENS,
            "numGpu": 0,
            "numBatch": 64,
        },
        "matrix": matrix,
        "baselineReference": deepcopy(BASELINE_REFERENCE),
        "policy": {
            "allRunsMustBeAccountedFor": True,
            "missingRunsMayNotBeExcluded": True,
            "syntheticRunsForbidden": True,
            "automaticPromotion": False,
        },
    }
    payload["artifactHash"] = domain_hash(PLAN_DOMAIN, payload)
    return payload


def validate_plan_shape(plan: dict[str, Any]) -> None:
    required = {
        "schemaVersion",
        "stage",
        "experimentId",
        "benchmark",
        "producer",
        "matrix",
        "baselineReference",
        "policy",
        "artifactHash",
    }
    if set(plan) != required:
        raise SemanticClaimsExperimentError("experiment plan keys do not match v0")
    if plan["schemaVersion"] != PLAN_SCHEMA or plan["stage"] != "measured-llm-semantic-claims-plan":
        raise SemanticClaimsExperimentError("unsupported experiment plan")
    run_ids = [item.get("runId") for item in plan["matrix"]]
    if len(run_ids) != len(set(run_ids)):
        raise SemanticClaimsExperimentError("experiment plan contains duplicate runId values")


def verify_plan(benchmark_root: Path, plan_path: Path) -> dict[str, Any]:
    plan, raw = read_object(plan_path.resolve(), "experiment plan")
    validate_plan_shape(plan)
    expected = build_plan(benchmark_root.resolve())
    if plan != expected:
        raise SemanticClaimsExperimentError("experiment plan does not reproduce frozen pilot v0")
    if raw != canonical_json_bytes(plan):
        raise SemanticClaimsExperimentError("experiment plan is not canonical JSON bytes")
    return plan


def claim_signature(candidate: dict[str, Any]) -> list[tuple[Any, ...]]:
    return sorted(
        (
            claim["dataElement"]["kind"],
            claim["dataElement"]["id"],
            claim["facet"],
            claim["role"],
            claim["status"],
        )
        for claim in candidate["claims"]
    )


def run_paths(root: Path, run_id: str) -> dict[str, Path]:
    directory = root / run_id
    return {
        "directory": directory,
        "request": directory / "request.json",
        "raw": directory / "raw-ollama-response.json",
        "response": directory / "model-response.json",
        "candidate": directory / "candidate.json",
        "evaluation": directory / "evaluation.json",
    }


def inspect_run(
    benchmark_root: Path,
    runs_root: Path,
    item: dict[str, Any],
    plan: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    paths = run_paths(runs_root, item["runId"])
    required = [paths[key] for key in ("request", "raw", "response", "candidate", "evaluation")]
    if not paths["directory"].exists():
        return {"runId": item["runId"], "caseId": item["caseId"], "seed": item["seed"], "status": "missing"}, None
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        return {"runId": item["runId"], "caseId": item["caseId"], "seed": item["seed"], "status": "incomplete", "missingFiles": missing}, None
    try:
        candidate = verify_candidate(
            benchmark_root,
            paths["request"],
            paths["raw"],
            paths["response"],
            paths["candidate"],
        )
        evaluation = verify_evaluation(
            benchmark_root,
            paths["candidate"],
            paths["evaluation"],
        )
        _request, request_raw = read_object(paths["request"], "run request")
        if sha256_prefixed(request_raw) != item["requestSha256"]:
            raise SemanticClaimsExperimentError("run request hash does not match the frozen plan")
        producer = candidate["producer"]
        if producer["model"] != plan["producer"]["model"] or producer["seed"] != item["seed"]:
            raise SemanticClaimsExperimentError("candidate producer does not match planned model/seed")
        metrics = evaluation["metrics"]
        exact = metrics["exactRole"]
        evidence = evaluation["contractEvidenceValidity"]
        record = {
            "runId": item["runId"],
            "caseId": item["caseId"],
            "seed": item["seed"],
            "status": "valid",
            "candidateArtifactHash": candidate["artifactHash"],
            "evaluationArtifactHash": evaluation["artifactHash"],
            "exactRole": deepcopy(exact),
            "macroF1ByRole": metrics["macroF1ByRole"],
            "falseSupportedCount": metrics["falseSupportedCount"],
            "ambiguityDetection": deepcopy(metrics["ambiguityDetection"]),
            "contractEvidenceValidity": deepcopy(evidence),
            "unclassifiedPredicateIds": deepcopy(candidate["unclassifiedPredicateIds"]),
        }
        return record, {"candidate": candidate, "signature": claim_signature(candidate)}
    except (SemanticClaimsLlmError, SemanticClaimsExperimentError) as error:
        return {"runId": item["runId"], "caseId": item["caseId"], "seed": item["seed"], "status": "invalid", "reason": str(error)}, None


def aggregate_report(
    benchmark_root: Path,
    plan: dict[str, Any],
    runs_root: Path,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    details: dict[str, dict[str, Any]] = {}
    for item in plan["matrix"]:
        record, detail = inspect_run(benchmark_root, runs_root, item, plan)
        records.append(record)
        if detail is not None:
            details[item["runId"]] = detail
    valid = [record for record in records if record["status"] == "valid"]
    tp = sum(record["exactRole"]["tp"] for record in valid)
    fp = sum(record["exactRole"]["fp"] for record in valid)
    fn = sum(record["exactRole"]["fn"] for record in valid)
    by_case: list[dict[str, Any]] = []
    stability_ok = True
    for case_id in PILOT_CASES:
        case_records = [record for record in records if record["caseId"] == case_id]
        case_valid = [record for record in case_records if record["status"] == "valid"]
        signatures = [details[record["runId"]]["signature"] for record in case_valid]
        stable = (
            len(case_valid) == len(PILOT_SEEDS)
            and bool(signatures)
            and all(signature == signatures[0] for signature in signatures[1:])
        )
        stability_ok = stability_ok and stable
        case_tp = sum(record["exactRole"]["tp"] for record in case_valid)
        case_fp = sum(record["exactRole"]["fp"] for record in case_valid)
        case_fn = sum(record["exactRole"]["fn"] for record in case_valid)
        by_case.append({
            "caseId": case_id,
            "plannedRuns": len(PILOT_SEEDS),
            "validRuns": len(case_valid),
            "stableAcrossSeeds": stable,
            "exactRole": {"tp": case_tp, "fp": case_fp, "fn": case_fn, "f1": f1_from_counts(case_tp, case_fp, case_fn)},
        })
    complete = len(valid) == len(plan["matrix"])
    evidence_safe = all(
        record["contractEvidenceValidity"]["rate"] == 1.0 for record in valid
    ) and bool(valid)
    false_supported_safe = all(record["falseSupportedCount"] == 0 for record in valid) and bool(valid)
    opaque = next(item for item in by_case if item["caseId"] == "opaque-revision-comparison")
    payload: dict[str, Any] = {
        "schemaVersion": REPORT_SCHEMA,
        "stage": "measured-llm-semantic-claims-report",
        "experimentId": plan["experimentId"],
        "planArtifactHash": plan["artifactHash"],
        "records": records,
        "summary": {
            "plannedRuns": len(plan["matrix"]),
            "validRuns": len(valid),
            "missingRuns": sum(record["status"] == "missing" for record in records),
            "incompleteRuns": sum(record["status"] == "incomplete" for record in records),
            "invalidRuns": sum(record["status"] == "invalid" for record in records),
            "exactRole": {"tp": tp, "fp": fp, "fn": fn, "f1": f1_from_counts(tp, fp, fn)},
            "byCase": by_case,
            "complete": complete,
            "contractEvidenceSafe": evidence_safe,
            "falseSupportedSafe": false_supported_safe,
            "stableAcrossSeeds": stability_ok,
        },
        "pilotSignals": {
            "opaqueBeatsDeterministicBaseline": complete and opaque["exactRole"]["f1"] > BASELINE_REFERENCE["opaqueCase"]["f1"],
            "allSafetyChecksPass": complete and evidence_safe and false_supported_safe,
            "resultsStableAcrossDeclaredSeeds": complete and stability_ok,
            "automaticPromotionAllowed": False,
        },
        "interpretation": "research-only pilot; benchmark size is insufficient for production promotion",
    }
    payload["artifactHash"] = domain_hash(REPORT_DOMAIN, payload)
    return payload


def verify_report(
    benchmark_root: Path,
    plan_path: Path,
    runs_root: Path,
    report_path: Path,
) -> dict[str, Any]:
    plan = verify_plan(benchmark_root, plan_path)
    report, raw = read_object(report_path.resolve(), "experiment report")
    expected = aggregate_report(benchmark_root, plan, runs_root.resolve())
    if report != expected:
        raise SemanticClaimsExperimentError("experiment report does not reproduce planned run artifacts")
    if raw != canonical_json_bytes(report):
        raise SemanticClaimsExperimentError("experiment report is not canonical JSON bytes")
    return report


def write_new(path: Path, value: dict[str, Any], label: str) -> None:
    path = path.resolve()
    if path.exists():
        raise SemanticClaimsExperimentError(f"{label} already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def create_plan_command(args: argparse.Namespace) -> int:
    plan = build_plan(args.benchmark_root)
    write_new(args.output, plan, "experiment plan")
    print(f"Created measured pilot plan: {plan['experimentId']}")
    print(f"Planned runs: {len(plan['matrix'])}")
    print(f"Plan hash: {plan['artifactHash']}")
    return 0


def verify_plan_command(args: argparse.Namespace) -> int:
    plan = verify_plan(args.benchmark_root, args.plan)
    print(f"Verified measured pilot plan: {plan['experimentId']}")
    return 0


def commands_command(args: argparse.Namespace) -> int:
    plan = verify_plan(args.benchmark_root, args.plan)
    root = args.runs_root
    for item in plan["matrix"]:
        output = root / item["runId"]
        print(
            "python .\\tools\\semantic_claims_llm.py run "
            f"--case-id {item['caseId']} --model {plan['producer']['model']} "
            f"--seed {item['seed']} --context-tokens {plan['producer']['numCtx']} "
            f"--output-tokens {plan['producer']['numPredict']} --output {output}"
        )
    return 0


def collect_command(args: argparse.Namespace) -> int:
    plan = verify_plan(args.benchmark_root, args.plan)
    report = aggregate_report(args.benchmark_root, plan, args.runs_root.resolve())
    write_new(args.output, report, "experiment report")
    print(f"Collected pilot report: {report['experimentId']}")
    print(f"Valid runs: {report['summary']['validRuns']}/{report['summary']['plannedRuns']}")
    print(f"Report hash: {report['artifactHash']}")
    return 0


def verify_report_command(args: argparse.Namespace) -> int:
    report = verify_report(args.benchmark_root, args.plan, args.runs_root, args.report)
    print(f"Verified pilot report: {report['experimentId']}")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)

    def common(item: argparse.ArgumentParser) -> None:
        item.add_argument(
            "--benchmark-root",
            type=Path,
            default=Path("experiments/presentation/semantic-planning-v0"),
        )

    create = sub.add_parser("create-plan")
    common(create)
    create.add_argument("--output", type=Path, required=True)
    create.set_defaults(handler=create_plan_command)

    verify = sub.add_parser("verify-plan")
    common(verify)
    verify.add_argument("--plan", type=Path, required=True)
    verify.set_defaults(handler=verify_plan_command)

    commands = sub.add_parser("commands")
    common(commands)
    commands.add_argument("--plan", type=Path, required=True)
    commands.add_argument("--runs-root", type=Path, required=True)
    commands.set_defaults(handler=commands_command)

    collect = sub.add_parser("collect")
    common(collect)
    collect.add_argument("--plan", type=Path, required=True)
    collect.add_argument("--runs-root", type=Path, required=True)
    collect.add_argument("--output", type=Path, required=True)
    collect.set_defaults(handler=collect_command)

    verify_report_parser = sub.add_parser("verify-report")
    common(verify_report_parser)
    verify_report_parser.add_argument("--plan", type=Path, required=True)
    verify_report_parser.add_argument("--runs-root", type=Path, required=True)
    verify_report_parser.add_argument("--report", type=Path, required=True)
    verify_report_parser.set_defaults(handler=verify_report_command)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.handler(args)
    except SemanticClaimsExperimentError as error:
        print(f"semantic claims experiment error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())