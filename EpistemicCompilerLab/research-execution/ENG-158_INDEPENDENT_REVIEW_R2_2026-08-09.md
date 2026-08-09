# ENG-158 / WP-006 — Independent Adversarial Statistical Review R2

Date: 2026-08-09

Reviewer role: **Adversarial Statistical Reviewer**.

Reviewer context: `ChatGPT ENG-158 independent statistical review R2 / 2026-08-09`.

This is a distinct reviewer context from the recorded 2026-08-09 WP-006 producer session. It is not represented as independent human or organizational review.

## Decision

**REVISE — no PIVOT.**

The new candidate is materially stronger than the 2026-08-06 design. In particular, it corrects the earlier mismatch between powering a zero-null superiority test and requiring an observed point estimate >= .08, introduces a source-family clustered paired design, freezes one primary contrast, adds a blinded nuisance-update protocol, separates system failures from scientific non-evaluability, and implements an executable power gate.

However, the candidate cannot receive statistical PASS yet. There are multiple contract/governance contradictions and several machine-gate false-PASS paths. The analytical N=802 is also not robust to the candidate's own frozen Monte-Carlo stress check.

## Candidate resolution

The handoff commit is:

`cf874078571503a8b6558a8138ef9360f9fc5e20`

The handoff states that the scientific candidate is the first parent of the handoff-introducing commit. Git comparison confirms that:

`10fb57c65b39782031155f23ed8f0a7bcdef830e -> cf874078571503a8b6558a8138ef9360f9fc5e20`

contains exactly one commit and only adds the handoff JSON.

Therefore this review evaluates the scientific candidate at:

`10fb57c65b39782031155f23ed8f0a7bcdef830e`

No HOLDOUT or REPLICATION data were accessed.

---

## What is accepted from this revision

The following design choices are good and should be retained unless another blocker requires a versioned change:

1. **One primary semantic fixed-weight contrast**, with exact executable arm IDs deferred to accepted WP-004 and best-DEV-arm selection prohibited.
2. **Binary paired endpoint** and paired treatment-minus-control absolute correctness difference.
3. **Two-sided alpha .05** and target power .90.
4. **Source-family clustering** as the primary dependence boundary.
5. **System/model failures are not silently dropped** merely because they hurt an arm.
6. **One pre-HOLDOUT blinded nuisance update at most**, with signed arm direction hidden from the power analyst.
7. **No optional stopping / significance-based extension.**
8. **Negative gate fixtures** for underpowered N and too few clusters.
9. The earlier mathematical error is corrected inside the new `power-analysis` package: .08 is a planning alternative/SESOI for a two-sided zero-null test, not a hard observed-point-estimate threshold in the new primary contract.

These are real improvements, not merely documentation changes.

---

# Blocking findings

## B1 — CRITICAL — WP-006 now has two incompatible normative specifications and the new package violates the frozen allowed-path contract

The frozen WP-006 task requires deliverables under:

- `research-execution/statistics/POWER_SIMULATION_PLAN.md`
- `statistics/ANALYSIS_REGISTRY.yaml`
- `statistics/FAILURE_AND_EXCLUSION_RULES.md`
- `statistics/power_simulation.py`
- `statistics/ASSUMPTIONS_MANIFEST.yaml`
- `statistics/table-shells/`

and `ALLOWED_PATHS.txt` permits only those `statistics/...` paths, the WP-006 context packet, and `handoffs/WP-006.json`.

The new candidate instead introduces its claimed normative statistical package under `research-execution/power-analysis/` and uses a different handoff path. No versioned supersession or allowed-path amendment was found.

Worse, the old required `statistics/ANALYSIS_REGISTRY.yaml` remains present and active-looking. It still says:

- unit = `base_scenario_id`;
- primary contrast = `M6 - M14(global B*)`;
- 600 HOLDOUT + 600 REPLICATION;
- two paraphrases x three repeats;
- and the old retain rule still requires `point estimate at least 0.08`.

The new `power-analysis/PRIMARY_ANALYSIS_CONTRACT.json` instead says unit = `benchmark_case`, uses semantic treatment/control IDs, and no longer uses the rejected hard observed point-estimate >= .08 rule.

An independent agent cannot determine which specification is authoritative. This alone prevents reproducible preregistration.

### Required remediation

Create a **versioned WP-006 context-packet revision** that either:

