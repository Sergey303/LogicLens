#!/usr/bin/env python3
"""Query verified capsule packages with ground logical DSL-B rules and proof DAGs."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
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
    load_assertions,
    load_predicates,
    load_semantic_ids,
    prolog_atom,
    prolog_target,
    read_request,
    validate_argument,
    write_result,
)

UTF8 = "utf-8"
QUERY_DOMAIN = b"LogicLensCapsuleQueryDslB\0"
STATUS_POLICY = {
    "supported": (
        "answer_with_source_scope",
        "loaded_or_derived_evidence_supports_claim",
    ),
    "refuted": (
        "explain_explicit_role_boundary",
        "loaded_or_derived_evidence_explicitly_opposes_claim",
    ),
    "unknown": (
        "abstain_and_request_context",
        "insufficient_loaded_or_derived_evidence",
    ),
    "conflicting": (
        "report_conflict_and_compare_models",
        "incompatible_loaded_or_derived_evidence",
    ),
}


@dataclass(frozen=True)
class Evaluation:
    status: str
    support_roots: tuple[str, ...]
    oppose_roots: tuple[str, ...]


class DslBError(CapsuleQueryError):
    pass


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contracts-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "contracts",
    )
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--request", required=True)
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--timeout-seconds", type=int, default=15)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    if args.timeout_seconds < 1 or args.timeout_seconds > 300:
        raise DslBError("invalid_timeout", "timeout must be between 1 and 300 seconds")
    request = read_request(args.request)
    request_schema = json_object(
        args.contracts_root / "capsule-query-dsl-b-v0.schema.json",
        "DSL-B query schema",
    )
    schema_check(request, request_schema, "DSL-B query")
    result = query_package(
        package_root=args.package,
        request=request,
        contracts_root=args.contracts_root,
        swipl=args.swipl,
        timeout_seconds=args.timeout_seconds,
    )
    result_schema = json_object(
        args.contracts_root / "capsule-query-dsl-b-result-v0.schema.json",
        "DSL-B result schema",
    )
    schema_check(result, result_schema, "DSL-B result")
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
    capsule = json_object(files_root / "capsule" / "capsule.json", "packaged capsule")
    predicates = load_predicates(files_root, world)
    semantic_ids = load_semantic_ids(files_root, world)
    target = request["target"]
    validate_target(target, predicates, semantic_ids)

    assertions = load_assertions(files_root, capsule)
    rules = load_rules(files_root, capsule, contracts_root)
    for rule in rules:
        validate_target(rule["head"]["target"], predicates, semantic_ids)
        for condition in body_conditions(rule["body"]):
            validate_target(condition_target(condition), predicates, semantic_ids)
    reject_rule_cycles(rules)

    evaluator = GroundRuleEvaluator(assertions, rules)
    evaluated = evaluator.evaluate(target)
    prolog = run_prolog_query(
        generated_assertions=files_root / "generated" / "assertions.pl",
        target=target,
        rules=rules,
        swipl=swipl,
        timeout_seconds=timeout_seconds,
    )
    if (
        prolog.get("status") != evaluated.status
        or prolog.get("support") != list(evaluated.support_roots)
        or prolog.get("oppose") != list(evaluated.oppose_roots)
    ):
        raise DslBError(
            "runtime_mismatch",
            "Python reference result does not match SWI-Prolog logical-rule result",
        )

    action, reason = STATUS_POLICY[evaluated.status]
    warnings = build_warnings(evaluated, evaluator.nodes, rules)
    return {
        "schemaVersion": "0.1",
        "dslLevel": "DSL-B",
        "queryHash": query_hash(request),
        "package": {
            "worldId": package["world"]["id"],
            "capsuleId": package["capsule"]["id"],
            "capsuleVersion": package["capsule"]["version"],
            "packageHash": package["packageHash"],
        },
        "query": request,
        "status": evaluated.status,
        "action": action,
        "reason": reason,
        "evidence": {
            "support": list(evaluated.support_roots),
            "oppose": list(evaluated.oppose_roots),
        },
        "proof": {
            "supportRoots": list(evaluated.support_roots),
            "opposeRoots": list(evaluated.oppose_roots),
            "nodes": [evaluator.nodes[key] for key in sorted(evaluator.nodes)],
        },
        "warnings": warnings,
        "runtime": {
            "engine": "python-reference+swi-prolog",
            "semantics": "ground-logical-rules-open-world",
            "verifiedAgainstGeneratedAssertions": True,
            "verifiedAgainstLogicalRules": True,
        },
    }


def validate_target(
    target: dict[str, Any],
    predicates: dict[str, dict[str, Any]],
    semantic_ids: dict[str, set[str]],
) -> None:
    predicate_id = target["predicate"]
    predicate = predicates.get(predicate_id)
    if predicate is None:
        raise DslBError("unknown_predicate", f"unknown predicate: {predicate_id}")
    if predicate.get("valueSpace") != "strict_claim":
        raise DslBError(
            "unsupported_value_space",
            f"predicate {predicate_id} is not strict_claim",
        )
    if predicate.get("world") != "open":
        raise DslBError(
            "unsupported_world_semantics",
            f"predicate {predicate_id} is not open-world",
        )
    if predicate.get("negation") != "explicit_evidence":
        raise DslBError(
            "unsupported_negation_semantics",
            f"predicate {predicate_id} does not use explicit evidence negation",
        )
    declarations = predicate.get("arguments")
    arguments = target["arguments"]
    if not isinstance(declarations, list):
        raise DslBError("invalid_semantic_model", f"predicate {predicate_id} has no arguments")
    if len(declarations) != len(arguments):
        raise DslBError(
            "arity_mismatch",
            f"predicate {predicate_id} expects {len(declarations)} arguments, received {len(arguments)}",
        )
    for index, (value, declaration) in enumerate(
        zip(arguments, declarations, strict=True),
        1,
    ):
        validate_argument(
            value=value,
            expected_type=declaration.get("type"),
            semantic_ids=semantic_ids,
            position=index,
            predicate_id=predicate_id,
        )


def load_rules(
    files_root: Path,
    capsule: dict[str, Any],
    contracts_root: Path,
) -> list[dict[str, Any]]:
    schema = json_object(
        contracts_root / "epistemic-logical-rule-v0.schema.json",
        "logical rule schema",
    )
    rows: list[dict[str, Any]] = []
    for entry in capsule.get("ruleFiles", []):
        relative = entry.get("path")
        if (
            entry.get("kind") == "rules"
            and isinstance(relative, str)
            and relative.lower().endswith(".jsonl")
        ):
            for index, row in enumerate(
                json_lines(
                    files_root / "capsule" / relative,
                    f"packaged logical rules {relative}",
                ),
                1,
            ):
                schema_check(row, schema, f"{relative}:{index}")
                rows.append(row)
    if not rows:
        raise DslBError(
            "missing_logical_rules",
            "capsule package declares no JSONL logical rule file",
        )
    identifiers = [row["ruleId"] for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise DslBError("duplicate_logical_rule", "duplicate logical rule ID")
    return sorted(rows, key=lambda item: item["ruleId"])


def body_conditions(body: dict[str, Any]) -> list[dict[str, Any]]:
    if "all" in body:
        return body["all"]
    return body["any"]


def body_operator(body: dict[str, Any]) -> str:
    return "all" if "all" in body else "any"


def condition_target(condition: dict[str, Any]) -> dict[str, Any]:
    if "claim" in condition:
        return condition["claim"]
    return condition["notExplicit"]["target"]


def target_key(target: dict[str, Any]) -> str:
    return json.dumps(target, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def reject_rule_cycles(rules: list[dict[str, Any]]) -> None:
    heads = {target_key(rule["head"]["target"]): rule["ruleId"] for rule in rules}
    graph: dict[str, set[str]] = {key: set() for key in heads}
    for rule in rules:
        head_key = target_key(rule["head"]["target"])
        for condition in body_conditions(rule["body"]):
            if "claim" not in condition:
                continue
            dependency = target_key(condition["claim"])
            if dependency in heads:
                graph[head_key].add(dependency)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise DslBError("logical_rule_cycle", f"logical rule cycle at {node}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in sorted(graph[node]):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        visit(node)


class GroundRuleEvaluator:
    def __init__(
        self,
        assertions: list[dict[str, Any]],
        rules: list[dict[str, Any]],
    ) -> None:
        self.assertions = assertions
        self.rules = rules
        self.assertions_by_target: dict[str, list[dict[str, Any]]] = {}
        self.rules_by_target: dict[str, list[dict[str, Any]]] = {}
        self.nodes: dict[str, dict[str, Any]] = {}
        self.memo: dict[str, Evaluation] = {}
        for row in assertions:
            self.assertions_by_target.setdefault(target_key(row["target"]), []).append(row)
        for rule in rules:
            self.rules_by_target.setdefault(target_key(rule["head"]["target"]), []).append(rule)

    def evaluate(self, target: dict[str, Any], stack: tuple[str, ...] = ()) -> Evaluation:
        key = target_key(target)
        if key in self.memo:
            return self.memo[key]
        if key in stack:
            raise DslBError("logical_rule_cycle", f"runtime cycle at {key}")

        support: set[str] = set()
        oppose: set[str] = set()
        for row in sorted(
            self.assertions_by_target.get(key, []),
            key=lambda item: item["assertionId"],
        ):
            node_id = f"assertion:{row['assertionId']}"
            self.nodes[node_id] = {
                "nodeId": node_id,
                "kind": "assertion",
                "target": row["target"],
                "stance": row["stance"],
                "assertionId": row["assertionId"],
            }
            (support if row["stance"] == "support" else oppose).add(node_id)

        for rule in self.rules_by_target.get(key, []):
            outcome = self.evaluate_body(rule["body"], stack + (key,))
            if outcome is None:
                continue
            premises, used_not_explicit = outcome
            node_id = f"rule:{rule['ruleId']}"
            node: dict[str, Any] = {
                "nodeId": node_id,
                "kind": "rule",
                "target": rule["head"]["target"],
                "stance": rule["head"]["stance"],
                "ruleId": rule["ruleId"],
                "operator": body_operator(rule["body"]),
                "premises": sorted(set(premises)),
            }
            if used_not_explicit:
                node["usedNotExplicit"] = True
            self.nodes[node_id] = node
            (support if rule["head"]["stance"] == "support" else oppose).add(node_id)

        evaluation = Evaluation(
            status=strict_status(support, oppose),
            support_roots=tuple(sorted(support)),
            oppose_roots=tuple(sorted(oppose)),
        )
        self.memo[key] = evaluation
        return evaluation

    def evaluate_body(
        self,
        body: dict[str, Any],
        stack: tuple[str, ...],
    ) -> tuple[list[str], bool] | None:
        operator = body_operator(body)
        outcomes: list[tuple[list[str], bool]] = []
        for condition in body_conditions(body):
            outcome = self.evaluate_condition(condition, stack)
            if operator == "all" and outcome is None:
                return None
            if outcome is not None:
                outcomes.append(outcome)
                if operator == "any":
                    return outcome
        if not outcomes:
            return None
        premises: list[str] = []
        used_not_explicit = False
        for condition_premises, condition_not_explicit in outcomes:
            premises.extend(condition_premises)
            used_not_explicit = used_not_explicit or condition_not_explicit
        return premises, used_not_explicit

    def evaluate_condition(
        self,
        condition: dict[str, Any],
        stack: tuple[str, ...],
    ) -> tuple[list[str], bool] | None:
        if "claim" in condition:
            evaluated = self.evaluate(condition["claim"], stack)
            required = condition["requires"]
            if evaluated.status != required:
                return None
            roots = (
                evaluated.support_roots
                if required == "supported"
                else evaluated.oppose_roots
            )
            return list(roots), False

        value = condition["notExplicit"]
        target_rows = self.assertions_by_target.get(target_key(value["target"]), [])
        if any(row["stance"] == value["stance"] for row in target_rows):
            return None
        return [], True


def strict_status(support: set[str], oppose: set[str]) -> str:
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
    rules: list[dict[str, Any]],
    swipl: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    if not generated_assertions.is_file():
        raise DslBError("missing_generated_assertions", "missing generated assertions.pl")
    rule_facts = "\n".join(prolog_rule(rule) for rule in rules)
    assertions_path = prolog_atom(generated_assertions.resolve().as_posix())
    target_term = prolog_target(target)
    program = f""":- use_module(library(http/json)).
