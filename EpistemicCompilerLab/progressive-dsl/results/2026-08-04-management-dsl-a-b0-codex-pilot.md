# Management DSL-A → DSL-B0 Codex pilot

Date: 2026-08-04  
Status: completed engineering pilot  
Model selection: Codex account default  
Repetitions: 1  
Cases: 4  
Calls: 12

## Frozen inputs

- LogicLens commit used by the run: `a177c8cb203a29cc8c929f4676e27f39f62b672c`
- CTO Practical Simulation commit: `50cd1d9067ce83f775cbdc23ce2259b8103c9436`
- cases hash: `sha256:3ad97b17b0159602cbe638905726d441d4ac1554365b29535c2dc46af043b667`
- prompt hash: `sha256:916fcef1a2bfa011d5f8b4cc896d5ecc2f85686956b7228f61246d40959b166b`
- response schema hash: `sha256:c962f9864f67464c572c0171b4535a50e6850bc9cbef66f1613daab9befa9488`
- DSL-A package: `sha256:7a8b529a9acde057ee667a3b3862e1db1006cc278959e92d213a25d337ea8e70`
- DSL-B0 package: `sha256:cd16f30bea7e4233737f3583e3cc943ea66c04ff583f21ed6466ba10a3ab9772`

## Aggregate results

| Condition | Task status | Task action | Frame status | Frame action | Evidence exact | Proof recall | Warning recall | Mean latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Direct | 1.00 | 0.50 | n/a | n/a | n/a | n/a | 0.00 | 12.866 s |
| Gold DSL-A | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | n/a | 1.00 | 9.035 s |
| Gold DSL-B0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 10.204 s |

No condition fabricated an evidence ID or proof node. Scope qualification and abstention fields were correct in every record.

## What the pilot supports

### 1. Codex follows a verified epistemic frame

With DSL-A, all four queried delegation claims were `unknown`. Codex preserved that status, abstained, returned no evidence and requested local organisational context.

With DSL-B0, all four claims became `supported` through local logical rules. Codex preserved the status and action, returned the exact rule root, copied every proof node, retained `derived-evidence-present` and `local-only`, and avoided universalising the local policy.

This supports frame adherence and proof transport under a schema-constrained prompt.

### 2. DSL version changes the answer without changing the question

The same four questions produced honest abstention under DSL-A and qualified support under DSL-B0. The difference is attributable to the additional executable rules, because the source management world and the questions remained unchanged.

### 3. The runtime is not the observed error source

The DSL-B0 frames had already been cross-verified between the Python reference evaluator and SWI-Prolog. Codex introduced no evidence or proof corruption in this pilot.

## What the pilot does not support

### 1. It does not demonstrate a task-accuracy gain over Direct

Direct Codex marked all four claims `supported`, matching the DSL-B0 task status in every case. The questions described ordinary management delegation patterns that the model could infer from parametric knowledge.

Two Direct answers selected `explain_explicit_role_boundary` rather than `answer_with_source_scope`, which reduced action accuracy, but their natural-language management advice was still broadly reasonable. Therefore the B0 case set is too guessable to establish that the capsule improves ordinary answer correctness.

### 2. Proof recall is not yet proof reasoning

Codex returned all proof-node IDs when they were supplied. This establishes faithful use of the frame, not that the model independently checked the logical derivation. A later ablation must compare full proof DAG, rule root only, raw premises only and deliberately corrupted proof structures.

### 3. Latency differences are not statistically interpretable

There were only four calls per condition and one repetition. Gold DSL-B0 was about 1.17 seconds slower than Gold DSL-A but about 2.66 seconds faster than Direct. These values are descriptive only and may be dominated by service variance.

## Decision caused by this pilot

Do not move directly to DSL-C based on B0.

First run a non-guessable DSL-B1 tranche containing:

- private local policy outcomes absent from model training;
- supported, refuted, conflicting and unknown targets;
- a two-hop proof;
- `any` semantics;
- a `notExplicit` premise;
- cases where general management intuition points in the wrong direction;
- a no-rule control.

The purpose of B1 is to test information necessity and epistemic discipline, not merely proof-frame formatting.

## Publication interpretation

The defensible pilot claim is:

> Codex can preserve verified open-world statuses, exact evidence roots, proof DAGs, warnings and local scope when these are supplied by LogicLens; however, the first ordinary-management case set does not show an accuracy advantage over direct parametric answering.

This result motivates the non-guessable B1 experiment rather than counting as positive evidence for a broad performance claim.
