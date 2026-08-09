# WP-006 — Monte-Carlo cluster sensitivity protocol

Status: producer design candidate; outcome-blind.

The analytical design-effect calculation is the preregistered sample-size gate. This simulation is an independent stress check that the planned N behaves as expected under an explicit clustered paired-difference generator and the planned cluster-robust analysis.

## Marginal paired outcome

For frozen `delta` and discordance `q`:

```text
P(D=+1) = (q + delta)/2
P(D=-1) = (q - delta)/2
P(D= 0) = 1 - q
```

where `D = treatment_correct - control_correct`.

The primary scenario uses `delta=.08`, `q=.35`.

## Exact exchangeable cluster-correlation generator

For every source-family cluster independently:

1. draw `shared ~ Bernoulli(rho)`;
2. if shared, draw one `D` from the marginal distribution and assign that same D to every case in the cluster;
3. otherwise draw each case D independently from the same marginal distribution.

For any two distinct cases in a cluster this construction has covariance `rho * Var(D)` and therefore pairwise ICC exactly `rho`, while preserving the marginal D distribution.

This is intentionally simple and inspectable. It is not claimed to model every realistic source-family dependence structure. Sensitivity across ICC and cluster sizes remains required.

## Attrition

Each case is independently marked non-evaluable with probability equal to the frozen planning attrition. This simulation treatment of attrition is a power stress model only. The actual experiment uses the stricter scientific missingness rules in `MULTIPLICITY_AND_MISSINGNESS.md`.

## Analysis inside each replicate

- retain evaluable cases;
- compute mean paired difference;
- form residual sums within source-family clusters;
- compute CR1-style intercept-only cluster-robust standard error:

```text
SE = sqrt( G/(G-1) * sum_g S_g^2 / N_obs^2 )
S_g = sum_{i in g}(D_i - mean(D))
```

- require at least two observed clusters inside the simulation replicate;
- reject two-sided H0 when `|estimate/SE| > z_(1-alpha/2)`;
- zero estimated SE is handled fail-closed: reject only if the observed effect is non-zero and the degenerate replicate is reported separately; the simulation report records degenerate count.

The confirmatory experiment still requires at least 30 independent source-family clusters.

## Frozen Monte-Carlo settings

- repetitions: `20000`;
- seed: `158006`;
- primary eligible N: `802`;
- mean cluster size: `8` (clusters are filled sequentially; final cluster may be smaller);
- ICC: `.05`;
- attrition: `.05`;
- alpha: `.05` two-sided.

## Acceptance interpretation

The simulation is a design cross-check, not an alternate way to lower required N.

For the primary planning scenario:

- simulated power must be finite and reported with Monte-Carlo standard error;
- absolute difference between simulated and analytical power at N=802 should be `<= .02`;
- if it exceeds `.02`, WP-006 returns to REVISE because the analytical planning approximation is not behaving consistently under its own explicit cluster stress model;
- simulation power below `.90` does **not** authorize changing alpha/SESOI or selecting a favorable generator. It triggers statistical review of whether N must be increased before HOLDOUT.

All sensitivity results are retained; no seed shopping.
