# Power Simulation Plan — WP-006

Status: **producer statistical-design artifact; pending independent review**  
As of: **2026-08-06**

## 1. Primary design

- Treatment: `M6 Compiled Frame`.
- Comparator: `M14(B*)`, where one global `B*` is selected only on DEV under `DEV-GLOBAL-STRONGEST-MATCHED-V1`.
- Endpoint: scenario-level exact epistemic contract accuracy.
- Primary unit: `base_scenario_id`.
- Two-sided alpha: `0.05`.
- Target power: at least `0.90`.
- Smallest practically meaningful absolute gain: `0.08`.

The 0.08 threshold means at least eight fewer exact-contract failures per 100 scenarios. It is fixed before scaled DEV/HOLDOUT results and is justified as the minimum gain worth the formal runtime, artifact governance, and integration complexity. It is not reverse-engineered from significance or pilot scores.

## 2. Scenario aggregation

Each base scenario is assigned, before execution, to one domain×model-profile stratum. All compared modes use the same assigned profile.

Within each scenario:

- two mandatory paraphrases;
- three independent stochastic repetitions per paraphrase;
- a paraphrase passes when at least `2/3` repetitions pass;
- the scenario passes only when both paraphrases pass;
- timeout, malformed output, exhausted retry, forbidden tool call and other declared failures count incorrect before aggregation.

This yields one paired binary M6/M14 outcome per base scenario. Paraphrases and repetitions are not independent analysis units.

## 3. Data-generating simulation

`power_simulation.py` uses a clustered paired latent-logit simulation with:

- scenario difficulty shared by both modes;
- domain baseline heterogeneity;
- model-profile baseline heterogeneity;
- paraphrase effects shared by both modes;
- scenario/domain/model treatment heterogeneity;
- independent stochastic repetitions;
- run failures counted incorrect;
- balanced allocation over three domains and four model profiles.

For every declared simulation scenario, a deterministic calibration stage solves for the treatment logit shift that yields exactly the same `0.08` expected scenario-level gain after repeat/paraphrase aggregation. The sample size is therefore not favored by a larger effect in the adverse scenario.

## 4. Declared scenarios

### Design

- scenario logit SD `0.80`;
- paraphrase logit SD `0.25`;
- treatment heterogeneity SD `0.12`;
- run failure rate `0.02`.

### Adverse heterogeneity and failures

- scenario logit SD `1.00`;
- paraphrase logit SD `0.35`;
- treatment heterogeneity SD `0.18`;
- run failure rate `0.04`;
- wider domain and model baseline/effect offsets.

Candidate counts are frozen from `360` through `840` in increments of `60`. Each candidate uses 4000 Monte Carlo replications. Calibration uses 200000 latent scenarios. Seeds and all parameters are stored in `ASSUMPTIONS_MANIFEST.yaml`.

## 5. Power test

The simulation applies a paired McNemar test:

- exact two-sided binomial form when fewer than 25 discordant scenarios occur;
- continuity-corrected chi-square form otherwise;
- detection requires `p < 0.05` and a positive paired difference.

The final analysis additionally reports the paired effect and frozen hierarchical-bootstrap 95% interval; power is based on the preregistered hypothesis test at the smallest meaningful data-generating effect.

## 6. Producer simulation result

Transient output: `POWER_RESULTS.json` generated outside the committed allowed paths.

| Base scenarios | Design power | Adverse power |
|---:|---:|---:|
| 360 | 0.7175 | 0.7500 |
| 420 | 0.7837 | 0.8153 |
| 480 | 0.8442 | 0.8518 |
| 540 | 0.8872 | 0.8978 |
| **600** | **0.9100** | **0.9257** |
| 660 | 0.9410 | 0.9545 |
| 720 | 0.9640 | 0.9653 |
| 780 | 0.9700 | 0.9742 |
| 840 | 0.9762 | 0.9842 |

At 600 scenarios, Monte Carlo SE is approximately `0.0045` for design and `0.0041` for adverse. The calibrated expected baseline/treatment scenario accuracies are approximately `0.610/0.690` and `0.570/0.650`.

The first candidate satisfying power ≥0.90 in both scenarios is **600**.

## 7. Consequence for corpus size

The recommendation applies independently to:

- frozen HOLDOUT: 600 base scenarios;
- independently sourced REPLICATION: 600 base scenarios.

Retaining the earlier 35/15/25/25 allocation implies a planning corpus of:

```text
TRAIN        840
DEV          360
HOLDOUT      600
REPLICATION  600
TOTAL       2400 base scenarios
```

This supersedes the earlier unpowered target of 600 total scenarios. WP-007 must determine feasibility. If infeasible, scope/models/modes/domains or the claim must be narrowed before data; the power threshold may not be reduced after outcomes.

## 8. Independent review attacks

The reviewer must challenge:

- the independent practical justification for 0.08;
- balanced assignment of one model profile per scenario;
- the all-paraphrase scenario pass rule;
- failure assumptions and adverse envelope;
- the paired-correlation mechanism;
- calibration correctness;
- Monte Carlo stability under different frozen seeds;
- feasibility of 1200 confirmatory scenarios and planned modes.

Any approved change requires a versioned assumptions diff and a full rerun before HOLDOUT.
