import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = ROOT.parent
PROGRAM = ROOT / "program.py"
RUNNER = ROOT / "runner.py"
CASES = ROOT / "cases.train_dev.json"
API = ROOT / "tool_api.json"
RUNTIME_LOCK = PACKAGE_ROOT / "PYTHON_RUNTIME_LOCK.json"
SANDBOX_PROFILE = PACKAGE_ROOT / "PYTHON_SANDBOX_PROFILE.json"

FORBIDDEN_NAMES = {
    "open", "eval", "exec", "compile", "__import__", "getattr", "setattr", "globals", "locals", "vars", "input", "breakpoint",
    "os", "sys", "socket", "subprocess", "pathlib", "requests", "urllib", "random", "secrets", "time", "datetime"
}
FORBIDDEN_VISIBLE = ("strict_status", "threshold_relation(", "interval_threshold(", "program.py", "runner.py", "Traceback", "__pycache__", "case_id", "expected")
CASE_ID_PATTERN = re.compile(r"(?:train|dev|holdout|replication)-[A-Za-z0-9_-]+")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def scan_program_source(text):
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise AssertionError("forbidden_import")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise AssertionError(f"forbidden_name:{node.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise AssertionError(f"forbidden_attribute:{node.attr}")
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and re.search(r"answer|expected|gold", target.id, re.I):
                    raise AssertionError(f"hidden_lookup_symbol:{target.id}")
    if CASE_ID_PATTERN.search(text):
        raise AssertionError("case_id_branch")


def scan_mapper_source(text):
    if CASE_ID_PATTERN.search(text):
        raise AssertionError("mapper_case_id_branch")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and re.search(r"answer|expected|gold|case_id", target.id, re.I):
                    raise AssertionError(f"mapper_hidden_symbol:{target.id}")


def scan_visible(payload):
    text = canonical(payload)
    for token in FORBIDDEN_VISIBLE:
        if token in text:
            raise AssertionError(f"visible_leak:{token}")


def load_runner():
    import sys
    sys.path.insert(0, str(ROOT))
    import runner
    return runner


def execute_case(runner, case):
    handle, args = runner.m21_map(case["public_request"])
    return runner.execute(handle, args, case["provenance"])


def assert_expected(case, result):
    if {"status": result["status"], "value": result["value"]} != case["expected"]:
        raise AssertionError("semantic_vector_mismatch")


def verify_runtime_contract(runner):
    lock = json.loads(RUNTIME_LOCK.read_text(encoding="utf-8"))
    sandbox = json.loads(SANDBOX_PROFILE.read_text(encoding="utf-8"))
    assert lock["implementation"] == "CPython"
    assert lock["version"] == "3.13.5"
    assert lock["third_party_dependencies"] == []
    assert lock["standard_library_only"] is True
    assert lock["program_imports_allowed"] == []
    assert sandbox["network"] is False
    assert sandbox["filesystem"] is False
    assert sandbox["subprocess"] is False
    assert sandbox["shell"] is False
    assert sandbox["dynamic_import"] is False
    assert sandbox["side_effects"] is False
    assert sandbox["max_calls_per_request"] == runner.API["limits"]["max_calls"]
    assert sandbox["wall_timeout_ms"] == runner.API["limits"]["timeout_ms"]
    assert sandbox["max_memory_mb"] == runner.API["limits"]["max_memory_mb"]
    assert sandbox["max_result_bytes"] == runner.API["limits"]["max_result_bytes"]


def verify_api_contract(runner):
    expected = {handle: set(args) for handle, args in runner._ALLOWED_ARGS.items()}
    seen = set()
    for cap in runner.API["capabilities"]:
        handle = cap["handle"]
        seen.add(handle)
        assert cap["arguments"]["type"] == "object"
        assert cap["arguments"]["additionalProperties"] is False
        assert set(cap["arguments"]["required"]) == expected[handle]
        assert set(cap["arguments"]["properties"]) == expected[handle]
        assert cap["result"]["type"] == "object"
        assert cap["result"]["additionalProperties"] is False
        assert set(cap["result"]["required"]) == {"status", "value"}
        assert cap["provenance_required"] is True
        assert cap["side_effects"] == "none"
    assert seen == set(expected)


def verify_cases(runner):
    data = json.loads(CASES.read_text(encoding="utf-8"))
    assert data["scope"] == "TRAIN_DEV_ONLY_SYNTHETIC"
    outputs = []
    for case in data["cases"]:
        pre_m21 = runner.qwen_visible_request("M21", case["question"])
        assert pre_m21["capabilities"] == []
        scan_visible(pre_m21)
        pre_m22 = runner.qwen_visible_request("M22", case["question"])
        assert len(pre_m22["capabilities"]) == 3
        scan_visible(pre_m22)

        result = execute_case(runner, case)
        assert_expected(case, result)
        payload = runner.qwen_visible_payload("M21", case["question"], result)
        assert payload["capabilities"] == []
        scan_visible(payload)
        m22_payload = runner.qwen_visible_payload("M22", case["question"], result)
        assert len(m22_payload["capabilities"]) == 3
        scan_visible(m22_payload)
        outputs.append(canonical(payload))
    again = []
    for case in data["cases"]:
        result = execute_case(runner, case)
        again.append(canonical(runner.qwen_visible_payload("M21", case["question"], result)))
    assert outputs == again
    return data, len(outputs)


def expect_reject(name, fn):
    try:
        fn()
    except (AssertionError, ValueError, KeyError, TypeError):
        return name
    raise AssertionError(f"mutation_not_rejected:{name}")


def mutations(runner, data):
    base = PROGRAM.read_text(encoding="utf-8")
    runner_source = RUNNER.read_text(encoding="utf-8")
    names = []

    evidence_case = next(c for c in data["cases"] if c["id"] == "train-evidence-positive")
    threshold_case = next(c for c in data["cases"] if c["id"] == "train-threshold-above")

    original_kind = dict(runner._KIND_TO_HANDLE)
    def wrong_branch():
        try:
            runner._KIND_TO_HANDLE["evidence_status"] = "py_cap_02"
            result = execute_case(runner, evidence_case)
            assert_expected(evidence_case, result)
        finally:
            runner._KIND_TO_HANDLE.clear()
            runner._KIND_TO_HANDLE.update(original_kind)
    names.append(expect_reject("wrong_branch", wrong_branch))

    original_impl = runner._HANDLE_TO_IMPL["py_cap_02"]
    def arithmetic_inversion():
        try:
            runner._HANDLE_TO_IMPL["py_cap_02"] = lambda value, threshold: {"status": "ok", "value": "below" if value > threshold else "above"}
            result = execute_case(runner, threshold_case)
            assert_expected(threshold_case, result)
        finally:
            runner._HANDLE_TO_IMPL["py_cap_02"] = original_impl
    names.append(expect_reject("arithmetic_inversion", arithmetic_inversion))

    original_version = runner.PROGRAM_VERSION
    def stale_version():
        try:
            runner.PROGRAM_VERSION = "0.0.0-stale"
            runner.execute("py_cap_02", {"value": 1, "threshold": 2}, ["synthetic:x"])
        finally:
            runner.PROGRAM_VERSION = original_version
    names.append(expect_reject("stale_program_version", stale_version))

    def fabricated_provenance():
        original = runner._HANDLE_TO_IMPL["py_cap_02"]
        try:
            runner._HANDLE_TO_IMPL["py_cap_02"] = lambda value, threshold: {"status": "ok", "value": "above", "provenance": ["fabricated:source"]}
            runner.execute("py_cap_02", {"value": 12, "threshold": 10}, ["synthetic:trusted"])
        finally:
            runner._HANDLE_TO_IMPL["py_cap_02"] = original
    names.append(expect_reject("fabricated_provenance", fabricated_provenance))

    names.append(expect_reject("hidden_lookup_table", lambda: scan_program_source(base + "\nANSWER_TABLE = {'x': True}\n")))
    names.append(expect_reject("case_id_branch", lambda: scan_program_source(base + "\nif 'dev-evidence-conflict':\n    pass\n")))
    names.append(expect_reject("mapper_case_id_branch", lambda: scan_mapper_source(runner_source + "\nif 'train-evidence-positive':\n    pass\n")))
    names.append(expect_reject("forbidden_import", lambda: scan_program_source("import os\n" + base)))
    names.append(expect_reject("filesystem_attempt", lambda: scan_program_source(base + "\nopen('x.txt', 'w')\n")))
    names.append(expect_reject("subprocess_attempt", lambda: scan_program_source("import subprocess\n" + base)))
    names.append(expect_reject("network_attempt", lambda: scan_program_source("import socket\n" + base)))
    names.append(expect_reject("dynamic_eval_attempt", lambda: scan_program_source(base + "\neval('1+1')\n")))
    leak = runner.qwen_visible_payload("M21", "q", {"capability_handle": "py_cap_01", "status": "ok", "value": None, "provenance": ["synthetic:x"]})
    leak["question"] += " program.py strict_status"
    names.append(expect_reject("qwen_visible_source_leak", lambda: scan_visible(leak)))
    return names


def main():
    scan_program_source(PROGRAM.read_text(encoding="utf-8"))
    scan_mapper_source(RUNNER.read_text(encoding="utf-8"))
    runner = load_runner()
    verify_runtime_contract(runner)
    verify_api_contract(runner)
    data, cases = verify_cases(runner)
    mutation_names = mutations(runner, data)
    report = {
        "issue": "ENG-201",
        "scope": "TRAIN_DEV_ONLY_SYNTHETIC",
        "cases_passed": cases,
        "deterministic_rerun": True,
        "program_sha256": hashlib.sha256(PROGRAM.read_bytes()).hexdigest(),
        "tool_api_sha256": hashlib.sha256(API.read_bytes()).hexdigest(),
        "qwen_source_visibility": "none",
        "runtime_lock": "PASS",
        "typed_api": "PASS",
        "pre_and_post_visibility": "PASS",
        "mutations_passed": mutation_names,
    }
    print(canonical(report))


if __name__ == "__main__":
    main()
