# WP-004 — Causal design and strongest matched controls

Linear issue: `ENG-156`  
Phase: `W0`  
Kind: `work_package`  
Acceptance gate: `GATE-001`

## Ownership

- Producer: **Causal Experiment Reviewer**
- Independent reviewer: **Senior Adversarial Gatekeeper**
- Gatekeeper: **Senior Adversarial Methodology Reviewer**
- Separate identity, session and conflict declaration are mandatory.

## Why now

Solver, typed structure, conclusion, length and renderer effects must be isolated before final power.

## Exact actions

1. Define estimands and one primary contrast; specify mode inputs, hidden fields, factor vectors and budgets.
2. Include M9–M14 controls and freeze DEV-only strongest-baseline selection.
3. Map answer-copying, length, solver and renderer objections to falsification controls.

## Deliverables

- `EpistemicCompilerLab/research-execution/CAUSAL_CONTRASTS.yaml`
- `EpistemicCompilerLab/research-execution/MODE_CONTRACTS`
- `EpistemicCompilerLab/research-execution/ALTERNATIVE_EXPLANATIONS.md`
- `EpistemicCompilerLab/research-execution/BASELINE_SELECTION_RULE.yaml`
- `EpistemicCompilerLab/research-execution/ESTIMANDS.yaml`

## STOP / PIVOT

- PIVOT to minimal decision-contract if effect cannot be separated from ready-answer copying; narrow before data.

Do not move this package to `Done` from the producer session. Producer completion means immutable handoff plus `In Review`.
