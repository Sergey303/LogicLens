# ENG-158 / WP-006 — Independent Adversarial Statistical Review

Date: 2026-08-06  
Decision: **REVISE**  
Reviewer role: Adversarial Statistical Reviewer  
Gate impact: `GATE-001`, `WP-105` and feasibility conclusions based on 600 scenarios remain blocked.

## 1. Scope reviewed

- Linear `ENG-158` and producer handoff;
- `statistics/POWER_SIMULATION_PLAN.md`;
- `statistics/ASSUMPTIONS_MANIFEST.yaml`;
- `statistics/power_simulation.py`;
- `statistics/ANALYSIS_REGISTRY.yaml`;
- `statistics/FAILURE_AND_EXCLUSION_RULES.md`;
- frozen table shells;
- current WP-004 causal/baseline contracts;
- `scripts/validate_analysis_registry.py`.

## 2. Confirmed strengths

- The primary unit is `base_scenario_id`; repetitions and paraphrases are aggregated rather than treated as independent samples.
- The simulation is paired and contains shared scenario difficulty, domain/model offsets, paraphrase noise, treatment heterogeneity and run failures.
- The planning effect is not taken from the favorable 18/18 or 24/24 pilots.
- Failures remain in the denominator and complete-case primary analysis is prohibited.
- One primary contrast/endpoint is declared; secondary metric families use frozen multiplicity rules.
- Candidate sizes, seeds and assumptions are written before HOLDOUT.
- The producer correctly reports that 600 total scenarios is not the same as 600 per confirmatory set and sends feasibility to WP-007.

## 3. Blocking findings

### B1 — The power simulation does not power the declared retain rule

The simulation calibrates the true effect to exactly `Δ = 0.08` and declares a detection when:

```text
p < 0.05 and observed Δ > 0
```

But `ANALYSIS_REGISTRY.yaml` requires, among other conditions:

```text
observed point estimate >= 0.08
```

and the claim documents say the confidence interval must support the meaningful-gain decision.

At a true effect exactly equal to `0.08`, an approximately unbiased estimator is above `0.08` only about half the time. Therefore the reported power near `0.91` is power for superiority over zero, not power for the actual claim-retention rule. If the intended criterion is a lower confidence bound above `0.08`, power at a true effect of `0.08` is necessarily very low.

Required correction: choose one coherent design before rerunning.

**Option A — superiority design**

- hypothesis test `H0: Δ <= 0`;
- planning alternative `Δ = 0.08`;
- power target applies to rejecting zero;
- `0.08` is a relevance benchmark reported alongside the estimate, not a hard `point >= 0.08` retention condition.

**Option B — minimum-effect design**

- hypothesis/non-inferiority-style margin `H0: Δ <= 0.08`;
- choose a substantively justified planning alternative strictly larger than `0.08`;
- power the exact margin test and confidence-bound decision.

Do not report power for Option A while applying Option B-like retention language.

### B2 — The 0.08 justification is circularly descriptive

“Eight fewer failures per 100” restates the number; it does not independently justify why the benefit outweighs runtime, annotation, governance, latency and maintenance costs.

Required correction:

- define a decision/utility model or at least a bounded operational cost table;
- state the relative cost of unsupported certainty, unknown/conflict loss and ordinary exact-contract failure;
- justify why 0.05, 0.08 or 0.10 changes the deployment/publication decision;
- perform sensitivity across multiple predeclared meaningful margins;
- coordinate with WP-007 feasibility without choosing the margin to fit available resources.

### B3 — Source/rule-family clustering is absent

The simulation contains scenario, domain, model and paraphrase effects, but no source-family, rule-template, entity-family or document-version cluster effects. Those are the exact grouping dimensions used to prevent leakage and are likely to induce correlated outcomes.

McNemar assumes independent scenario pairs. Treating many scenarios from the same source/rule family as independent can materially overstate effective sample size and power.

Required correction:

- simulate declared source/rule/entity family cluster sizes and intraclass correlations;
- freeze maximum cases per family;
- use a primary inferential method valid for the sampling design, such as cluster-aware randomization/bootstrap or a justified hierarchical model;
- power the same method used for the primary claim, not only ordinary McNemar;
- retain McNemar as a complementary paired summary if desired.

### B4 — Failure model is too favorable

Failures are simulated as equal, independent Bernoulli events for M6 and M14. Real failures may be:

- correlated within an infrastructure block;
- mode-specific;
- model-specific;
- dependent on input length/complexity;
- more common for the longer full-source M14 or for compiler-dependent M6.

Required correction: add adverse scenarios with correlated block failures, differential mode failure rates, length-dependent failures and asymmetric retry exhaustion. Apply the exact frozen block-rerun rule.

