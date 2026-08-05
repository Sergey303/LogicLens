# Statistics and Analysis Protocol
Статус: **MUST preregister before HOLDOUT**
## 1. Primary contrast
Fix exactly one primary contrast:
```text
M6 Compiled Frame versus strongest matched non-compiled baseline
```
Select strongest baseline on DEV using a frozen deterministic rule.
`M6 versus Raw Prolog` alone is not sufficient because it mixes solver execution and interface structure.
## 2. Smallest effect of interest
Before power simulation declare an absolute improvement that matters operationally.
Record:
```text
metric
minimum absolute gain
reason
cost/risk interpretation
```
Do not derive this value from HOLDOUT or desired significance.
## 3. Unit of analysis
Primary unit:
```text
base_scenario_id
```
Paraphrases, model repeats and model profiles are nested observations, not independent samples.
## 4. Power simulation
Simulation MUST include:
- within-scenario paraphrase correlation;
- paired baseline/treatment discordance;
- domain heterogeneity;
- model heterogeneity;
- repeated stochastic runs;
- expected missing/failure rate.
Target:
```text
power >= 0.90
two-sided alpha = 0.05
```
Save simulation code, seed and assumptions.
## 5. Confirmatory analysis
Primary report MUST contain:
1. paired scenario outcome table;
2. absolute accuracy difference;
3. hierarchical bootstrap 95% CI;
4. McNemar test;
5. results by domain and model family;
6. comparison with smallest meaningful gain.
Report effect size even when non-significant.
## 6. Secondary metric families
Freeze families before HOLDOUT:
```text
epistemic behaviour
query boundary
renderer fidelity
efficiency
teacher effect
```
For each family specify:
- definitions;
- direction;
- failure handling;
- correction method;
- target table.
Use Holm correction within each declared family unless a different method is justified before freeze.
## 7. Stochastic runs
Run at least three independent repetitions for stochastic settings.
MUST:
- store all repetitions;
- never select best seed;
- report dispersion;
- use frozen aggregation;
- document when runtime cannot honor seed.
Deterministic settings require one subset reproducibility rerun.
## 8. Missing and failures
Count as incorrect:
- timeout after allowed retries;
- provider error after allowed retries;
- malformed JSON;
- schema invalid;
- empty output;
- forbidden tool call;
- mandatory-language violation.
Infrastructure-wide outage may trigger complete-block rerun only under preregistered rule.
## 9. Analysis freeze
Before HOLDOUT commit:
```text
primary contrast
primary endpoint
effect threshold
power report
metric registry
exclusion/retry rules
analysis script hash
table shells
figure shells
```
Do not inspect partial confirmatory scores during execution.
## 10. Interpretation rules
Central claim survives only if:
- primary CI supports practically meaningful advantage;
- advantage survives strongest matched control;
- direction replicates independently;
- effect is not solely `allowedConclusion` copying;
- result is not created by treating paraphrases as independent.
Null or negative results remain published in artifacts and force claim narrowing.
## 11. STOP rules
STOP or pivot when:
- replication reverses effect;
- strongest matched baseline is non-inferior within declared margin;
- significance disappears under correct clustering;
- one domain/model entirely explains pooled effect;
- analysis requires a new post-hoc headline metric.