1. formally supersedes the old `statistics/` artifacts and permits the new `power-analysis/` root; or
2. moves the accepted revised design back into the already frozen allowed paths.

There must be exactly one normative statistical registry. Old artifacts must be explicitly marked superseded/non-normative, and a semantic validator must fail when two active WP-006 primary contracts coexist.

Do not silently mutate the old packet without versioning and hashable handoff.

---

## B2 — CRITICAL — Primary unit / nesting acceptance is not satisfied

The frozen WP-006 task and Linear acceptance require:

`primary unit = base_scenario_id`

with paraphrases, models and repeats treated as nested rather than independent units.

The new primary contract instead declares:

`unit = benchmark_case`

without a normative one-to-one definition equating `benchmark_case` to `base_scenario_id` and without freezing how paraphrases/repeats/model assignment collapse to one binary primary outcome.

The old statistics registry does contain a 2-paraphrase x 3-repeat aggregation rule, but because B1 leaves two competing specifications, that old rule cannot safely be imported implicitly.

### Required remediation

The single normative contract must explicitly freeze:

- `unit = base_scenario_id`;
- model profile assignment/stratification rule;
- paraphrase count and repeat count, if those remain part of the design;
- repeat -> paraphrase -> base-scenario aggregation;
- failure handling before aggregation;
- exactly one paired binary primary observation per `base_scenario_id`.

If the design intentionally abandons the old repeat/paraphrase structure, state that explicitly and re-power the new design rather than silently changing the unit.

---

## B3 — HIGH — The new simulation no longer satisfies the issue's required heterogeneity/failure stress model

ENG-158 acceptance requires the simulation to include paired discordance, clustering, **domain/model heterogeneity and failures**.

The new `simulate_power.py` models:

- marginal paired difference `D in {-1,0,1}`;
- exchangeable source-family ICC;
- independent attrition;
- cluster-robust paired analysis.

It does **not** simulate domain heterogeneity, model-profile heterogeneity, treatment heterogeneity by domain/model, nested paraphrases/repeats, or treatment/runtime failure processes.

The old `statistics/power_simulation.py` was designed to stress several of those factors, but B1 means it cannot be assumed to remain part of the new normative package.

### Required remediation

Either:

- add a versioned stress simulation that includes the required domain/model/nested/failure mechanisms under the newly accepted estimand and inference rule; or
- prove, before outcomes, that a simpler aggregate `q/ICC/attrition` envelope is conservative for the omitted mechanisms and freeze the proof/assumption bounds.

The design should include correlated infrastructure/tool failures where relevant, not only iid scientific attrition.

---

## B4 — HIGH — N=802 is an analytical knife-edge and fails the candidate's own frozen Monte-Carlo target on independent replay

Under the candidate's analytical approximation:

- N=801 power ≈ 0.89977;
- N=802 power ≈ 0.90013.

So the claimed minimum is only about 0.00013 above the target.

I independently replayed the exact algorithm in `simulate_power.py` with the frozen parameters:

- repetitions = 20,000;
- seed = 158006;
- N = 802;
- delta = .08;
- q = .35;
- mean cluster size = 8;
- ICC = .05;
- attrition = .05;
- two-sided alpha = .05.

Result:

- simulated power = **0.89635**;
- Monte-Carlo SE ≈ **0.002155**;
- degenerate replicates = 0.

The producer preflight only reports `crosscheck_pass=true` because the analytical-vs-simulation gap is <= .02. It does not surface the important fact that the frozen simulated power is below the required .90.

The simulation protocol itself says that simulated power below .90 triggers statistical review of whether N must increase.

This does not imply that one reviewer-selected N should now be frozen. It means the acceptance rule must be made conservative and versioned.

### Required remediation

Before accepting an N:

- freeze a Monte-Carlo acceptance criterion that accounts for Monte-Carlo uncertainty, e.g. a lower confidence bound >= .90 or another predeclared conservative margin;
- retain the actual simulated power and MC SE in the immutable evidence, not only a boolean gap check;
- re-evaluate N under that rule;
- preferably include several predeclared seeds or otherwise demonstrate seed stability without choosing the favorable seed.

Do **not** lower the .90 power target.

For orientation only, reviewer exploration under the same one seed gave values around .905 at N≈818–824, whose simple 95% MC lower bounds exceed .90; this is **not** an accepted sample-size recommendation and must not be used as a post-review shortcut. The producer/statistical design must freeze the criterion first and then compute N.

---

