from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


def resolve(source: dict[str, Any], proposition_id: str, scope_id: str, version: str) -> dict[str, Any]:
    positive_roots: dict[str, list[tuple[str, str]]] = defaultdict(list)
    negatives: dict[str, list[tuple[str, str]]] = defaultdict(list)
    edges: dict[str, list[str]] = defaultdict(list)

    for assertion in source["assertions"]:
        if assertion["scope_id"] != scope_id or assertion["version"] != version:
            continue
        pair = (assertion["id"], assertion["source_id"])
        target = assertion["proposition_id"]
        (positive_roots if assertion["polarity"] == "positive" else negatives)[target].append(pair)

    for rule in source["implications"]:
        if rule["scope_id"] == scope_id and rule["version"] == version:
            edges[rule["antecedent_proposition_id"]].append(rule["consequent_proposition_id"])

    reached: dict[str, set[tuple[str, str]]] = defaultdict(set)
    queue: deque[str] = deque()
    for proposition, evidence in positive_roots.items():
        reached[proposition].update(evidence)
        queue.append(proposition)

    while queue:
        current = queue.popleft()
        for nxt in edges[current]:
            before = len(reached[nxt])
            reached[nxt].update(reached[current])
            if len(reached[nxt]) != before:
                queue.append(nxt)

    positive = reached.get(proposition_id, set())
    negative = set(negatives.get(proposition_id, []))
    if positive and negative:
        status = "conflicting"
    elif positive:
        status = "supported"
    elif negative:
        status = "refuted"
    else:
        status = "unknown"
    action = "accept" if status == "supported" else "reject" if status == "refuted" else "review"
    evidence = sorted(assertion for assertion, _ in positive | negative)
    provenance = sorted(source_id for _, source_id in positive | negative)
    return {"status_code": status, "action_code": action, "evidence": evidence, "provenance": provenance}