### B5 — Target population and weights are undefined

The design equally balances 3 domains × 4 model profiles, assigning one model profile to each base scenario. The primary effect is therefore an artificial equal-weight mixture unless a target population and weighting rule are declared.

Required correction:

- define whether the estimand is equal-weight over profiles/domains, deployment-weighted, or a finite benchmark average;
- freeze stratum weights and missing/failure handling;
- explain why a scenario is evaluated by one model profile rather than crossed across profiles;
- distinguish pooled bundle efficacy from per-profile generalization;
- power any model-family claim separately or explicitly classify it as descriptive/secondary.

### B6 — Paraphrase/repeat design is not justified or optimized

Two paraphrases, three repetitions, majority-of-three and “all paraphrases pass” are frozen without comparison to alternative allocations. This rule can turn small per-run differences into a harsh scenario-level endpoint and substantially changes both cost and power.

Required correction:

- compare predeclared designs such as more scenarios/fewer repeats, one versus two paraphrases, and alternative scenario aggregation;
- use expected information/power per model call and robustness to stochasticity;
- choose the design before dataset scaling;
- report sensitivity of required scenarios and total calls.

### B7 — Joint HOLDOUT/REPLICATION success probability is not evaluated

The manuscript retain rule requires both a HOLDOUT result and agreeing independent replication. Power is reported separately for one set and then 600 is copied to replication.

Required correction:

- define the exact replication success criterion: direction only, confidence interval, minimum effect or significance;
- simulate the joint probability that the full publication decision passes;
- report expected probabilities of `retain`, `narrow`, `null`, `replication reversal` and `stop`;
- justify the replication sample size from that rule rather than automatically duplicating HOLDOUT.

### B8 — Monte Carlo uncertainty and seed robustness are not part of the gate

At 600 the design power is only about 0.91, close to the 0.90 boundary. One seed and 4000 replications are insufficient for an unqualified “first PASS” without a frozen Monte Carlo uncertainty rule.

Required correction:

- require a conservative confidence bound for estimated power or substantially more simulations near the boundary;
- rerun several predeclared seeds;
- use an adaptive simulation count based only on Monte Carlo uncertainty, not favorable power;
- require the lower confidence bound to satisfy the target or choose the next candidate size.

### B9 — The central result artifact is not committed

`POWER_RESULTS.json` is described as transient and only its hash is recorded. The numeric recommendation cannot be verified byte-for-byte from the repository, and the Python dependency environment is not lock-pinned.

Required correction:

- commit the result JSON under an allowed generated-artifact path;
- record exact command, script/assumption/result hashes and software lock/container;
- include calibration values and every candidate row;
- add an independent reproduction check comparing regenerated bytes or canonical semantic content.

### B10 — Cross-package baseline drift

WP-006 references `DEV-GLOBAL-STRONGEST-MATCHED-V1`; current WP-004 freezes `V2` and has materially different lossless matching/profile sensitivity.

Required correction: synchronize exact comparator, rule version, estimand and falsification criteria before any power rerun. A semantic validator must fail on future drift.

### B11 — No semantic validator

`validate_analysis_registry.py` is a generic wrapper. It does not verify:

- exact cross-file primary IDs;
- coherence of hypothesis, retention and power decision rules;
- source-cluster assumptions;
- result JSON/hash;
- table-shell coverage;
- failure/retry alignment;
- replication rule;
- V1/V2 drift;
- scenario/call arithmetic;
- prohibited complete-case or post-HOLDOUT changes.

Required correction: commit a non-mutating statistical validator and a machine-readable independent-review report.

### B12 — Pre-execution token-fit failure is misclassified

`FAILURE_AND_EXCLUSION_RULES.md` counts “inability to token-match M14” as an incorrect model outcome. Current WP-004 says over-context scenarios must fail benchmark construction before split assignment and never become scored missing observations.

Required correction: align the rule:

- pre-split lossless-envelope infeasibility is a benchmark-construction rejection, recorded before assignment;
- post-freeze unexpected transformation/hash drift is a protocol failure invalidating the affected block;
- it is not an ordinary semantic incorrect response.

## 4. Status of the 600-scenario recommendation

The current simulation is useful exploratory planning evidence, but **600 HOLDOUT + 600 REPLICATION is not yet a valid powered recommendation**. It may remain a provisional feasibility upper-bound input only, clearly labeled as such.

## 5. Decision

**REVISE.** Reconcile the exact decision rule, justify the meaningful margin, model family clustering/failures/weights, optimize paraphrase/repeat allocation, power the joint replication decision, control Monte Carlo uncertainty, commit results, synchronize WP-004 V2 and add semantic validation before re-review.
