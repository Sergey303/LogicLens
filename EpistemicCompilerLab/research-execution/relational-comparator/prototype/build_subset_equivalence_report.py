from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from adapter import canonical_json_bytes, validate_call, validate_result_rows
from reference_oracle import resolve
from subset_eligibility import evaluate_source

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source.prototype.json"
REGISTRY = ROOT / "query-registry.prototype.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-output", type=Path, required=True)
    args = parser.parse_args()
    output = args.smoke_output.resolve()
    smoke_report_path = output / "eng197-live-postgres-report.json"
    smoke = load(smoke_report_path)
    require(smoke.get("status") == "PASS", "live PostgreSQL report is not PASS")

    source = load(SOURCE)
    eligibility = evaluate_source(source)
    require(eligibility == {"eligible": True, "reason_codes": []}, "source is not losslessly relational-eligible")

    registry = load(REGISTRY)["entries"]
    rows = []
    for entry in registry:
        case_id = entry["case_id"]
        _, params = validate_call(entry["call"])
        reference = validate_result_rows([resolve(source, *params)])

        pre_score_path = output / "pre-score" / f"{case_id}.json"
        pre_score = load(pre_score_path)
        require(pre_score["stage"] == "pre_score_db_result", f"not DB pre-score evidence: {case_id}")
        require(pre_score["score"] is None, f"score leaked into DB record: {case_id}")
        db_result = json.loads(pre_score["result_bytes_utf8"])
        db_result = validate_result_rows([db_result])

        exact = reference == db_result
        require(exact, f"direct-source/DB semantic mismatch: {case_id}")
        rows.append({
            "case_id": case_id,
            "reference_result_sha256": hashlib.sha256(canonical_json_bytes(reference)).hexdigest(),
            "db_result_sha256": hashlib.sha256(canonical_json_bytes(db_result)).hexdigest(),
            "status_equal": reference["status_code"] == db_result["status_code"],
            "action_equal": reference["action_code"] == db_result["action_code"],
            "evidence_equal": reference["evidence"] == db_result["evidence"],
            "provenance_equal": reference["provenance"] == db_result["provenance"],
            "exact_result_equal": exact,
        })

    report = {
        "schema_version": "1.0.0",
        "linear_issue": "ENG-197",
        "contract_id": "eng197.relational-subset.v1",
        "scope": "TRAIN_DEV_ONLY_SYNTHETIC",
        "live_postgres_report_sha256": sha256_file(smoke_report_path),
        "source_sha256": sha256_file(SOURCE),
        "query_registry_sha256": sha256_file(REGISTRY),
        "eligible": True,
        "cases": rows,
        "exact_case_count": sum(1 for row in rows if row["exact_result_equal"]),
        "case_count": len(rows),
        "all_exact": all(row["exact_result_equal"] for row in rows),
        "proof_graph_equivalence_claimed": False,
        "interpretation": "lossless equality is asserted only for the frozen relational subset result fields status/action/root-evidence/source-provenance; M6 full proof-frame visibility is not matched",
    }
    require(report["all_exact"] is True, "subset equivalence report contains mismatch")
    report_path = output / "eng197-subset-equivalence-report.json"
    report_path.write_bytes(canonical_json_bytes(report))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
