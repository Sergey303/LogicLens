import json
from pathlib import Path

from program import PROGRAM_VERSION, interval_threshold, strict_status, threshold_relation

API = json.loads((Path(__file__).parent / "tool_api.json").read_text(encoding="utf-8"))

_HANDLE_TO_IMPL = {
    "py_cap_01": strict_status,
    "py_cap_02": threshold_relation,
    "py_cap_03": interval_threshold,
}
_KIND_TO_HANDLE = {
    "evidence_status": "py_cap_01",
    "threshold_relation": "py_cap_02",
    "interval_threshold": "py_cap_03",
}
_ALLOWED_ARGS = {
    "py_cap_01": ("positive_evidence", "negative_evidence"),
    "py_cap_02": ("value", "threshold"),
    "py_cap_03": ("lower", "upper", "threshold"),
}


def m21_map(public_request):
    kind = public_request.get("kind")
    if kind not in _KIND_TO_HANDLE:
        raise ValueError("contract_violation")
    handle = _KIND_TO_HANDLE[kind]
    arguments = {name: public_request[name] for name in _ALLOWED_ARGS[handle]}
    return handle, arguments


def execute(handle, arguments, provenance):
    if PROGRAM_VERSION != API["program_version"]:
        raise ValueError("contract_violation")
    if handle not in _HANDLE_TO_IMPL:
        raise ValueError("contract_violation")
    expected = set(_ALLOWED_ARGS[handle])
    if set(arguments) != expected:
        raise ValueError("invalid_arguments")
    if not provenance or not all(isinstance(item, str) and item for item in provenance):
        raise ValueError("contract_violation")
    raw = _HANDLE_TO_IMPL[handle](**arguments)
    result = {
        "capability_handle": handle,
        "status": raw["status"],
        "value": raw["value"],
        "provenance": list(provenance),
    }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(encoded) > API["limits"]["max_result_bytes"]:
        raise ValueError("budget_exceeded")
    return result


def qwen_visible_payload(mode, question, result):
    if mode not in {"M21", "M22"}:
        raise ValueError("contract_violation")
    return {
        "mode": mode,
        "question": question,
        "capabilities": [
            {k: cap[k] for k in ("handle", "name", "description", "arguments", "result")}
            for cap in API["capabilities"]
        ],
        "execution_result": result,
        "response_schema_id": "eng201.student-response.v1",
    }
