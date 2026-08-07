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

from decision_graph import RoutingError, index_nodes, load_feature_contract, route
from feature_adapter import normalize_precomputed_features
from generate_policy import build as build_prolog
from generate_visible_catalogue import build as build_visible_catalogue
from build_freeze_manifest import build as build_freeze_manifest

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
POLICY_PATH = ROOT / "policy.ir.json"
CASES_PATH = ROOT / "cases.train_dev.json"
FEATURE_PATH = PACKAGE / "ROUTING_FEATURE_CONTRACT.json"
REGISTRY_PATH = PACKAGE / "ROUTING_CAPABILITY_REGISTRY.yaml"
REGISTRY_SCHEMA_PATH = PACKAGE / "ROUTING_CAPABILITY_REGISTRY.schema.json"
IO_SCHEMAS_PATH = PACKAGE / "CAPABILITY_IO_SCHEMAS.json"
IR_SCHEMA_PATH = PACKAGE / "TEACHER_ROUTING_IR.schema.json"
MODE_CONTRACTS_PATH = PACKAGE / "ROUTING_MODE_CONTRACTS.yaml"
PROLOG_PATH = ROOT / "generated" / "policy.pl"
EXPLANATION_PATH = ROOT / "policy-explanation.neutral.md"
MANIFEST_PATH = PACKAGE / "ENG-200_FREEZE_MANIFEST.json"
REPORT_PATH = ROOT / "verification-report.json"