## B5 — CRITICAL — The executable real-inventory power gate can false-PASS unaccepted or internally inconsistent evidence

The handoff claims that the real inventory gate cannot pass without accepted WP-004/WP-005/reviewer dependencies. The current evaluator does not establish that.

`evaluate_power_gate.py` verifies only that:

- arm IDs are nonempty/different;
- hashes look like 64 hexadecimal characters;
- review references are nonempty strings;
- WP-005 semantic version matches a string constant;
- sealed-access booleans are false;
- N and cluster count satisfy the numerical thresholds.

It does **not** resolve the referenced reviews/artifacts, verify their verdict is PASS, verify the supplied hashes correspond to those accepted artifacts, or verify that the exact WP-004 arm binding is the reviewed binding.

The synthetic positive fixture demonstrates the weakness directly: it uses hashes like `aaaaaaaa...`, `bbbbbbbb...` and review references `FIXTURE_ONLY`, and the complete validator expects that fixture to receive `POWER_GATE_PASS`.

That is fine for a fixture only if a separate real-mode trust boundary exists. Currently the same evaluator accepts the same shape for a real inventory.

There is a second consistency hole: `cluster_size_summary_sha256` and `attrition_ledger_sha256` are syntactically checked but never parsed. The gate accepts `eligible_n=802`, `clusters=30` and nuisance `mean_cluster_size=8` even though those values cannot describe the same complete inventory without a specific unequal cluster-size distribution; the average N/G would be about 26.7. Thus the numerical design effect can be disconnected from the asserted inventory.

A third hole: `single_blinded_nuisance_update` accepts arbitrary in-range q/m/ICC/attrition plus an arbitrary-looking hash; the evaluator does not validate the blinded-update report or its provenance.

### Required remediation

The real gate must have a mode distinguishable from synthetic fixtures and must machine-verify, from immutable local/attested inputs:

- accepted WP-004 review verdict and exact arm-binding artifact hash;
- accepted WP-005 scorer review verdict and scorer hash;
- accepted independent WP-006 review artifact/hash;
- actual benchmark inventory manifest;
- actual source-family cluster-size summary consistent with eligible N and cluster count;
- actual attrition ledger;
- blinded nuisance-update artifact and proof of allowed fields/blinding, if used;
- calculator/protocol/validator hashes against the reviewed candidate.

Add adversarial negative fixtures for fake review refs/hashes, mismatched cluster summary, mismatched N, forged nuisance-update report, and stale accepted-artifact hash.

The gate must fail closed on any unresolved reference.

---

## B6 — HIGH — Blinded nuisance update can reduce required N from noisy favorable nuisance estimates without uncertainty protection

The nuisance protocol correctly removes arm direction, but it allows q, mean cluster size, ICC/proxy and attrition to be re-estimated once and then recomputes the minimum N from the point estimates.

There is no frozen confidence-bound rule, shrinkage/conservative estimator, or non-decreasing-N floor. A noisy favorable blinded estimate can therefore reduce N below the initial 802 even though the true nuisance parameters are worse.

Blinding prevents treatment-effect chasing; it does not by itself remove sampling error in nuisance estimates.

### Required remediation

Freeze one of the following before any nuisance packet exists:

- conservative confidence bounds for q/dependence/attrition used in the power calculation; or
- a rule `final required N = max(initial frozen N, blinded-update required N)`; or
- another independently justified conservative blinded sample-size re-estimation method.

Also freeze the estimator and its finite-sample behavior, not only the list of permitted fields.

---

## B7 — HIGH — HOLDOUT/REPLICATION decision power remains undefined

The old normative-looking registry requires replication direction agreement as part of the retain rule and allocates 600 HOLDOUT + 600 REPLICATION scenarios.

The new package powers only one confirmatory dataset/contrast and does not define:

- the replication decision threshold;
- whether replication is independently inferential, directional-only, or descriptive;
- whether the headline claim requires both HOLDOUT and REPLICATION to succeed;
- the resulting joint probability of claim retention.

If success of the paper's headline claim requires two study-stage conditions, .90 power for one stage is not .90 power for the combined decision.

### Required remediation

Freeze one coherent rule:

- either HOLDOUT is the sole powered primary decision and replication has a separately stated corroboration rule that is not required for primary retain; or
- replication is part of the retain rule, in which case power/sample size must address the joint decision probability and independent-source structure.

Remove the conflicting old rule once B1 is resolved.

---

