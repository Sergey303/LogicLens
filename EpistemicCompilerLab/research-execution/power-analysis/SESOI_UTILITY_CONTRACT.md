# WP-006 SESOI utility contract — R2

Status: **pre-outcome governance threshold; not an empirical effect estimate**.

## Decision quantity

The primary endpoint is binary `publication_composite_correctness` at one `base_scenario_id`. An absolute gain of `+0.08` therefore means **8 additional fully contract-correct scenario outcomes per 100 base scenarios** under the frozen target population and weighting.

Equivalent decision framing:

- `+0.05` = one additional exact-contract success per 20 base scenarios;
- `+0.08` = one additional exact-contract success per 12.5 base scenarios;
- `+0.10` = one additional exact-contract success per 10 base scenarios.

The project adopts `+0.08` as the smallest gain for which it will use the phrase **practically meaningful advantage**. This is a deliberately conservative publication/governance policy because the compiled interface adds implementation, verification, update and audit surface. It is **not** inferred from pilot outcomes, not estimated from customer willingness-to-pay, and not a hidden second hypothesis test.

## Statistical role

The primary hypothesis remains superiority:

```text
H0: delta = 0
H1: delta != 0
alpha = 0.05 two-sided
```

`delta = +0.08` is the planning alternative at which power is required. A statistically significant positive estimate smaller than 0.08 may support a narrow superiority statement, but it does **not** satisfy the project's practical-advantage wording policy. Conversely, an observed point estimate >=0.08 is not by itself a retain condition and cannot replace the confidence interval/test.

## Mandatory reporting

Always report:

1. absolute paired effect and 95% interval;
2. two-sided superiority test relative to zero;
3. the 0.08 SESOI reference line as a practical interpretation aid, not a second p-value gate;
4. sensitivity/power planning at 0.05, 0.08 and 0.10;
5. cost/audit/update measurements from WP-007 alongside any practical-advantage statement.

## Freeze rationale

This contract is frozen before HOLDOUT/REPLICATION and before final sample-size acceptance. Changing 0.08 because the observed effect is convenient is prohibited. A future empirical utility study could replace this policy only through a new preregistered version before sealed outcome access.
