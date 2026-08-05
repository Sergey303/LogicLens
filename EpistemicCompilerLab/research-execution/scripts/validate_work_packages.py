#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

PACKET_NAMES = ["TASK.md", "REQUIRED_READING.md", "INPUT_MANIFEST.json", "ALLOWED_PATHS.txt", "FORBIDDEN_PATHS.txt", "ACCEPTANCE.yaml", "HANDOFF_SCHEMA.json"]
CHECK_CLASSES = {"artifact", "scientific", "independence", "adversarial", "reproducibility"}
ROBUSTNESS = {f"ROB-00{i}" for i in range(1, 6)}
SPLITS = {"WP-201": {"WP-201A", "WP-201B"}, "WP-203": {"WP-203A", "WP-203B", "WP-203C"}, "WP-301": {"WP-301H", "WP-301R"}}
W0_PACKET_IDS = ["WP-001", "WP-002", "WP-003", "WP-004", "WP-005", "WP-006", "WP-007", "GATE-001"]
BANNED = ["approved predecessor artifacts", "issue acceptance pass", "issue stop/pivot", "required non-sealed contracts and linear package"]
REPORT_REPO_PATH = "EpistemicCompilerLab/research-execution/validation/validation-report.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def finding(items: list[dict], code: str, message: str, **details: object) -> None:
    items.append({"severity": "ERROR", "code": code, "message": message, "details": details})


def run_git(repo: Path, *args: str) -> str:
    cp = subprocess.run(["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if cp.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {cp.stderr.strip()}")
    return cp.stdout.strip()


def repo_state(repo: Path, findings: list[dict], require_clean: bool) -> dict:
    try:
        head = run_git(repo, "rev-parse", "HEAD")
        status = run_git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    except Exception as exc:
        finding(findings, "GIT_STATE", str(exc))
        return {"head": None, "dirty": None, "status_lines": []}
    lines = [line for line in status.splitlines() if line]
    if require_clean and lines:
        finding(findings, "DIRTY_TREE", "validation requires a clean checkout", status=lines)
    return {"head": head, "dirty": bool(lines), "status_lines": lines}


def merge_dict(dst: dict, src: dict, source: Path, findings: list[dict]) -> None:
    for key, value in src.items():
        if key == "nodes":
            dst.setdefault("nodes", {})
            for node_id, spec in value.items():
                if node_id in dst["nodes"]:
                    finding(findings, "DUPLICATE_INCLUDED_NODE", node_id, source=str(source))
                dst["nodes"][node_id] = spec
        elif key in dst:
            finding(findings, "DUPLICATE_INCLUDED_KEY", key, source=str(source))
        else:
            dst[key] = value


def load_work_packages(path: Path, findings: list[dict]) -> tuple[dict, list[Path]]:
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    if manifest.get("format") != "split-dag-manifest":
        return manifest, []
    includes = manifest.get("includes", [])
    if not includes or includes[0] != "work-packages/program.yaml":
        finding(findings, "INCLUDE_MANIFEST", "program registry must be first", actual=includes)
    phase_order = {f"W{i}": i for i in range(6)}
    seen = []
    for rel in includes[1:]:
        match = re.fullmatch(r"work-packages/fragments/(W[0-5])-\d{2}\.yaml", rel)
        if not match:
            finding(findings, "INCLUDE_MANIFEST", "invalid fragment path", path=rel)
            continue
        seen.append(phase_order[match.group(1)])
    if seen != sorted(seen):
        finding(findings, "INCLUDE_MANIFEST", "phase fragments are out of order", actual=includes)
    data = {"schema_version": manifest.get("schema_version")}
    included: list[Path] = []
    for rel in includes:
        file = path.parent / rel
        if not file.is_file():
            finding(findings, "INCLUDE_MISSING", rel)
            continue
        included.append(file)
        merge_dict(data, yaml.safe_load(file.read_text(encoding="utf-8")) or {}, file, findings)
    return data, included


def flatten(value: object) -> str:
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, list):
        return " ".join(flatten(x) for x in value)
    if isinstance(value, dict):
        return " ".join(flatten(x) for x in value.values())
    return ""


