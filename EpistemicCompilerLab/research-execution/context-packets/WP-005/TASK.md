# WP-005 — Independent oracle/scorer boundary

Linear issue: `ENG-157`  
Phase: `W0`  
Kind: `work_package`  
Acceptance gate: `GATE-001`  
Remediation version: **R2 lifecycle closure, 2026-08-11**

## Ownership

- Producer: **Independent Oracle Architect**
- Independent reviewer: **Mutation and Dependency Auditor**
- Gatekeeper: **Senior Adversarial Methodology Reviewer**
- Separate identity, session and conflict declaration are mandatory.
- The context that produces this R2 remediation is conflicted from independently accepting it.

## Why now

Confirmatory evidence requires validation path B independent of production path A. Independent R2 retained the semantic/clean-room backbone but found four bounded governance defects: stale packet field vocabulary, preflight evidence inconsistent with candidate bytes, contradictory gold/B freeze ordering, and validators unable to catch candidate-wide lifecycle drift.

## Exact actions

1. Preserve the already reviewed four-state semantic registry, declarative policy, invariant/mutation/human-audit and clean-room dependency backbone.
2. Freeze one lifecycle in which blind query/outcome gold is completed and hash-frozen before B-oracle execution, while outcome gold is physically unavailable to B during computation.
3. Make outcome gold the sole scorer expected-value authority; B-oracle is an independent consistency implementation and may neither override nor repair gold.
4. Align `ORACLE_PACKET_CONTRACT.json`, `GOLD_ADJUDICATION_PROTOCOL.json`, `INDEPENDENCE_BOUNDARY.md` and acceptance metadata to the same lifecycle and exact positive/negative evidence-root + proof-normal-form vocabulary.
5. Add a fail-closed cross-artifact lifecycle validator and frozen negative regression fixtures for the two R2 failure classes: legacy generic evidence vocabulary and B execution before blind outcome-gold freeze.
6. Regenerate producer preflight evidence on the exact immutable candidate bytes; do not reuse prior PASS claims.

## Original deliverables retained

- `EpistemicCompilerLab/research-execution/oracle/SEMANTIC_SPEC.md`
- `EpistemicCompilerLab/research-execution/oracle/INDEPENDENCE_BOUNDARY.md`
- `EpistemicCompilerLab/research-execution/oracle/MUTATION_MATRIX.yaml`
- `EpistemicCompilerLab/research-execution/oracle/DEPENDENCY_AUDIT_PLAN.md`

## R2 remediation deliverables

- `EpistemicCompilerLab/research-execution/oracle/ORACLE_LIFECYCLE_CONTRACT.json`
- `EpistemicCompilerLab/research-execution/oracle/ORACLE_LIFECYCLE_NEGATIVE_FIXTURES.json`
- aligned `ORACLE_PACKET_CONTRACT.json`
- aligned `GOLD_ADJUDICATION_PROTOCOL.json`
- aligned `INDEPENDENCE_BOUNDARY.md`
- cross-artifact `validate_oracle_gold_governance.py`
- updated versioned acceptance/write-scope metadata
- fresh machine-executed producer preflight tied to one immutable candidate
- final immutable remediation handoff committed after the candidate

## Acceptance boundary

Producer-side PASS requires all current semantic/boundary validators plus lifecycle governance to pass on the same candidate and both lifecycle negative fixtures to fail for their expected reasons.

Producer PASS is **not**:

- accepted Path B implementation;
- execution of future dependency/canary audit against Path B;
- execution of the frozen 120-case human audit;
- independent Mutation and Dependency Auditor approval;
- GATE-001 approval;
- authorization to access HOLDOUT or REPLICATION.

## STOP / PIVOT

- STOP confirmatory route until redesign if B can observe outcome gold, expected outcome/frame or model output while computing.
- STOP if outcome gold can be repaired from B/model behavior or if B can override gold.
- STOP if the lifecycle is not identical across acceptance, machine lifecycle, gold protocol, packet stage bindings and boundary documentation.
- STOP if either frozen lifecycle negative fixture survives.
- PIVOT is not required merely for these governance defects; independent reviewer decides after the bounded remediation.

Do not move this package to `Done` from the producer session. Producer completion means immutable handoff plus `In Review`.
