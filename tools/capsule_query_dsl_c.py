#!/usr/bin/env python3
"""Query verified LogicLens typed observations with deterministic interval semantics."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from decimal import Decimal, InvalidOperation
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
from capsule_query import (
    CapsuleQueryError,
    load_semantic_ids,
    load_sources,
    read_request,
    write_result,
)

UTF8 = "utf-8"
QUERY_DOMAIN = b"LogicLensCapsuleQueryDslC\0"
SUPPORTED_OPERATIONS = {"observation", "numeric-comparison"}

UNITS: dict[str, tuple[str, Decimal, str]] = {
    "millisecond": ("duration", Decimal("0.001"), "second"),
    "second": ("duration", Decimal("1"), "second"),
    "minute": ("duration", Decimal("60"), "second"),
    "hour": ("duration", Decimal("3600"), "second"),
    "day": ("duration", Decimal("86400"), "second"),
    "fraction": ("ratio", Decimal("1"), "fraction"),
    "percent": ("ratio", Decimal("0.01"), "fraction"),
    "count": ("count", Decimal("1"), "count"),
}

TARGET_TYPES = {
    "metric": "management_metric",
    "subject": "measurement_subject",
    "window": "time_window",
}

STATUS_POLICY = {
    "observed": ("report_observation", "typed_observation_loaded"),
    "supported": (
        "answer_with_measurement_scope",
        "entire_observation_supports_comparison",
    ),
    "refuted": (
        "explain_threshold_miss",
        "entire_observation_refutes_comparison",
    ),
}


class DslCError(CapsuleQueryError):
    pass


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
        raise DslCError(
            "invalid_timeout",
            "timeout must be between 1 and 300 seconds",
        )
    request = read_request(args.request)
    request_schema = json_object(
        args.contracts_root / "capsule-query-dsl-c-v0.schema.json",
        "DSL-C query schema",
    )
    schema_check(request, request_schema, "DSL-C query")
    result = query_package(
        package_root=args.package,
        request=request,
        contracts_root=args.contracts_root,
        swipl=args.swipl,
        timeout_seconds=args.timeout_seconds,
    )
    result_schema = json_object(
        args.contracts_root / "capsule-query-dsl-c-result-v0.schema.json",
        "DSL-C query result schema",
    )
    schema_check(result, result_schema, "DSL-C query result")
    write_result(result, args.output, args.pretty)
    return 0


def query_package(
    *,
    package_root: Path,
    request: dict[str, Any],
    contracts_root: Path,
    swipl: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    package = verify_package(package_root)
    files_root = package_root.resolve() / "files"
    world = json_object(files_root / "world" / "world.json", "packaged world")
    capsule = json_object(
        files_root / "capsule" / "capsule.json",
        "packaged capsule",
    )

    operation = request.get("operation")
    if operation not in SUPPORTED_OPERATIONS:
        raise DslCError(
            "unsupported_operation",
            f"unsupported DSL-C operation: {operation!r}",
        )

    validate_target(request["target"], files_root, world)
    sources = load_sources(files_root, capsule)
    observations = load_observations(
        files_root=files_root,
        capsule=capsule,
        contracts_root=contracts_root,
        sources=sources,
    )
    observation = observations.get(target_key(request["target"]))

    package_frame = {
        "worldId": package["world"]["id"],
        "capsuleId": package["capsule"]["id"],
        "capsuleVersion": package["capsule"]["version"],
        "packageHash": package["packageHash"],
    }

    if observation is None:
        prolog_status = run_prolog_kernel(
            model=None,
            comparison=request.get("comparison"),
            expected_operation=operation,
            swipl=swipl,
            timeout_seconds=timeout_seconds,
        )
        if prolog_status != "unknown":
            raise DslCError(
                "runtime_mismatch",
                "SWI-Prolog missing-observation result does not match Python",
            )
        return {
            "schemaVersion": "0.1",
            "dslLevel": "DSL-C",
            "queryHash": query_hash(request),
            "package": package_frame,
            "query": request,
            "observation": None,
            "normalized": None,
            "status": "unknown",
            "action": "abstain_on_numeric_decision",
            "reason": "observation_not_loaded",
            "comparison": None,
            "provenance": [],
            "dependencyGroups": [],
            "warnings": ["missing-observation"],
            "runtime": runtime_frame(),
        }

    normalized = normalize_model(observation["model"])
    result_observation = {
        "observationId": observation["observationId"],
        "target": observation["target"],
        "model": observation["model"],
        "dependencyGroup": observation["dependencyGroup"],
        "generalisability": observation["generalisability"],
        "scope": observation.get("scope", {}),
    }
    provenance = [
        source_record(reference, sources)
        for reference in observation["provenance"]
    ]
    warnings = base_warnings(observation, normalized)

    if operation == "observation":
        prolog_status = run_prolog_kernel(
            model=normalized,
            comparison=None,
            expected_operation=operation,
            swipl=swipl,
            timeout_seconds=timeout_seconds,
        )
        if prolog_status != "observed":
            raise DslCError(
                "runtime_mismatch",
                "SWI-Prolog observation result does not match Python",
            )
        action, reason = STATUS_POLICY["observed"]
        return {
            "schemaVersion": "0.1",
            "dslLevel": "DSL-C",
            "queryHash": query_hash(request),
            "package": package_frame,
            "query": request,
            "observation": result_observation,
            "normalized": normalized,
            "status": "observed",
            "action": action,
            "reason": reason,
            "comparison": None,
            "provenance": provenance,
            "dependencyGroups": [observation["dependencyGroup"]],
            "warnings": sorted(warnings),
            "runtime": runtime_frame(),
        }

    comparison = normalize_comparison(request["comparison"])
    if comparison["dimension"] != normalized["dimension"]:
        raise DslCError(
            "unit_dimension_mismatch",
            f"observation dimension {normalized['dimension']} does not match "
            f"comparison dimension {comparison['dimension']}",
        )

    status, reason = compare_normalized(normalized, comparison)
    comparison_result = {
        "operator": comparison["operator"],
        "dimension": comparison["dimension"],
        "baseUnit": comparison["baseUnit"],
        "status": status,
        "normalizedThreshold": comparison["normalizedThreshold"],
    }
    prolog_status = run_prolog_kernel(
        model=normalized,
        comparison=comparison,
        expected_operation=operation,
        swipl=swipl,
        timeout_seconds=timeout_seconds,
    )
    if prolog_status != status:
        raise DslCError(
            "runtime_mismatch",
            f"SWI-Prolog status {prolog_status!r} does not match Python {status!r}",
        )

    if status in STATUS_POLICY:
        action, default_reason = STATUS_POLICY[status]
        if not reason:
            reason = default_reason
    else:
        action = "abstain_on_numeric_decision"

    warnings.update(comparison_warnings(
        observation=observation,
        normalized=normalized,
        comparison=comparison,
        status=status,
    ))

    return {
        "schemaVersion": "0.1",
        "dslLevel": "DSL-C",
        "queryHash": query_hash(request),
        "package": package_frame,
        "query": request,
        "observation": result_observation,
        "normalized": normalized,
        "status": status,
        "action": action,
        "reason": reason,
        "comparison": comparison_result,
        "provenance": provenance,
        "dependencyGroups": [observation["dependencyGroup"]],
        "warnings": sorted(warnings),
        "runtime": runtime_frame(),
    }


def validate_target(
    target: dict[str, Any],
    files_root: Path,
    world: dict[str, Any],
) -> None:
    semantic_ids = load_semantic_ids(files_root, world)
    for field, expected_type in TARGET_TYPES.items():
        value = target.get(field)
        allowed = semantic_ids.get(expected_type)
        if allowed is None:
            raise DslCError(
                "unresolved_semantic_type",
                f"semantic type {expected_type!r} has no declared identifiers",
            )
        if not isinstance(value, str) or value not in allowed:
            raise DslCError(
                "target_type_mismatch",
                f"target field {field} is not a declared {expected_type}: {value!r}",
            )


def load_observations(
    *,
    files_root: Path,
    capsule: dict[str, Any],
    contracts_root: Path,
    sources: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    schema = json_object(
        contracts_root / "epistemic-observation-v0.schema.json",
        "typed observation schema",
    )
    rows: list[dict[str, Any]] = []
    for entry in capsule.get("preparedFiles", []):
        if entry.get("kind") != "observations":
            continue
        relative = entry.get("path")
        if not isinstance(relative, str):
            raise DslCError(
                "invalid_capsule_manifest",
                "observation file path is invalid",
            )
        for index, row in enumerate(
            json_lines(
                files_root / "capsule" / relative,
                f"packaged observations {relative}",
            ),
            1,
        ):
            schema_check(row, schema, f"{relative}:{index}")
            validate_observation(row)
            for reference in row["provenance"]:
                source_id = reference.split("#", 1)[0]
                if source_id not in sources:
                    raise DslCError(
                        "unknown_observation_source",
                        f"{relative}:{index} references unknown source {source_id}",
                    )
            rows.append(row)

    if not rows:
        raise DslCError(
            "missing_observations",
            "capsule package contains no typed observations",
        )

    observation_ids = [row["observationId"] for row in rows]
    if len(observation_ids) != len(set(observation_ids)):
        raise DslCError(
            "duplicate_observation",
            "capsule package contains duplicate observation IDs",
        )

    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = target_key(row["target"])
        if key in result:
            raise DslCError(
                "duplicate_observation_target",
                f"multiple observations are loaded for target {key}",
            )
        result[key] = row
    return result


def validate_observation(row: dict[str, Any]) -> None:
    model = row["model"]
    kind = model["kind"]
    if kind == "bounded":
        lower = decimal_value(model["lower"], "bounded lower")
        upper = decimal_value(model["upper"], "bounded upper")
        if lower > upper:
            raise DslCError(
                "invalid_observation_bounds",
                f"observation {row['observationId']} has lower > upper",
            )
        if (
            lower == upper
            and (
                not model["lowerInclusive"]
                or not model["upperInclusive"]
            )
        ):
            raise DslCError(
                "empty_observation_interval",
                f"observation {row['observationId']} has an empty interval",
            )
    elif kind == "normal":
        standard_deviation = decimal_value(
            model["standardDeviation"],
            "normal standard deviation",
        )
        if standard_deviation <= 0:
            raise DslCError(
                "invalid_standard_deviation",
                f"observation {row['observationId']} has non-positive deviation",
            )


def normalize_model(model: dict[str, Any]) -> dict[str, Any]:
    dimension, factor, base_unit = unit_info(model["unit"])
    kind = model["kind"]
    result: dict[str, Any] = {
        "kind": kind,
        "dimension": dimension,
        "baseUnit": base_unit,
    }
    if kind == "point":
        result["value"] = decimal_text(
            decimal_value(model["value"], "point value") * factor
        )
    elif kind == "bounded":
        result.update(
            {
                "lower": decimal_text(
                    decimal_value(model["lower"], "bounded lower") * factor
                ),
                "upper": decimal_text(
                    decimal_value(model["upper"], "bounded upper") * factor
                ),
                "lowerInclusive": model["lowerInclusive"],
                "upperInclusive": model["upperInclusive"],
            }
        )
    elif kind == "normal":
        result.update(
            {
                "mean": decimal_text(
                    decimal_value(model["mean"], "normal mean") * factor
                ),
                "standardDeviation": decimal_text(
                    decimal_value(
                        model["standardDeviation"],
                        "normal standard deviation",
                    )
                    * factor
                ),
            }
        )
    else:
        raise DslCError(
            "unsupported_observation_model",
            f"unsupported observation model: {kind!r}",
        )
    return result


def normalize_comparison(comparison: dict[str, Any]) -> dict[str, Any]:
    dimension, factor, base_unit = unit_info(comparison["unit"])
    operator = comparison["operator"]
    threshold: dict[str, Any]
    if operator == "between":
        lower = decimal_value(comparison["lower"], "comparison lower") * factor
        upper = decimal_value(comparison["upper"], "comparison upper") * factor
        if lower > upper:
            raise DslCError(
                "invalid_comparison_bounds",
                "between comparison has lower > upper",
            )
        if (
            lower == upper
            and (
                not comparison["lowerInclusive"]
                or not comparison["upperInclusive"]
            )
        ):
            raise DslCError(
                "empty_comparison_interval",
                "between comparison has an empty interval",
            )
        threshold = {
            "lower": decimal_text(lower),
            "upper": decimal_text(upper),
            "lowerInclusive": comparison["lowerInclusive"],
            "upperInclusive": comparison["upperInclusive"],
        }
    else:
        threshold = {
            "value": decimal_text(
                decimal_value(comparison["value"], "comparison value") * factor
            )
        }
    return {
        "operator": operator,
        "dimension": dimension,
        "baseUnit": base_unit,
        "normalizedThreshold": threshold,
        "sourceUnit": comparison["unit"],
    }


def compare_normalized(
    model: dict[str, Any],
    comparison: dict[str, Any],
) -> tuple[str, str]:
    if model["kind"] == "normal":
        return "unknown", "probabilistic_policy_not_declared"

    lower, lower_inclusive, upper, upper_inclusive = interval_of(model)
    operator = comparison["operator"]
    threshold = comparison["normalizedThreshold"]

    if operator == "lt":
        value = Decimal(threshold["value"])
        if upper < value or (upper == value and not upper_inclusive):
            return "supported", ""
        if lower >= value:
            return "refuted", ""
        return "unknown", "observation_interval_crosses_threshold"

    if operator == "lte":
        value = Decimal(threshold["value"])
        if upper <= value:
            return "supported", ""
        if lower > value or (lower == value and not lower_inclusive):
            return "refuted", ""
        return "unknown", "observation_interval_crosses_threshold"

    if operator == "gt":
        value = Decimal(threshold["value"])
        if lower > value or (lower == value and not lower_inclusive):
            return "supported", ""
        if upper <= value:
            return "refuted", ""
        return "unknown", "observation_interval_crosses_threshold"

    if operator == "gte":
        value = Decimal(threshold["value"])
        if lower >= value:
            return "supported", ""
        if upper < value or (upper == value and not upper_inclusive):
            return "refuted", ""
        return "unknown", "observation_interval_crosses_threshold"

    query_lower = Decimal(threshold["lower"])
    query_upper = Decimal(threshold["upper"])
    query_lower_inclusive = threshold["lowerInclusive"]
    query_upper_inclusive = threshold["upperInclusive"]

    left_contained = (
        lower > query_lower
        or (
            lower == query_lower
            and (not lower_inclusive or query_lower_inclusive)
        )
    )
    right_contained = (
        upper < query_upper
        or (
            upper == query_upper
            and (not upper_inclusive or query_upper_inclusive)
        )
    )
    if left_contained and right_contained:
        return "supported", ""

    left_disjoint = (
        upper < query_lower
        or (
            upper == query_lower
            and not (upper_inclusive and query_lower_inclusive)
        )
    )
    right_disjoint = (
        lower > query_upper
        or (
            lower == query_upper
            and not (lower_inclusive and query_upper_inclusive)
        )
    )
    if left_disjoint or right_disjoint:
        return "refuted", ""
    return "unknown", "observation_interval_partially_overlaps_allowed_range"


def interval_of(model: dict[str, Any]) -> tuple[Decimal, bool, Decimal, bool]:
    if model["kind"] == "point":
        value = Decimal(model["value"])
        return value, True, value, True
    if model["kind"] == "bounded":
        return (
            Decimal(model["lower"]),
            bool(model["lowerInclusive"]),
            Decimal(model["upper"]),
            bool(model["upperInclusive"]),
        )
    raise DslCError(
        "distribution_has_no_strict_interval",
        "normal observation has no strict finite interval",
    )


def unit_info(unit: str) -> tuple[str, Decimal, str]:
    result = UNITS.get(unit)
    if result is None:
        raise DslCError("unknown_unit", f"unit is not allowlisted: {unit!r}")
    return result


def decimal_value(value: Any, label: str) -> Decimal:
    if isinstance(value, bool):
        raise DslCError("invalid_number", f"{label} must be numeric")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise DslCError("invalid_number", f"{label} is not a decimal") from exc
    if not result.is_finite():
        raise DslCError("invalid_number", f"{label} must be finite")
    return result


def decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def target_key(target: dict[str, Any]) -> str:
    return json.dumps(
        target,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def source_record(
    reference: str,
    sources: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_id, separator, fragment = reference.partition("#")
    source = sources[source_id]
    return {
        "reference": reference,
        "sourceId": source_id,
        "fragment": fragment if separator else "",
        "title": str(source.get("title", "")),
        "locator": str(source.get("locator", "")),
    }


def base_warnings(
    observation: dict[str, Any],
    normalized: dict[str, Any],
) -> set[str]:
    warnings: set[str] = set()
    if observation["generalisability"] == "local":
        warnings.add("local-only")
    elif observation["generalisability"] == "context-dependent":
        warnings.add("context-dependent")
    if normalized["kind"] == "bounded":
        warnings.add("bounded-observation")
    elif normalized["kind"] == "normal":
        warnings.add("normal-observation")
    _, factor, _ = unit_info(observation["model"]["unit"])
    if factor != 1:
        warnings.add("unit-conversion-applied")
    if (
        normalized["kind"] == "bounded"
        and (
            not normalized["lowerInclusive"]
            or not normalized["upperInclusive"]
        )
    ):
        warnings.add("exclusive-bound-present")
    return warnings


def comparison_warnings(
    *,
    observation: dict[str, Any],
    normalized: dict[str, Any],
    comparison: dict[str, Any],
    status: str,
) -> set[str]:
    warnings: set[str] = set()
    _, factor, _ = unit_info(comparison["sourceUnit"])
    if factor != 1:
        warnings.add("unit-conversion-applied")
    if normalized["kind"] == "normal":
        warnings.add("distribution-requires-probabilistic-policy")
    elif status == "unknown":
        warnings.add("interval-overlaps-decision-boundary")
    if observation["generalisability"] == "local":
        warnings.add("local-only")
    return warnings


def run_prolog_kernel(
    *,
    model: dict[str, Any] | None,
    comparison: dict[str, Any] | None,
    expected_operation: str,
    swipl: str,
    timeout_seconds: int,
) -> str:
    if model is None:
        program = prolog_emit("unknown")
    elif expected_operation == "observation":
        program = prolog_emit("observed")
    elif model["kind"] == "normal":
        program = prolog_emit("unknown")
    else:
        program = prolog_program_interval(model, comparison)

    try:
        with tempfile.TemporaryDirectory(prefix="capsule-query-dsl-c-") as temporary:
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
        raise DslCError(
            "swipl_not_found",
            f"SWI-Prolog executable not found: {swipl}",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise DslCError(
            "swipl_timeout",
            "SWI-Prolog DSL-C query timed out",
        ) from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise DslCError(
            "swipl_failed",
            f"SWI-Prolog DSL-C query failed: {detail}",
        )
    try:
        payload = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise DslCError(
            "invalid_swipl_output",
            "invalid SWI-Prolog DSL-C JSON",
        ) from exc
    status = payload.get("status") if isinstance(payload, dict) else None
    if status not in {"observed", "supported", "refuted", "unknown"}:
        raise DslCError(
            "invalid_swipl_output",
            f"invalid SWI-Prolog DSL-C status: {status!r}",
        )
    return status


def prolog_emit(status: str) -> str:
    return f""":- use_module(library(http/json)).
