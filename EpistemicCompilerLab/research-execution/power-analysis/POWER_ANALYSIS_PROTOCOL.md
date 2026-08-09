# WP-006 / ENG-158 — Statistical power protocol

Status: **producer design candidate; outcome-blind; independent statistical review required**.

## 1. Scientific question

For the preregistered flagship fixed-weight contrast, how many paired benchmark cases are required to detect a scientifically meaningful absolute improvement in publication composite correctness without choosing the effect size, arm, endpoint or nuisance assumptions from favorable model outcomes?

The primary contrast is semantic, not yet a movable implementation label:

- treatment: `authoritative_semantic_result_placement_fixed_weight`;
- control: `matched_fixed_weight_baseline`.

Exact executable arm IDs must be bound from the accepted WP-004 comparator contract before confirmatory execution. The binding must not be selected by “best DEV arm” performance.

## 2. Primary endpoint and estimand

The outcome for each arm/case is binary `publication_composite_correctness` under the accepted WP-005 scorer: correct only when every publication-critical applicable field is correct.

For case `i`:

```text
T_i ∈ {0,1}
C_i ∈ {0,1}
D_i = T_i - C_i ∈ {-1,0,1}
```

Primary estimand:

```text
δ = E[D_i] = P(T=1,C=0) - P(T=0,C=1)
```

The reported point estimate is the mean paired absolute difference, not an odds ratio selected because it looks larger.

`source_family_id` is the dependence cluster for primary uncertainty.

## 3. SESOI

The smallest effect of scientific interest is frozen at:

```text
δ_SESOI = +0.08
```

that is, an eight-percentage-point absolute increase in publication composite correctness.

This threshold is a design choice made before confirmatory outcomes. It is not estimated from a directional DEV treatment effect and is not changed if observed effects are disappointing.

Sensitivity at `0.05` and `0.10` is reported to show fragility, but those values do not replace `0.08` as the gate threshold.

## 4. Type-I error and power

- two-sided alpha: `0.05`;
- target power at the SESOI: `0.90`;
- primary confirmatory contrast count: exactly `1`.

Two-sided inference is retained even though the intended effect direction is improvement, so an unexpected material reversal remains inferentially visible.

## 5. Paired-binary planning model

Let:

```text
p10 = P(T=1,C=0)
p01 = P(T=0,C=1)
q   = p10 + p01
δ   = p10 - p01
```

Then the variance of the paired difference is:

```text
Var(D) = q - δ²
```

For planning only, cluster dependence is conservatively approximated by:

```text
DE = 1 + (m - 1)ρ
```

where `m` is mean source-family cluster size and `ρ` is the intracluster correlation of the paired-difference process or its frozen conservative proxy.

With attrition fraction `a`:

```text
N_eff = N(1-a) / DE
μ = |δ| sqrt(N_eff / (q-δ²))
power = Φ(-z_(1-α/2)-μ) + 1 - Φ(z_(1-α/2)-μ)
```

This approximation is the **sample-size planning model**, not a replacement for the final cluster-robust primary analysis.

## 6. Frozen conservative planning scenario

Primary gate assumptions before a blinded nuisance update:

- `δ = 0.08`;
- `q = 0.35` paired discordance;
- mean source-family size `m = 8`;
- `ρ = 0.05`;
- non-evaluable attrition `a = 0.05`;
- two-sided `α = 0.05`;
- target power `0.90`.

The executable calculator gives minimum eligible paired case inventory `N = 802` under these assumptions.

This is intentionally not an optimistic independence calculation. Sensitivity spans smaller/larger effect, discordance, cluster size, ICC and attrition.

## 7. Primary inferential analysis

On the frozen confirmatory dataset, estimate `δ` from paired case-level differences and use source-family cluster-robust sandwich uncertainty under the accepted analysis implementation.

Minimum independent source-family clusters for this asymptotic contract: `30`.

If fewer than 30 clusters remain, the current primary-analysis contract cannot receive a power/statistical PASS. A finite-cluster procedure would require a new preregistered version before confirmatory scoring; it cannot be chosen after seeing p-values.

Report at minimum:

- eligible paired N;
- independent cluster count and cluster-size distribution;
- `p10`, `p01`, total discordance `q`;
- absolute paired difference;
- 95% confidence interval;
- two-sided primary p-value or equivalent frozen inferential output;
- all exclusions/failures under the frozen attrition ledger.

## 8. Blinded nuisance update

A once-only pre-HOLDOUT nuisance update is permitted by `BLINDED_NUISANCE_UPDATE_PROTOCOL.json`.

It may update only:

- non-directional paired discordance `q`;
- cluster-size information;
- blinded dependence/ICC proxy;
- non-evaluable attrition.

It must not reveal which arm wins discordant pairs, signed treatment difference, arm-labelled accuracy, field-level direction, HOLDOUT or REPLICATION.

SESOI, alpha, target power, endpoint and primary contrast remain immutable.

If blinding cannot be demonstrated, do not update nuisance parameters; retain the frozen conservative planning scenario.

## 9. Multiplicity

Exactly one primary contrast receives alpha `0.05`.

Secondary inferential comparisons, if retained as one declared family, use Holm step-down at FWER `0.05`. Field-level results are diagnostic secondary outcomes. Exploratory comparisons remain explicitly exploratory.

No secondary result can substitute for a failed primary claim.

## 10. Missingness and system failures

`MULTIPLICITY_AND_MISSINGNESS.md` is normative.

Model-/response-attributable malformed output, forbidden tool use, exhausted retry, schema failure or other frozen system failure is not silently dropped as missing. It is incorrect when the experiment contract defines it as an evaluated-system failure.

Only arm-independent scientific non-evaluability may remove a pair, with a frozen reason code and symmetric rule. Planning reserves `5%` attrition.

## 11. Power gate

Before any HOLDOUT access, freeze:

- exact primary arm binding from accepted WP-004;
- accepted WP-005 endpoint/scorer version;
- eligible paired case inventory N;
- independent source-family cluster count;
- either the original nuisance assumptions or one valid blinded nuisance-update report;
- calculator/validator hashes;
- independent statistical reviewer verdict.

PASS requires:

1. computed power at `δ=0.08` is at least `0.90`;
2. eligible paired N is at least the computed required N;
3. at least 30 independent source-family clusters exist for the frozen asymptotic primary analysis;
4. no directional outcome was used to alter SESOI, alpha, endpoint, primary arm, or nuisance update;
5. multiplicity/missingness contracts are frozen;
6. independent statistical review accepts the design.

## 12. STOP / redesign

STOP before HOLDOUT if:

- available cases are below required N;
- fewer than 30 independent source-family clusters remain;
- the primary arm would be selected by DEV performance;
- nuisance updating reveals directional arm performance;
- the SESOI/alpha/power target is changed after model outcomes;
- the endpoint is weakened from publication composite to a favorable field metric;
- failures are reclassified as missing to improve an arm;
- optional stopping or significance-based sample extension is proposed;
- WP-004 arm binding or WP-005 scorer is not independently accepted.

A redesigned experiment gets a new version and new review before confirmatory data access.
