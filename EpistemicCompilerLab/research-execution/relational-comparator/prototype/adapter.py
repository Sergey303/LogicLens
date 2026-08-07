from __future__ import annotations

import hashlib
import json
from typing import Any

ENDPOINT = "resolve_claim"
ARGUMENTS = ("proposition_id", "scope_id", "version")
QUERY = "SELECT * FROM relational_cmp.resolve_claim(%s, %s, %s);"
STATUS = {"supported", "refuted", "unknown", "conflicting"}
ACTION = {"accept", "reject", "review"}


class ContractError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def validate_call(call: dict[str, Any]) -> tuple[str, tuple[str, str, str]]:
    if set(call) != {"endpoint", "arguments"}:
        raise ContractError("call must contain endpoint and arguments only")
    if call["endpoint"] != ENDPOINT:
        raise ContractError("undeclared endpoint")
    args = call["arguments"]
    if not isinstance(args, dict) or set(args) != set(ARGUMENTS):
        raise ContractError("arguments do not match declared endpoint")
    values: list[str] = []
    for name in ARGUMENTS:
        value = args[name]
        if not isinstance(value, str) or not value or len(value) > 128:
            raise ContractError(f"invalid {name}")
        values.append(value)
    return QUERY, tuple(values)  # type: ignore[return-value]


def validate_result_rows(rows: list[dict[str, Any]], maximum_rows: int = 1) -> dict[str, Any]:
    if len(rows) != maximum_rows:
        raise ContractError("result row count violates frozen one-row policy")
    row = rows[0]
    if set(row) != {"status_code", "action_code", "evidence", "provenance"}:
        raise ContractError("result columns do not match frozen schema")
    if row["status_code"] not in STATUS or row["action_code"] not in ACTION:
        raise ContractError("invalid status/action code")
    for field in ("evidence", "provenance"):
        value = row[field]
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ContractError(f"invalid {field}")
        if len(value) != len(set(value)):
            raise ContractError(f"duplicate {field}")
    return row


def make_pre_score_record(call: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    validate_call(call)
    row = validate_result_rows(rows)
    call_bytes = canonical_json_bytes(call)
    result_bytes = canonical_json_bytes(row)
    return {
        "stage": "pre_score",
        "call_sha256": hashlib.sha256(call_bytes).hexdigest(),
        "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
        "call_bytes_utf8": call_bytes.decode("utf-8"),
        "result_bytes_utf8": result_bytes.decode("utf-8"),
        "provenance": list(row["provenance"]),
        "score": None,
    }
