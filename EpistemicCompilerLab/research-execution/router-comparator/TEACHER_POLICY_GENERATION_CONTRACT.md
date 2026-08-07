# Teacher policy generation contract

Status: TRAIN/DEV design contract for ENG-200. It does not authorize confirmatory execution.

## Teacher inputs

Codex may receive only:

- TRAIN routing cases and their routing labels;
- the frozen feature schema;
- capability metadata from `ROUTING_CAPABILITY_REGISTRY.yaml`;
- generic security/side-effect constraints;
- the canonical routing-IR schema;
- aggregate DEV routing metrics only after a candidate is generated, if WP-004 later authorizes teacher optimization.

Codex must not receive DEV questions, HOLDOUT, REPLICATION, model outcomes from those splits, final epistemic statuses, or renderer answers.

## Teacher output

The teacher emits only a canonical routing IR conforming to `TEACHER_ROUTING_IR.schema.json` plus an optional explanation derived from the accepted IR.

The IR may inspect frozen request features and choose a canonical capability ID. It may not:

- execute a database, Prolog, Python, or prompt capability;
- compute epistemic status, action, conclusion, or final answer;
- encode case IDs or benchmark questions;
- change capability labels/descriptions as part of the routing-policy treatment;
- create free-form commands or free SQL.

## Freeze and selection

Each candidate records teacher model identity, generation prompt hash, TRAIN input hash, feature schema hash, capability registry hash, IR hash, explanation hash, token budget, and validation result.

Candidate selection, if any, is TRAIN plus aggregate DEV only and is frozen before HOLDOUT. Rejected candidates remain evidence.

## Prototype note

`prototype/policy.ir.json` is a synthetic producer-authored exemplar used to verify the contract and equivalence machinery. It is not represented as an experimental Codex-generated policy and cannot support an empirical teacher-effect claim.
