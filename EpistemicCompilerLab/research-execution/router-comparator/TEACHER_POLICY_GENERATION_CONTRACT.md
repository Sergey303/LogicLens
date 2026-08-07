# Teacher policy generation contract

Status: TRAIN/DEV design contract for ENG-200. It does not authorize confirmatory execution.

## Independent feature boundary

The normative routing feature contract is `ROUTING_FEATURE_CONTRACT.json`.
It is owned and frozen independently of the teacher policy. Every teacher-policy candidate MUST record the exact feature-contract ID and SHA-256 and is invalid if that hash changes.

For the primary routing-policy comparison, the teacher, deterministic router, M20 Qwen router, and direct-Qwen selection baseline operate on the same typed feature vocabulary. Raw natural-language feature extraction is not part of the primary M19-vs-M20 contrast.

## Teacher inputs

Codex may receive only:

- TRAIN routing cases and their routing labels;
- the frozen feature contract and its hash;
- capability metadata from `ROUTING_CAPABILITY_REGISTRY.yaml`;
- typed capability I/O schemas from `CAPABILITY_IO_SCHEMAS.json`;
- generic security, budget, and failure-semantics constraints;
- the canonical routing-IR schema;
- aggregate DEV routing metrics only after a candidate is generated, if WP-004 later authorizes teacher optimization.

Codex must not receive DEV questions, HOLDOUT, REPLICATION, model outcomes from those splits, final epistemic statuses, or renderer answers.

## Teacher output

The teacher emits only a canonical routing IR conforming to `TEACHER_ROUTING_IR.schema.json` plus an optional explanation derived from the accepted IR.

The IR may inspect the frozen typed request features and choose a canonical capability ID. It may not:

- parse raw natural-language questions in the primary M19-vs-M20 contrast;
- execute a database, Prolog, Python, or prompt capability;
- compute epistemic status, action, conclusion, or final answer;
- bind tool arguments;
- encode case IDs or benchmark questions;
- change capability labels/descriptions as part of the routing-policy treatment;
- create free-form commands or free SQL.

## Capability-only scope

ENG-200 evaluates **capability selection only**. Argument binding is owned by the independent held-equal adapter defined in `ARGUMENT_BINDING_CONTRACT.md`. A teacher candidate that emits or modifies arguments is out of scope and invalid.

## Freeze and selection

Each candidate records teacher model identity, generation prompt hash, TRAIN input hash, feature-contract ID/hash, capability registry hash, capability-I/O-schema hash, IR hash, explanation hash, token budget, and validation result.

Candidate selection, if any, is TRAIN plus aggregate DEV only and is frozen before HOLDOUT. Rejected candidates remain evidence.

## Prototype note

`prototype/policy.ir.json` is a synthetic producer-authored exemplar used to verify the contract and equivalence machinery. It is not represented as an experimental Codex-generated policy and cannot support an empirical teacher-effect claim.
