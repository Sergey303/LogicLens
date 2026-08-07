from __future__ import annotations
import json
from pathlib import Path
from typing import Any


class RoutingError(RuntimeError):
    pass


ROOT = Path(__file__).resolve().parent
FEATURE_CONTRACT_PATH = ROOT.parent / "ROUTING_FEATURE_CONTRACT.json"


def load_feature_contract() -> dict[str, Any]:
    return json.loads(FEATURE_CONTRACT_PATH.read_text(encoding="utf-8"))


def feature_names(contract: dict[str, Any]) -> set[str]:
    return set(contract["features"])


def index_nodes(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = policy["nodes"]
    index = {node["id"]: node for node in nodes}
    if len(index) != len(nodes):
        raise RoutingError("duplicate node id")
    return index


def validate_features(features: dict[str, Any], contract: dict[str, Any] | None = None) -> None:
    contract = contract or load_feature_contract()
    expected = feature_names(contract)
    if set(features) != expected:
        raise RoutingError("feature vector must contain exactly the frozen feature set")

    for name, spec in contract["features"].items():
        value = features[name]
        if spec["type"] == "boolean":
            if not isinstance(value, bool):
                raise RoutingError(f"{name} must be boolean")
        elif spec["type"] == "string":
            if not isinstance(value, str):
                raise RoutingError(f"{name} must be string")
            allowed = spec.get("enum")
            if allowed is not None and value not in allowed:
                raise RoutingError(f"{name} is outside the frozen enum")
        else:
            raise RoutingError(f"unsupported feature type in contract: {name}")


def route(
    policy: dict[str, Any],
    features: dict[str, Any],
    available: dict[str, tuple[str, bool]],
    contract: dict[str, Any] | None = None,
) -> str:
    contract = contract or load_feature_contract()
    validate_features(features, contract)
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
