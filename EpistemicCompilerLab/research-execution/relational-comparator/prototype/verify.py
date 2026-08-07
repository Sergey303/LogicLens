from __future__ import annotations

import json
import tempfile
from pathlib import Path

from adapter import ContractError, make_pre_score_record, validate_call, validate_result_rows
from generate_package import GENERATED_FILES, build, sha256_file
from reference_oracle import resolve

ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = ROOT.parent
GENERATED = ROOT / "generated"
SOURCE = ROOT / "source.prototype.json"
REGISTRY = ROOT / "query-registry.prototype.json"
EXPECTED = ROOT / "evaluator" / "expected.prototype.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_contract() -> None:
    contract = load(PACKAGE_ROOT / "contract.json")
    require(contract["prototype_scope"] == "TRAIN_DEV_ONLY_SYNTHETIC", "prototype scope drift")
    owners = contract["semantic_ownership"]
    for key in ("retrieval", "recursive_closure", "epistemic_status", "decision_policy"):
        require(owners[key] == "postgresql", f"semantic owner drift: {key}")
    require(contract["eligibility"]["m14_baseline_eligible"] is False, "trusted execution cannot enter M14/B*")
    require(contract["typed_endpoint"]["maximum_rows"] == 1, "row policy drift")


def verify_rebuild() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        manifest = build(SOURCE, temp)
        for name in (*GENERATED_FILES, "package-manifest.json"):
            require((temp / name).read_bytes() == (GENERATED / name).read_bytes(), f"non-deterministic artifact: {name}")
        committed = load(GENERATED / "package-manifest.json")
        require(committed == manifest, "manifest drift")
        for name, digest in committed["generated_sha256"].items():
            require(sha256_file(GENERATED / name) == digest, f"hash mismatch: {name}")
        require(sha256_file(SOURCE) == committed["source_sha256"], "source hash mismatch")


def verify_runtime_semantics() -> None:
    source = load(SOURCE)
    registry = load(REGISTRY)
    expected = {item["case_id"]: item for item in load(EXPECTED)["cases"]}
    seen_statuses: set[str] = set()
    for entry in registry["entries"]:
        case_id = entry["case_id"]
        _, params = validate_call(entry["call"])
        row = resolve(source, *params)
        validate_result_rows([row])
        want = expected[case_id]
        require(row["status_code"] == want["expected_status"], f"status mismatch: {case_id}")
        require(row["action_code"] == want["expected_action"], f"action mismatch: {case_id}")
        record = make_pre_score_record(entry["call"], [row])
        require(record["stage"] == "pre_score" and record["score"] is None, "scoring leaked into transport record")
        require(record["provenance"] == row["provenance"], "provenance not preserved")
        seen_statuses.add(row["status_code"])
    require(seen_statuses == {"supported", "refuted", "conflicting", "unknown"}, "four-state coverage incomplete")


def verify_security() -> None:
    valid = {"endpoint": "resolve_claim", "arguments": {"proposition_id": "p-allowed", "scope_id": "prototype-scope", "version": "v1"}}
    query, params = validate_call(valid)
    require(query.count("%s") == 3, "call is not parameterized")
    require(params[0] == "p-allowed", "argument order drift")

    payload = {"endpoint": "resolve_claim", "arguments": {"proposition_id": "x'; DROP TABLE relational_cmp.proposition; --", "scope_id": "prototype-scope", "version": "v1"}}
    injected_query, injected_params = validate_call(payload)
    require(injected_query == query, "argument changed SQL text")
    require("DROP TABLE" in injected_params[0], "payload was silently repaired instead of parameterized")

    invalid_calls = [
        {"endpoint": "resolve_claim; DROP TABLE x", "arguments": valid["arguments"]},
        {"endpoint": "undeclared", "arguments": valid["arguments"]},
        {"endpoint": "resolve_claim", "arguments": valid["arguments"], "raw_sql": "DELETE FROM x"},
        {"endpoint": "resolve_claim", "arguments": {**valid["arguments"], "extra": "SELECT 1"}},
    ]
    for call in invalid_calls:
        try:
            validate_call(call)
        except ContractError:
            pass
        else:
            raise AssertionError(f"unsafe call accepted: {call}")

    try:
        validate_result_rows([])
    except ContractError:
        pass
    else:
        raise AssertionError("zero-row anomaly accepted")
    try:
        validate_result_rows([
            {"status_code": "unknown", "action_code": "review", "evidence": [], "provenance": []},
            {"status_code": "unknown", "action_code": "review", "evidence": [], "provenance": []},
        ])
    except ContractError:
        pass
    else:
        raise AssertionError("oversize result was truncated or accepted")


def verify_leakage() -> None:
    expected = load(EXPECTED)["cases"]
    generated_text = "\n".join((GENERATED / name).read_text(encoding="utf-8") for name in (*GENERATED_FILES, "package-manifest.json"))
    for case in expected:
        require(case["case_id"] not in generated_text, f"case id leaked: {case['case_id']}")
        require(case["question"] not in generated_text, f"question leaked: {case['case_id']}")
    source_text = SOURCE.read_text(encoding="utf-8")
    require("expected_status" not in source_text and "expected_action" not in source_text, "expected fields leaked into source")
    guide = (GENERATED / "query-guide.md").read_text(encoding="utf-8")
    require("proto-" not in guide and "component-alpha" not in guide, "case-specific guide leak")


def verify_feasibility() -> None:
    feasibility = load(PACKAGE_ROOT / "FEASIBILITY_INPUT.json")
    require(feasibility["prototype_scope"] == "TRAIN_DEV_ONLY_SYNTHETIC", "feasibility scope drift")
    static = feasibility["static_costs"]
    require(static["m15_typed_calls_per_scenario"] == 1 and static["m16_typed_calls_per_scenario"] == 1, "call budget drift")
    require(static["maximum_result_rows"] == 1, "feasibility row budget drift")
    actual_bytes = sum(path.stat().st_size for path in GENERATED.iterdir() if path.is_file())
    require(static["generated_package_bytes"] == actual_bytes, "generated package byte count drift")


def verify_sql_contract() -> None:
    schema = (GENERATED / "schema.sql").read_text(encoding="utf-8")
    permissions = (GENERATED / "permissions.sql").read_text(encoding="utf-8")
    require("WITH RECURSIVE" in schema, "recursive closure missing")
    require("STABLE" in schema and "SECURITY INVOKER" in schema, "read-only function declaration missing")
    require("INSERT " not in schema and "UPDATE " not in schema and "DELETE " not in schema, "runtime schema function contains DML")
    require("GRANT SELECT" in permissions and "GRANT EXECUTE" in permissions, "reader grants missing")
    require("NOLOGIN" in permissions, "reader role is not no-login")


def main() -> int:
    checks = [
        verify_contract,
        verify_rebuild,
        verify_runtime_semantics,
        verify_security,
        verify_leakage,
        verify_feasibility,
        verify_sql_contract,
    ]
    for check in checks:
        check()
        print(f"PASS {check.__name__}")
    print("ENG-197 relational comparator producer verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
