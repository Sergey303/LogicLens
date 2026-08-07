from __future__ import annotations
from typing import Any


class RoutingError(RuntimeError):
    pass


FEATURES = {"goal_class", "has_scope", "has_version", "asks_write", "requires_strict_policy"}


def index_nodes(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = policy["nodes"]
    index = {node["id"]: node for node in nodes}
    if len(index) != len(nodes):
        raise RoutingError("duplicate node id")
    return index


def validate_features(features: dict[str, Any], policy: dict[str, Any]) -> None:
    if set(features) != FEATURES:
        raise RoutingError("feature vector must contain exactly the frozen feature set")
    allowed_goals = set(policy["feature_contract"]["goal_class"])
    if features["goal_class"] not in allowed_goals:
        raise RoutingError("unknown goal_class")
    for name in ("has_scope", "has_version", "asks_write", "requires_strict_policy"):
        if not isinstance(features[name], bool):
            raise RoutingError(f"{name} must be boolean")


def route(policy: dict[str, Any], features: dict[str, Any], available: dict[str, tuple[str, bool]]) -> str:
    validate_features(features, policy)
    nodes = index_nodes(policy)
    current = policy["root"]
    visited: set[str] = set()
    while True:
        if current in visited:
            raise RoutingError("policy cycle detected")
        visited.add(current)
        node = nodes.get(current)
        if node is None:
            raise RoutingError(f"missing node: {current}")
        if node["type"] == "action":
            capability = node["capability_id"]
            version = node["capability_version"]
            actual = available.get(capability)
            if actual is None:
                raise RoutingError(f"unknown capability: {capability}")
            actual_version, is_available = actual
            if actual_version != version:
                raise RoutingError(f"stale capability version: {capability}")
            if not is_available:
                raise RoutingError(f"unavailable capability: {capability}")
            return capability
        if node["type"] != "condition" or node.get("op") != "eq":
            raise RoutingError(f"unsupported node: {current}")
        result = features[node["feature"]] == node["value"]
        current = node["if_true"] if result else node["if_false"]