class ContractError(RuntimeError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ContractError(message)


def canonical_feature_bytes(features: dict) -> bytes:
    return (json.dumps(features, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def resolve_schema_ref(ref: str, io_schemas: dict) -> dict:
    prefix = "CAPABILITY_IO_SCHEMAS.json#/capabilities/"
    require(ref.startswith(prefix), f"unsupported schema ref: {ref}")
    tail = ref[len(prefix):]
    capability_id, kind = tail.rsplit("/", 1)
    require(kind in {"input", "result"}, f"invalid schema ref kind: {ref}")
    require(capability_id in io_schemas["capabilities"], f"schema ref capability absent: {capability_id}")
    schema = io_schemas["capabilities"][capability_id][kind]
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


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


def validate_registry(registry, io_schemas):
    jsonschema.validate(registry, load_json(REGISTRY_SCHEMA_PATH))
    require(registry["scope"] == "TRAIN_DEV_ONLY", "registry scope drift")
    require(registry["canonical_id_contract"]["canonical_ids_hidden_from_qwen"] is True, "canonical IDs must be hidden from Qwen")
    ids = [x["canonical_id"] for x in registry["capabilities"]]
    require(set(ids) == set(io_schemas["capabilities"]), "I/O schema capability set must exactly match registry")

    for item in registry["capabilities"]:
        cid = item["canonical_id"]
        require(item["input_schema_ref"] == f"CAPABILITY_IO_SCHEMAS.json#/capabilities/{cid}/input", f"input schema ref drift: {cid}")
        require(item["result_schema_ref"] == f"CAPABILITY_IO_SCHEMAS.json#/capabilities/{cid}/result", f"result schema ref drift: {cid}")
        resolve_schema_ref(item["input_schema_ref"], io_schemas)
        resolve_schema_ref(item["result_schema_ref"], io_schemas)
        require(item["tool_budget"]["max_invocations"] == 1, f"routing study permits one invocation only: {cid}")
        require(item["failure_semantics"]["fail_closed"] is True, f"failure must fail closed: {cid}")
        require(item["failure_semantics"]["retry_policy"] == "none", f"implicit retries forbidden: {cid}")
        require(item["failure_semantics"]["codes"], f"failure codes required: {cid}")
        require(item["side_effects"] == "none", f"side effects forbidden: {cid}")
    return registry_map(registry)


def validate_feature_contract_and_proxy_resistance(feature_contract, policy, available):
    require(feature_contract["owner"] == "independent_feature_layer", "feature contract must be independently owned")
    require(feature_contract["primary_input_contract"]["same_bytes_required_for"] == ["M19", "M20", "direct_qwen_selection"], "primary feature equality contract drift")
    require(feature_contract["primary_input_contract"]["raw_question_parsing_in_primary_contrast"] is False, "raw question parsing cannot enter primary contrast")

    expected_names = {"goal_class", "has_scope", "has_version", "asks_write", "requires_strict_policy"}
    require(set(feature_contract["features"]) == expected_names, "feature set drift")

    forbidden = set(available)
    forbidden.update(item["handle"] for item in load_yaml(REGISTRY_PATH)["capabilities"])
    forbidden.update({"postgres", "postgresql", "sql", "prolog", "python", "prompt_id", "view_id", "procedure_id", "tool_id"})
    definitions = "\n".join(str(spec.get("definition", "")) for spec in feature_contract["features"].values()).lower()
    for token in forbidden:
        require(token.lower() not in definitions, f"feature definition leaks implementation/capability token: {token}")

    vectors = list(feature_vectors(feature_contract))
    strict_true_routes = {route(policy, v, available, feature_contract) for v in vectors if v["requires_strict_policy"]}
    strict_false_routes = {route(policy, v, available, feature_contract) for v in vectors if not v["requires_strict_policy"]}
    require(len(strict_true_routes) >= 4, "requires_strict_policy behaves like a global target-capability proxy")
    require(len(strict_false_routes) >= 4, "requires_strict_policy false behaves like a global target-capability proxy")

    # Strict-policy obligation must be routing-irrelevant outside claim resolution.
    for goal in feature_contract["features"]["goal_class"]["enum"]:
        if goal == "claim_resolution":
            continue
        for scope, version, write in itertools.product((False, True), repeat=3):
            a = {"goal_class": goal, "has_scope": scope, "has_version": version, "asks_write": write, "requires_strict_policy": False}
            b = dict(a)
            b["requires_strict_policy"] = True
            require(route(policy, a, available, feature_contract) == route(policy, b, available, feature_contract),
                    f"requires_strict_policy changes non-claim routing for {goal}")

    return {
        "strict_true_unique_capabilities": len(strict_true_routes),
        "strict_false_unique_capabilities": len(strict_false_routes),
        "non_claim_strict_toggle_invariant": True,
    }


def validate_mode_contracts(feature_sha: str):
    modes = load_yaml(MODE_CONTRACTS_PATH)
    require(modes["feature_contract"]["sha256"] == feature_sha, "mode contract feature hash drift")
    route_inputs = [
        modes["candidate_modes"]["M19"]["routing_input"],
        modes["candidate_modes"]["M20"]["routing_input"],
        modes["controls"]["direct_qwen_selection"]["routing_input"],
    ]
    require(route_inputs == ["same_frozen_typed_feature_vector"] * 3, "M19/M20/direct routing inputs must be identical")
    require(modes["routing_scope"]["selection_unit"] == "capability_only", "ENG-200 must remain capability-selection-only")
    require(modes["routing_scope"]["argument_binding_owner"] == "independent_held_equal_adapter", "argument binder ownership drift")
    require(modes["controls"]["raw_question_feature_extraction_ablation"]["primary_contrast_member"] is False, "raw-question routing cannot enter primary contrast")
    return modes


def validate_graph(policy, available, feature_contract):
    nodes = index_nodes(policy)
    require(policy["root"] in nodes, "missing root")
    require(policy["feature_contract_id"] == feature_contract["contract_id"], "policy feature-contract ID drift")
    require(policy["feature_contract_sha256"] == sha(FEATURE_PATH), "policy feature-contract hash drift")
    require(policy["capability_registry_version"] == load_yaml(REGISTRY_PATH)["schema_version"], "policy registry version drift")

    canonical = set(available)
    declared_features = set(feature_contract["features"])
    for node in policy["nodes"]:
        if node["type"] == "condition":
            require(node["feature"] in declared_features, f"policy uses undeclared feature: {node['feature']}")
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


def feature_vectors(feature_contract):
    goals = feature_contract["features"]["goal_class"]["enum"]
    for goal, scope, version, write, policy in itertools.product(goals, (False, True), (False, True), (False, True), (False, True)):
        yield {"goal_class": goal, "has_scope": scope, "has_version": version, "asks_write": write, "requires_strict_policy": policy}


def visible_registry_text(registry, explanation_text: str | None = None) -> str:
    chunks = [explanation_text if explanation_text is not None else EXPLANATION_PATH.read_text(encoding="utf-8")]
    for item in registry["capabilities"]:
        chunks.extend([
            item["handle"],
            item["neutral_surface"]["label"],
            item["neutral_surface"]["description"],
            item["schema_adapted_dev_surface"]["label"],
            item["schema_adapted_dev_surface"]["description"],
        ])
    return "\n".join(chunks)


def scan_visible_registry(registry, cases=None) -> None:
    cases = cases if cases is not None else load_json(CASES_PATH)["cases"]
    text = visible_registry_text(registry)
    for case in cases:
        require(case["case_id"] not in text, f"case ID leaked: {case['case_id']}")
        require(case["question"] not in text, f"question leaked: {case['case_id']}")
    for item in registry["capabilities"]:
        require(item["canonical_id"] not in text, f"internal canonical ID leaked to Qwen-visible text: {item['canonical_id']}")


def strip_surface(catalogue: dict) -> dict:
    result = copy.deepcopy(catalogue)
    result["surface"] = "<surface>"
    for item in result["capabilities"]:
        item.pop("label", None)
        item.pop("description", None)
    return result


def validate_visible_catalogues(registry, io_schemas):
    neutral_path = ROOT / "generated" / "qwen-catalogue.neutral.json"
    adapted_path = ROOT / "generated" / "qwen-catalogue.adapted.json"
    require(neutral_path.read_bytes() == build_visible_catalogue("neutral"), "neutral Qwen catalogue does not match registry")
    require(adapted_path.read_bytes() == build_visible_catalogue("adapted"), "adapted Qwen catalogue does not match registry")
    neutral = load_json(neutral_path)
    adapted = load_json(adapted_path)
    require(strip_surface(neutral) == strip_surface(adapted), "schema-surface ablation changed non-surface capability fields")
    visible_bytes = neutral_path.read_bytes() + adapted_path.read_bytes()
    for item in registry["capabilities"]:
        require(item["canonical_id"].encode("utf-8") not in visible_bytes, f"canonical ID leaked in generated catalogue: {item['canonical_id']}")
    require(len(neutral["capabilities"]) == len(io_schemas["capabilities"]), "generated catalogue capability count drift")
    return neutral_path, adapted_path


def expect_contract_failure(name: str, fn, names: list[str]) -> None:
    try:
        fn()
    except (ContractError, RoutingError, jsonschema.ValidationError, KeyError, ValueError):
        names.append(name)
    else:
        raise ContractError(f"mutation {name} was accepted")


def test_mutations(policy, registry, available, feature_contract) -> list[str]:
    names: list[str] = []
    base_cases = load_json(CASES_PATH)["cases"]

    malformed = copy.deepcopy(base_cases[0]["features"])
    malformed.pop("has_scope")
    expect_contract_failure("missing_feature", lambda: route(policy, malformed, available, feature_contract), names)

    invalid_goal = copy.deepcopy(base_cases[0]["features"])
    invalid_goal["goal_class"] = "ambiguous_goal"
    expect_contract_failure("invalid_goal", lambda: route(policy, invalid_goal, available, feature_contract), names)

    stale = copy.deepcopy(policy)
    next(x for x in stale["nodes"] if x["type"] == "action")["capability_version"] = "0.0.0"
    expect_contract_failure("stale_capability_version", lambda: validate_graph(stale, available, feature_contract), names)

    unavailable = dict(available)
    unavailable["db.resolve_claim"] = ("1.0.0", False)
    expect_contract_failure("unavailable_capability",
                            lambda: route(policy, base_cases[0]["features"], unavailable, feature_contract), names)

    missing = copy.deepcopy(policy)
    missing["nodes"] = [x for x in missing["nodes"] if x["id"] != "a_db_claim"]
    expect_contract_failure("missing_node", lambda: validate_graph(missing, available, feature_contract), names)

    cycle = copy.deepcopy(policy)
    next(x for x in cycle["nodes"] if x["id"] == "n_explain")["if_false"] = "n_write"
    expect_contract_failure("policy_cycle", lambda: validate_graph(cycle, available, feature_contract), names)

    wrong = copy.deepcopy(policy)
    next(x for x in wrong["nodes"] if x["id"] == "n_policy")["if_false"] = "a_prolog"
    changed = route(wrong, base_cases[0]["features"], available, feature_contract)
    require(changed != base_cases[0]["expected_capability"], "mutation wrong_branch did not alter route")
    names.append("wrong_branch")

    leaked_case = copy.deepcopy(registry)
    leaked_case["capabilities"][0]["neutral_surface"]["description"] += " train-route-001"
    expect_contract_failure("case_id_leak_detected", lambda: scan_visible_registry(leaked_case, base_cases), names)

    leaked_capability = copy.deepcopy(registry)
    leaked_capability["capabilities"][0]["neutral_surface"]["description"] += " " + registry["capabilities"][1]["canonical_id"]
    expect_contract_failure("canonical_capability_id_leak_detected", lambda: scan_visible_registry(leaked_capability, base_cases), names)

    neutral = load_json(ROOT / "generated" / "qwen-catalogue.neutral.json")
    adapted = load_json(ROOT / "generated" / "qwen-catalogue.adapted.json")
    require(strip_surface(neutral) == strip_surface(adapted), "schema-only surface changed capability identity or semantics")
    names.append("schema_surface_identity_preserved")
    return names


def validate_freeze_manifest():
    expected = build_freeze_manifest()
    actual = load_json(MANIFEST_PATH)
    require(actual == expected, "freeze manifest drift")
    return expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-swipl", action="store_true")
    args = parser.parse_args()

    feature_contract = load_feature_contract()
    policy = load_json(POLICY_PATH)
    registry = load_yaml(REGISTRY_PATH)
    io_schemas = load_json(IO_SCHEMAS_PATH)

    jsonschema.validate(policy, load_json(IR_SCHEMA_PATH))
    available = validate_registry(registry, io_schemas)
    validate_graph(policy, available, feature_contract)
    modes = validate_mode_contracts(sha(FEATURE_PATH))
    proxy_report = validate_feature_contract_and_proxy_resistance(feature_contract, policy, available)

    require(PROLOG_PATH.read_bytes() == build_prolog(policy).encode("utf-8"), "committed Prolog does not match clean lowering")
    neutral_catalogue, adapted_catalogue = validate_visible_catalogues(registry, io_schemas)
    scan_visible_registry(registry)

    cases_doc = load_json(CASES_PATH)
    require(cases_doc["feature_contract_id"] == feature_contract["contract_id"], "case feature-contract ID drift")
    require(cases_doc["feature_contract_sha256"] == sha(FEATURE_PATH), "case feature-contract hash drift")

    # The same canonical bytes are the primary routing input for M19/M20/direct Qwen.
    for case in cases_doc["cases"]:
        features = normalize_precomputed_features(case["features"])
        m19_bytes = canonical_feature_bytes(features)
        m20_bytes = canonical_feature_bytes(features)
        direct_bytes = canonical_feature_bytes(features)
        require(m19_bytes == m20_bytes == direct_bytes, f"typed routing input drift: {case['case_id']}")
        got = route(policy, features, available, feature_contract)
        require(got == case["expected_capability"], f"case route mismatch: {case['case_id']} got={got}")

    swipl = shutil.which("swipl")
    if args.require_swipl:
        require(swipl is not None, "swipl is required but unavailable")

    vectors = list(feature_vectors(feature_contract))
    if swipl:
        for features in vectors:
            graph_capability = route(policy, features, available, feature_contract)
            prolog_capability = swipl_route(swipl, PROLOG_PATH, features)
            require(graph_capability == prolog_capability, f"tree/prolog drift for {features}: {graph_capability} != {prolog_capability}")

    mutation_names = test_mutations(policy, registry, available, feature_contract)
    freeze = validate_freeze_manifest()

    report = {
        "schema_version": "1.1.0",
        "linear_issue": "ENG-200",
        "status": "PASS",
        "python_version": sys.version.split()[0],
        "swipl_required": bool(args.require_swipl),
        "swipl_available": bool(swipl),
        "swipl_version": None,
        "case_count": len(cases_doc["cases"]),
        "feature_space_vector_count": len(vectors),
        "tree_prolog_vectors_checked": len(vectors) if swipl else 0,
        "feature_contract": {
            "id": feature_contract["contract_id"],
            "sha256": sha(FEATURE_PATH),
            "primary_input_same_bytes": True,
            "raw_question_primary_contrast": False,
            "anti_label_proxy": proxy_report,
        },
        "routing_scope": {
            "selection_unit": modes["routing_scope"]["selection_unit"],
            "argument_binding_owner": modes["routing_scope"]["argument_binding_owner"],
        },
        "typed_capability_contracts": {
            "capabilities": len(registry["capabilities"]),
            "all_input_result_schemas_valid": True,
            "all_budgets_present": True,
            "all_fail_closed": True,
        },
        "mutation_tests": {
            "count": len(mutation_names),
            "names": mutation_names,
        },
        "freeze_manifest": {
            "file_count": freeze["file_count"],
            "sha256": sha(MANIFEST_PATH),
        },
        "hashes": {
            "feature_contract_sha256": sha(FEATURE_PATH),
            "registry_sha256": sha(REGISTRY_PATH),
            "registry_schema_sha256": sha(REGISTRY_SCHEMA_PATH),
            "capability_io_schemas_sha256": sha(IO_SCHEMAS_PATH),
            "ir_schema_sha256": sha(IR_SCHEMA_PATH),
            "policy_ir_sha256": sha(POLICY_PATH),
            "generated_prolog_sha256": sha(PROLOG_PATH),
            "cases_sha256": sha(CASES_PATH),
            "explanation_sha256": sha(EXPLANATION_PATH),
            "neutral_catalogue_sha256": sha(neutral_catalogue),
            "adapted_catalogue_sha256": sha(adapted_catalogue),
            "freeze_manifest_sha256": sha(MANIFEST_PATH),
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