:- use_module({assertions_path}).

{rule_facts}

explicit_evidence(Target, Stance, Label) :-
    capsule_assertions:prepared_assertion(Id, Target, Stance, _, _, _),
    atomic_list_concat(['assertion:', Id], Label).

evidence(Target, Stance, _, Label) :-
    explicit_evidence(Target, Stance, Label).
evidence(Target, Stance, Visited, Label) :-
    \\+ memberchk(Target, Visited),
    logical_rule(Id, Target, Stance, Body),
    eval_expr(Body, [Target|Visited]),
    atomic_list_concat(['rule:', Id], Label).

claim_status(Target, Visited, Status, Support, Oppose) :-
    findall(Label, evidence(Target, support, Visited, Label), Support0),
    sort(Support0, Support),
    findall(Label, evidence(Target, oppose, Visited, Label), Oppose0),
    sort(Oppose0, Oppose),
    ( Support \\= [], Oppose \\= [] -> Status = conflicting
    ; Support \\= [] -> Status = supported
    ; Oppose \\= [] -> Status = refuted
    ; Status = unknown
    ).

eval_expr(all(Conditions), Visited) :-
    maplist(eval_condition(Visited), Conditions).
eval_expr(any(Conditions), Visited) :-
    member(Condition, Conditions),
    eval_condition(Visited, Condition),
    !.

