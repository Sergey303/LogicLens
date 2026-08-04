#!/usr/bin/env python3
"""Query a verified LogicLens capsule package with strict open-world semantics."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from capsule import (
    CapsuleError,
    canonical_json,
    json_lines,
    json_object,
    schema_check,
    verify_package,
)

UTF8 = "utf-8"
QUERY_DOMAIN = b"LogicLensCapsuleQuery\0"
SUPPORTED_OPERATION = "strict-claim"
STATUS_POLICY = {
    "supported": (
        "answer_with_source_scope",
        "loaded_evidence_supports_claim",
    ),
    "refuted": (
        "explain_explicit_role_boundary",
        "loaded_evidence_explicitly_opposes_claim",
    ),
    "unknown": (
        "abstain_and_request_context",
        "insufficient_loaded_evidence",
    ),
    "conflicting": (
        "report_conflict_and_compare_models",
        "incompatible_loaded_assertions",
    ),
}


class CapsuleQueryError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contracts-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "contracts",
    )
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument(
        "--request",
        required=True,
        help="JSON request path, or '-' to read one JSON object from stdin.",
    )
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--timeout-seconds", type=int, default=15)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    if args.timeout_seconds < 1 or args.timeout_seconds > 300:
        raise CapsuleQueryError(
            "invalid_timeout",
            "timeout must be between 1 and 300 seconds",
        )
    request = read_request(args.request)
    request_schema = json_object(
        args.contracts_root / "capsule-query-v0.schema.json",
        "capsule query schema",
    )
    schema_check(request, request_schema, "capsule query")
    result = query_package(
        package_root=args.package,
        request=request,
        swipl=args.swipl,
        timeout_seconds=args.timeout_seconds,
    )
    result_schema = json_object(
        args.contracts_root / "capsule-query-result-v0.schema.json",
        "capsule query result schema",
    )
    schema_check(result, result_schema, "capsule query result")
    write_result(result, args.output, args.pretty)
    return 0


def query_package(
    *,
    package_root: Path,
    request: dict[str, Any],
    swipl: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    package = verify_package(package_root)
    root = package_root.resolve()
    files_root = root / "files"
    world = json_object(files_root / "world" / "world.json", "packaged world")
    capsule = json_object(
        files_root / "capsule" / "capsule.json",
        "packaged capsule",
    )
    if request.get("operation") != SUPPORTED_OPERATION:
        raise CapsuleQueryError(
            "unsupported_operation",
            f"unsupported query operation: {request.get('operation')!r}",
        )

    predicates = load_predicates(files_root, world)
    target = request["target"]
    predicate_id = target["predicate"]
    predicate = predicates.get(predicate_id)
    if predicate is None:
        raise CapsuleQueryError(
            "unknown_predicate",
            f"predicate is not declared by the packaged world: {predicate_id}",
        )
    if predicate.get("valueSpace") != "strict_claim":
        raise CapsuleQueryError(
            "unsupported_value_space",
            f"predicate {predicate_id} is not a strict_claim predicate",
        )
    if predicate.get("world") != "open":
        raise CapsuleQueryError(
            "unsupported_world_semantics",
            f"predicate {predicate_id} does not declare an open world",
        )
    if predicate.get("negation") != "explicit_evidence":
        raise CapsuleQueryError(
            "unsupported_negation_semantics",
            f"predicate {predicate_id} does not use explicit evidence negation",
        )
    declared_arguments = predicate.get("arguments")
    if not isinstance(declared_arguments, list):
        raise CapsuleQueryError(
            "invalid_semantic_model",
            f"predicate {predicate_id} has no argument declaration",
        )
    supplied_arguments = target["arguments"]
    if len(supplied_arguments) != len(declared_arguments):
        raise CapsuleQueryError(
            "arity_mismatch",
            f"predicate {predicate_id} expects {len(declared_arguments)} arguments, "
            f"received {len(supplied_arguments)}",
        )

    semantic_ids = load_semantic_ids(files_root, world)
    for index, (value, declaration) in enumerate(
        zip(supplied_arguments, declared_arguments, strict=True),
        1,
    ):
        expected_type = declaration.get("type")
        validate_argument(
            value=value,
            expected_type=expected_type,
            semantic_ids=semantic_ids,
            position=index,
            predicate_id=predicate_id,
        )

    assertions = load_assertions(files_root, capsule)
    matching = [row for row in assertions if row.get("target") == target]
    support = sorted(
        (row for row in matching if row.get("stance") == "support"),
        key=lambda row: row["assertionId"],
    )
    oppose = sorted(
        (row for row in matching if row.get("stance") == "oppose"),
        key=lambda row: row["assertionId"],
    )
    python_status = strict_status(support, oppose)

    prolog = run_prolog_query(
        generated_assertions=files_root / "generated" / "assertions.pl",
        target=target,
        swipl=swipl,
        timeout_seconds=timeout_seconds,
    )
    expected_support = [row["assertionId"] for row in support]
    expected_oppose = [row["assertionId"] for row in oppose]
    if (
        prolog.get("status") != python_status
        or prolog.get("support") != expected_support
        or prolog.get("oppose") != expected_oppose
    ):
        raise CapsuleQueryError(
            "runtime_mismatch",
            "SWI-Prolog result does not match packaged assertion metadata",
        )

    sources = load_sources(files_root, capsule)
    action, reason = STATUS_POLICY[python_status]
    evidence = {
        "support": [evidence_record(row, sources) for row in support],
        "oppose": [evidence_record(row, sources) for row in oppose],
    }
    dependency_groups = sorted(
        {row["dependencyGroup"] for row in support + oppose}
    )
    warnings = build_warnings(python_status, support + oppose)
    predicate_frame = {
        "id": predicate_id,
        "valueSpace": predicate["valueSpace"],
        "world": predicate["world"],
        "negation": predicate["negation"],
        "argumentTypes": [item["type"] for item in declared_arguments],
    }
    return {
        "schemaVersion": "0.1",
        "queryHash": query_hash(request),
        "package": {
            "worldId": package["world"]["id"],
            "capsuleId": package["capsule"]["id"],
            "capsuleVersion": package["capsule"]["version"],
            "packageHash": package["packageHash"],
        },
        "query": request,
        "predicate": predicate_frame,
        "status": python_status,
        "action": action,
        "reason": reason,
        "evidence": evidence,
        "dependencyGroups": dependency_groups,
        "warnings": warnings,
        "runtime": {
            "engine": "swi-prolog",
            "semantics": "strict-support-oppose-open-world",
            "verifiedAgainstGeneratedAssertions": True,
        },
    }


def read_request(value: str) -> dict[str, Any]:
    try:
        if value == "-":
            payload = json.load(sys.stdin)
        else:
            payload = json.loads(Path(value).read_text(encoding=UTF8))
    except (OSError, json.JSONDecodeError) as exc:
        raise CapsuleQueryError("invalid_request_json", str(exc)) from exc
    if not isinstance(payload, dict):
        raise CapsuleQueryError(
            "invalid_request_json",
            "query request must be a JSON object",
        )
    return payload


def write_result(
    result: dict[str, Any],
    output: Path | None,
    pretty: bool,
) -> None:
    if pretty:
        content = (
            json.dumps(
                result,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
                allow_nan=False,
            )
            + "\n"
        ).encode(UTF8)
    else:
        content = canonical_json(result)
    if output is None:
        sys.stdout.buffer.write(content)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(content)


def load_predicates(
    files_root: Path,
    world: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    relative = world.get("semantic", {}).get("predicates")
    if not isinstance(relative, str):
        raise CapsuleQueryError(
            "invalid_semantic_model",
            "world semantic model does not declare predicates",
        )
    document = json_object(
        files_root / "world" / relative,
        "packaged predicates",
    )
    records = document.get("predicates")
    if not isinstance(records, list):
        raise CapsuleQueryError(
            "invalid_semantic_model",
            "predicate document does not contain a predicates array",
        )
    result: dict[str, dict[str, Any]] = {}
    for item in records:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise CapsuleQueryError(
                "invalid_semantic_model",
                "invalid predicate declaration",
            )
        identifier = item["id"]
        if identifier in result:
            raise CapsuleQueryError(
                "invalid_semantic_model",
                f"duplicate predicate ID: {identifier}",
            )
        result[identifier] = item
    return result


def load_semantic_ids(
    files_root: Path,
    world: dict[str, Any],
) -> dict[str, set[str]]:
    registry: dict[str, set[str]] = {}
    semantic = world.get("semantic")
    if not isinstance(semantic, dict):
        raise CapsuleQueryError(
            "invalid_semantic_model",
            "world semantic declaration is missing",
        )
    for key, relative in semantic.items():
        if key == "predicates":
            continue
        if not isinstance(relative, str):
            raise CapsuleQueryError(
                "invalid_semantic_model",
                f"invalid semantic path for {key}",
            )
        document = json_object(
            files_root / "world" / relative,
            f"packaged semantic file {key}",
        )
        for collection_name, records in document.items():
            if collection_name == "schemaVersion" or not isinstance(records, list):
                continue
            default_type = singular(collection_name)
            for item in records:
                if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                    continue
                identifier = item["id"]
                registry.setdefault(default_type, set()).add(identifier)
                kind = item.get("kind")
                if isinstance(kind, str):
                    registry.setdefault(kind, set()).add(identifier)
    return registry


def singular(value: str) -> str:
    if value.endswith("ies") and len(value) > 3:
        return value[:-3] + "y"
    if value.endswith("s") and len(value) > 1:
        return value[:-1]
    return value


def validate_argument(
    *,
    value: Any,
    expected_type: Any,
    semantic_ids: dict[str, set[str]],
    position: int,
    predicate_id: str,
) -> None:
    if not isinstance(expected_type, str):
        raise CapsuleQueryError(
            "invalid_semantic_model",
            f"predicate {predicate_id} argument {position} has no type",
        )
    if expected_type == "string":
        valid = isinstance(value, str)
    elif expected_type == "integer":
        valid = isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "boolean":
        valid = isinstance(value, bool)
    else:
        allowed = semantic_ids.get(expected_type)
        if allowed is None:
            raise CapsuleQueryError(
                "unresolved_semantic_type",
                f"semantic type {expected_type!r} has no declared identifiers",
            )
        valid = isinstance(value, str) and value in allowed
    if not valid:
        raise CapsuleQueryError(
            "argument_type_mismatch",
            f"predicate {predicate_id} argument {position} is not a declared "
            f"{expected_type}: {value!r}",
        )


def load_assertions(
    files_root: Path,
    capsule: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in capsule.get("preparedFiles", []):
        if entry.get("kind") == "assertions":
            relative = entry.get("path")
            if not isinstance(relative, str):
                raise CapsuleQueryError(
                    "invalid_capsule_manifest",
                    "assertion file path is invalid",
                )
            rows.extend(
                json_lines(
                    files_root / "capsule" / relative,
                    f"packaged assertions {relative}",
                )
            )
    if not rows:
        raise CapsuleQueryError(
            "missing_assertions",
            "capsule package contains no prepared assertions",
        )
    identifiers = [row.get("assertionId") for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise CapsuleQueryError(
            "duplicate_assertion",
            "capsule package contains duplicate assertion IDs",
        )
    return rows


def load_sources(
    files_root: Path,
    capsule: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    relative = capsule.get("sourceManifest")
    if not isinstance(relative, str):
        raise CapsuleQueryError(
            "invalid_capsule_manifest",
            "capsule source manifest path is invalid",
        )
    document = json_object(
        files_root / "capsule" / relative,
        "packaged source manifest",
    )
    records = document.get("sources")
    if not isinstance(records, list):
        raise CapsuleQueryError(
            "invalid_capsule_manifest",
            "source manifest contains no sources array",
        )
    result: dict[str, dict[str, Any]] = {}
    for item in records:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            result[item["id"]] = item
    return result


def strict_status(
    support: list[dict[str, Any]],
    oppose: list[dict[str, Any]],
) -> str:
    if support and oppose:
        return "conflicting"
    if support:
        return "supported"
    if oppose:
        return "refuted"
    return "unknown"


def run_prolog_query(
    *,
    generated_assertions: Path,
    target: dict[str, Any],
    swipl: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    if not generated_assertions.is_file():
        raise CapsuleQueryError(
            "missing_generated_assertions",
            "capsule package has no generated assertions.pl",
        )
    target_term = prolog_target(target)
    assertions_path = prolog_atom(generated_assertions.resolve().as_posix())
    program = f""":- use_module(library(http/json)).
