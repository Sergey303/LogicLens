from __future__ import annotations

import copy
import json
import statistics
import tempfile
from pathlib import Path

from adapter import ContractError, validate_call, validate_result_rows
from build_freeze_manifest import FILES as FREEZE_FILES
from generate_package import GENERATED_FILES, build, sha256_file
from reference_oracle import resolve
from subset_eligibility import evaluate_source

ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = ROOT.parent
REPO_ROOT = PACKAGE_ROOT.parents[2]
GENERATED = ROOT / "generated"
SOURCE = ROOT / "source.prototype.json"
REGISTRY = ROOT / "query-registry.prototype.json"
EXPECTED = ROOT / "evaluator" / "expected.prototype.json"
HEX = set("0123456789abcdef")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_sha256(value: object, label: str) -> None:
    require(isinstance(value, str) and len(value) == 64 and set(value) <= HEX, f"invalid SHA-256: {label}")


def verify_contract() -> None:
    contract = load(PACKAGE_ROOT / "contract.json")
    require(contract["schema_version"] == "1.1.0", "contract remediation version drift")
    require(contract["prototype_scope"] == "TRAIN_DEV_ONLY_SYNTHETIC", "prototype scope drift")
    owners = contract["semantic_ownership"]
    for key in ("retrieval", "recursive_closure", "epistemic_status", "decision_policy"):
        require(owners[key] == "postgresql", f"semantic owner drift: {key}")
    require(contract["eligibility"]["m14_baseline_eligible"] is False, "trusted execution cannot enter M14/B*")
    require(contract["eligibility"]["m15_wp004_candidate"] is False, "single-endpoint M15 must remain DEV-only")
    require(contract["candidate_modes"]["M15"]["confirmatory_status"] == "DEV_ONLY_SINGLE_ENDPOINT_NOT_QUERY_SELECTION", "M15 adjudication drift")
    require("LIVE_POSTGRES" in contract["candidate_modes"]["M16"]["confirmatory_status"], "M16 live DB gate missing")
    require(contract["live_execution"]["python_reference_oracle_may_substitute"] is False, "reference oracle cannot substitute for PostgreSQL")
    require(contract["contrast_interpretation"]["proof_obligations_identical"] is False, "M16 must not claim M6 proof equivalence")
    require(contract["typed_endpoint"]["maximum_rows"] == 1, "row policy drift")


def verify_rebuild() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        manifest = build(SOURCE, temp)
        for name in (*GENERATED_FILES, "package-manifest.json"):
            require((temp / name).read_bytes() == (GENERATED / name).read_bytes(), f"non-deterministic artifact: {name}")
        committed = load(GENERATED / "package-manifest.json")
        require(committed == manifest, "generated package manifest drift")
        for name, digest in committed["generated_sha256"].items():
            require(sha256_file(GENERATED / name) == digest, f"hash mismatch: {name}")
        require(sha256_file(SOURCE) == committed["source_sha256"], "source hash mismatch")


def verify_reference_semantics_only() -> None:
    """Test-only semantics cross-check. This is explicitly NOT live DB evidence."""
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
        require(row["status_code"] == want["expected_status"], f"reference status mismatch: {case_id}")
        require(row["action_code"] == want["expected_action"], f"reference action mismatch: {case_id}")
        seen_statuses.add(row["status_code"])
    require(seen_statuses == {"supported", "refuted", "conflicting", "unknown"}, "reference four-state coverage incomplete")