eval_condition(Visited, requires(Status, Target)) :-
    claim_status(Target, Visited, Status, _, _).
eval_condition(_, not_explicit(Stance, Target)) :-
    \\+ explicit_evidence(Target, Stance, _).

main :-
    Target = {target_term},
    claim_status(Target, [], Status, Support, Oppose),
    json_write_dict(current_output, _{{status:Status, support:Support, oppose:Oppose}}, [width(0)]),
    nl.

:- initialization(main, main).
"""
    try:
        with tempfile.TemporaryDirectory(prefix="capsule-query-dsl-b-") as temporary:
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
        raise DslBError("swipl_not_found", f"SWI-Prolog executable not found: {swipl}") from exc
    except subprocess.TimeoutExpired as exc:
        raise DslBError("swipl_timeout", "SWI-Prolog DSL-B query timed out") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise DslBError("swipl_failed", f"SWI-Prolog DSL-B query failed: {detail}")
    try:
        payload = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise DslBError("invalid_swipl_output", "invalid SWI-Prolog DSL-B JSON") from exc
    if not isinstance(payload, dict):
        raise DslBError("invalid_swipl_output", "SWI-Prolog DSL-B result is not an object")
    payload["support"] = sorted(payload.get("support", []))
    payload["oppose"] = sorted(payload.get("oppose", []))
    return payload


def prolog_rule(rule: dict[str, Any]) -> str:
    body = rule["body"]
    operator = body_operator(body)
    conditions = ", ".join(prolog_condition(item) for item in body_conditions(body))
    return (
        "logical_rule("
        + prolog_atom(rule["ruleId"])
        + ", "
        + prolog_target(rule["head"]["target"])
        + ", "
        + rule["head"]["stance"]
        + ", "
        + operator
        + "(["
        + conditions
        + "]))."
    )


def prolog_condition(condition: dict[str, Any]) -> str:
    if "claim" in condition:
        return (
            "requires("
            + condition["requires"]
            + ", "
            + prolog_target(condition["claim"])
            + ")"
        )
    value = condition["notExplicit"]
    return (
        "not_explicit("
        + value["stance"]
        + ", "
        + prolog_target(value["target"])
        + ")"
    )


def build_warnings(
    evaluated: Evaluation,
    nodes: dict[str, dict[str, Any]],
    rules: list[dict[str, Any]],
) -> list[str]:
    warnings: set[str] = set()
    if evaluated.status == "unknown":
        warnings.add("insufficient-loaded-or-derived-evidence")
    if evaluated.status == "conflicting":
        warnings.add("incompatible-loaded-or-derived-evidence")
    used_rule_ids = {
        node["ruleId"]
        for node in nodes.values()
        if node["kind"] == "rule"
    }
    if used_rule_ids:
        warnings.add("derived-evidence-present")
    if any(node.get("usedNotExplicit") for node in nodes.values()):
        warnings.add("not-explicit-premise-used")
    for rule in rules:
        if rule["ruleId"] not in used_rule_ids:
            continue
        if rule["generalisability"] == "context-dependent":
            warnings.add("context-dependent")
        elif rule["generalisability"] == "local":
            warnings.add("local-only")
    return sorted(warnings)


def query_hash(request: dict[str, Any]) -> str:
    digest = hashlib.sha256(QUERY_DOMAIN + bytes((1,)) + canonical_json(request))
    return "sha256:" + digest.hexdigest()


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
    except (CapsuleError, CapsuleQueryError, OSError, ValueError) as exc:
        sys.stderr.buffer.write(error_payload(exc))
        raise SystemExit(1) from exc
