# WP-006 — Power and confirmatory analysis plan

Linear issue: `ENG-158`  
Phase: `W0`  
Kind: `work_package`  
Acceptance gate: `GATE-001`

## Ownership

- Producer: **Statistical Design Reviewer**
- Independent reviewer: **Adversarial Statistical Reviewer**
- Gatekeeper: **Senior Adversarial Methodology Reviewer**
- Separate identity, session and conflict declaration are mandatory.

## Why now

Sample size, estimands, exclusions and multiplicity must be fixed before scaling.

## Exact actions

1. Justify smallest meaningful effect independently; implement clustered paired simulation with failures/heterogeneity.
2. Fix base_scenario_id as unit, nesting, one endpoint/contrast, secondary families, correction and exclusions.
3. Produce table shells and feasibility interface.

## Deliverables

- `EpistemicCompilerLab/research-execution/statistics/POWER_SIMULATION_PLAN.md`
- `EpistemicCompilerLab/research-execution/statistics/ANALYSIS_REGISTRY.yaml`
- `EpistemicCompilerLab/research-execution/statistics/FAILURE_AND_EXCLUSION_RULES.md`
- `EpistemicCompilerLab/research-execution/statistics/power_simulation.py`
- `EpistemicCompilerLab/research-execution/statistics/ASSUMPTIONS_MANIFEST.yaml`
- `EpistemicCompilerLab/research-execution/statistics/table-shells`

## STOP / PIVOT

- If infeasible, narrow models/modes/domains or claim before data; never lower power after results.

Do not move this package to `Done` from the producer session. Producer completion means immutable handoff plus `In Review`.
