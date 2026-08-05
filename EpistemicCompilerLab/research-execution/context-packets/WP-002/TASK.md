# WP-002 — Claim–evidence matrix and abstract contract

Linear issue: `ENG-154`  
Phase: `W0`  
Kind: `work_package`  
Acceptance gate: `GATE-001`

## Ownership

- Producer: **Claim–Evidence Architect**
- Independent reviewer: **Manuscript Evidence Reviewer**
- Gatekeeper: **Senior Adversarial Methodology Reviewer**
- Separate identity, session and conflict declaration are mandatory.

## Why now

Claims must be bound to planned evidence and null wording before confirmatory design.

## Exact actions

1. Define claim-row schema, estimand, metric, table ID, control, alternative explanation and null wording.
2. Create one row per draft-abstract sentence; freeze prohibited wording; delete/future-work unsupported claims.

## Deliverables

- `EpistemicCompilerLab/research-execution/CLAIM_EVIDENCE_MATRIX.yaml`
- `EpistemicCompilerLab/research-execution/ABSTRACT_CONTRACT.md`
- `EpistemicCompilerLab/research-execution/PROHIBITED_CLAIMS.md`
- `EpistemicCompilerLab/research-execution/schemas/claim-evidence-row.schema.json`

## STOP / PIVOT

- Delete or narrow any claim not testable by a frozen experiment; pilots do not satisfy confirmatory rows.

Do not move this package to `Done` from the producer session. Producer completion means immutable handoff plus `In Review`.
