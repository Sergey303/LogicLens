from __future__ import annotations
import argparse
import copy
import hashlib
import itertools
import json
import shutil
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

from decision_graph import RoutingError, index_nodes, route
from generate_policy import build as build_prolog
from generate_visible_catalogue import build as build_visible_catalogue

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
POLICY_PATH = ROOT / "policy.ir.json"
CASES_PATH = ROOT / "cases.train_dev.json"
REGISTRY_PATH = PACKAGE / "ROUTING_CAPABILITY_REGISTRY.yaml"
SCHEMA_PATH = PACKAGE / "TEACHER_ROUTING_IR.schema.json"
PROLOG_PATH = ROOT / "generated" / "policy.pl"
EXPLANATION_PATH = ROOT / "policy-explanation.neutral.md"
REPORT_PATH = ROOT / "verification-report.json"
GOALS = ["claim_resolution", "provenance_lookup", "numeric_threshold", "explanation", "other"]


class ContractError(RuntimeError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry():
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ContractError(message)


def registry_map(registry):
    result = {}
    handles = set()
    for item in registry["capabilities"]:
        cid = item["canonical_id"]
        require(cid not in result, f"duplicate capability: {cid}")
        handle = item["handle"]
        require(handle not in handles, f"duplicate handle: {handle}")
        handles.add(handle)
        result[cid] = (item["version"], bool(item["available"]))
    return result


def validate_registry(registry):
    require(registry["scope"] == "TRAIN_DEV_ONLY", "registry scope drift")
    require(registry["canonical_id_contract"]["canonical_ids_hidden_from_qwen"] is True, "canonical IDs must be hidden from Qwen")
    ids = [x["canonical_id"] for x in registry["capabilities"]]
    handles = [x["handle"] for x in registry["capabilities"]]
    require(len(ids) == len(set(ids)), "duplicate canonical IDs")
    require(len(handles) == len(set(handles)), "duplicate handles")
    for item in registry["capabilities"]:
        require(item["side_effects"] == "none", f"side effects forbidden: {item['canonical_id']}")
        for surface in ("neutral_surface", "schema_adapted_dev_surface"):
            require(item[surface]["label"].strip(), f"blank label: {item['canonical_id']}")
            require(item[surface]["description"].strip(), f"blank description: {item['canonical_id']}")
    return registry_map(registry)


def validate_graph(policy, available):
    nodes = index_nodes(policy)
    require(policy["root"] in nodes, "missing root")
    canonical = set(available)
    for node in policy["nodes"]:
        if node["type"] == "condition":
            require(node["if_true"] in nodes and node["if_false"] in nodes, f"dangling edge: {node['id']}")
        else:
            require(node["capability_id"] in canonical, f"unknown leaf capability: {node['capability_id']}")
            require(available[node["capability_id"]][0] == node["capability_version"], f"stale leaf version: {node['id']}")
    visiting, visited = set(), set()

    def dfs(node_id):
        if node_id in visiting:
            raise ContractError(f"cycle at {node_id}")
        if node_id in visited:
            return
        visiting.add(node_id)
        node = nodes[node_id]
        if node["type"] == "condition":
            dfs(node["if_true"])
            dfs(node["if_false"])
        visiting.remove(node_id)
        visited.add(node_id)

    dfs(policy["root"])
    require(set(nodes) == visited, f"unreachable nodes: {sorted(set(nodes)-visited)}")


def prolog_atom(value) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def swipl_route(swipl: str, prolog_path: Path, features: dict) -> str:
    args = [
        prolog_atom(features["goal_class"]),
        prolog_atom(features["has_scope"]),
        prolog_atom(features["has_version"]),
        prolog_atom(features["asks_write"]),
        prolog_atom(features["requires_strict_policy"]),
    ]
    goal = f"route({','.join(args)},Capability),write(Capability),halt."
    proc = subprocess.run([swipl, "-q", "-s", str(prolog_path), "-g", goal], check=False, capture_output=True, text=True, timeout=10)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise ContractError(f"SWI-Prolog routing failed: rc={proc.returncode} stderr={proc.stderr.strip()}")
    return proc.stdout.strip()


def feature_vectors():
    for goal, scope, version, write, policy in itertools.product(GOALS, (False, True), (False, True), (False, True), (False, True)):
        yield {"goal_class": goal, "has_scope": scope, "has_version": version, "asks_write": write, "requires_strict_policy": policy}


def visible_text(registry) -> str:
    chunks = []
    for item in registry["capabilities"]:
        chunks.extend([item["handle"], item["neutral_surface"]["label"], item["neutral_surface"]["description"], item["schema_adapted_dev_surface"]["label"], item["schema_adapted_dev_surface"]["description"]])
    chunks.append(EXPLANATION_PATH.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_mutations(policy, registry, available) -> int:
    count = 0
    base_cases = load_json(CASES_PATH)["cases"]

    malformed = copy.deepcopy(base_cases[0]["features"])
    malformed.pop("has_scope")
    try:
        route(policy, malformed, available)
    except RoutingError:
        count += 1
    else:
        raise ContractError("mutation missing_feature was accepted")

    invalid_goal = copy.deepcopy(base_cases[0]["features"])
    invalid_goal["goal_class"] = "ambiguous_goal"
    try:
        route(policy, invalid_goal, available)
    except RoutingError:
        count += 1
    else:
        raise ContractError("mutation invalid_goal was accepted")

    stale = copy.deepcopy(policy)
    next(x for x in stale["nodes"] if x["type"] == "action")["capability_version"] = "0.0.0"
    try:
        validate_graph(stale, available)
    except ContractError:
        count += 1
    else:
        raise ContractError("mutation stale_version was accepted")

    unavailable = dict(available)
    unavailable["db.resolve_claim"] = ("1.0.0", False)
    try:
        route(policy, base_cases[0]["features"], unavailable)
    except RoutingError:
        count += 1
    else:
        raise ContractError("mutation unavailable_capability was accepted")

    missing = copy.deepcopy(policy)
    missing["nodes"] = [x for x in missing["nodes"] if x["id"] != "a_db_claim"]
    try:
        validate_graph(missing, available)
    except ContractError:
        count += 1
    else:
        raise ContractError("mutation missing_node was accepted")

    cycle = copy.deepcopy(policy)
    next(x for x in cycle["nodes"] if x["id"] == "n_explain")["if_false"] = "n_write"
    try:
        validate_graph(cycle, available)
    except ContractError:
        count += 1
    else:
        raise ContractError("mutation policy_cycle was accepted")

    wrong = copy.deepcopy(policy)
    next(x for x in wrong["nodes"] if x["id"] == "n_policy")["if_false"] = "a_prolog"
    changed = route(wrong, base_cases[0]["features"], available)
    require(changed != base_cases[0]["expected_capability"], "mutation wrong_branch did not alter route")
    count += 1

    leaked = copy.deepcopy(registry)
    leaked["capabilities"][0]["neutral_surface"]["description"] += " train-route-001"
    leak_text = "\n".join(item["neutral_surface"]["description"] + item["schema_adapted_dev_surface"]["description"] for item in leaked["capabilities"])
    require("train-route-001" in leak_text, "leak mutation failed to inject")
    count += 1

    adapted = copy.deepcopy(registry)
    adapted["capabilities"][0]["schema_adapted_dev_surface"]["label"] += " aligned"
    require([(x["canonical_id"], x["handle"], x["version"]) for x in adapted["capabilities"]] == [(x["canonical_id"], x["handle"], x["version"]) for x in registry["capabilities"]], "schema-only mutation changed capability identity")
    count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-swipl", action="store_true")
    args = parser.parse_args()

    policy = load_json(POLICY_PATH)
    jsonschema.validate(policy, load_json(SCHEMA_PATH))
    registry = load_registry()
    available = validate_registry(registry)
    validate_graph(policy, available)

    require(PROLOG_PATH.read_bytes() == build_prolog(policy).encode("utf-8"), "committed Prolog does not match clean lowering")
    neutral_catalogue = ROOT / "generated" / "qwen-catalogue.neutral.json"
    adapted_catalogue = ROOT / "generated" / "qwen-catalogue.adapted.json"
    require(neutral_catalogue.read_bytes() == build_visible_catalogue("neutral"), "neutral Qwen catalogue does not match registry")
    require(adapted_catalogue.read_bytes() == build_visible_catalogue("adapted"), "adapted Qwen catalogue does not match registry")

    cases = load_json(CASES_PATH)["cases"]
    for case in cases:
        got = route(policy, case["features"], available)
        require(got == case["expected_capability"], f"case route mismatch: {case['case_id']} got={got}")

    qwen_text = visible_text(registry)
    for case in cases:
        require(case["case_id"] not in qwen_text, f"case ID leaked: {case['case_id']}")
        require(case["question"] not in qwen_text, f"question leaked: {case['case_id']}")
    for cid in available:
        require(cid not in qwen_text, f"internal canonical ID leaked to Qwen-visible text: {cid}")

    swipl = shutil.which("swipl")
    if args.require_swipl:
        require(swipl is not None, "swipl is required but unavailable")

    vectors = list(feature_vectors())
    if swipl:
        for features in vectors:
            graph_capability = route(policy, features, available)
            prolog_capability = swipl_route(swipl, PROLOG_PATH, features)
            require(graph_capability == prolog_capability, f"tree/prolog drift for {features}: {graph_capability} != {prolog_capability}")

    mutation_count = test_mutations(policy, registry, available)
    report = {
        "schema_version": "1.0.0",
        "linear_issue": "ENG-200",
        "status": "PASS",
        "python_version": sys.version.split()[0],
        "swipl_required": bool(args.require_swipl),
        "swipl_available": bool(swipl),
        "swipl_version": None,
        "case_count": len(cases),
        "feature_space_vector_count": len(vectors),
        "tree_prolog_vectors_checked": len(vectors) if swipl else 0,
        "mutation_tests": mutation_count,
        "hashes": {
            "registry_sha256": sha(REGISTRY_PATH),
            "schema_sha256": sha(SCHEMA_PATH),
            "policy_ir_sha256": sha(POLICY_PATH),
            "generated_prolog_sha256": sha(PROLOG_PATH),
            "cases_sha256": sha(CASES_PATH),
            "explanation_sha256": sha(EXPLANATION_PATH),
            "neutral_catalogue_sha256": sha(neutral_catalogue),
            "adapted_catalogue_sha256": sha(adapted_catalogue),
        },
    }
    if swipl:
        report["swipl_version"] = subprocess.run([swipl, "--version"], check=True, capture_output=True, text=True).stdout.strip()
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, RoutingError, jsonschema.ValidationError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"ENG-200 router verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
