# WP-006 / ENG-158 — statistical power and sample-size contract

Status: **producer design candidate; outcome-blind; TRAIN/DEV nuisance estimation only; independent statistical review required**.

This package freezes the statistical planning rules for the flagship fixed-weight comparison before any confirmatory HOLDOUT or REPLICATION execution.

The primary estimand is the paired absolute difference in **publication composite correctness** between one preregistered authoritative-semantic-result-placement treatment and one preregistered matched fixed-weight baseline on the same benchmark cases.

The power design does **not** select the best DEV arm. Exact arm identifiers must be bound from the accepted WP-004 comparator contract before confirmatory execution; changing the treatment or baseline after outcome inspection creates a new scientific candidate.

## Primary planning constants

- SESOI: `+0.08` absolute paired composite-correctness difference.
- Type-I error: two-sided `alpha = 0.05`.
- Target power: `0.90`.
- Conservative planning discordance: `q = P(10)+P(01) = 0.35`.
- Planning mean source-family cluster size: `8`.
- Planning intracluster correlation of the paired-difference process: `0.05`.
- Planning non-evaluable attrition: `0.05`.
- Minimum independent source-family clusters for primary asymptotic inference: `30`.

Under the frozen design-effect approximation these assumptions require approximately **802 eligible paired cases**. The executable calculator is authoritative for the integer result and sensitivity table; the prose number is a convenience cross-check, not a substitute for running the validator/calculator.

## Files

- `POWER_ANALYSIS_PROTOCOL.md`
- `PRIMARY_ANALYSIS_CONTRACT.json`
- `POWER_SCENARIOS.json`
- `BLINDED_NUISANCE_UPDATE_PROTOCOL.json`
- `MULTIPLICITY_AND_MISSINGNESS.md`
- `prototype/calculate_power.py`
- `prototype/validate_wp006_contract.py`

No model result, DEV treatment difference, HOLDOUT value or REPLICATION value is used to choose the SESOI or target power.
