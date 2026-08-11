# WP-006 SESOI utility contract — R3 endpoint normalization over R2

Status: **pre-outcome governance threshold; not an empirical effect estimate**.

Canonical endpoint identity is frozen in `ENDPOINT_IDENTITY_CONTRACT.json`.

## Decision quantity

The primary endpoint is binary **`scenario_level_exact_epistemic_contract_accuracy`** at one `base_scenario_id`. The legacy R2 phrase `publication_composite_correctness` names the response-level conjunction that every publication-critical applicable scorer field is correct; after the frozen 2-of-3 repeat rule and all-2 mandatory-paraphrase rule, the resulting base-scenario event is the canonical endpoint above.

An absolute gain of `+0.08` therefore means **8 additional fully contract-correct scenario outcomes per 100 base scenarios** under the frozen target population and weighting.

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

Endpoint identifier normalization does not change the binary scoring event, denominator, nested aggregation, Monte-Carlo parameters, R2 simulation bytes, selected producer floor `820`, or SESOI.

## Mandatory reporting

Always report:

1. absolute paired effect and 95% interval on `scenario_level_exact_epistemic_contract_accuracy`;
2. two-sided superiority test relative to zero;
3. the 0.08 SESOI reference line as a practical interpretation aid, not a second p-value gate;
4. sensitivity/power planning at 0.05, 0.08 and 0.10;
5. cost/audit/update measurements from WP-007 alongside any practical-advantage statement.

## Freeze rationale

This contract is frozen before HOLDOUT/REPLICATION and before final sample-size acceptance. Changing 0.08 because the observed effect is convenient is prohibited. A future empirical utility study could replace this policy only through a new preregistered version before sealed outcome access.
