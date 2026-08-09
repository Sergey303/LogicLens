from __future__ import annotations

from typing import Any


class EligibilityError(ValueError):
    pass


ALLOWED_POLARITIES = {"positive", "negative"}
FORBIDDEN_SOURCE_KEYS = {
    "dependency_groups": "DEPENDENCY_SEMANTICS_REQUIRED",
    "opinion_groups": "DEPENDENCY_SEMANTICS_REQUIRED",
    "priorities": "PRIORITY_OR_EXCEPTION",
    "exceptions": "PRIORITY_OR_EXCEPTION",
    "negation_as_failure": "NEGATION_AS_FAILURE",
    "arithmetic_predicates": "ARITHMETIC_PREDICATE",
}


def _reject(reasons: list[str], code: str) -> None:
    if code not in reasons:
        reasons.append(code)


def evaluate_source(source: dict[str, Any]) -> dict[str, Any]:
    """Outcome-blind structural eligibility for eng197.relational-subset.v1.

    This function must not receive evaluator expectations, model outputs, status,
    action, or scorer fields. Unknown structure fails closed.
    """
    allowed_top = {"package_id", "scope", "scope_id", "version", "propositions", "assertions", "implications"}
    reasons: list[str] = []

    unknown_top = set(source) - allowed_top
    if unknown_top:
        for key in sorted(unknown_top):
            _reject(reasons, FORBIDDEN_SOURCE_KEYS.get(key, "UNKNOWN_STRUCTURE"))

    if source.get("scope") != "TRAIN_DEV_ONLY_SYNTHETIC":
        _reject(reasons, "UNKNOWN_STRUCTURE")
    if not isinstance(source.get("scope_id"), str) or not source.get("scope_id"):
        _reject(reasons, "UNKNOWN_STRUCTURE")
    if not isinstance(source.get("version"), str) or not source.get("version"):
        _reject(reasons, "UNKNOWN_STRUCTURE")

    propositions = source.get("propositions")
    assertions = source.get("assertions")
    implications = source.get("implications")
    if not isinstance(propositions, list) or not isinstance(assertions, list) or not isinstance(implications, list):
        return {"eligible": False, "reason_codes": sorted(set(reasons + ["UNKNOWN_STRUCTURE"]))}

    proposition_ids = set()
    for p in propositions:
        if set(p) != {"id", "subject", "predicate", "object"}:
            _reject(reasons, "UNKNOWN_STRUCTURE")
            continue
        pid = p.get("id")
        if not isinstance(pid, str) or not pid or pid in proposition_ids:
            _reject(reasons, "UNKNOWN_STRUCTURE")
        proposition_ids.add(pid)

    assertion_ids = set()
    for a in assertions:
        if set(a) != {"id", "proposition_id", "polarity", "scope_id", "version", "source_id"}:
            _reject(reasons, "UNKNOWN_STRUCTURE")
            continue
        if a.get("polarity") not in ALLOWED_POLARITIES:
            _reject(reasons, "POLARITY_TRANSFORM")
        if a.get("scope_id") != source.get("scope_id") or a.get("version") != source.get("version"):
            _reject(reasons, "MIXED_SCOPE_OR_VERSION")
        if a.get("proposition_id") not in proposition_ids:
            _reject(reasons, "UNKNOWN_STRUCTURE")
        aid = a.get("id")
        if not isinstance(aid, str) or not aid or aid in assertion_ids:
            _reject(reasons, "UNKNOWN_STRUCTURE")
        assertion_ids.add(aid)
        if not isinstance(a.get("source_id"), str) or not a.get("source_id"):
            _reject(reasons, "PROVENANCE_NOT_LOSSLESS")

    rule_ids = set()
    for r in implications:
        expected = {"id", "antecedent_proposition_id", "consequent_proposition_id", "scope_id", "version"}
        if set(r) != expected:
            extra = set(r) - expected
            if {"premises", "all", "any"} & extra:
                _reject(reasons, "MULTI_PREMISE_RULE")
            if {"negative_premise", "negative_premises"} & extra:
                _reject(reasons, "NEGATIVE_PREMISE")
            if {"head_polarity", "negative_head"} & extra:
                _reject(reasons, "NEGATIVE_RULE_HEAD")
            if not extra:
                _reject(reasons, "UNKNOWN_STRUCTURE")
            elif not ({"premises", "all", "any", "negative_premise", "negative_premises", "head_polarity", "negative_head"} & extra):
                _reject(reasons, "UNKNOWN_STRUCTURE")
        if r.get("scope_id") != source.get("scope_id") or r.get("version") != source.get("version"):
            _reject(reasons, "MIXED_SCOPE_OR_VERSION")
        if r.get("antecedent_proposition_id") not in proposition_ids or r.get("consequent_proposition_id") not in proposition_ids:
            _reject(reasons, "UNKNOWN_STRUCTURE")
        rid = r.get("id")
        if not isinstance(rid, str) or not rid or rid in rule_ids:
            _reject(reasons, "UNKNOWN_STRUCTURE")
        rule_ids.add(rid)

    return {"eligible": not reasons, "reason_codes": sorted(reasons)}