## B8 — HIGH — Minimum-30-cluster inference is underspecified and not Type-I calibrated

The primary contract names source-family cluster-robust sandwich variance and says fewer than 30 clusters requires a new finite-cluster method.

The Monte-Carlo implementation uses a CR1-like variance estimator with a **standard-normal z critical value**. No null Type-I simulation is provided for the boundary case of 30 clusters, and no small-sample reference distribution/correction is frozen (e.g. t with cluster df, CR2/Satterthwaite, wild cluster bootstrap, or randomization inference where appropriate).

Thirty clusters is therefore a heuristic threshold, not yet a validated inferential contract.

### Required remediation

Before statistical PASS:

- specify the exact primary cluster-robust implementation and reference distribution;
- test empirical Type-I error at and near the minimum permitted cluster count under plausible imbalance/ICC envelopes;
- if 30 clusters is not adequate, increase the cluster minimum or preregister a finite-cluster method now, not after p-values are seen.

The inventory consistency checks in B5 must also make sure the cluster-size distribution used for power corresponds to the actual frozen inventory.

---

## B9 — MEDIUM/HIGH — The .08 SESOI remains only qualitatively justified

The old statistics plan says .08 corresponds to eight fewer exact-contract failures per 100 scenarios and asserts that this is the minimum gain worth formal-runtime/governance/integration complexity. The new protocol mostly repeats .08 as a pre-outcome design choice.

This is outcome-independent, which is good, but it is still not a reproducible utility/cost or decision-threshold justification. The earlier reviewer explicitly requested an independent substantive basis rather than choosing a convenient effect size.

### Required remediation

Add a short frozen SESOI rationale that makes the decision criterion auditable, for example:

- an explicit operational utility/cost table for 1, 5, 8 and 10 percentage-point gains; or
- a domain-independent decision rule explaining why <8pp would not justify the added verified-interface complexity but >=8pp would;
- sensitivity remains descriptive and cannot be used to switch the threshold after outcomes.

The exact justification need not be economically perfect; it must be written before outcomes and be more than the assertion that .08 is meaningful.

---

# Previously reported blockers: disposition

From the 2026-08-06 independent review:

1. **power-vs-retain mathematical mismatch** — CLOSED inside new package, but globally reintroduced by stale old registry until B1 is fixed.
2. **SESOI rationale** — OPEN (B9).
3. **source-family clustering** — PARTIALLY CLOSED; cluster inference/inventory consistency remain B5/B8.
4. **failure heterogeneity** — OPEN in the new simulation (B3).
5. **target population/stratum/model design** — PARTIALLY OPEN via B2/B3.
6. **paraphrase/repeat allocation efficiency** — OPEN because new design does not normatively define nesting (B2).
7. **joint HOLDOUT + REPLICATION decision** — OPEN (B7).
8. **MC lower-bound/multi-seed robustness** — OPEN (B4).
9. **WP-004 V1/V2 drift** — structurally improved by semantic IDs and deferred exact binding; final binding still must wait for accepted WP-004.
10. **generic validator** — OPEN in a more concrete form: machine gate false-PASS paths (B5).
11. **token-fit/missingness mismatch** — substantially improved in the new missingness contract; final resolution depends on eliminating the stale dual specification under B1.

---

# Required bounded remediation package

Do not add new scientific modes while fixing WP-006. The next producer package should be bounded to:

1. versioned context/allowed-path + single-source-of-truth repair;
2. exact `base_scenario_id` nesting/aggregation contract;
3. simulation stress coverage for required heterogeneity/failures;
4. conservative Monte-Carlo sample-size acceptance rule and immutable numeric result;
5. hardened dependency/inventory/nuisance real power gate with adversarial mutations;
6. conservative blinded nuisance re-estimation rule;
7. explicit replication/joint-decision rule;
8. exact small-cluster inference + Type-I stress test;
9. auditable pre-outcome SESOI rationale.

Then publish a new immutable handoff and return to a distinct statistical reviewer.

No real HOLDOUT/REPLICATION run is required for this remediation. The real inventory power gate remains a later prerequisite after accepted WP-004/WP-005 and frozen benchmark inventory exist.

## Final verdict

**REVISE.**

The statistical direction is viable and substantially improved, so no PIVOT is warranted. But `N=802` is **not accepted** as the confirmatory sample-size requirement yet, and this WP-006 candidate must not authorize GATE-001, HOLDOUT, or REPLICATION.
