from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from active_epoch.hashing import aggregate_hash, canonical_json_bytes, sha256

from .contract import (
    ALLOWED_UI_COMPONENTS,
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_TOTAL_BYTES,
    CandidateError,
    expected_kind,
    validate_kind,
    validate_relative_path,
)


FORBIDDEN_PROLOG_CALLS = re.compile(
    r"\b(?:"
    r"shell|process_create|consult|load_files|open|tell|told|see|seen|"
    r"working_directory|delete_file|rename_file|copy_file|make_directory|"
    r"http_open|http_get|tcp_connect|tcp_socket|udp_socket|socket|"
    r"asserta|assertz|retract|retractall|abolish|nb_setval|setenv|"
    r"call|call_cleanup|setup_call_cleanup|phrase_from_file"
    r")\s*\(",
    re.IGNORECASE,
)
DIRECTIVE_NAME = re.compile(r":-\s*([A-Za-z_][A-Za-z0-9_]*)")
USE_MODULE = re.compile(r":-\s*use_module\s*\((.*?)\)\s*\.", re.DOTALL)
ALLOWED_DIRECTIVES = frozenset({"module", "use_module", "begin_tests", "end_tests"})
OUTPUT_LIMIT_BYTES = 1_000_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build and validate a provider-neutral LogicLens epoch candidate "
            "without modifying the active epoch."
        )
    )
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--proposal", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--timeout-ms", type=int, default=10_000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.timeout_ms < 100 or args.timeout_ms > 60_000:
        raise CandidateError("timeout-ms must be between 100 and 60000")

    baseline = args.baseline.resolve()
    proposal_root = args.proposal.resolve()
    schema_path = args.schema.resolve()
    output = args.output.resolve()
    report_path = args.report.resolve()

    require_directory(baseline, "baseline package")
    require_directory(proposal_root, "candidate proposal")
    require_file(schema_path, "candidate schema")
    require_separate_paths(baseline, proposal_root, output, report_path)
    require_clean_output(output)
    require_new_report(report_path)

    baseline_files = tree_bytes(baseline)
    baseline_manifest = verify_active_baseline(baseline_files)
    proposal = load_and_validate_proposal(proposal_root, schema_path)
    verify_base_binding(proposal, baseline_manifest)
    candidate_files, kinds = collect_candidate_files(proposal_root, proposal)
    validate_candidate_files(candidate_files, kinds)

    shutil.copytree(baseline, output, dirs_exist_ok=True)
    for relative_path, content in candidate_files.items():
        destination = safe_destination(output, relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    timeout_seconds = args.timeout_ms / 1000.0
    rule_paths = [
        output / Path(*path.parts)
        for path, kind in kinds.items()
        if kind == "rule"
    ]
    test_paths = [
        output / Path(*path.parts)
        for path, kind in kinds.items()
        if kind == "test"
    ]

    run_prolog_load(args.swipl, output, rule_paths, timeout_seconds)
    run_candidate_tests(args.swipl, output, test_paths, timeout_seconds)
    smoke_outputs_equal = compare_portable_smoke(
        args.swipl,
        baseline,
        output,
        timeout_seconds,
    )
    if not smoke_outputs_equal:
        raise CandidateError("candidate changed the stable active-epoch smoke output")

    if tree_bytes(baseline) != baseline_files:
        raise CandidateError("candidate validation modified the active baseline package")

    candidate_manifest = build_candidate_manifest(
        proposal,
        baseline_manifest,
        candidate_files,
        kinds,
        output,
    )
    (output / "candidate-manifest.json").write_bytes(
        canonical_json_bytes(candidate_manifest)
    )

    report = build_comparison_report(
        proposal,
        baseline_manifest,
        candidate_manifest,
        kinds,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(canonical_json_bytes(report))

    print(f"Candidate accepted: {proposal['candidateId']}")
    print(f"Candidate hash: {candidate_manifest['candidateHash']}")
    print(f"Candidate package hash: {candidate_manifest['candidatePackageHash']}")
    print(f"Output: {output}")
    print(f"Report: {report_path}")
    return 0


def require_directory(path: Path, name: str) -> None:
    if not path.is_dir():
        raise CandidateError(f"{name} directory does not exist: {path}")


def require_file(path: Path, name: str) -> None:
    if not path.is_file():
        raise CandidateError(f"{name} file does not exist: {path}")


def paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def require_separate_paths(
    baseline: Path,
    proposal: Path,
    output: Path,
    report: Path,
) -> None:
    for source_name, source in (("baseline", baseline), ("proposal", proposal)):
        if paths_overlap(source, output):
            raise CandidateError(f"output overlaps {source_name}: {output}")
        if report == source or source in report.parents:
            raise CandidateError(f"report is inside {source_name}: {report}")
    if output == report or output in report.parents:
        raise CandidateError("report cannot be inside the candidate package")


def require_clean_output(output: Path) -> None:
    if output.exists():
        if not output.is_dir():
            raise CandidateError(f"output exists and is not a directory: {output}")
        if any(output.iterdir()):
            raise CandidateError(f"output directory must be empty: {output}")
    else:
        output.mkdir(parents=True)


def require_new_report(report: Path) -> None:
    if report.exists():
        raise CandidateError(f"comparison report already exists: {report}")


def tree_bytes(root: Path) -> dict[PurePosixPath, bytes]:
    result: dict[PurePosixPath, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise CandidateError(f"symlink is forbidden: {path}")
        if path.is_file():
            relative = PurePosixPath(path.relative_to(root).as_posix())
            result[relative] = path.read_bytes()
    return result


def verify_active_baseline(files: dict[PurePosixPath, bytes]) -> dict[str, Any]:
    manifest_path = PurePosixPath("manifest.json")
    if manifest_path not in files:
        raise CandidateError("active baseline is missing manifest.json")
    try:
        manifest = json.loads(files[manifest_path].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateError(f"active baseline manifest is invalid: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("stage") != "active":
        raise CandidateError("baseline manifest must describe an active package")

    payload = {path: content for path, content in files.items() if path != manifest_path}
    expected_hashes = {str(path): sha256(content) for path, content in payload.items()}
    if manifest.get("files") != expected_hashes:
        raise CandidateError("active baseline per-file hashes do not match its contents")
    expected_package_hash = aggregate_hash(
        b"LogicLensActiveEpoch\0",
        1,
        payload.items(),
    )
    if manifest.get("packageHash") != expected_package_hash:
        raise CandidateError("active baseline packageHash is invalid")
    return manifest


def load_json_object(path: Path, context: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateError(f"cannot read {context} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CandidateError(f"{context} must be a JSON object: {path}")
    return value


def load_and_validate_proposal(
    proposal_root: Path,
    schema_path: Path,
) -> dict[str, Any]:
    proposal_path = proposal_root / "proposal.json"
    require_file(proposal_path, "proposal")
    proposal = load_json_object(proposal_path, "proposal")
    schema = load_json_object(schema_path, "candidate schema")
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(proposal), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.path) or "<root>"
        raise CandidateError(
            f"candidate proposal schema violation at {location}: {first.message}"
        )
    return proposal


def verify_base_binding(
    proposal: dict[str, Any],
    baseline_manifest: dict[str, Any],
) -> None:
    expected = proposal["base"]
    if expected["epoch"] != baseline_manifest.get("epoch"):
        raise CandidateError("candidate epoch does not match the active baseline")
    if expected["revision"] != baseline_manifest.get("baseRevision"):
        raise CandidateError("candidate revision does not match the active baseline")
    if proposal["uiContractVersion"] != baseline_manifest.get("uiContractVersion"):
        raise CandidateError("candidate UI contract version does not match baseline")
    if proposal["cliProtocolVersion"] != baseline_manifest.get("cliProtocolVersion"):
        raise CandidateError("candidate CLI protocol version does not match baseline")


def collect_candidate_files(
    proposal_root: Path,
    proposal: dict[str, Any],
) -> tuple[dict[PurePosixPath, bytes], dict[PurePosixPath, str]]:
    declarations = proposal["files"]
    if len(declarations) > MAX_FILES:
        raise CandidateError(f"candidate exceeds {MAX_FILES} files")

    kinds: dict[PurePosixPath, str] = {}
    for declaration in declarations:
        path = validate_relative_path(declaration["path"])
        validate_kind(path, declaration["kind"])
        if path in kinds:
            raise CandidateError(f"duplicate candidate file declaration: {path}")
        kinds[path] = declaration["kind"]

    files_root = proposal_root / "files"
    require_directory(files_root, "candidate files")
    actual: dict[PurePosixPath, bytes] = {}
    total_bytes = 0
    for source in sorted(files_root.rglob("*")):
        if source.is_symlink():
            raise CandidateError(f"candidate symlink is forbidden: {source}")
        if not source.is_file():
            continue
        relative = validate_relative_path(source.relative_to(files_root).as_posix())
        content = source.read_bytes()
        if len(content) > MAX_FILE_BYTES:
            raise CandidateError(
                f"candidate file exceeds {MAX_FILE_BYTES} bytes: {relative}"
            )
        total_bytes += len(content)
        if total_bytes > MAX_TOTAL_BYTES:
            raise CandidateError(
                f"candidate files exceed {MAX_TOTAL_BYTES} total bytes"
            )
        actual[relative] = content

    declared_paths = set(kinds)
    actual_paths = set(actual)
    missing = sorted(str(path) for path in declared_paths - actual_paths)
    undeclared = sorted(str(path) for path in actual_paths - declared_paths)
    if missing:
        raise CandidateError(f"declared candidate files are missing: {missing}")
    if undeclared:
        raise CandidateError(f"candidate contains undeclared files: {undeclared}")

    if "rule" not in kinds.values():
        raise CandidateError("candidate must declare at least one rule file")
    if "test" not in kinds.values():
        raise CandidateError("candidate must declare at least one test file")

    return dict(sorted(actual.items(), key=lambda item: str(item[0]))), kinds


def validate_candidate_files(
    files: dict[PurePosixPath, bytes],
    kinds: dict[PurePosixPath, str],
) -> None:
    rule_paths = {path for path, kind in kinds.items() if kind == "rule"}
    for path, content in files.items():
        kind = kinds[path]
        expected_kind(path)
        if kind in {"rule", "test"}:
            validate_prolog_file(path, content, kind, rule_paths)
        elif kind == "ui":
            validate_ui_bindings(path, content)
        else:
            raise CandidateError(f"unsupported candidate file kind: {kind}")


def decode_text(path: PurePosixPath, content: bytes) -> str:
    if b"\x00" in content:
        raise CandidateError(f"candidate text contains NUL: {path}")
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CandidateError(f"candidate file is not UTF-8: {path}") from exc


def validate_prolog_file(
    path: PurePosixPath,
    content: bytes,
    kind: str,
    rule_paths: set[PurePosixPath],
) -> None:
    text = decode_text(path, content)
    lowered = text.lower()
    if any(marker in lowered for marker in ("http://", "https://", "file://", "\\\\")):
        raise CandidateError(f"candidate Prolog contains an external path or URL: {path}")
    if re.search(r"(?:^|[^A-Za-z0-9_])(?:[A-Za-z]:[\\/]|/(?:tmp|etc|home|var|usr)/)", text):
        raise CandidateError(f"candidate Prolog contains an absolute path: {path}")
    forbidden = FORBIDDEN_PROLOG_CALLS.search(text)
    if forbidden:
        raise CandidateError(
            f"candidate Prolog uses forbidden call {forbidden.group(0)!r}: {path}"
        )

    directives = set(DIRECTIVE_NAME.findall(text))
    unknown_directives = sorted(directives - ALLOWED_DIRECTIVES)
    if unknown_directives:
        raise CandidateError(
            f"candidate Prolog uses unreviewed directives {unknown_directives}: {path}"
        )

    if kind == "rule":
        if "module" not in directives:
            raise CandidateError(f"candidate rule must declare a module: {path}")
    else:
        if "begin_tests" not in directives or "end_tests" not in directives:
            raise CandidateError(f"candidate test must use begin_tests/end_tests: {path}")

    allowed_rule_imports = {"'../data/epoch_data.pl'", '"../data/epoch_data.pl"'}
    allowed_test_imports = {
        f"'../rules/{rule_path.name}'" for rule_path in rule_paths
    } | {
        f'"../rules/{rule_path.name}"' for rule_path in rule_paths
    }
    allowed_imports = allowed_rule_imports if kind == "rule" else allowed_test_imports
    for raw_import in USE_MODULE.findall(text):
        normalized = "".join(raw_import.split())
        if normalized not in allowed_imports:
            raise CandidateError(
                f"candidate Prolog import is not allowlisted: {raw_import!r} in {path}"
            )


def validate_ui_bindings(path: PurePosixPath, content: bytes) -> None:
    try:
        value = json.loads(decode_text(path, content))
    except json.JSONDecodeError as exc:
        raise CandidateError(f"candidate UI binding JSON is invalid: {path}: {exc}") from exc
    if not isinstance(value, dict) or set(value) != {"schemaVersion", "bindings"}:
        raise CandidateError(
            f"candidate UI binding must contain only schemaVersion and bindings: {path}"
        )
    if value["schemaVersion"] != "0.1":
        raise CandidateError(f"candidate UI binding schemaVersion must be 0.1: {path}")
    bindings = value["bindings"]
    if not isinstance(bindings, list) or not bindings:
        raise CandidateError(f"candidate UI binding list must be non-empty: {path}")

    predicates: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, dict) or set(binding) != {"predicate", "component"}:
            raise CandidateError(
                f"candidate UI binding entries require predicate and component: {path}"
            )
        predicate = binding["predicate"]
        component = binding["component"]
        if not isinstance(predicate, str) or not predicate:
            raise CandidateError(f"candidate UI predicate must be non-empty: {path}")
        if predicate in predicates:
            raise CandidateError(f"duplicate candidate UI predicate {predicate!r}: {path}")
        predicates.add(predicate)
        if component not in ALLOWED_UI_COMPONENTS:
            raise CandidateError(
                f"unknown UI component {component!r}; allowed: "
                f"{sorted(ALLOWED_UI_COMPONENTS)}"
            )


def quote_prolog_path(path: Path) -> str:
    return "'" + path.resolve().as_posix().replace("'", "''") + "'"


def run_process(
    command: list[str],
    cwd: Path,
    timeout_seconds: float,
    context: str,
    stdin_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            command,
            input=stdin_text,
            text=True,
            capture_output=True,
            cwd=cwd,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise CandidateError(f"{context} exceeded the reviewed timeout") from exc
    output_size = len(completed.stdout.encode("utf-8")) + len(
        completed.stderr.encode("utf-8")
    )
    if output_size > OUTPUT_LIMIT_BYTES:
        raise CandidateError(f"{context} exceeded the process output limit")
    if completed.returncode != 0:
        raise CandidateError(
            f"{context} failed with exit {completed.returncode}: "
            f"stdout={completed.stdout[-2000:]!r}, stderr={completed.stderr[-2000:]!r}"
        )
    return completed


def run_prolog_load(
    swipl: str,
    output: Path,
    rule_paths: list[Path],
    timeout_seconds: float,
) -> None:
    files = ",".join(quote_prolog_path(path) for path in sorted(rule_paths))
    goal = f"load_files([{files}], [silent(true)]), halt"
    run_process(
        [swipl, "-q", "-g", goal, "-t", "halt(1)"],
        output,
        timeout_seconds,
        "candidate Prolog load",
    )


def run_candidate_tests(
    swipl: str,
    output: Path,
    test_paths: list[Path],
    timeout_seconds: float,
) -> None:
    files = ",".join(quote_prolog_path(path) for path in sorted(test_paths))
    goal = f"load_files([{files}], [silent(true)]), run_tests, halt"
    run_process(
        [swipl, "-q", "-g", goal, "-t", "halt(1)"],
        output,
        timeout_seconds,
        "candidate Prolog tests",
    )


def smoke_requests(package: Path) -> list[tuple[str, str]]:
    smoke_root = package / "smoke"
    requests: list[tuple[str, str]] = []
    for path in sorted(smoke_root.glob("*.request.json")):
        requests.append((path.name, path.read_text(encoding="utf-8")))
    if not requests:
        raise CandidateError("active package has no portable smoke requests")
    return requests


def run_smoke(
    swipl: str,
    package: Path,
    request_text: str,
    timeout_seconds: float,
    context: str,
) -> bytes:
    completed = run_process(
        [swipl, "-q", "-s", str(package / "entry.pl"), "--"],
        package,
        timeout_seconds,
        context,
        stdin_text=request_text,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise CandidateError(f"{context} must return exactly one JSON line")
    try:
        response = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise CandidateError(f"{context} returned invalid JSON") from exc
    if not isinstance(response, dict) or response.get("status") != "ok":
        raise CandidateError(f"{context} returned a non-success response")
    return completed.stdout.encode("utf-8")


def compare_portable_smoke(
    swipl: str,
    baseline: Path,
    candidate: Path,
    timeout_seconds: float,
) -> bool:
    for name, request_text in smoke_requests(baseline):
        baseline_output = run_smoke(
            swipl,
            baseline,
            request_text,
            timeout_seconds,
            f"baseline smoke {name}",
        )
        candidate_output = run_smoke(
            swipl,
            candidate,
            request_text,
            timeout_seconds,
            f"candidate smoke {name}",
        )
        if baseline_output != candidate_output:
            return False
    return True


def candidate_hash(
    proposal: dict[str, Any],
    files: dict[PurePosixPath, bytes],
) -> str:
    entries: list[tuple[PurePosixPath, bytes]] = [
        (PurePosixPath("proposal.json"), canonical_json_bytes(proposal))
    ]
    entries.extend(files.items())
    return aggregate_hash(b"LogicLensEpochCandidate\0", 1, entries)


def build_candidate_manifest(
    proposal: dict[str, Any],
    baseline_manifest: dict[str, Any],
    files: dict[PurePosixPath, bytes],
    kinds: dict[PurePosixPath, str],
    output: Path,
) -> dict[str, Any]:
    candidate_digest = candidate_hash(proposal, files)
    package_files = tree_bytes(output)
    package_hash = aggregate_hash(
        b"LogicLensCandidatePackage\0",
        1,
        package_files.items(),
    )
    return {
        "schemaVersion": "0.1",
        "stage": "candidate",
        "candidateId": proposal["candidateId"],
        "taskId": proposal["taskId"],
        "baseEpoch": baseline_manifest["epoch"],
        "baseRevision": baseline_manifest["baseRevision"],
        "basePackageHash": baseline_manifest["packageHash"],
        "uiContractVersion": proposal["uiContractVersion"],
        "cliProtocolVersion": proposal["cliProtocolVersion"],
        "provider": proposal["provider"],
        "metrics": proposal.get("metrics", {}),
        "candidateHash": candidate_digest,
        "candidatePackageHash": package_hash,
        "files": {
            str(path): {
                "kind": kinds[path],
                "sha256": sha256(content),
                "bytes": len(content),
            }
            for path, content in files.items()
        },
    }


def build_comparison_report(
    proposal: dict[str, Any],
    baseline_manifest: dict[str, Any],
    candidate_manifest: dict[str, Any],
    kinds: dict[PurePosixPath, str],
) -> dict[str, Any]:
    counts = {
        kind: sum(1 for value in kinds.values() if value == kind)
        for kind in ("rule", "test", "ui")
    }
    return {
        "schemaVersion": "0.1",
        "candidateId": proposal["candidateId"],
        "taskId": proposal["taskId"],
        "provider": proposal["provider"],
        "metrics": proposal.get("metrics", {}),
        "baseline": {
            "epoch": baseline_manifest["epoch"],
            "revision": baseline_manifest["baseRevision"],
            "packageHash": baseline_manifest["packageHash"],
        },
        "candidate": {
            "candidateHash": candidate_manifest["candidateHash"],
            "candidatePackageHash": candidate_manifest["candidatePackageHash"],
            "fileCount": len(kinds),
            "ruleFiles": counts["rule"],
            "testFiles": counts["test"],
            "uiFiles": counts["ui"],
        },
        "validation": [
            {"name": "baselineIntegrity", "status": "passed"},
            {"name": "proposalSchema", "status": "passed"},
            {"name": "pathAndSizePolicy", "status": "passed"},
            {"name": "staticSafety", "status": "passed"},
            {"name": "uiVocabulary", "status": "passed"},
            {"name": "prologLoad", "status": "passed"},
            {"name": "candidateTests", "status": "passed"},
            {"name": "portableSmoke", "status": "passed"},
            {"name": "activePackageUnchanged", "status": "passed"},
        ],
        "comparison": {
            "runtimeOutputsEqual": True,
            "addedFiles": sorted(str(path) for path in kinds),
            "modifiedActiveFiles": [],
            "removedActiveFiles": [],
        },
    }


def safe_destination(root: Path, relative_path: PurePosixPath) -> Path:
    destination = (root / Path(*relative_path.parts)).resolve()
    if root != destination and root not in destination.parents:
        raise CandidateError(f"candidate path escaped output directory: {relative_path}")
    return destination


def run_entry() -> int:
    try:
        return main()
    except (
        CandidateError,
        OSError,
        ValidationError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as exc:
        print(f"Epoch candidate build failed: {exc}", file=__import__("sys").stderr)
        return 1
