# Prolog router contract

The Prolog router is a **derived representation** of the same canonical routing IR used by the decision-graph executor.

`prototype/generate_policy.py` deterministically lowers `policy.ir.json` into `prototype/generated/policy.pl`.

## Why derived

No routing rule is independently authored twice. The canonical IR is normative; Prolog is a checked lowering. This prevents semantic duplication from manufacturing an apparent tree-versus-Prolog effect.

The representation ablation therefore evaluates engineering properties such as byte size, execution latency, auditability, runtime dependency, and agreement with the canonical graph. It cannot be used to claim that Prolog changed Qwen behavior when both routers select the same downstream capability.

## Runtime

SWI-Prolog receives only the frozen typed feature vector and returns one canonical capability ID. It does not receive questions, expected labels, tool results, or epistemic outcomes.

The generated program performs no network, file, database, Python, or domain-semantic action.

## Equivalence gate

Before any model run, exhaustive enumeration over the frozen feature domain must show exact decision-graph/Prolog routing agreement. The committed Prolog file must byte-match a clean regeneration from the canonical IR.

Any disagreement is a STOP condition.