def verify_subset_eligibility() -> None:
    source = load(SOURCE)
    contract = load(PACKAGE_ROOT / "RELATIONAL_SUBSET_CONTRACT.json")
    require(contract["contract_id"] == "eng197.relational-subset.v1", "subset contract id drift")
    require(contract["decision_timing"] == "before_split_assignment_outcome_blind", "subset timing drift")
    require(evaluate_source(source) == {"eligible": True, "reason_codes": []}, "prototype should be losslessly eligible")

    tests: list[tuple[str, dict, str]] = []
    mixed = copy.deepcopy(source)
    mixed["assertions"][0]["version"] = "v2"
    tests.append(("mixed_version", mixed, "MIXED_SCOPE_OR_VERSION"))

    multi = copy.deepcopy(source)
    multi["implications"][0]["premises"] = ["p-qualified", "p-certified"]
    tests.append(("multi_premise", multi, "MULTI_PREMISE_RULE"))

    negative_head = copy.deepcopy(source)
    negative_head["implications"][0]["head_polarity"] = "negative"
    tests.append(("negative_head", negative_head, "NEGATIVE_RULE_HEAD"))

    dependency = copy.deepcopy(source)
    dependency["dependency_groups"] = [{"id": "g1"}]
    tests.append(("dependency", dependency, "DEPENDENCY_SEMANTICS_REQUIRED"))

    unknown = copy.deepcopy(source)
    unknown["future_semantics"] = True
    tests.append(("unknown_structure", unknown, "UNKNOWN_STRUCTURE"))

    for name, candidate, expected_reason in tests:
        result = evaluate_source(candidate)
        require(result["eligible"] is False, f"subset mutation unexpectedly eligible: {name}")
        require(expected_reason in result["reason_codes"], f"subset mutation missing reason {expected_reason}: {name}")


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

    for rows in ([], [
        {"status_code": "unknown", "action_code": "review", "evidence": [], "provenance": []},
        {"status_code": "unknown", "action_code": "review", "evidence": [], "provenance": []},
    ]):
        try:
            validate_result_rows(rows)
        except ContractError:
            pass
        else:
            raise AssertionError("zero/multiple-row anomaly accepted")


def verify_live_path_is_database_owned() -> None:
    db_executor = (ROOT / "db_executor.py").read_text(encoding="utf-8")
    live = (ROOT / "live_postgres_smoke.py").read_text(encoding="utf-8")
    require("reference_oracle" not in db_executor, "DB executor imports reference oracle")
    require("reference_oracle" not in live, "live PostgreSQL smoke imports reference oracle")
    require("cursor.execute(query, params)" in db_executor, "real parameterized database execution missing")
    require("pre_score_db_result" in db_executor, "database pre-score stage missing")
    persist_call = 'pre_score_hashes[case_id] = persist_pre_score_record'
    expected_load = 'expected = {row["case_id"]: row for row in load(EXPECTED)["cases"]}'
    require(persist_call in live and expected_load in live, "live execution/evaluation phase markers missing")
    require(live.index(persist_call) < live.index(expected_load), "evaluator expectations can precede persisted DB evidence")
    require("Phase 1:" in live and "Phase 2:" in live, "explicit pre-score/evaluation phase boundary missing")
    for token in ("INSERT INTO relational_cmp.proposition", "UPDATE relational_cmp.proposition", "DELETE FROM relational_cmp.proposition", "CREATE TABLE relational_cmp.evil"):
        require(token in live, f"live permission negative missing: {token}")


def verify_runtime_lock() -> None:
    runtime = load(PACKAGE_ROOT / "RUNTIME_DEPENDENCIES.json")
    require(runtime["postgresql"]["required_server_version"] == "18.4", "PostgreSQL version pin drift")
    require(runtime["postgresql"]["required_server_version_num"] == 180004, "PostgreSQL numeric pin drift")
    require(runtime["python"]["psycopg"]["version"] == "3.3.4", "psycopg pin drift")
    requirements = (PACKAGE_ROOT / "requirements-eng197.txt").read_text(encoding="utf-8").strip()
    require(requirements == "psycopg[binary]==3.3.4", "requirements/runtime lock mismatch")


