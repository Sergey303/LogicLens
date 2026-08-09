from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import time
from pathlib import Path
from typing import Any

import psycopg
from psycopg import errors

from adapter import ContractError, canonical_json_bytes, validate_call
from build_freeze_manifest import build as build_freeze_manifest
from db_executor import execute_typed_call, persist_pre_score_record
from subset_eligibility import evaluate_source

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
GENERATED = ROOT / "generated"
SOURCE = ROOT / "source.prototype.json"
REGISTRY = ROOT / "query-registry.prototype.json"
EXPECTED = ROOT / "evaluator" / "expected.prototype.json"
RUNTIME = PACKAGE / "RUNTIME_DEPENDENCIES.json"
FREEZE = PACKAGE / "ENG-197_FREEZE_MANIFEST.json"
ADVISORY_LOCK = 197004


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def execute_script(connection: Any, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    connection.execute(sql, prepare=False)


def assert_adapter_negatives() -> list[str]:
    valid_args = {"proposition_id": "p-allowed", "scope_id": "prototype-scope", "version": "v1"}
    negatives = {
        "undeclared_endpoint": {"endpoint": "other", "arguments": valid_args},
        "free_sql_field": {"endpoint": "resolve_claim", "arguments": valid_args, "sql": "DELETE FROM x"},
        "extra_argument": {"endpoint": "resolve_claim", "arguments": {**valid_args, "extra": "x"}},
    }
    passed = []
    for name, payload in negatives.items():
        try:
            validate_call(payload)
        except ContractError:
            passed.append(name)
        else:
            raise RuntimeError(f"adapter negative unexpectedly accepted: {name}")
    return passed


def assert_db_write_denials(connection: Any) -> list[str]:
    statements = {
        "insert_denied": "INSERT INTO relational_cmp.proposition VALUES ('evil','x','x','x')",
        "update_denied": "UPDATE relational_cmp.proposition SET subject_text='evil' WHERE proposition_id='p-allowed'",
        "delete_denied": "DELETE FROM relational_cmp.proposition WHERE proposition_id='p-allowed'",
        "create_table_denied": "CREATE TABLE relational_cmp.evil(x integer)",
    }
    passed = []
    for name, sql in statements.items():
        try:
            connection.execute(sql)
        except errors.InsufficientPrivilege:
            passed.append(name)
        else:
            raise RuntimeError(f"read-only role unexpectedly allowed: {name}")
    return passed


def database_size_bytes(connection: Any) -> int:
    row = connection.execute(
        """
        SELECT COALESCE(SUM(pg_total_relation_size(c.oid)), 0)::bigint
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'relational_cmp'
          AND c.relkind IN ('r','i','m','t')
        """
    ).fetchone()
    return int(row[0])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("ENG197_POSTGRES_DSN"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.dsn:
        raise RuntimeError("ENG197_POSTGRES_DSN or --dsn is required")

    runtime = load(RUNTIME)
    expected_server = runtime["postgresql"]
    require(psycopg.__version__ == runtime["python"]["psycopg"]["version"], "psycopg version drift")

    source = load(SOURCE)
    eligibility = evaluate_source(source)
    require(eligibility["eligible"] is True, f"prototype source is relational-ineligible: {eligibility}")

    expected_freeze = build_freeze_manifest()
    actual_freeze = load(FREEZE)
    require(actual_freeze == expected_freeze, "ENG-197 freeze manifest drift before PostgreSQL smoke")

    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError("smoke output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    pre_score_dir = output / "pre-score"

    registry = load(REGISTRY)["entries"]
    expected = {row["case_id"]: row for row in load(EXPECTED)["cases"]}
    report: dict[str, Any] = {
        "schema_version": "1.0.0",
        "linear_issue": "ENG-197",
        "evidence_class": "TRAIN_DEV_LIVE_POSTGRESQL_NOT_MODEL_EFFECT",
        "status": "RUNNING",
        "subset_eligibility": eligibility,
        "runtime": {},
        "hashes": {},
        "cases": [],
        "security_negatives": {},
        "measurements": {},
    }

    with psycopg.connect(args.dsn, autocommit=True) as connection:
        db_name = connection.execute("SELECT current_database()").fetchone()[0]
        require(str(db_name).startswith(expected_server["database_name_prefix"]), "refusing non-disposable database name")

        server_version = connection.execute("SHOW server_version").fetchone()[0]
        server_version_num = int(connection.execute("SHOW server_version_num").fetchone()[0])
        version_string = connection.execute("SELECT version()").fetchone()[0]
        require(server_version == expected_server["required_server_version"], f"PostgreSQL server_version drift: {server_version}")
        require(server_version_num == expected_server["required_server_version_num"], f"PostgreSQL server_version_num drift: {server_version_num}")

        image_digest = os.environ.get("ENG197_POSTGRES_IMAGE_DIGEST")
        execution_identity = "container_digest_pinned" if image_digest else "native_exact_version_not_image_pinned"
        report["runtime"] = {
            "database_name": db_name,
            "postgresql_version_string": version_string,
            "server_version": server_version,
            "server_version_num": server_version_num,
            "psycopg_version": psycopg.__version__,
            "libpq_version": psycopg.pq.version(),
            "execution_identity": execution_identity,
            "container_image_digest": image_digest,
        }

        connection.execute("SELECT pg_advisory_lock(%s)", (ADVISORY_LOCK,))
        try:
            build_started = time.perf_counter_ns()
            connection.execute("DROP SCHEMA IF EXISTS relational_cmp CASCADE")
            execute_script(connection, GENERATED / "schema.sql")
            execute_script(connection, GENERATED / "seed.sql")
            execute_script(connection, GENERATED / "permissions.sql")
            build_ns = time.perf_counter_ns() - build_started

            connection.execute("SET statement_timeout = '5s'")
            connection.execute("SET ROLE relational_cmp_reader")

            adapter_negatives = assert_adapter_negatives()
            db_denials = assert_db_write_denials(connection)

            # Execute and persist every actual DB result before opening evaluator expectations.
            raw_results: dict[str, dict[str, Any]] = {}
            pre_score_hashes: dict[str, str] = {}
            for entry in registry:
                case_id = entry["case_id"]
                row, pre_score = execute_typed_call(connection, entry["call"])
                artifact_path = pre_score_dir / f"{case_id}.json"
                pre_score_hashes[case_id] = persist_pre_score_record(artifact_path, pre_score)
                raw_results[case_id] = row
                report["cases"].append({
                    "case_id": case_id,
                    "db_latency_ns": pre_score["db_latency_ns"],
                    "pre_score_artifact": str(artifact_path.relative_to(output)).replace("\\", "/"),
                    "pre_score_sha256": pre_score_hashes[case_id],
                    "result_sha256": pre_score["result_sha256"],
                    "evaluation": "NOT_OPENED_YET",
                })

            # Only after all DB result artifacts exist do we consult evaluator-only expectations.
            for case_report in report["cases"]:
                case_id = case_report["case_id"]
                want = expected[case_id]
                got = raw_results[case_id]
                require(got["status_code"] == want["expected_status"], f"live DB status mismatch: {case_id}")
                require(got["action_code"] == want["expected_action"], f"live DB action mismatch: {case_id}")
                case_report["evaluation"] = "PASS"

            require(raw_results["proto-01"]["status_code"] == "supported", "recursive positive closure did not support proto-01")
            require(raw_results["proto-01"]["evidence"] == ["a-001"], "recursive closure root evidence drift")
            require(raw_results["proto-01"]["provenance"] == ["src-spec-001"], "recursive closure provenance drift")
            require({raw_results[k]["status_code"] for k in raw_results} == {"supported", "refuted", "conflicting", "unknown"}, "four-state live DB coverage incomplete")

            connection.execute("RESET ROLE")
            db_bytes = database_size_bytes(connection)
        finally:
            try:
                connection.execute("RESET ROLE")
            except Exception:
                pass
            connection.execute("SELECT pg_advisory_unlock(%s)", (ADVISORY_LOCK,))

    latencies = [case["db_latency_ns"] for case in report["cases"]]
    generated_files = [p for p in GENERATED.iterdir() if p.is_file()]
    report["security_negatives"] = {
        "adapter": adapter_negatives,
        "database_read_only_role": db_denials,
        "all_passed": True,
    }
    report["measurements"] = {
        "database_build_ns": build_ns,
        "db_call_latency_ns_min": min(latencies),
        "db_call_latency_ns_median": int(statistics.median(latencies)),
        "db_call_latency_ns_max": max(latencies),
        "database_relation_index_bytes": db_bytes,
        "generated_package_bytes": sum(p.stat().st_size for p in generated_files),
        "pre_score_artifact_count": len(report["cases"]),
    }
    report["hashes"] = {
        "freeze_manifest_sha256": sha256_file(FREEZE),
        "source_sha256": sha256_file(SOURCE),
        "query_registry_sha256": sha256_file(REGISTRY),
        "evaluator_expected_sha256": sha256_file(EXPECTED),
        "schema_sql_sha256": sha256_file(GENERATED / "schema.sql"),
        "seed_sql_sha256": sha256_file(GENERATED / "seed.sql"),
        "permissions_sql_sha256": sha256_file(GENERATED / "permissions.sql"),
        "package_manifest_sha256": sha256_file(GENERATED / "package-manifest.json"),
    }
    report["status"] = "PASS"

    report_path = output / "eng197-live-postgres-report.json"
    report_path.write_bytes(canonical_json_bytes(report))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
