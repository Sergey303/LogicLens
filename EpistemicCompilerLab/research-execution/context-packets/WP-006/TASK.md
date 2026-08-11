# WP-006 — Power and confirmatory analysis plan

Linear issue: `ENG-158`  
Phase: `W0`  
Kind: `work_package`  
Acceptance gate: `GATE-001`  
Remediation version: **R2 statistical contract, 2026-08-11**

## Ownership

- Producer: **Statistical Design Reviewer**
- Independent reviewer: **Adversarial Statistical Reviewer**
- Gatekeeper: **Senior Adversarial Methodology Reviewer**
- Separate identity/session/conflict declaration is mandatory.
- The context producing this R2 remediation is conflicted from independently accepting it.

## Why now

Sample size, estimand, failure treatment, nesting and multiplicity must be fixed before scaling. Independent R2 found that the previous producer candidate still had two active-looking statistical specifications, unit drift, an analytical `N=802` with Monte-Carlo power below 0.90, no explicit heterogeneous/failure-aware joint HOLDOUT+REPLICATION design, weak dependency attestations and a nuisance update that could lower N from favorable estimates.

## One statistical authority

The original `statistics/*` package remains as historical/reproducibility material. `statistics/ANALYSIS_REGISTRY.yaml` is now an explicit supersession pointer. The normative R2 package is:

`EpistemicCompilerLab/research-execution/power-analysis/`

Machine authority: `power-analysis/WP006_STATISTICAL_AUTHORITY.json`.

## Exact R2 actions

1. Keep `base_scenario_id` as the only independent primary analysis unit. Paraphrases, repeats, training/model seeds and infrastructure reruns are nested and never multiply benchmark N.
2. Keep one binary primary endpoint: `publication_composite_correctness` after frozen repeat/paraphrase aggregation; declared runtime/model failures count as incorrect.
3. Keep superiority `H0: delta=0`, two-sided alpha 0.05. SESOI `+0.08` is an auditable planning/practical-reference alternative, not a hard observed point-estimate retain gate.
4. Implement frozen heterogeneous paired Monte-Carlo planning with 3 domains × 4 model profiles, source-family dependence and explicit correlated/arm-specific failures scored incorrect.
5. Use CR1 source-family cluster robust variance with Student-t `df=G-1`; independently calibrate Type-I error at exactly 30 source-family clusters.
6. Power **joint** success: HOLDOUT positive two-sided significance plus independently sourced REPLICATION positive direction, with a one-sided 95% Monte-Carlo lower bound >=0.90 at SESOI.
7. Never lower the R2 N from a favorable nuisance update. At most one blinded update may increase N using conservative one-sided nuisance bounds.
8. Replace free-text/fake dependency references in the real power gate with locally resolved machine attestations tied to accepted WP-004/WP-005/WP-007 artifacts and hashes.
9. Keep final confirmatory arm IDs, final inventory and final N unauthorized until required upstream packages are independently accepted.

## R2 deliverables

- `power-analysis/WP006_STATISTICAL_AUTHORITY.json`
- `power-analysis/SESOI_UTILITY_CONTRACT.md`
- `power-analysis/PRIMARY_ANALYSIS_CONTRACT.json`
- `power-analysis/BLINDED_NUISANCE_UPDATE_PROTOCOL.json`
- `power-analysis/R2_SIMULATION_SCENARIOS.json`
- `power-analysis/prototype/simulate_power_r2.py`
- R2 simulation result + machine validator
- fail-closed dependency resolver/power gate
- versioned acceptance + immutable producer handoff

Historical original deliverables under `statistics/` are retained and explicitly superseded rather than silently rewritten.

## Producer acceptance boundary

Producer-side readiness requires:

- one authority with no competing active statistical registry;
- exact `base_scenario_id` unit/nesting contract;
- successful frozen R2 Type-I and joint-power Monte-Carlo gates with uncertainty bounds;
- no accepted final N below the public non-decreasing floor `802`;
- real dependency/inventory gate still `NOT_EVALUATED` until accepted upstream artifacts exist;
- no HOLDOUT/REPLICATION access;
- immutable handoff for distinct Adversarial Statistical Reviewer.

Producer readiness is not independent statistical PASS, GATE-001 approval or authorization to score sealed data.

## STOP / PIVOT

- STOP if the R2 Type-I calibration fails or no feasible N in the frozen grid reaches the joint lower-bound target; redesign before data.
- STOP if exact arm/scorer/feasibility dependencies cannot be machine-resolved before confirmatory freeze.
- If infeasible, narrow models/modes/domains or claim before data; never lower power/SESOI after outcomes.
- Never treat repeated model calls, seeds or infrastructure runs as additional `base_scenario_id` units.

Do not move this package to `Done` from the producer session. Producer completion means immutable handoff plus `In Review`.
