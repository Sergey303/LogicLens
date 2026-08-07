from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
POLICY = ROOT / "policy.ir.json"
OUT = ROOT / "generated" / "policy.pl"


def atom(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    text = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{text}'"


def build(policy: dict[str, Any]) -> str:
    lines = [
        ":- set_prolog_flag(double_quotes, string).",
        "% Generated from policy.ir.json. Do not hand-edit.",
        f"% Feature contract: {policy['feature_contract_id']} sha256={policy['feature_contract_sha256']}",
        "",
    ]
    for node in policy["nodes"]:
        node_id = atom(node["id"])
        if node["type"] == "action":
            lines.append(f"action({node_id}, {atom(node['capability_id'])}, {atom(node['capability_version'])}).")
        else:
            lines.append(
                "condition("
                f"{node_id}, {atom(node['feature'])}, {atom(node['value'])}, "
                f"{atom(node['if_true'])}, {atom(node['if_false'])})."
            )
    lines.extend([
        "",
        "feature_value('goal_class', Goal, _, _, _, _, Goal).",
        "feature_value('has_scope', _, HasScope, _, _, _, HasScope).",
        "feature_value('has_version', _, _, HasVersion, _, _, HasVersion).",
        "feature_value('asks_write', _, _, _, AsksWrite, _, AsksWrite).",
        "feature_value('requires_strict_policy', _, _, _, _, RequiresPolicy, RequiresPolicy).",
        "",
        "route(Goal, HasScope, HasVersion, AsksWrite, RequiresPolicy, Capability) :-",
        f"    walk({atom(policy['root'])}, Goal, HasScope, HasVersion, AsksWrite, RequiresPolicy, Capability, []).",
        "",
        "walk(Node, _, _, _, _, _, _, Seen) :- memberchk(Node, Seen), !, fail.",
        "walk(Node, _, _, _, _, _, Capability, _) :- action(Node, Capability, _), !.",
        "walk(Node, Goal, HasScope, HasVersion, AsksWrite, RequiresPolicy, Capability, Seen) :-",
        "    condition(Node, Feature, Expected, IfTrue, IfFalse),",
        "    feature_value(Feature, Goal, HasScope, HasVersion, AsksWrite, RequiresPolicy, Actual),",
        "    ( Actual == Expected -> Next = IfTrue ; Next = IfFalse ),",
        "    walk(Next, Goal, HasScope, HasVersion, AsksWrite, RequiresPolicy, Capability, [Node|Seen]).",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    text = build(policy)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
