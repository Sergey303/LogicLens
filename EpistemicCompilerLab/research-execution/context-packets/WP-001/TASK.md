# WP-001 — Executable research-program DAG

Linear issue: `ENG-153`  
Phase: `W0`  
Kind: `work_package`  
Acceptance gate: `GATE-001`

## Ownership

- Producer: **Research Program Architect**
- Independent reviewer: **Senior Adversarial Gatekeeper**
- Gatekeeper: **Senior Adversarial Methodology Reviewer**
- Separate identity, session and conflict declaration are mandatory.

## Why now

Every later package depends on an exact executable DAG; the previous artifact received REVISE.

## Exact actions

1. Transcribe all mandatory issues, exact roles, direct dependencies and complete deliverables.
2. Define exact context packets, actions, commands, checks, STOP/PIVOT and handoffs.
3. Represent composite issue splits as independent execution units.
4. Add optional robustness, blind W3, actual submission, W5, validator and immutable report.

## Deliverables

- `EpistemicCompilerLab/research-execution/WORK_PACKAGES.yaml`
- `EpistemicCompilerLab/research-execution/CRITICAL_PATH.md`
- `EpistemicCompilerLab/research-execution/schemas/work-package.schema.json`
- `EpistemicCompilerLab/research-execution/schemas/work-package-handoff.schema.json`
- `EpistemicCompilerLab/research-execution/scripts/validate_work_packages.py`
- `EpistemicCompilerLab/research-execution/validation/linear-relations-snapshot.json`
- `EpistemicCompilerLab/research-execution/validation/validation-report.json`

## STOP / PIVOT

- STOP if a node lacks a claim/threat link.
- REVISE on any Linear snapshot drift.
- No self-acceptance.

Do not move this package to `Done` from the producer session. Producer completion means immutable handoff plus `In Review`.