:- use_module({assertions_path}).

main :-
    Target = {target_term},
    findall(Id, capsule_assertions:prepared_assertion(Id, Target, support, _, _, _), Support0),
    sort(Support0, Support),
    findall(Id, capsule_assertions:prepared_assertion(Id, Target, oppose, _, _, _), Oppose0),
    sort(Oppose0, Oppose),
    ( Support \\= [], Oppose \\= [] -> Status = conflicting
    ; Support \\= [] -> Status = supported
    ; Oppose \\= [] -> Status = refuted
    ; Status = unknown
    ),
    json_write_dict(current_output, _{{status:Status, support:Support, oppose:Oppose}}, [width(0)]),
    nl.

:- initialization(main, main).
"""
    try:
        with tempfile.TemporaryDirectory(prefix="capsule-query-") as temporary:
            runner = Path(temporary) / "query.pl"
            runner.write_text(program, encoding=UTF8, newline="\n")
            completed = subprocess.run(
                [swipl, "-q", "-f", str(runner)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
                check=False,
            )
    except FileNotFoundError as exc:
        raise CapsuleQueryError(
            "swipl_not_found",
            f"SWI-Prolog executable was not found: {swipl}",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise CapsuleQueryError(
            "swipl_timeout",
            "SWI-Prolog query timed out",
        ) from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise CapsuleQueryError(
            "swipl_failed",
            f"SWI-Prolog query failed: {detail}",
        )
    try:
        payload = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise CapsuleQueryError(
            "invalid_swipl_output",
            "SWI-Prolog did not return one valid JSON object",
        ) from exc
    if not isinstance(payload, dict):
        raise CapsuleQueryError(
            "invalid_swipl_output",
            "SWI-Prolog result is not a JSON object",
        )
    payload["support"] = sorted(payload.get("support", []))
    payload["oppose"] = sorted(payload.get("oppose", []))
    return payload


def prolog_target(target: dict[str, Any]) -> str:
    predicate = prolog_atom(target["predicate"])
    arguments = ", ".join(prolog_value(value) for value in target["arguments"])
    return f"{predicate}({arguments})"


def prolog_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return prolog_atom(value)
    raise CapsuleQueryError(
        "unsupported_argument_value",
        f"unsupported Prolog value: {value!r}",
    )


def prolog_atom(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def evidence_record(
    row: dict[str, Any],
    sources: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    summaries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for provenance in row["provenance"]:
        source_id = provenance.split("#", 1)[0]
        if source_id in seen:
            continue
        seen.add(source_id)
        source = sources.get(source_id)
        if source is None:
            raise CapsuleQueryError(
                "missing_source",
                f"assertion {row['assertionId']} references missing source {source_id}",
            )
        summaries.append(source_summary(source))
    result: dict[str, Any] = {
        "assertionId": row["assertionId"],
        "stance": row["stance"],
        "dependencyGroup": row["dependencyGroup"],
        "provenance": row["provenance"],
        "sources": sorted(summaries, key=lambda item: item["id"]),
        "generalisability": row["generalisability"],
    }
    if isinstance(row.get("scope"), dict):
        result["scope"] = row["scope"]
    if isinstance(row.get("note"), str):
        result["note"] = row["note"]
    return result


def source_summary(source: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "id": source["id"],
        "kind": source["kind"],
        "title": source["title"],
        "locator": source["locator"],
    }
    for key in ("version", "language"):
        if isinstance(source.get(key), str):
            summary[key] = source[key]
    license_value = source.get("license")
    if isinstance(license_value, dict):
        if isinstance(license_value.get("id"), str):
            summary["licenseId"] = license_value["id"]
        if isinstance(license_value.get("status"), str):
            summary["licenseStatus"] = license_value["status"]
    return summary


def build_warnings(
    status: str,
    rows: list[dict[str, Any]],
) -> list[str]:
    warnings: set[str] = set()
    if status == "unknown":
        warnings.add("insufficient-loaded-evidence")
    if status == "conflicting":
        warnings.add("incompatible-loaded-assertions")
    for row in rows:
        generalisability = row.get("generalisability")
        if generalisability == "context-dependent":
            warnings.add("context-dependent")
        elif generalisability == "local":
            warnings.add("local-only")
    return sorted(warnings)


def query_hash(request: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        QUERY_DOMAIN + bytes((1,)) + canonical_json(request)
    )
    return "sha256:" + digest.hexdigest()


def error_payload(exc: BaseException) -> bytes:
    code = exc.code if isinstance(exc, CapsuleQueryError) else "query_failed"
    return canonical_json(
        {
            "schemaVersion": "0.1",
            "error": {
                "code": code,
                "message": str(exc),
            },
        }
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        CapsuleError,
        CapsuleQueryError,
        OSError,
        ValueError,
    ) as exc:
        sys.stderr.buffer.write(error_payload(exc))
        raise SystemExit(1) from exc
