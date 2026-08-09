from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from adapter import canonical_json_bytes, validate_call, validate_result_rows


def _normalize_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        row = dict(row)
    normalized = {
        "status_code": row["status_code"],
        "action_code": row["action_code"],
        "evidence": list(row["evidence"] or []),
        "provenance": list(row["provenance"] or []),
    }
    return validate_result_rows([normalized])


def execute_typed_call(connection: Any, call: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute the exact constant parameterized adapter query against PostgreSQL.

    No semantic fallback exists here. In particular this function never imports
    or calls the Python reference oracle.
    """
    query, params = validate_call(call)
    started = time.perf_counter_ns()
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        description = [column.name for column in cursor.description]
        raw_rows = cursor.fetchall()
    latency_ns = time.perf_counter_ns() - started

    if description != ["status_code", "action_code", "evidence", "provenance"]:
        raise RuntimeError(f"database result column drift: {description}")
    rows = [dict(zip(description, row, strict=True)) for row in raw_rows]
    normalized = _normalize_row(rows[0]) if len(rows) == 1 else validate_result_rows(rows)

    call_bytes = canonical_json_bytes(call)
    result_bytes = canonical_json_bytes(normalized)
    pre_score = {
        "schema_version": "1.0.0",
        "stage": "pre_score_db_result",
        "execution_owner": "postgresql",
        "call_sha256": hashlib.sha256(call_bytes).hexdigest(),
        "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
        "call_bytes_utf8": call_bytes.decode("utf-8"),
        "result_bytes_utf8": result_bytes.decode("utf-8"),
        "provenance": list(normalized["provenance"]),
        "db_latency_ns": latency_ns,
        "score": None,
    }
    return normalized, pre_score


def persist_pre_score_record(path: Path, record: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(record)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()
