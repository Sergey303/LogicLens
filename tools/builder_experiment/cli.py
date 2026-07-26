from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from active_epoch.hashing import aggregate_hash, canonical_json_bytes, sha256
from builder_candidate.cli import tree_bytes, verify_active_baseline


UTF8 = "utf-8"
WORKSPACE_VERSION = "0.1"
RUN_VERSION = "0.1"
MAX_PROCESS_OUTPUT_BYTES = 1_000_000
MAX_RAW_OUTPUT_BYTES = 10 * 1024 * 1024
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PROLOG_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
SENSITIVE_KEY = re.compile(
    r"(?:token|secret|password|authorization|api[_-]?key|credential)",
    re.IGNORECASE,
)
WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


class ExperimentError(RuntimeError):
    """Raised when a Builder experiment artifact violates its contract."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare frozen Builder workspaces, import validated provider runs, "
            "and compare runs without provider-specific privileges."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="prepare a provider workspace")
    prepare.add_argument("--baseline", required=True, type=Path)
    prepare.add_argument("--task", required=True, type=Path)
    prepare.add_argument("--task-schema", required=True, type=Path)
    prepare.add_argument("--candidate-schema", required=True, type=Path)
    prepare.add_argument("--output", required=True, type=Path)
    prepare.add_argument("--swipl", default="swipl")
    prepare.add_argument("--timeout-ms", type=int, default=10_000)

    import_run = subparsers.add_parser(
        "import-run",
        help="validate one provider proposal and create a run artifact",
    )
    import_run.add_argument("--baseline", required=True, type=Path)
    import_run.add_argument("--task", required=True, type=Path)
    import_run.add_argument("--task-schema", required=True, type=Path)
    import_run.add_argument("--candidate-schema", required=True, type=Path)
    import_run.add_argument("--run-schema", required=True, type=Path)
    import_run.add_argument("--workspace", required=True, type=Path)
    import_run.add_argument("--proposal", required=True, type=Path)
    import_run.add_argument("--output", required=True, type=Path)
    import_run.add_argument("--run-id", required=True)
    import_run.add_argument("--raw-output", type=Path)
    import_run.add_argument("--swipl", default="swipl")
    import_run.add_argument("--timeout-ms", type=int, default=10_000)

    compare = subparsers.add_parser("compare", help="compare two or more run artifacts")
    compare.add_argument("--run", required=True, action="append", type=Path)
    compare.add_argument("--run-schema", required=True, type=Path)
    compare.add_argument("--output", required=True, type=Path)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "prepare":
        prepare_workspace(args)
    elif args.command == "import-run":
        import_run(args)
    elif args.command == "compare":
        compare_runs(args)
    else:
        raise ExperimentError(f"unsupported command: {args.command}")
    return 0


def prepare_workspace(args: argparse.Namespace) -> None:
    timeout_seconds = validate_timeout(args.timeout_ms)
    baseline = args.baseline.resolve()
    task_root = args.task.resolve()
    task_schema_path = args.task_schema.resolve()
    candidate_schema_path = args.candidate_schema.resolve()
    output = args.output.resolve()

    require_directory(baseline, "baseline")
    require_directory(task_root, "task")
    require_file(task_schema_path, "task schema")
    require_file(candidate_schema_path, "candidate schema")
    require_disjoint_output(output, (baseline, task_root))
    require_clean_directory(output)

    baseline_files = tree_bytes(baseline)
    baseline_manifest = verify_active_baseline(baseline_files)
    task, prompt, oracle = load_task(task_root, task_schema_path)
    verify_task_binding(task, baseline_manifest)

    task_hash = hash_task(task, prompt)
    oracle_hash = hash_oracle(oracle)
    files: dict[PurePosixPath, bytes] = {
        PurePosixPath("task.json"): canonical_json_bytes(task),
        PurePosixPath("prompt.md"): prompt,
        PurePosixPath("contracts/epoch-candidate-v0.schema.json"): canonical_json_bytes(
            read_json_object(candidate_schema_path, "candidate schema")
        ),
    }

    for index, request_template in enumerate(task["evidenceRequests"], start=1):
        request = {
            "protocolVersion": task["contracts"]["cli"],
            "requestId": f"builder:{task['taskId']}:{index:02d}",
            "command": request_template["command"],
            "epoch": task["base"]["epoch"],
            "revision": task["base"]["revision"],
            "options": request_template["options"],
        }
        response = run_active_cli(
            args.swipl,
            baseline,
            request,
            timeout_seconds,
            f"evidence request {request_template['name']}",
        )
        evidence = {"request": request, "response": response}
        filename = f"{index:02d}-{request_template['name']}.json"
        files[PurePosixPath("evidence") / filename] = canonical_json_bytes(evidence)

    for relative_path, content in files.items():
        destination = safe_destination(output, relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    manifest = {
        "schemaVersion": WORKSPACE_VERSION,
        "stage": "builder-workspace",
        "taskId": task["taskId"],
        "taskHash": task_hash,
        "oracleHash": oracle_hash,
        "base": {
            "epoch": baseline_manifest["epoch"],
            "revision": baseline_manifest["baseRevision"],
            "packageHash": baseline_manifest["packageHash"],
        },
        "contracts": task["contracts"],
        "files": {str(path): sha256(content) for path, content in files.items()},
    }
    assert_portable_json(manifest, "workspace manifest")
    (output / "workspace-manifest.json").write_bytes(canonical_json_bytes(manifest))

    if tree_bytes(baseline) != baseline_files:
        raise ExperimentError("workspace preparation modified the active baseline")

    print(f"Prepared Builder workspace: {task['taskId']}")
    print(f"Task hash: {task_hash}")
    print(f"Oracle hash: {oracle_hash}")
    print(f"Evidence files: {len(task['evidenceRequests'])}")
    print(f"Output: {output}")


def import_run(args: argparse.Namespace) -> None:
    timeout_seconds = validate_timeout(args.timeout_ms)
    baseline = args.baseline.resolve()
    task_root = args.task.resolve()
    task_schema_path = args.task_schema.resolve()
    candidate_schema_path = args.candidate_schema.resolve()
    run_schema_path = args.run_schema.resolve()
    workspace = args.workspace.resolve()
    proposal = args.proposal.resolve()
    output = args.output.resolve()
    raw_output = args.raw_output.resolve() if args.raw_output is not None else None

    require_identifier(args.run_id, "run ID")
    for path, name in (
        (baseline, "baseline"),
        (task_root, "task"),
        (workspace, "workspace"),
        (proposal, "proposal"),
    ):
        require_directory(path, name)
    for path, name in (
        (task_schema_path, "task schema"),
        (candidate_schema_path, "candidate schema"),
        (run_schema_path, "run schema"),
    ):
        require_file(path, name)
    if raw_output is not None:
        require_file(raw_output, "raw provider output")
        if raw_output.stat().st_size > MAX_RAW_OUTPUT_BYTES:
            raise ExperimentError(
                f"raw provider output exceeds {MAX_RAW_OUTPUT_BYTES} bytes"
            )

    require_disjoint_output(output, (baseline, task_root, workspace, proposal))
    require_clean_directory(output)

    baseline_files = tree_bytes(baseline)
    baseline_manifest = verify_active_baseline(baseline_files)
    task, prompt, oracle = load_task(task_root, task_schema_path)
    verify_task_binding(task, baseline_manifest)
    task_hash = hash_task(task, prompt)
    oracle_hash = hash_oracle(oracle)
    verify_workspace(
        workspace,
        task,
        task_hash,
        oracle_hash,
        baseline_manifest,
    )

    proposal_value = read_json_object(proposal / "proposal.json", "proposal")
    verify_proposal_for_task(proposal, proposal_value, task, args.run_id)

    proposal_target = output / "proposal"
    copy_tree_without_symlinks(proposal, proposal_target)
    candidate_output = output / "candidate"
    comparison_path = output / "comparison.json"

    run_candidate_builder(
        baseline,
        proposal_target,
        candidate_schema_path,
        candidate_output,
        comparison_path,
        args.swipl,
        args.timeout_ms,
    )
    candidate_manifest = read_json_object(
        candidate_output / "candidate-manifest.json",
        "candidate manifest",
    )
    comparison = read_json_object(comparison_path, "candidate comparison report")
    verify_candidate_matches_task(candidate_output, task)
    run_oracle(
        args.swipl,
        candidate_output,
        task,
        oracle,
        timeout_seconds,
    )

    raw_descriptor: dict[str, Any] | None = None
    if raw_output is not None:
        raw_target = output / "raw" / "provider-output.txt"
        raw_target.parent.mkdir(parents=True, exist_ok=True)
        content = raw_output.read_bytes()
        raw_target.write_bytes(content)
        raw_descriptor = {
            "path": "raw/provider-output.txt",
            "sha256": sha256(content),
            "bytes": len(content),
        }

    proposal_hash = aggregate_hash(
        b"LogicLensBuilderProposal\0",
        1,
        tree_bytes(proposal_target).items(),
    )
    comparison_bytes = canonical_json_bytes(comparison)
    comparison_path.write_bytes(comparison_bytes)

    metrics_source = proposal_value.get("metrics", {})
    metrics = {
        "cliCalls": metrics_source.get("cliCalls"),
        "manualFixes": metrics_source.get("manualFixes"),
        "elapsedMs": metrics_source.get("elapsedMs"),
        "costUsd": metrics_source.get("costUsd"),
    }
    run = {
        "schemaVersion": RUN_VERSION,
        "runId": args.run_id,
        "taskId": task["taskId"],
        "taskHash": task_hash,
        "oracleHash": oracle_hash,
        "basePackageHash": baseline_manifest["packageHash"],
        "provider": {
            "kind": proposal_value["provider"]["kind"],
            "name": proposal_value["provider"]["name"],
            "model": proposal_value["provider"]["model"],
        },
        "metrics": metrics,
        "rawOutput": raw_descriptor,
        "proposalHash": proposal_hash,
        "candidateHash": candidate_manifest["candidateHash"],
        "candidatePackageHash": candidate_manifest["candidatePackageHash"],
        "comparisonReportHash": sha256(comparison_bytes),
        "validation": {
            "candidate": "passed",
            "oracle": "passed",
        },
    }
    validate_json(run, run_schema_path, "run envelope")
    assert_portable_json(run, "run envelope")
    (output / "run.json").write_bytes(canonical_json_bytes(run))

    if tree_bytes(baseline) != baseline_files:
        raise ExperimentError("run import modified the active baseline")

    print(f"Imported Builder run: {args.run_id}")
    print(f"Provider: {run['provider']['kind']} / {run['provider']['model']}")
    print(f"Candidate hash: {run['candidateHash']}")
    print("Hidden oracle: passed")
    print(f"Output: {output}")


def compare_runs(args: argparse.Namespace) -> None:
    run_schema_path = args.run_schema.resolve()
    output = args.output.resolve()
    require_file(run_schema_path, "run schema")
    if output.exists():
        raise ExperimentError(f"comparison output already exists: {output}")
    if len(args.run) < 2:
        raise ExperimentError("at least two run artifacts are required")

    entries: list[dict[str, Any]] = []
    for run_path_value in args.run:
        run_root = run_path_value.resolve()
        require_directory(run_root, "run artifact")
        run = read_json_object(run_root / "run.json", "run envelope")
        validate_json(run, run_schema_path, "run envelope")
        assert_portable_json(run, "run envelope")
        comparison_path = run_root / "comparison.json"
        comparison_bytes = comparison_path.read_bytes()
        if sha256(comparison_bytes) != run["comparisonReportHash"]:
            raise ExperimentError(
                f"comparison report hash mismatch for run {run['runId']}"
            )
        comparison = read_json_object(comparison_path, "comparison report")
        if comparison.get("candidateId") != run.get("candidateHash") and comparison.get(
            "candidate", {}
        ).get("candidateHash") != run.get("candidateHash"):
            # ENG-46 reports identify the proposal by candidateId and separately
            # carry candidateHash. Require the latter when available.
            candidate_hash = comparison.get("candidate", {}).get("candidateHash")
            if candidate_hash is not None and candidate_hash != run["candidateHash"]:
                raise ExperimentError(
                    f"candidate hash mismatch for run {run['runId']}"
                )
        entries.append({"run": run, "comparison": comparison})

    ensure_comparable(entries)
    run_ids = [entry["run"]["runId"] for entry in entries]
    if len(set(run_ids)) != len(run_ids):
        raise ExperimentError("run IDs must be unique")

    sorted_entries = sorted(entries, key=lambda entry: entry["run"]["runId"])
    recommendation, reason = recommend(sorted_entries)
    report = {
        "schemaVersion": "0.1",
        "taskId": sorted_entries[0]["run"]["taskId"],
        "taskHash": sorted_entries[0]["run"]["taskHash"],
        "oracleHash": sorted_entries[0]["run"]["oracleHash"],
        "basePackageHash": sorted_entries[0]["run"]["basePackageHash"],
        "runs": [comparison_entry(entry) for entry in sorted_entries],
        "recommendedRunId": recommendation,
        "recommendationReason": reason,
    }
    assert_portable_json(report, "run comparison")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(report))

    print(f"Compared Builder runs: {len(sorted_entries)}")
    print(f"Recommendation: {recommendation or 'none'}")
    print(f"Reason: {reason}")
    print(f"Output: {output}")


def validate_timeout(timeout_ms: int) -> float:
    if timeout_ms < 100 or timeout_ms > 60_000:
        raise ExperimentError("timeout-ms must be between 100 and 60000")
    return timeout_ms / 1000.0


def load_task(
    task_root: Path,
    schema_path: Path,
) -> tuple[dict[str, Any], bytes, dict[str, Any]]:
    task_path = task_root / "task.json"
    prompt_path = task_root / "prompt.md"
    oracle_path = task_root / "oracle.json"
    for path, name in (
        (task_path, "task.json"),
        (prompt_path, "prompt.md"),
        (oracle_path, "oracle.json"),
    ):
        require_file(path, name)

    task = read_json_object(task_path, "task")
    validate_json(task, schema_path, "task")
    prompt = normalize_text(prompt_path.read_bytes(), "prompt")
    oracle = read_json_object(oracle_path, "oracle")
    validate_oracle(oracle, task)
    return task, prompt, oracle


def validate_oracle(oracle: dict[str, Any], task: dict[str, Any]) -> None:
    if set(oracle) != {
        "schemaVersion",
        "taskId",
        "module",
        "predicate",
        "expected",
    }:
        raise ExperimentError("oracle contains unknown or missing fields")
    if oracle["schemaVersion"] != "0.1" or oracle["taskId"] != task["taskId"]:
        raise ExperimentError("oracle identity does not match task")
    candidate = task["candidate"]
    if oracle["module"] != candidate["module"]:
        raise ExperimentError("oracle module does not match task")
    if oracle["predicate"] != candidate["predicate"]:
        raise ExperimentError("oracle predicate does not match task")
    if not isinstance(oracle["expected"], list) or not oracle["expected"]:
        raise ExperimentError("oracle expected result set must be non-empty")

    seen_people: set[str] = set()
    for entry in oracle["expected"]:
        if not isinstance(entry, dict) or set(entry) != {"person", "evidenceFactIds"}:
            raise ExperimentError("oracle result entries are invalid")
        person = entry["person"]
        evidence = entry["evidenceFactIds"]
        if not isinstance(person, str) or not person or person in seen_people:
            raise ExperimentError("oracle person identifiers must be unique strings")
        seen_people.add(person)
        if (
            not isinstance(evidence, list)
            or not evidence
            or evidence != sorted(evidence)
            or len(set(evidence)) != len(evidence)
            or not all(
                isinstance(fact_id, str) and fact_id.startswith("f:sha256:")
                for fact_id in evidence
            )
        ):
            raise ExperimentError("oracle evidence FactIds must be unique and sorted")


def verify_task_binding(task: dict[str, Any], manifest: dict[str, Any]) -> None:
    if task["base"]["epoch"] != manifest.get("epoch"):
        raise ExperimentError("task epoch does not match active package")
    if task["base"]["revision"] != manifest.get("baseRevision"):
        raise ExperimentError("task revision does not match active package")
    contracts = task["contracts"]
    if contracts["candidate"] != "0.1":
        raise ExperimentError("unsupported candidate contract version")
    if contracts["cli"] != manifest.get("cliProtocolVersion"):
        raise ExperimentError("task CLI contract does not match active package")
    if contracts["ui"] != manifest.get("uiContractVersion"):
        raise ExperimentError("task UI contract does not match active package")


def hash_task(task: dict[str, Any], prompt: bytes) -> str:
    return aggregate_hash(
        b"LogicLensBuilderTask\0",
        1,
        (
            (PurePosixPath("task.json"), canonical_json_bytes(task)),
            (PurePosixPath("prompt.md"), prompt),
        ),
    )


def hash_oracle(oracle: dict[str, Any]) -> str:
    return aggregate_hash(
        b"LogicLensBuilderOracle\0",
        1,
        ((PurePosixPath("oracle.json"), canonical_json_bytes(oracle)),),
    )


def run_active_cli(
    swipl: str,
    baseline: Path,
    request: dict[str, Any],
    timeout_seconds: float,
    context: str,
) -> dict[str, Any]:
    request_text = json.dumps(request, ensure_ascii=False, separators=(",", ":"))
    completed = run_process(
        [swipl, "-q", "-s", str(baseline / "entry.pl"), "--"],
        baseline,
        timeout_seconds,
        context,
        request_text,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise ExperimentError(f"{context} returned {len(lines)} JSON lines")
    try:
        response = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise ExperimentError(f"{context} returned invalid JSON") from exc
    if not isinstance(response, dict) or response.get("status") != "ok":
        raise ExperimentError(f"{context} did not return status=ok")
    if response.get("requestId") != request["requestId"]:
        raise ExperimentError(f"{context} correlation ID mismatch")
    return response


def verify_workspace(
    workspace: Path,
    task: dict[str, Any],
    task_hash: str,
    oracle_hash: str,
    baseline_manifest: dict[str, Any],
) -> None:
    manifest = read_json_object(
        workspace / "workspace-manifest.json",
        "workspace manifest",
    )
    if manifest.get("schemaVersion") != WORKSPACE_VERSION:
        raise ExperimentError("workspace schema version is unsupported")
    if manifest.get("stage") != "builder-workspace":
        raise ExperimentError("workspace stage is invalid")
    if manifest.get("taskId") != task["taskId"]:
        raise ExperimentError("workspace task ID mismatch")
    if manifest.get("taskHash") != task_hash:
        raise ExperimentError("workspace task hash mismatch")
    if manifest.get("oracleHash") != oracle_hash:
        raise ExperimentError("workspace oracle hash mismatch")
    expected_base = {
        "epoch": baseline_manifest["epoch"],
        "revision": baseline_manifest["baseRevision"],
        "packageHash": baseline_manifest["packageHash"],
    }
    if manifest.get("base") != expected_base:
        raise ExperimentError("workspace base package binding mismatch")
    if manifest.get("contracts") != task["contracts"]:
        raise ExperimentError("workspace contract versions mismatch")

    files = tree_bytes(workspace)
    files.pop(PurePosixPath("workspace-manifest.json"), None)
    expected_hashes = {str(path): sha256(content) for path, content in files.items()}
    if manifest.get("files") != expected_hashes:
        raise ExperimentError("workspace file hashes do not match its contents")
    if PurePosixPath("oracle.json") in files:
        raise ExperimentError("trusted oracle leaked into provider workspace")


def verify_proposal_for_task(
    proposal_root: Path,
    proposal: dict[str, Any],
    task: dict[str, Any],
    run_id: str,
) -> None:
    if proposal.get("taskId") != task["taskId"]:
        raise ExperimentError("proposal task ID does not match frozen task")
    provider = proposal.get("provider")
    if not isinstance(provider, dict) or provider.get("runId") != run_id:
        raise ExperimentError("proposal provider runId does not match requested run")
    expected_paths = {
        task["candidate"]["rulePath"],
        task["candidate"]["testPath"],
        task["candidate"]["uiPath"],
    }
    declarations = proposal.get("files")
    if not isinstance(declarations, list):
        raise ExperimentError("proposal files declaration is missing")
    actual_paths = {
        item.get("path")
        for item in declarations
        if isinstance(item, dict)
    }
    if actual_paths != expected_paths or len(declarations) != len(expected_paths):
        raise ExperimentError(
            "proposal must contain exactly the three task-declared files"
        )

    actual_files = {
        path.relative_to(proposal_root / "files").as_posix()
        for path in (proposal_root / "files").rglob("*")
        if path.is_file()
    }
    if actual_files != expected_paths:
        raise ExperimentError("proposal file tree does not match task-declared files")


def run_candidate_builder(
    baseline: Path,
    proposal: Path,
    candidate_schema: Path,
    candidate_output: Path,
    comparison_path: Path,
    swipl: str,
    timeout_ms: int,
) -> None:
    script = Path(__file__).resolve().parents[1] / "build_epoch_candidate.py"
    completed = run_process(
        [
            sys.executable,
            str(script),
            "--baseline",
            str(baseline),
            "--proposal",
            str(proposal),
            "--schema",
            str(candidate_schema),
            "--output",
            str(candidate_output),
            "--report",
            str(comparison_path),
            "--swipl",
            swipl,
            "--timeout-ms",
            str(timeout_ms),
        ],
        Path(__file__).resolve().parents[2],
        max(90.0, timeout_ms / 1000.0 * 10),
        "trusted candidate validator",
    )
    if "Candidate accepted:" not in completed.stdout:
        raise ExperimentError("candidate validator did not confirm acceptance")


def verify_candidate_matches_task(candidate_output: Path, task: dict[str, Any]) -> None:
    candidate = task["candidate"]
    rule_path = candidate_output / candidate["rulePath"]
    test_path = candidate_output / candidate["testPath"]
    ui_path = candidate_output / candidate["uiPath"]
    for path, name in (
        (rule_path, "task rule"),
        (test_path, "task test"),
        (ui_path, "task UI binding"),
    ):
        require_file(path, name)

    rule_text = rule_path.read_text(encoding=UTF8)
    module_signature = (
        f":- module({candidate['module']}, [{candidate['predicate']}/"
        f"{candidate['arity']}])."
    )
    if module_signature not in " ".join(rule_text.split()):
        compact_expected = " ".join(module_signature.split())
        compact_actual = " ".join(rule_text.split())
        if compact_expected not in compact_actual:
            raise ExperimentError("candidate rule does not export the task predicate")

    ui = read_json_object(ui_path, "candidate UI binding")
    expected_ui = {
        "schemaVersion": "0.1",
        "bindings": [
            {
                "predicate": candidate["uiPredicate"],
                "component": candidate["uiComponent"],
            }
        ],
    }
    if ui != expected_ui:
        raise ExperimentError("candidate UI binding does not exactly match task")


def run_oracle(
    swipl: str,
    candidate_output: Path,
    task: dict[str, Any],
    oracle: dict[str, Any],
    timeout_seconds: float,
) -> None:
    module = task["candidate"]["module"]
    predicate = task["candidate"]["predicate"]
    if not PROLOG_NAME.fullmatch(module) or not PROLOG_NAME.fullmatch(predicate):
        raise ExperimentError("task contains an unsafe Prolog module or predicate name")

    expected_terms = []
    for item in sorted(oracle["expected"], key=lambda value: value["person"]):
        evidence = ",".join(prolog_atom(value) for value in item["evidenceFactIds"])
        expected_terms.append(
            f"{prolog_atom(item['person'])}-[{evidence}]"
        )
    expected = "[" + ",".join(expected_terms) + "]"
    goal = (
        f"findall(Person-Evidence,{module}:{predicate}(Person,Evidence),Raw),"
        f"msort(Raw,Results),Results=={expected},halt"
    )
    rule_path = candidate_output / task["candidate"]["rulePath"]
    run_process(
        [swipl, "-q", "-s", str(rule_path), "-g", goal, "-t", "halt(1)"],
        candidate_output,
        timeout_seconds,
        "trusted hidden oracle",
    )


def ensure_comparable(entries: list[dict[str, Any]]) -> None:
    first = entries[0]["run"]
    keys = ("taskId", "taskHash", "oracleHash", "basePackageHash")
    for entry in entries[1:]:
        run = entry["run"]
        for key in keys:
            if run[key] != first[key]:
                raise ExperimentError(f"runs differ in {key} and are not comparable")


def comparison_entry(entry: dict[str, Any]) -> dict[str, Any]:
    run = entry["run"]
    comparison = entry["comparison"]
    candidate = comparison.get("candidate", {})
    return {
        "runId": run["runId"],
        "provider": run["provider"],
        "metrics": run["metrics"],
        "proposalHash": run["proposalHash"],
        "candidateHash": run["candidateHash"],
        "candidatePackageHash": run["candidatePackageHash"],
        "validation": run["validation"],
        "fileCounts": {
            "total": candidate.get("fileCount"),
            "rules": candidate.get("ruleFiles"),
            "tests": candidate.get("testFiles"),
            "ui": candidate.get("uiFiles"),
        },
    }


def recommend(entries: list[dict[str, Any]]) -> tuple[str | None, str]:
    if any(entry["run"]["provider"]["kind"] == "fixture" for entry in entries):
        return None, "fixture runs verify the pipeline and are not provider recommendations"
    if len(entries) != 2:
        return None, "automatic recommendation is defined only for one Qwen/Codex pair"

    left = entries[0]["run"]
    right = entries[1]["run"]
    metric_names = ("manualFixes", "cliCalls", "elapsedMs", "costUsd")
    if any(
        left["metrics"][name] is None or right["metrics"][name] is None
        for name in metric_names
    ):
        return None, "one or more comparison metrics are missing"

    left_values = [float(left["metrics"][name]) for name in metric_names]
    right_values = [float(right["metrics"][name]) for name in metric_names]
    left_dominates = all(a <= b for a, b in zip(left_values, right_values)) and any(
        a < b for a, b in zip(left_values, right_values)
    )
    right_dominates = all(b <= a for a, b in zip(left_values, right_values)) and any(
        b < a for a, b in zip(left_values, right_values)
    )
    if left_dominates:
        return left["runId"], "run Pareto-dominates the other measured run"
    if right_dominates:
        return right["runId"], "run Pareto-dominates the other measured run"
    return None, "validated runs trade off measured metrics; human review is required"


def run_process(
    command: list[str],
    cwd: Path,
    timeout_seconds: float,
    context: str,
    stdin_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    stdin_bytes = stdin_text.encode(UTF8) if stdin_text is not None else None
    try:
        completed = subprocess.run(
            command,
            input=stdin_bytes,
            capture_output=True,
            cwd=cwd,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExperimentError(f"{context} exceeded the reviewed timeout") from exc

    stdout_bytes = completed.stdout or b""
    stderr_bytes = completed.stderr or b""
    if not isinstance(stdout_bytes, bytes) or not isinstance(stderr_bytes, bytes):
        raise ExperimentError(f"{context} returned non-binary process output")
    if len(stdout_bytes) + len(stderr_bytes) > MAX_PROCESS_OUTPUT_BYTES:
        raise ExperimentError(f"{context} exceeded the process output limit")
    try:
        stdout = stdout_bytes.decode(UTF8)
        stderr = stderr_bytes.decode(UTF8)
    except UnicodeDecodeError as exc:
        raise ExperimentError(f"{context} returned output that is not valid UTF-8") from exc

    decoded = subprocess.CompletedProcess(
        completed.args,
        completed.returncode,
        stdout,
        stderr,
    )
    if decoded.returncode != 0:
        raise ExperimentError(
            f"{context} failed with exit {decoded.returncode}: "
            f"stdout={decoded.stdout[-2000:]!r}, stderr={decoded.stderr[-2000:]!r}"
        )
    return decoded


def validate_json(value: Any, schema_path: Path, context: str) -> None:
    schema = read_json_object(schema_path, f"{context} schema")
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        error = errors[0]
        location = "/".join(str(part) for part in error.path) or "<root>"
        raise ExperimentError(
            f"{context} schema violation at {location}: {error.message}"
        )


def read_json_object(path: Path, context: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding=UTF8))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentError(f"cannot read {context} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExperimentError(f"{context} must be a JSON object: {path}")
    return value


def normalize_text(content: bytes, context: str) -> bytes:
    try:
        text = content.decode(UTF8)
    except UnicodeDecodeError as exc:
        raise ExperimentError(f"{context} must be UTF-8") from exc
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    return text.encode(UTF8)


def assert_portable_json(value: Any, context: str) -> None:
    walk_portable(value, context, ())


def walk_portable(value: Any, context: str, path: tuple[str, ...]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE_KEY.search(str(key)):
                raise ExperimentError(
                    f"{context} contains sensitive field {'/'.join((*path, str(key)))}"
                )
            walk_portable(child, context, (*path, str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_portable(child, context, (*path, str(index)))
    elif isinstance(value, str):
        if value.startswith("/") or WINDOWS_ABSOLUTE.match(value) or "\\\\" in value:
            raise ExperimentError(
                f"{context} contains an absolute or machine-specific path at "
                f"{'/'.join(path)}"
            )
    elif isinstance(value, float) and not math.isfinite(value):
        raise ExperimentError(f"{context} contains a non-finite number")


def prolog_atom(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def require_identifier(value: str, context: str) -> None:
    if not IDENTIFIER.fullmatch(value):
        raise ExperimentError(f"{context} is invalid: {value!r}")


def require_directory(path: Path, context: str) -> None:
    if not path.is_dir():
        raise ExperimentError(f"{context} directory does not exist: {path}")


def require_file(path: Path, context: str) -> None:
    if not path.is_file():
        raise ExperimentError(f"{context} file does not exist: {path}")


def paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def require_disjoint_output(output: Path, inputs: Iterable[Path]) -> None:
    for input_path in inputs:
        if paths_overlap(output, input_path):
            raise ExperimentError(f"output overlaps protected input: {input_path}")


def require_clean_directory(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise ExperimentError(f"output exists and is not a directory: {path}")
        if any(path.iterdir()):
            raise ExperimentError(f"output directory must be empty: {path}")
    else:
        path.mkdir(parents=True)


def safe_destination(root: Path, path: PurePosixPath) -> Path:
    destination = (root / Path(*path.parts)).resolve()
    if destination != root and root not in destination.parents:
        raise ExperimentError(f"path escaped output: {path}")
    return destination


def copy_tree_without_symlinks(source: Path, destination: Path) -> None:
    for path in source.rglob("*"):
        if path.is_symlink():
            raise ExperimentError(f"symlink is forbidden: {path}")
    shutil.copytree(source, destination)


def run_entry() -> int:
    try:
        return main()
    except (
        ExperimentError,
        OSError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"Builder experiment failed: {exc}", file=sys.stderr)
        return 1