def topo(nodes: dict) -> tuple[list[str], dict[str, list[str]]]:
    indegree = {node: 0 for node in nodes}
    successors: dict[str, list[str]] = defaultdict(list)
    for node, spec in nodes.items():
        for dep in spec["dependencies"]:
            if dep in nodes:
                indegree[node] += 1
                successors[dep].append(node)
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for successor in sorted(successors[node]):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                queue.append(successor)
    return order, successors


def reaching(nodes: dict, terminal: str) -> set[str]:
    successors: dict[str, list[str]] = defaultdict(list)
    for node, spec in nodes.items():
        for dep in spec["dependencies"]:
            successors[dep].append(node)
    reached = set()
    for start in nodes:
        stack = [start]
        seen = set()
        while stack:
            node = stack.pop()
            if node == terminal:
                reached.add(start)
                break
            if node in seen:
                continue
            seen.add(node)
            stack.extend(successors[node])
    return reached


def longest(nodes: dict, order: list[str], terminal: str) -> tuple[list[str], int]:
    distance = {node: 1 for node in nodes}
    previous = {node: None for node in nodes}
    for node in order:
        for dep in nodes[node]["dependencies"]:
            if distance[dep] + 1 > distance[node]:
                distance[node] = distance[dep] + 1
                previous[node] = dep
    path = []
    cursor = terminal
    while cursor is not None:
        path.append(cursor)
        cursor = previous[cursor]
    return list(reversed(path)), distance[terminal]


