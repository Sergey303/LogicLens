# Abstract Contract — Compile, Don’t Teach

Status: **WP-002 producer artifact; not a manuscript abstract**  
Linear issue: `ENG-154`  
Matrix: `CLAIM_EVIDENCE_MATRIX.yaml`  
Normative prohibited wording: `PROHIBITED_CLAIMS.md`

## 1. Purpose

This file freezes the allowable structure of the future abstract before confirmatory data exist. It does not contain numerical results and must not be read as evidence that any conditional sentence will survive.

Every abstract sentence below has exactly one row in `CLAIM_EVIDENCE_MATRIX.yaml`. A sentence may be populated only from its declared table and only after the corresponding retain rule passes independent review. Failed or unsupported sentences are deleted or replaced by their frozen failure wording; they are never repaired with a post-hoc claim.

## 2. Frozen seven-sentence structure

### ABS-01 — Scope and problem

Claim row: `CLM-001`  
Class: technical scope  
Required evidence: immutable model/config audit (`S1`)

Allowed template:

> We study how fixed-weight small language models consume formal knowledge across raw, teacher-edited, and runtime-compiled interfaces.

Activation rule:

- retain only when model artifacts are hash-identical across compared conditions;
- otherwise remove `fixed-weight` and invalidate any comparison affected by model-state change.

### ABS-02 — Causal design

Claim row: `CLM-002`  
Class: technical design  
Required evidence: matched mode registry and ablation table (`T2`)

Allowed template:

> We compare matched interfaces that isolate contextual teaching, trusted semantic execution, typed structure, and authoritative decision fields.

Activation rule:

- retain only when the frozen mode design contains the strongest matched non-compiled baseline, token control, typed-frame control, and answer-field copying control;
- do not describe `Compiled Frame versus Raw Prolog` alone as the primary causal test.

### ABS-03 — Primary result

Claim row: `CLM-003`  
Class: **the only primary empirical claim**  
Required evidence: frozen HOLDOUT and independent REPLICATION (`T1`)

Allowed template:

> On the preregistered scenario-level exact epistemic contract endpoint, the compiled verified frame [PRIMARY_RESULT_CLAUSE] relative to the strongest matched non-compiled baseline, with [REPLICATION_CLAUSE].

`[PRIMARY_RESULT_CLAUSE]` may contain only:

- paired absolute effect;
- hierarchical bootstrap 95% confidence interval;
- smallest meaningful gain comparison;
- preregistered McNemar result.

`[REPLICATION_CLAUSE]` may contain only the frozen independent replication direction and interval.

Activation rule:

- retain only when the confidence interval supports the preregistered smallest meaningful gain and replication has the same direction;
- narrow to named strata when pooled evidence is heterogeneous;
- replace with the frozen null wording when the strongest matched baseline is non-inferior;
- never use pilot `18/18` or `24/24` as the result clause.

### ABS-04 — Generalization boundary

Claim row: `CLM-004`  
Class: secondary  
Required evidence: hierarchical effects by model, domain, source family, and replication (`T3`)

Allowed template:

> The effect direction was [GENERALIZATION_RESULT] across the preregistered model, domain, and replication strata.

Activation rule:

- use `consistent across the evaluated strata` only when no preregistered stratum shows a practically important reversal and the independent replication direction agrees;
- otherwise list the supported strata explicitly;
- delete the sentence if one model/domain/source family entirely explains the pooled result.

Prohibited substitution:

> The method generalizes to unseen tasks or arbitrary language models.

### ABS-05 — Error localization

Claim row: `CLM-005`  
Class: secondary  
Required evidence: independent layer audit (`T4`)

Allowed template:

> Layer-wise auditing localized residual errors primarily to [SUPPORTED_ERROR_LAYERS], conditional on independently verified frame correctness.

Activation rule:

- retain only when the independent oracle, mutation suite, source-bound gold, and layer-specific scorer agree;
- never infer source-extraction correctness from a successful Prolog proof;
- delete relocation wording when deterministic execution remains a substantial unexplained error source.

### ABS-06 — Contextual teaching limitation

Claim row: `CLM-006`  
Class: secondary  
Required evidence: frozen teacher-track table (`T5`)

Allowed template:

> Under the preregistered teacher budgets, contextual teacher editing [TEACHER_RESULT_CLAUSE]; this is a conditional finding, not a claim that teaching never works.

Activation rule:

- use only the mean paired change, uncertainty, and regression frequency from the frozen teacher protocol;
- restrict wording to the tested teacher, student, budget, and task strata;
- delete from the abstract if teacher editing is consistently beneficial or the track is not independently reproducible.

### ABS-07 — Bounded interpretation

Claim row: `CLM-007`  
Class: interpretive synthesis  
Required evidence: retained `CLM-003`, retained/narrowed `CLM-005`, and answer-copying control (`F1`)

Allowed template:

> Within the evaluated strict epistemic scope, verified semantic compilation [INTERPRETATION_CLAUSE] while the fixed-weight model remained responsible for interpretation and rendering.

`[INTERPRETATION_CLAUSE]` may say that execution was moved into an auditable runtime contract only when:

- the primary effect survives the strongest matched baseline;
- answer-field copying does not explain the effect;
- production runtime and independent oracle are separated;
- source truth and source extraction remain explicitly outside the guarantee.

It may not say that the architecture guarantees correctness, eliminates hallucination, proves privacy, or makes the language model trustworthy.

## 3. Draft abstract shell

The future abstract must contain at most the seven sentences below, in this order. Conditional sentences that fail are removed rather than replaced by newly invented claims.

1. `[ABS-01]`
2. `[ABS-02]`
3. `[ABS-03]`
4. `[ABS-04 if retained]`
5. `[ABS-05 if retained]`
6. `[ABS-06 if retained]`
7. `[ABS-07 if retained]`

No novelty sentence is authorized until `WP-003` independently establishes the novelty boundary. No privacy sentence is authorized in the flagship abstract.

## 4. Result insertion contract

When confirmatory analysis is unblinded, the analyst may insert values only by a deterministic rendering step that reads approved table cells. Manual free-form editing of effect sizes, intervals, p-values, sample counts, or replication wording is prohibited.

Each inserted value must resolve to:

```text
claim_id
table_id
metric_id
split
model/domain scope
analysis script hash
artifact hash
```

Rounded values must follow the preregistered table specification. Unfavorable, null, malformed, timeout, and failure outcomes remain represented under the frozen analysis rules.

## 5. Change control

Before HOLDOUT, changes require:

- a versioned diff;
- a reason tied to a protocol or independent review finding;
- synchronized updates to the matrix and prohibited-claims file;
- a new hash and structured handoff;
- no access to HOLDOUT or REPLICATION outcomes.

After HOLDOUT access, no new headline sentence or claim class may be added. The only permitted operations are `retain`, `narrow`, `delete`, or substitution of the frozen failure wording.
