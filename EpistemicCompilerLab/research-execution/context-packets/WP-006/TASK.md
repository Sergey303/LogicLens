# WP-006 — Power and confirmatory analysis plan

Linear issue: `ENG-158`  
Phase: `W0`  
Kind: `work_package`  
Acceptance gate: `GATE-001`  
Remediation version: **R3 endpoint-identity normalization over unchanged R2 statistical design, 2026-08-11**

## Ownership

- Producer: **Statistical Design Reviewer**
- Independent reviewer: **Adversarial Statistical Reviewer**
- Gatekeeper: **Senior Adversarial Methodology Reviewer**
- Separate identity/session/conflict declaration is mandatory.
- The context producing the R2/R3 remediation is conflicted from independently accepting it.

## Why now

Sample size, estimand, failure treatment, nesting, endpoint identity and multiplicity must be fixed before scaling. Independent R2 found competing statistical specifications, unit drift, an analytical `N=802` whose Monte-Carlo lower-bound evidence was insufficient, incomplete heterogeneous/failure-aware joint HOLDOUT+REPLICATION design, weak dependency attestations and a nuisance update that could lower N from favorable estimates. A later WP-004 integration audit found one additional naming defect: WP-006 called the primary event `publication_composite_correctness` while WP-002/WP-004 use the flagship identifier `scenario_level_exact_epistemic_contract_accuracy`.

## One statistical authority

The original `statistics/*` package remains historical/reproducibility material. `statistics/ANALYSIS_REGISTRY.yaml` is an explicit supersession pointer. The normative package is:

`EpistemicCompilerLab/research-execution/power-analysis/`

Machine authority: `power-analysis/WP006_STATISTICAL_AUTHORITY.json`.

Canonical endpoint identity: `power-analysis/ENDPOINT_IDENTITY_CONTRACT.json`.

## Exact R3-over-R2 actions

1. Keep `base_scenario_id` as the only independent primary analysis unit. Paraphrases, repeats, training/model seeds and infrastructure reruns are nested and never multiply benchmark N.
2. Use exactly one canonical binary primary endpoint: **`scenario_level_exact_epistemic_contract_accuracy`**. The legacy phrase `publication_composite_correctness` names only the response-level conjunction that every applicable publication-critical scorer field is correct. The canonical scenario endpoint applies the already frozen `2-of-3` repeat rule and `all-2` mandatory-paraphrase rule. Declared runtime/model failures count as incorrect.
3. Treat endpoint normalization as an identifier repair only. It must not change the WP-005 scorer, field applicability, aggregation, denominator, failure handling, R2 simulation config/result bytes, random seeds, selected producer floor, SESOI or hypothesis.
4. Keep superiority `H0: delta=0`, two-sided alpha 0.05. SESOI `+0.08` is an auditable planning/practical-reference alternative, not a hard observed point-estimate retain gate.
5. Keep the frozen heterogeneous paired Monte-Carlo planning with 3 domains × 4 model profiles, source-family dependence and explicit correlated/arm-specific failures scored incorrect.
6. Use CR1 source-family cluster robust variance with Student-t `df=G-1`; Type-I error remains independently calibrated at exactly 30 source-family clusters.
7. Power **joint** success: HOLDOUT positive two-sided significance plus independently sourced REPLICATION positive direction, with a one-sided 95% Monte-Carlo lower bound >=0.90 at SESOI.
8. Never lower the R2 producer floor from a favorable nuisance update. At most one blinded update may increase N using conservative one-sided nuisance bounds.
9. Real power-gate dependencies must be locally resolved machine attestations tied to accepted WP-004/WP-005/WP-007 artifacts and hashes; free text and fake hashes cannot produce PASS.
10. Keep final confirmatory arm IDs, final inventory and final N unauthorized until required upstream packages are independently accepted.

## R3/R2 deliverables

- `power-analysis/WP006_STATISTICAL_AUTHORITY.json`
- `power-analysis/ENDPOINT_IDENTITY_CONTRACT.json`
- `power-analysis/SESOI_UTILITY_CONTRACT.md`
- `power-analysis/PRIMARY_ANALYSIS_CONTRACT.json`
- `power-analysis/BLINDED_NUISANCE_UPDATE_PROTOCOL.json`
- unchanged `power-analysis/R2_SIMULATION_SCENARIOS.json`
- unchanged `power-analysis/R2_SIMULATION_RESULT.json`
- unchanged `power-analysis/R2_SIMULATION_EVIDENCE.json`
- R2/R3 machine validator;
- fail-closed dependency resolver/power gate;
- immutable producer handoff for a distinct reviewer.

Historical original deliverables under `statistics/` are retained and explicitly superseded rather than silently rewritten.

## Producer acceptance boundary

Producer-side readiness requires:

- one authority with no competing active statistical registry;
- exact canonical endpoint alignment with WP-002/WP-004, backed by the versioned endpoint-identity contract;
- exact `base_scenario_id` unit/nesting contract;
- successful frozen R2 Type-I and joint-power Monte-Carlo gates with uncertainty bounds;
- producer grid floor `820` unchanged by the identifier remediation;
- real dependency/inventory gate still `NOT_EVALUATED` until accepted upstream artifacts exist;
- no HOLDOUT/REPLICATION access;
- immutable handoff for distinct Adversarial Statistical Reviewer.

Producer readiness is not independent statistical PASS, GATE-001 approval or authorization to score sealed data.

## STOP / PIVOT

- STOP if the endpoint identity contract cannot prove identical response scoring, aggregation, denominator and failure handling; then this is not a naming repair and R2 must be redesigned/recomputed before sealed data.
- STOP if the R2 Type-I calibration fails or no feasible N in the frozen grid reaches the joint lower-bound target; redesign before data.
- STOP if exact arm/scorer/feasibility dependencies cannot be machine-resolved before confirmatory freeze.
- If infeasible, narrow models/modes/domains or claim before data; never lower power/SESOI after outcomes.
- Never treat repeated model calls, seeds or infrastructure runs as additional `base_scenario_id` units.

Do not move this package to `Done` from the producer session. Producer completion means immutable handoff plus `In Review`.