def resolve_repo_path(repo: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo / path


def validate_manifest(repo: Path, manifest_path: Path, expected_id: str, findings: list[dict]) -> list[dict]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        finding(findings, "INPUT_MANIFEST_PARSE", str(exc), path=str(manifest_path))
        return []
    if manifest.get("work_package_id") != expected_id or manifest.get("hash_algorithm") != "sha256":
        finding(findings, "INPUT_MANIFEST_CONTRACT", expected_id, actual=manifest)
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        finding(findings, "INPUT_MANIFEST_EMPTY", expected_id)
        return []
    seen = set()
    for entry in entries:
        path_text = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(path_text, str) or not re.fullmatch(r"[a-f0-9]{64}", str(expected)):
            finding(findings, "INPUT_MANIFEST_ENTRY", expected_id, entry=entry)
            continue
        if path_text in seen:
            finding(findings, "INPUT_MANIFEST_DUPLICATE", expected_id, path=path_text)
        seen.add(path_text)
        path = resolve_repo_path(repo, path_text)
        if not path.is_file():
            finding(findings, "INPUT_FILE_MISSING", expected_id, path=path_text)
        elif sha256(path) != expected:
            finding(findings, "INPUT_HASH_DRIFT", expected_id, path=path_text, actual=sha256(path), expected=expected)
    return entries


def validate_command_contract(repo: Path, node_id: str, contract: dict, findings: list[dict]) -> None:
    cwd_text = contract.get("working_directory")
    argv = contract.get("argv")
    if not isinstance(cwd_text, str) or not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
        finding(findings, "COMMAND_CONTRACT", node_id, contract=contract)
        return
    cwd = resolve_repo_path(repo, cwd_text)
    if not cwd.is_dir():
        finding(findings, "COMMAND_CWD_MISSING", node_id, cwd=cwd_text)
        return
    executable = argv[0]
    if shutil.which(executable) is None:
        finding(findings, "COMMAND_EXECUTABLE_MISSING", node_id, executable=executable)
    if len(argv) > 1 and argv[1].endswith(".py"):
        script = cwd / argv[1]
        if not script.is_file():
            finding(findings, "COMMAND_SCRIPT_MISSING", node_id, script=str(script.relative_to(repo)) if script.is_relative_to(repo) else str(script))
            return
        probe = subprocess.run([sys.executable, str(script), "--help"], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if probe.returncode != 0:
            finding(findings, "COMMAND_SCRIPT_UNLOADABLE", node_id, script=str(script), stderr=probe.stderr[-1000:])


def validate_packet(repo: Path, node_id: str, node: dict, findings: list[dict]) -> dict:
    packet_dir = resolve_repo_path(repo, node["context_packet"]["directory"])
    declared = [resolve_repo_path(repo, path) for path in node["context_packet"]["files"]]
    if [path.name for path in declared] != PACKET_NAMES:
        finding(findings, "PACKET_DECLARATION", node_id, actual=[p.name for p in declared])
    if packet_dir != declared[0].parent:
        finding(findings, "PACKET_DIRECTORY_DRIFT", node_id)
    hashes = {}
    for expected_name, path in zip(PACKET_NAMES, declared):
        if path.name != expected_name or not path.is_file():
            finding(findings, "PACKET_FILE_MISSING", node_id, path=str(path))
        else:
            hashes[str(path.relative_to(repo)).replace("\\", "/")] = sha256(path)
    if len(hashes) != len(PACKET_NAMES):
        return {"work_package_id": node_id, "files": hashes}
    validate_manifest(repo, packet_dir / "INPUT_MANIFEST.json", node_id, findings)
    allowed = [line.strip() for line in (packet_dir / "ALLOWED_PATHS.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    forbidden = [line.strip() for line in (packet_dir / "FORBIDDEN_PATHS.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    if not allowed or not forbidden:
        finding(findings, "PATH_POLICY_EMPTY", node_id)
    overlap = sorted(set(allowed) & set(forbidden))
    if overlap:
        finding(findings, "PATH_POLICY_OVERLAP", node_id, overlap=overlap)
    try:
        acceptance = yaml.safe_load((packet_dir / "ACCEPTANCE.yaml").read_text(encoding="utf-8"))
    except Exception as exc:
        finding(findings, "ACCEPTANCE_PARSE", node_id, error=str(exc))
        acceptance = {}
    if acceptance.get("work_package_id") != node_id or acceptance.get("linear_issue") != node["linear_issue"]:
        finding(findings, "ACCEPTANCE_ID_DRIFT", node_id)
    if set((acceptance.get("checks") or {}).keys()) != CHECK_CLASSES:
        finding(findings, "ACCEPTANCE_CHECK_CLASSES", node_id, actual=sorted((acceptance.get("checks") or {}).keys()))
    contracts = acceptance.get("command_contracts") or []
    if not contracts or not any(c.get("stage") == "pre_start" for c in contracts) or not any(c.get("stage") == "post_completion" for c in contracts):
        finding(findings, "COMMAND_STAGE_CONTRACT", node_id)
    for contract in contracts:
        validate_command_contract(repo, node_id, contract, findings)
    try:
        handoff_ref = json.loads((packet_dir / "HANDOFF_SCHEMA.json").read_text(encoding="utf-8"))
    except Exception as exc:
        finding(findings, "HANDOFF_REF_PARSE", node_id, error=str(exc))
        handoff_ref = {}
    schema_path = handoff_ref.get("schema_path")
    if schema_path != node["handoff"]["schema"] or handoff_ref.get("handoff_path") != node["handoff"]["path"]:
        finding(findings, "HANDOFF_REF_DRIFT", node_id)
    if isinstance(schema_path, str):
        resolved = resolve_repo_path(repo, schema_path)
        if not resolved.is_file() or handoff_ref.get("schema_sha256") != sha256(resolved):
            finding(findings, "HANDOFF_SCHEMA_HASH", node_id)
    return {"work_package_id": node_id, "files": hashes}


def validate_handoff(repo: Path, node_id: str, node: dict, schema: dict, findings: list[dict]) -> dict | None:
    path = resolve_repo_path(repo, node["handoff"]["path"])
    if not path.is_file():
        finding(findings, "HANDOFF_MISSING", node_id, path=node["handoff"]["path"])
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        finding(findings, "HANDOFF_PARSE", node_id, error=str(exc))
        return None
    for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data):
        finding(findings, "HANDOFF_SCHEMA", error.message, path="/".join(map(str, error.path)))
    if data.get("work_package_id") != node_id or data.get("linear_issue") != node["linear_issue"]:
        finding(findings, "HANDOFF_ID_DRIFT", node_id)
    if data.get("recommended_next_state") != "review" or data.get("status") != "ready_for_review":
        finding(findings, "HANDOFF_STATE", node_id, status=data.get("status"), next=data.get("recommended_next_state"))
    deviations = " ".join(data.get("protocol_deviations") or []).lower()
    if "done" not in deviations or "premature" not in deviations:
        finding(findings, "PROTOCOL_DEVIATION_MISSING", node_id)
    for rel, expected in (data.get("input_hashes") or {}).items():
        input_path = resolve_repo_path(repo, rel)
        if not input_path.is_file() or sha256(input_path) != expected:
            finding(findings, "HANDOFF_INPUT_HASH", node_id, path=rel)
    return {"path": node["handoff"]["path"], "sha256": sha256(path)}


def build_report(args: argparse.Namespace, repo: Path, git: dict) -> dict:
    findings: list[dict] = []
    required_files = [args.work_packages, args.schema, args.handoff_schema, args.linear_snapshot, args.critical_path]
    for path in required_files:
        if not path.is_file():
            finding(findings, "FILE_MISSING", str(path))
    if findings:
        return {"schema_version": "2.0.0", "status": "FAIL", "as_of": args.as_of, "findings": findings}
    data, included_files = load_work_packages(args.work_packages, findings)
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    handoff_schema = json.loads(args.handoff_schema.read_text(encoding="utf-8"))
    snapshot = json.loads(args.linear_snapshot.read_text(encoding="utf-8"))
    critical_doc = args.critical_path.read_text(encoding="utf-8")
    for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data):
        finding(findings, "SCHEMA", error.message, path="/".join(map(str, error.path)))
    try:
        Draft202012Validator.check_schema(handoff_schema)
    except Exception as exc:
        finding(findings, "HANDOFF_SCHEMA_INVALID", str(exc))
    nodes = data.get("nodes", {})
    roles = set(data.get("role_registry", []))
    graph = data.get("graph", {})
    if len(nodes) != 40:
        finding(findings, "NODE_COUNT", "expected 40", actual=len(nodes))
    issues = [spec["linear_issue"] for spec in nodes.values()]
    if len(set(issues)) != len(issues):
        finding(findings, "DUPLICATE_ISSUE", "issues must be unique")
    unknown = sorted({dep for spec in nodes.values() for dep in spec["dependencies"] if dep not in nodes})
    if unknown:
        finding(findings, "UNKNOWN_DEP", "unknown dependencies", actual=unknown)
    roots = {node for node, spec in nodes.items() if not spec["dependencies"]}
    if roots != set(graph.get("roots", [])):
        finding(findings, "ROOTS", "declared roots differ", actual=sorted(roots))
    for gate in graph.get("gates", []):
        if gate not in nodes or nodes[gate]["kind"] != "gate":
            finding(findings, "GATE_KIND", gate)
    for node, spec in nodes.items():
        if node.startswith("GATE-") != (spec["kind"] == "gate"):
            finding(findings, "KIND_ID", node)
    order, _ = topo(nodes)
    if len(order) != len(nodes):
        finding(findings, "CYCLE", "topological sort incomplete", count=len(order))
    edge_count = sum(len(spec["dependencies"]) for spec in nodes.values())
    if edge_count != 68:
        finding(findings, "EDGE_COUNT", "expected 68", actual=edge_count)
    if graph.get("submission_terminal") != "WP-406" or nodes.get("WP-406", {}).get("dependencies") != ["GATE-401"]:
        finding(findings, "SUBMISSION_TERMINAL", "GATE-401 must lead to WP-406")
    if graph.get("lifecycle_terminal") != "WP-504":
        finding(findings, "LIFECYCLE_TERMINAL", "must be WP-504")
    reachable = reaching(nodes, "WP-504")
    if len(reachable) != len(nodes):
        finding(findings, "UNREACHABLE", "nodes do not reach WP-504", missing=sorted(set(nodes) - reachable))
    issue_to_node = {spec["linear_issue"]: node for node, spec in nodes.items()}
    if set(snapshot["issues"]) != set(issue_to_node):
        finding(findings, "LINEAR_SET", "snapshot issue set differs")
    for issue, entry in snapshot["issues"].items():
        if issue not in issue_to_node:
            continue
        node = issue_to_node[issue]
        spec = nodes[node]
        deps = [issue_to_node[x] for x in entry["direct_blocked_by"] if x in issue_to_node]
        if spec["dependencies"] != deps:
            finding(findings, "LINEAR_DEP_DRIFT", node, yaml=spec["dependencies"], snapshot=deps)
        for key, snap_key in (("producer", "producer_role"), ("independent_reviewer", "reviewer_role"), ("gatekeeper", "gatekeeper_role")):
            if spec["roles"][key] != entry[snap_key]:
                finding(findings, "LINEAR_ROLE_DRIFT", node, field=key)
        deliverable_hash = hashlib.sha256(json.dumps(spec["deliverables"], ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        if deliverable_hash != entry["deliverables_sha256"]:
            finding(findings, "LINEAR_DELIVERABLE_DRIFT", node, actual=deliverable_hash, expected=entry["deliverables_sha256"])
    for node, spec in nodes.items():
        node_roles = spec["roles"]
        if any(node_roles[key] not in roles for key in ("producer", "independent_reviewer", "gatekeeper")):
            finding(findings, "UNKNOWN_ROLE", node)
        if len({node_roles["producer"], node_roles["independent_reviewer"], node_roles["gatekeeper"]}) < 3:
            finding(findings, "ROLE_COLLISION", node)
        if not all(node_roles[key] for key in ("identity_record_required", "session_separation_required", "conflict_declaration_required")):
            finding(findings, "IDENTITY", node)
        if set(spec["acceptance"]["checks"]) != CHECK_CLASSES:
            finding(findings, "CHECK_CLASSES", node)
        if not spec["acceptance"]["commands"] or not spec["deliverables"] or len(spec["actions"]) < 2:
            finding(findings, "NOT_EXECUTABLE", node)
        text = flatten({key: spec[key] for key in ("required_context", "allowed_paths", "forbidden_context", "actions", "deliverables", "acceptance", "stop_or_pivot")})
        for phrase in BANNED:
            if phrase in text:
                finding(findings, "PLACEHOLDER", node, phrase=phrase)
        if spec["handoff"]["schema"] != "EpistemicCompilerLab/research-execution/schemas/work-package-handoff.schema.json":
            finding(findings, "HANDOFF_REF", node)
        if not spec["claim_or_threat_links"]:
            finding(findings, "NO_LINK", node)
    for node, expected in SPLITS.items():
        actual = {unit["id"] for unit in nodes[node].get("execution_units", [])}
        if actual != expected:
            finding(findings, "SPLIT", node, expected=sorted(expected), actual=sorted(actual))
        for unit in nodes[node].get("execution_units", []):
            if unit["producer"] == unit["reviewer"]:
                finding(findings, "UNIT_ROLE_COLLISION", unit["id"])
    if graph.get("required_blind_sequence") != ["WP-302", "WP-303", "WP-305", "WP-306", "GATE-301"]:
        finding(findings, "W3_SEQUENCE", "wrong")
    if set(nodes["WP-306"]["dependencies"]) != {"WP-303", "WP-305"}:
        finding(findings, "UNBLIND_DEPS", "WP-306")
    if "WP-303" in nodes["WP-305"]["dependencies"] or "WP-305" in nodes["WP-303"]["dependencies"]:
        finding(findings, "BLIND_SERIAL", "runs must be parallel")
    if len({nodes[x]["roles"]["producer"] for x in ("WP-303", "WP-305", "WP-306")}) != 3:
        finding(findings, "W3_ROLES", "operators/analyst collide")
    for node in ("WP-302", "WP-303", "WP-305"):
        if "embargo" not in nodes[node]:
            finding(findings, "EMBARGO", node)
    options = set(data.get("optional_robustness_work", {}))
    if options != ROBUSTNESS:
        finding(findings, "OPTIONAL_SET", "wrong", actual=sorted(options))
    doc_options = set(re.findall(r"`(ROB-\d{3})`", critical_doc))
    if not ROBUSTNESS.issubset(doc_options):
        finding(findings, "DOC_OPTIONAL", "missing", actual=sorted(doc_options))
    for token in ("WP-406", "WP-504", "WP-305", "WP-306", "40 mandatory nodes", "68 direct dependency edges", "24 nodes / 23 edges", "Only W0"):
        if token not in critical_doc:
            finding(findings, "DOC_DRIFT", token)
    required_bases = {
        "WP-002": {"CLAIM_EVIDENCE_MATRIX.yaml", "ABSTRACT_CONTRACT.md", "PROHIBITED_CLAIMS.md"},
        "WP-003": {"RELATED_WORK_MATRIX.csv", "NOVELTY_BOUNDARY.md", "NEAREST_PRIOR_WORK.md"},
        "WP-406": {"SUBMISSION_RECEIPT.json", "OPENREVIEW_RECORD.md", "UPLOADED_HASH_AUDIT.json"},
    }
    for node, required in required_bases.items():
        actual = {Path(x).name for x in nodes[node]["deliverables"]}
        if not required.issubset(actual):
            finding(findings, "DELIVERABLES", node, missing=sorted(required - actual))
    packet_records = [validate_packet(repo, node_id, nodes[node_id], findings) for node_id in W0_PACKET_IDS]
    handoff_record = validate_handoff(repo, "WP-001", nodes["WP-001"], handoff_schema, findings)
    path, length = ([], 0)
    if len(order) == len(nodes):
        path, length = longest(nodes, order, "WP-504")
        if length != 24:
            finding(findings, "LONGEST", "expected 24", actual=length, path=path)
    if args.attest_commit and git.get("head") != args.attest_commit:
        finding(findings, "ATTEST_COMMIT_DRIFT", "HEAD differs from requested attested commit", head=git.get("head"), expected=args.attest_commit)
    errors = [item for item in findings if item["severity"] == "ERROR"]
    checks = {
        "json_schema": "PASS" if not any(x["code"] == "SCHEMA" for x in errors) else "FAIL",
        "linear_snapshot_alignment": "PASS" if not any(x["code"].startswith("LINEAR_") for x in errors) else "FAIL",
        "acyclicity": "PASS" if len(order) == len(nodes) else "FAIL",
        "roles_and_identity": "PASS" if not any(x["code"] in {"UNKNOWN_ROLE", "ROLE_COLLISION", "IDENTITY"} for x in errors) else "FAIL",
        "context_packet_existence_and_integrity": "PASS" if not any(x["code"].startswith(("PACKET_", "INPUT_", "PATH_POLICY", "ACCEPTANCE_", "COMMAND_", "HANDOFF_REF", "HANDOFF_SCHEMA_HASH")) for x in errors) else "FAIL",
        "wp001_handoff_integrity": "PASS" if not any(x["code"].startswith("HANDOFF_") or x["code"] == "PROTOCOL_DEVIATION_MISSING" for x in errors) else "FAIL",
        "deliverable_completeness": "PASS" if not any(x["code"] in {"DELIVERABLES", "LINEAR_DELIVERABLE_DRIFT"} for x in errors) else "FAIL",
        "composite_splits": "PASS" if not any(x["code"] in {"SPLIT", "UNIT_ROLE_COLLISION"} for x in errors) else "FAIL",
        "blind_w3": "PASS" if not any(x["code"] in {"W3_SEQUENCE", "UNBLIND_DEPS", "BLIND_SERIAL", "W3_ROLES", "EMBARGO"} for x in errors) else "FAIL",
        "actual_submission_and_w5": "PASS" if not any(x["code"] in {"SUBMISSION_TERMINAL", "LIFECYCLE_TERMINAL", "UNREACHABLE"} for x in errors) else "FAIL",
        "optional_document_consistency": "PASS" if not any(x["code"] in {"OPTIONAL_SET", "DOC_OPTIONAL", "DOC_DRIFT"} for x in errors) else "FAIL",
        "clean_git_attestation": "PASS" if not git.get("dirty") and not any(x["code"] in {"GIT_STATE", "DIRTY_TREE", "ATTEST_COMMIT_DRIFT"} for x in errors) else "FAIL",
    }
    return {
        "schema_version": "2.0.0",
        "status": "FAIL" if errors else "PASS",
        "as_of": args.as_of,
        "attestation": {
            "model": "clean candidate parent plus report-only child",
            "reviewed_git_commit": args.attest_commit or git.get("head"),
            "head_at_validation": git.get("head"),
            "dirty_tree_before_validation": git.get("dirty"),
            "validator_sha256": sha256(Path(__file__).resolve()),
            "report_path": REPORT_REPO_PATH,
            "report_self_excluded_from_attested_inputs": True,
            "verification_rule": "the committed report must be the only path changed by the child commit; CI regenerates this object against the parent and compares bytes",
        },
        "inputs": {
            "work_packages": {"path": str(args.work_packages.relative_to(repo)).replace("\\", "/"), "sha256": sha256(args.work_packages)},
            "schema": {"path": str(args.schema.relative_to(repo)).replace("\\", "/"), "sha256": sha256(args.schema)},
            "handoff_schema": {"path": str(args.handoff_schema.relative_to(repo)).replace("\\", "/"), "sha256": sha256(args.handoff_schema)},
            "linear_snapshot": {"path": str(args.linear_snapshot.relative_to(repo)).replace("\\", "/"), "sha256": sha256(args.linear_snapshot)},
            "critical_path": {"path": str(args.critical_path.relative_to(repo)).replace("\\", "/"), "sha256": sha256(args.critical_path)},
            "validator": {"path": str(Path(__file__).resolve().relative_to(repo)).replace("\\", "/"), "sha256": sha256(Path(__file__).resolve())},
            "included_files": [{"path": str(file.relative_to(repo)).replace("\\", "/"), "sha256": sha256(file)} for file in included_files],
            "assembled_canonical_sha256": canonical_sha(data),
            "context_packets": packet_records,
            "wp001_handoff": handoff_record,
        },
        "summary": {
            "mandatory_nodes": len(nodes),
            "direct_dependency_edges": edge_count,
            "roots": sorted(roots),
            "topological_nodes": len(order),
            "cycles": 0 if len(order) == len(nodes) else 1,
            "unknown_dependencies": len(unknown),
            "linear_issues": len(issue_to_node),
            "w0_context_packets": len(packet_records),
            "optional_robustness_packages": len(options),
            "submission_terminal": graph.get("submission_terminal"),
            "lifecycle_terminal": graph.get("lifecycle_terminal"),
            "longest_chain_nodes": length,
            "longest_chain_edges": max(0, length - 1),
            "longest_chain": path,
            "blind_sequence": graph.get("required_blind_sequence"),
        },
        "checks": checks,
        "findings": findings,
    }


def verify_committed_report(args: argparse.Namespace, repo: Path, git: dict) -> int:
    report_path = args.verify_committed_report
    if not report_path.is_file():
        print(json.dumps({"status": "FAIL", "reason": "report missing"}, indent=2))
        return 1
    committed = json.loads(report_path.read_text(encoding="utf-8"))
    parent = run_git(repo, "rev-parse", "HEAD^")
    changed = [x for x in run_git(repo, "diff", "--name-only", "HEAD^", "HEAD").splitlines() if x]
    failures = []
    if committed.get("attestation", {}).get("reviewed_git_commit") != parent:
        failures.append({"code": "REPORT_PARENT", "expected": parent, "actual": committed.get("attestation", {}).get("reviewed_git_commit")})
    if changed != [REPORT_REPO_PATH]:
        failures.append({"code": "REPORT_ONLY_DIFF", "changed": changed})
    if git.get("dirty"):
        failures.append({"code": "DIRTY_TREE", "status": git.get("status_lines")})
    regen_args = argparse.Namespace(**vars(args))
    regen_args.attest_commit = parent
    regenerated = build_report(regen_args, repo, {"head": parent, "dirty": False, "status_lines": []})
    expected = json.dumps(regenerated, ensure_ascii=False, indent=2) + "\n"
    actual = report_path.read_text(encoding="utf-8")
    if actual != expected:
        failures.append({"code": "REPORT_BYTE_DRIFT", "expected_sha256": hashlib.sha256(expected.encode()).hexdigest(), "actual_sha256": hashlib.sha256(actual.encode()).hexdigest()})
    result = {"status": "FAIL" if failures else "PASS", "head": git.get("head"), "attested_parent": parent, "changed_paths": changed, "report_sha256": sha256(report_path), "failures": failures}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent.parent
    parser.add_argument("--work-packages", type=Path, default=here / "WORK_PACKAGES.yaml")
    parser.add_argument("--schema", type=Path, default=here / "schemas/work-package.schema.json")
    parser.add_argument("--handoff-schema", type=Path, default=here / "schemas/work-package-handoff.schema.json")
    parser.add_argument("--linear-snapshot", type=Path, default=here / "validation/linear-relations-snapshot.json")
    parser.add_argument("--critical-path", type=Path, default=here / "CRITICAL_PATH.md")
    parser.add_argument("--report", type=Path, default=here / "validation/validation-report.json")
    parser.add_argument("--as-of", default="2026-08-06")
    parser.add_argument("--attest-commit")
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument("--verify-committed-report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    research = Path(__file__).resolve().parent.parent
    repo = research.parents[1]
    state_findings: list[dict] = []
    git = repo_state(repo, state_findings, args.require_clean)
    if args.verify_committed_report:
        return verify_committed_report(args, repo, git)
    report = build_report(args, repo, git)
    if state_findings:
        report.setdefault("findings", []).extend(state_findings)
        report["status"] = "FAIL"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