main :-
    json_write_dict(current_output, _{{status:{status}}}, [width(0)]),
    nl.
:- initialization(main, main).
"""


def prolog_program_interval(
    model: dict[str, Any],
    comparison: dict[str, Any] | None,
) -> str:
    if comparison is None:
        raise DslCError(
            "missing_comparison",
            "numeric comparison is missing",
        )
    lower, lower_inclusive, upper, upper_inclusive = interval_of(model)
    values = [lower, upper]
    threshold = comparison["normalizedThreshold"]
    if comparison["operator"] == "between":
        values.extend(
            [Decimal(threshold["lower"]), Decimal(threshold["upper"])]
        )
    else:
        values.append(Decimal(threshold["value"]))
    scale = decimal_scale(values)
    integers = [scaled_integer(value, scale) for value in values]
    lower_i, upper_i = integers[0], integers[1]
    li = prolog_bool(lower_inclusive)
    ui = prolog_bool(upper_inclusive)
    operator = comparison["operator"]

    if operator == "between":
        query_lower, query_upper = integers[2], integers[3]
        qli = prolog_bool(threshold["lowerInclusive"])
        qui = prolog_bool(threshold["upperInclusive"])
        query_term = (
            f"between({query_lower},{qli},{query_upper},{qui})"
        )
    else:
        query_term = f"single({operator},{integers[2]})"

    return f""":- use_module(library(http/json)).

