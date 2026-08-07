# Prolog router contract

The Prolog router is a **derived representation** of the same canonical routing IR used by the decision-graph executor.

`prototype/generate_policy.py` deterministically lowers `policy.ir.json` into `prototype/generated/policy.pl`.

## Why derived

No routing rule is independently authored twice. The canonical IR is normative; Prolog is a checked lowering. This prevents semantic duplication from manufacturing an apparent tree-versus-Prolog effect.

The representation ablation therefore evaluates engineering properties such as byte size, execution latency, auditability, runtime dependency, and agreement with the canonical graph. It cannot be used to claim that Prolog changed Qwen behavior when both routers select the same downstream capability.

## Feature boundary

SWI-Prolog receives only the exact frozen typed feature vector defined by `ROUTING_FEATURE_CONTRACT.json`. The canonical IR records the feature-contract ID and SHA-256, and the generated Prolog header records the same reference.

The Prolog router does not parse raw natural-language questions.

## Runtime scope

SWI-Prolog returns one canonical capability ID. It does not receive questions, expected labels, tool results, epistemic outcomes, or bound arguments.

The generated program performs no network, file, database, Python, prompt execution, argument binding, or domain-semantic action.

## Equivalence gate

Before any model run, exhaustive enumeration over the frozen feature domain must show exact decision-graph/Prolog routing agreement. The committed Prolog file must byte-match a clean regeneration from the canonical IR.

Any disagreement, feature-contract hash mismatch, or generated-file drift is a STOP condition.
