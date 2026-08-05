# WP-005 — Independent oracle/scorer boundary

Linear issue: `ENG-157`  
Phase: `W0`  
Kind: `work_package`  
Acceptance gate: `GATE-001`

## Ownership

- Producer: **Independent Oracle Architect**
- Independent reviewer: **Mutation and Dependency Auditor**
- Gatekeeper: **Senior Adversarial Methodology Reviewer**
- Separate identity, session and conflict declaration are mandatory.

## Why now

Confirmatory evidence requires validation path B independent of production path A.

## Exact actions

1. Write implementation-independent semantics and the only shared A/B surfaces.
2. Enumerate critical mutations; define property, mutation, human and differential tests.
3. Specify clean-room implementation context and dependency scanner.

## Deliverables

- `EpistemicCompilerLab/research-execution/oracle/SEMANTIC_SPEC.md`
- `EpistemicCompilerLab/research-execution/oracle/INDEPENDENCE_BOUNDARY.md`
- `EpistemicCompilerLab/research-execution/oracle/MUTATION_MATRIX.yaml`
- `EpistemicCompilerLab/research-execution/oracle/DEPENDENCY_AUDIT_PLAN.md`

## STOP / PIVOT

- STOP confirmatory route until redesign if independence or semantic agreement cannot be demonstrated.

Do not move this package to `Done` from the producer session. Producer completion means immutable handoff plus `In Review`.