status(_, _, U, UI, single(lt, T), supported) :-
    ( U < T ; U =:= T, UI == false ), !.
status(L, _, _, _, single(lt, T), refuted) :-
    L >= T, !.
status(_, _, U, _, single(lte, T), supported) :-
    U =< T, !.
status(L, LI, _, _, single(lte, T), refuted) :-
    ( L > T ; L =:= T, LI == false ), !.
status(L, LI, _, _, single(gt, T), supported) :-
    ( L > T ; L =:= T, LI == false ), !.
status(_, _, U, _, single(gt, T), refuted) :-
    U =< T, !.
status(L, _, _, _, single(gte, T), supported) :-
    L >= T, !.
status(_, _, U, UI, single(gte, T), refuted) :-
    ( U < T ; U =:= T, UI == false ), !.
status(L, LI, U, UI, between(QL, QLI, QU, QUI), supported) :-
    ( L > QL ; L =:= QL, (LI == false ; QLI == true) ),
    ( U < QU ; U =:= QU, (UI == false ; QUI == true) ), !.
status(L, LI, U, UI, between(QL, QLI, QU, QUI), refuted) :-
    ( U < QL
    ; U =:= QL, \\+ (UI == true, QLI == true)
    ; L > QU
    ; L =:= QU, \\+ (LI == true, QUI == true)
    ), !.
