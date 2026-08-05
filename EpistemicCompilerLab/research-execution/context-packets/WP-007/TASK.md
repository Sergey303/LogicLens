# WP-007 — Resource, compute and annotation feasibility

Linear issue: `ENG-188`  
Phase: `W0`  
Kind: `work_package`  
Acceptance gate: `GATE-001`

## Ownership

- Producer: **Research Feasibility Architect**
- Independent reviewer: **Independent Budget and Operations Reviewer**
- Gatekeeper: **Senior Adversarial Methodology Reviewer**
- Separate identity, session and conflict declaration are mandatory.

## Why now

GATE-001 cannot authorize a powered benchmark without compute, staffing, licensing, storage and schedule feasibility.

## Exact actions

1. Estimate source/scenario/A-B annotation/adjudication workload; specify independent roles.
2. Estimate calls, tokens, time, RAM/VRAM, storage and teacher budgets per cell.
3. Model best/base/worst cases, provider loss, contingencies preserving estimand and hard stops.

## Deliverables

- `EpistemicCompilerLab/research-execution/feasibility/RESOURCE_ENVELOPE.yaml`
- `EpistemicCompilerLab/research-execution/feasibility/ANNOTATION_STAFFING_PLAN.md`
- `EpistemicCompilerLab/research-execution/feasibility/COMPUTE_BUDGET.md`
- `EpistemicCompilerLab/research-execution/feasibility/CONTINGENCY_TREE.md`

## STOP / PIVOT

- Return feasible / feasible after narrowing / infeasible; narrow before case generation.

Do not move this package to `Done` from the producer session. Producer completion means immutable handoff plus `In Review`.
