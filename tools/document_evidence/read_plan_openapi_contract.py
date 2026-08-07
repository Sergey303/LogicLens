# Copyright (c) 2026 Sergey Leshtaev
"""Validate security-sensitive read-plan details in the pinned OpenAPI contract."""

from __future__ import annotations

from typing import cast

TOKEN_MIN_LENGTH = 1
TOKEN_MAX_LENGTH = 4096


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        message = f"OpenAPI field must be an object: {label}"
        raise ValueError(message)
    return cast("dict[str, object]", value)


def _sequence(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        message = f"OpenAPI field must be an array: {label}"
        raise ValueError(message)
    return cast("list[object]", value)


def validate_read_plan_security(spec: dict[str, object]) -> None:
    """Reject OpenAPI drift that could expose or misroute the read-plan credential."""
    components = _mapping(spec.get("components"), "components")
    parameters = _mapping(components.get("parameters"), "components.parameters")
    token = _mapping(parameters.get("readPlanToken"), "readPlanToken")
    token_schema = _mapping(token.get("schema"), "readPlanToken.schema")
    if (
        token.get("name") != "X-Read-Plan-Token"
        or token.get("in") != "header"
        or token.get("required") is not True
        or token_schema.get("minLength") != TOKEN_MIN_LENGTH
        or token_schema.get("maxLength") != TOKEN_MAX_LENGTH
    ):
        message = "Read-plan credential must remain a required bounded header."
        raise ValueError(message)

    schemas = _mapping(components.get("schemas"), "components.schemas")
    read_plan = _mapping(schemas.get("ReadPlan"), "ReadPlan")
    properties = _mapping(read_plan.get("properties"), "ReadPlan.properties")
    required = _sequence(read_plan.get("required"), "ReadPlan.required")
    if "token" not in required or "relativeUrl" in properties:
        message = "ReadPlan must expose the opaque token without a credential-bearing URL."
        raise ValueError(message)

    paths = _mapping(spec.get("paths"), "paths")
    content_path = _mapping(paths.get("/api/v1/read-plans/content"), "read-plan content path")
    operation = _mapping(content_path.get("get"), "GET read-plan content")
    operation_parameters = _sequence(operation.get("parameters"), "openReadPlan.parameters")
    references = {
        _mapping(item, "openReadPlan parameter").get("$ref") for item in operation_parameters
    }
    expected = {
        "#/components/parameters/actorId",
        "#/components/parameters/readPlanToken",
    }
    if references != expected:
        message = "Read-plan content must accept only actor and read-plan header credentials."
        raise ValueError(message)