status(_, _, _, _, _, unknown).

main :-
    status({lower_i}, {li}, {upper_i}, {ui}, {query_term}, Status),
    json_write_dict(current_output, _{{status:Status}}, [width(0)]),
    nl.

:- initialization(main, main).
"""


def decimal_scale(values: list[Decimal]) -> int:
    places = [
        max(0, -value.normalize().as_tuple().exponent)
        for value in values
    ]
    return max(places, default=0)


def scaled_integer(value: Decimal, scale: int) -> int:
    scaled = value * (Decimal(10) ** scale)
    integral = scaled.to_integral_exact()
    return int(integral)


def prolog_bool(value: bool) -> str:
    return "true" if value else "false"


def query_hash(request: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        QUERY_DOMAIN + bytes((1,)) + canonical_json(request)
    )
    return "sha256:" + digest.hexdigest()


def runtime_frame() -> dict[str, Any]:
    return {
        "engine": "python+swi-prolog",
        "semantics": "typed-interval-comparison-v0",
        "verifiedAgainstPackagedObservations": True,
        "verifiedAgainstPrologKernel": True,
    }


def error_payload(exc: BaseException) -> bytes:
    code = exc.code if isinstance(exc, CapsuleQueryError) else "query_failed"
    return canonical_json(
        {
            "schemaVersion": "0.1",
            "error": {"code": code, "message": str(exc)},
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
        subprocess.SubprocessError,
    ) as exc:
        sys.stderr.buffer.write(error_payload(exc))
        raise SystemExit(1) from exc
