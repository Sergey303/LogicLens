import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROGRAM = ROOT / "program.py"
CASES = ROOT / "cases.train_dev.json"
API = ROOT / "tool_api.json"

FORBIDDEN_NAMES = {
    "open", "eval", "exec", "compile", "__import__", "getattr", "setattr", "globals", "locals", "vars", "input", "breakpoint",
    "os", "sys", "socket", "subprocess", "pathlib", "requests", "urllib", "random", "secrets", "time", "datetime"
}
FORBIDDEN_VISIBLE = ("strict_status", "threshold_relation(", "interval_threshold(", "program.py", "Traceback", "__pycache__", "case_id", "expected")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def scan_source(text):
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
    if re.search(r"(?:train|dev|holdout|replication)-[A-Za-z0-9_-]+", text):
        raise AssertionError("case_id_branch")


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


def verify_cases(runner):
    data = json.loads(CASES.read_text(encoding="utf-8"))
    assert data["scope"] == "TRAIN_DEV_ONLY_SYNTHETIC"
    outputs = []
    for case in data["cases"]:
        result = execute_case(runner, case)
        assert_expected(case, result)
        payload = runner.qwen_visible_payload("M21", case["question"], result)
        scan_visible(payload)
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

    names.append(expect_reject("fabricated_provenance", lambda: runner.execute("py_cap_02", {"value": 1, "threshold": 2}, [])))
    names.append(expect_reject("hidden_lookup_table", lambda: scan_source(base + "\nANSWER_TABLE = {'x': True}\n")))
    names.append(expect_reject("case_id_branch", lambda: scan_source(base + "\nif 'dev-evidence-conflict':\n    pass\n")))
    names.append(expect_reject("forbidden_import", lambda: scan_source("import os\n" + base)))
    names.append(expect_reject("filesystem_attempt", lambda: scan_source(base + "\nopen('x.txt', 'w')\n")))
    names.append(expect_reject("subprocess_attempt", lambda: scan_source("import subprocess\n" + base)))
    leak = runner.qwen_visible_payload("M21", "q", {"capability_handle": "py_cap_01", "status": "ok", "value": None, "provenance": ["synthetic:x"]})
    leak["question"] += " program.py strict_status"
    names.append(expect_reject("qwen_visible_source_leak", lambda: scan_visible(leak)))
    return names


def main():
    scan_source(PROGRAM.read_text(encoding="utf-8"))
    runner = load_runner()
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
        "mutations_passed": mutation_names,
    }
    print(canonical(report))


if __name__ == "__main__":
    main()