def verify_freeze_closure_definition() -> None:
    required_suffixes = {
        "contract.json", "call.schema.json", "result.schema.json", "FEASIBILITY_INPUT.json",
        "M15_IDENTIFIER_VISIBILITY_CONTRACT.md", "RELATIONAL_SUBSET_CONTRACT.json",
        "RUNTIME_DEPENDENCIES.json", "LIVE_POSTGRES_SMOKE_CONTRACT.md",
        "prototype/adapter.py", "prototype/db_executor.py", "prototype/subset_eligibility.py",
        "prototype/live_postgres_smoke.py", "prototype/reference_oracle.py", "prototype/verify.py",
        "prototype/query-registry.prototype.json", "prototype/evaluator/expected.prototype.json",
        "scripts/run-relational-comparator-tests.ps1", "scripts/run-relational-postgres-smoke.ps1",
    }
    for suffix in required_suffixes:
        require(any(path.endswith(suffix) for path in FREEZE_FILES), f"freeze closure missing {suffix}")
    require(len(FREEZE_FILES) >= 30, "freeze closure unexpectedly small")
    for path in FREEZE_FILES:
        require((REPO_ROOT / path).is_file(), f"freeze closure path missing: {path}")


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
    require(feasibility["schema_version"] == "1.2.0", "feasibility schema version drift")
    require(feasibility["prototype_scope"] == "TRAIN_DEV_ONLY_SYNTHETIC", "feasibility scope drift")
    require(feasibility["mode_adjudication"]["M15"] == "DEV_ONLY_SINGLE_ENDPOINT", "M15 feasibility status drift")
    require(feasibility["mode_adjudication"]["M16"] == "CANDIDATE_AFTER_LIVE_POSTGRES_AND_REVIEW", "M16 feasibility status drift")

    static = feasibility["static_costs"]
    require(static["m15_typed_calls_per_scenario"] == 1 and static["m16_typed_calls_per_scenario"] == 1, "call budget drift")
    require(static["database_executions_per_scenario"] == 1, "database execution budget drift")
    require(static["maximum_result_rows"] == 1, "feasibility row budget drift")
    actual_bytes = sum(path.stat().st_size for path in GENERATED.iterdir() if path.is_file())
    require(static["generated_package_bytes"] == actual_bytes, "generated package byte count drift")

    measured = feasibility["measured_costs"]
    require(measured["status"] == "BASELINE_LIVE_POSTGRES_OBSERVATION_RECORDED_NOT_SCALING_ESTIMATE", "live feasibility evidence status drift")
    require(measured["measurement_date"] == "2026-08-11", "live feasibility date drift")
    require(measured["github_actions_run_id"] == 31483217680, "live feasibility run binding drift")
    require(measured["github_actions_job_id"] == 93752645632, "live feasibility job binding drift")

    runtime = measured["runtime"]
    require(runtime["postgresql_server_version"] == "18.4", "measured PostgreSQL version drift")
    require(runtime["postgresql_server_version_num"] == 180004, "measured PostgreSQL numeric version drift")
    require(runtime["postgresql_image_digest"] == "postgres@sha256:a02db8cac496f15b094798a38254f14d6e00741f709360e5e00bb6668ea31636", "measured PostgreSQL image digest drift")
    require(runtime["psycopg_version"] == "3.3.4", "measured psycopg version drift")
    require(runtime["runner"] == "GitHub Actions ubuntu-24.04 hosted runner", "measured runner identity drift")

    require(isinstance(measured["postgresql_build_ns"], int) and measured["postgresql_build_ns"] > 0, "invalid measured PostgreSQL build time")
    latency = measured["db_call_latency_ns"]
    per_case_latency = latency["per_case"]
    require(set(per_case_latency) == {"proto-01", "proto-02", "proto-03", "proto-04"}, "measured latency case-set drift")
    latency_values = list(per_case_latency.values())
    require(all(isinstance(value, int) and value > 0 for value in latency_values), "invalid measured DB latency")
    require(latency["case_count"] == len(latency_values) == 4, "measured DB latency case count drift")
    require(latency["min"] == min(latency_values), "measured DB latency minimum drift")
    require(latency["median"] == int(statistics.median(latency_values)), "measured DB latency median drift")
    require(latency["max"] == max(latency_values), "measured DB latency maximum drift")
    require(latency["min"] <= latency["median"] <= latency["max"], "measured DB latency ordering invalid")

    require(isinstance(measured["database_relation_index_bytes"], int) and measured["database_relation_index_bytes"] > 0, "invalid measured database bytes")
    require(measured["generated_package_bytes_observed"] == actual_bytes, "observed generated package byte count drift")

    result_bytes = measured["pre_score_result_bytes"]
    per_case_bytes = result_bytes["per_case"]
    require(set(per_case_bytes) == {"proto-01", "proto-02", "proto-03", "proto-04"}, "pre-score result-byte case-set drift")
    byte_values = list(per_case_bytes.values())
    require(all(isinstance(value, int) and value > 0 for value in byte_values), "invalid pre-score result byte measurement")
    require(result_bytes["total"] == sum(byte_values), "pre-score result-byte total drift")
    require(result_bytes["min"] == min(byte_values), "pre-score result-byte minimum drift")
    require(result_bytes["median"] == int(statistics.median(byte_values)), "pre-score result-byte median drift")
    require(result_bytes["max"] == max(byte_values), "pre-score result-byte maximum drift")
    require("canonical one-row DB result" in result_bytes["definition"], "pre-score byte definition drift")

    require_sha256(measured["live_report_sha256"], "live report")
    require_sha256(measured["subset_equivalence_report_sha256"], "subset equivalence report")
    require_sha256(measured["artifact_zip_sha256"], "artifact zip")
    require(measured["live_report_sha256"] == "3f2c34d6e892b684a02a49451eb5fc13b00b8cccb5546754007e245052a21c0c", "live report evidence binding drift")
    require(measured["subset_equivalence_report_sha256"] == "c3371db1e5e0b965d71fea8229f0d6d5350283e86e106dccb9687ac73d4df2f3", "subset report evidence binding drift")
    require(measured["artifact_zip_sha256"] == "94b4a73cb0792b422c0b86414b87c2e23b33c900eb4cf15ea4fa60e54a828f5b", "artifact evidence binding drift")
    require(measured["artifact_id"] == 9098050218, "artifact ID binding drift")
    require("not a production-capacity estimate" in measured["interpretation"], "baseline observation overclaim guard missing")
    require("not be treated as an independent sample" in measured["interpretation"], "power pseudoreplication guard missing")

    live_contract = feasibility["live_evidence_contract"]
    require(live_contract["must_be_real_postgresql"] is True, "real PostgreSQL evidence requirement drift")
    require(live_contract["python_reference_oracle_is_not_measurement_evidence"] is True, "reference-oracle measurement guard drift")
    require(live_contract["baseline_observation_must_not_replace_final_WP007_profile_measurement"] is True, "WP-007 remeasurement guard drift")

    required = feasibility["measurement_required_before_confirmatory_freeze"]
    for key in (
        "catalogue_tokens_by_model_profile",
        "guide_tokens_by_model_profile",
        "result_tokens_by_scenario_and_model_profile",
        "postgresql_build_time_ms",
        "postgresql_query_latency_ms",
        "database_storage_bytes",
        "m16_registry_annotation_seconds",
        "relational_subset_eligible_count_and_source_families",
    ):
        require(key in required and required[key], f"confirmatory feasibility requirement missing: {key}")
    power_note = feasibility["power_note_for_wp006"]
    require("base_scenario_id" in power_note, "WP-006 unit binding missing")
    require("do not increase benchmark N" in power_note, "WP-006 smoke pseudoreplication guard missing")
    require("M15 remains DEV-only" in power_note, "M15 DEV-only boundary missing from feasibility handoff")


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
        verify_reference_semantics_only,
        verify_subset_eligibility,
        verify_security,
        verify_live_path_is_database_owned,
        verify_runtime_lock,
        verify_freeze_closure_definition,
        verify_leakage,
        verify_feasibility,
        verify_sql_contract,
    ]
    for check in checks:
        check()
        print(f"PASS {check.__name__}")
    print("ENG-197 static producer verification passed; recorded live PostgreSQL evidence remains subject to independent review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
