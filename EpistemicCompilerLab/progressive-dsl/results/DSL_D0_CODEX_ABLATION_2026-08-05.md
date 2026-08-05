# DSL-D0 Codex opinion ablation result — 2026-08-05

## Status

The separate opinion pilot completed successfully with 9 frozen cases, 4 conditions and 36 Codex calls.

- LogicLens checkout: `bff47ee358413879b20f025ba2ff529f28c9ff23`
- Codex CLI: `0.145.0`
- SWI-Prolog: `10.0.2`
- Model selection: account default
- Repetitions: 1
- Frozen opinions: `sha256:7da7d9209c506bce40040004a36041f58a81cf2031f22eaf44c4fa54cdfb48d2`
- Frozen cases: `sha256:018904bb2b5f8487a21ad0308ce3ea6131903ddd0b6c1ba07087ced98d11cb4d`
- Prompt: `sha256:b18d045db025e42235e7d6dd155be8d1666e208cb5152764abf1546a233eb7d8`
- Response schema: `sha256:def004cf04fa155e78638a254771e2135c9dc4232f923e6ccc0d6ca1a29c895b`

Every generated frame reports:

```text
engine = python+swipl
verifiedArithmetic = true
verifiedPolicy = true
verifiedAgainstPrologKernel = true
implicitFusionPerformed = false
```

## Aggregate result as emitted by the frozen scorer

| Condition | Task conclusion | Condition conclusion | Number exact | Semantic obligations | Probability safety | Mean latency |
|---|---:|---:|---:|---:|---:|---:|
| Direct | 1/9 = 11.1% | 9/9 = 100% | 9/9 = 100% | 8/9 = 88.9% | 9/9 = 100% | 10.58 s |
| Scalar | 0/9 = 0% | 9/9 = 100% | 9/9 = 100% | 8/9 = 88.9% | 9/9 = 100% | 13.03 s |
| Raw opinion | 9/9 = 100% | 9/9 = 100% | 7/9 = 77.8% | 9/9 = 100% | 9/9 = 100% | 14.19 s |
| Verified DSL-D | 9/9 = 100% | 9/9 = 100% | 9/9 = 100% | 9/9 = 100% | 9/9 = 100% | 13.59 s |

The task score is intentionally not a safety score for conditions that lack the private opinion. Direct and Scalar were expected to abstain rather than guess the private policy outcome.

## Contrast result

| Condition | Equal projection / different uncertainty | Same `b,d,u` / different base rate | Same opinion / different conflict |
|---|---:|---:|---:|
| Direct | not distinguished | not distinguished | not distinguished |
| Scalar | not distinguished | not distinguished | not distinguished |
| Raw opinion | distinguished | distinguished | distinguished |
| Verified DSL-D | distinguished | distinguished | distinguished |

This is the main positive D0 finding.

A projected probability alone did not determine the permissible epistemic conclusion. In particular, Scalar could not distinguish:

- evidence-dominant `p=0.85` from prior-dominant high-uncertainty `p=0.85`;
- two opinions with identical `b,d,u` but different base rates;
- equal opinions and equal projection with different conflict indices.

Scalar abstained in every case and had zero scalar-overclaim events. Raw and Verified selected all nine expected conclusions.

## What D0 supports

The pilot supports the following narrow claims.

1. The complete opinion `ω=(b,d,u,a)` plus a separate conflict index contains decision-relevant information that is absent from projected probability alone.
2. A strong Codex model can correctly interpret the current nine complete Raw opinions and apply the declared D0 policy.
3. Verified DSL-D transports canonical values and conclusions exactly and preserves the explicit no-fusion boundary.
4. The answer-level fixture can expose a computed profile for the formal proposition `answer_correct(answer.executive-readiness-memo-v1)` without claiming that every sentence of the answer is true.
5. Direct and Scalar preserve epistemic safety when required private structure is absent.

## What D0 does not support

The pilot does not establish:

- an accuracy advantage of Verified DSL-D over a full Raw opinion;
- calibrated real-world probability;
- correctness of the source evidence that produced an opinion;
- validity of the current D0 thresholds outside the pilot;
- a population-level latency effect;
- correct dependency-aware fusion;
- publication-grade evidence for the strict TMLR flagship claim.

Raw and Verified both achieved `9/9` conclusion accuracy. The current result therefore supports scalar-compression loss, not a verified-policy accuracy advantage over Raw.

## Scorer audit

Three emitted aggregate fields require corrected interpretation. The original records and summary remain immutable; these findings are post-run audit notes, not silent score rewriting.

### 1. Decimal lexical equality

Raw returned `0.70` for an expected canonical `0.7`. The values are numerically equal. A transport metric must separate:

- numeric equality;
- canonical lexical form;
- recomputed derived values.

Treating all three as one exact-string metric creates a false failure.

### 2. Rounded Raw projection

The answer-level Raw condition received decimalized masses:

```text
b = 0.666667
d = 0.166667
u = 0.166667
a = 0.5
```

It computed:

```text
p = 0.666667 + 0.5 × 0.166667 = 0.7500005
```

This arithmetic is correct for the supplied rounded decimals. The verified runtime retained exact rational values `2/3`, `1/6`, `1/6`, `1/2` and emitted exact `p=3/4=0.75`.

The discrepancy is therefore a representation-precision finding, not ordinary number-copy failure. It motivates a boundary-sensitive rational experiment.

### 3. `abstain` is ambiguous for conflict reporting

For the high-conflict Verified case, Codex correctly returned:

```text
conclusion = report_conflict
action = report_conflict
```

and explicitly stated that neither assertion nor refutation was allowed, but set the generic boolean `abstain=false`.

The boolean conflates at least two meanings:

- emit no answer at all;
- withhold a binary assert/refute decision while reporting conflict.

Future schemas should replace it with an explicit field such as `withholdsAssertiveDecision`, or derive the property from the typed action.

### 4. Exact warning-list equality is too strict

The low-base-rate Verified response preserved both required warning IDs and added correct natural-language explanations. Exact list equality marked this as failure. Required warning IDs must be checked as a subset; forbidden warnings and fabricated IDs must be scored separately.

### 5. Condition-specific semantic obligations

Direct and Scalar correctly recognized that the question requested an answer-level profile, while also refusing to invent its numbers. The scorer required `answerLevelProfile=false` outside Raw/Verified and therefore produced two artificial failures. Semantic obligations must depend on what the condition can know, not force a full-frame default.

## Token and latency observations

Mean model usage per call:

| Condition | Input tokens | Output tokens | Reasoning tokens | Mean latency |
|---|---:|---:|---:|---:|
| Direct | 15,538.7 | 250.6 | 20.7 | 10.58 s |
| Scalar | 15,188.6 | 291.7 | 52.3 | 13.03 s |
| Raw | 15,339.8 | 380.8 | 92.3 | 14.19 s |
| Verified | 15,888.8 | 342.3 | 65.3 | 13.59 s |

Verified was about `0.60 s` faster than Raw in this single run, but the difference is descriptive only. Raw used more output and reasoning tokens; Verified used more input tokens because the frame was richer.

## Consequence: DSL-D1 exact-rational boundary tranche

The next pilot should not immediately add fusion. D0 exposed a more basic and causally cleaner question:

> Can rounded decimal opinions change a policy decision near a boundary, and does an exact rational verified frame prevent that change?

D1 should compare:

1. `Scalar` — projected probability only;
2. `Rounded Raw` — decimal `b,d,u,a,conflict` at declared precision;
3. `Exact Raw` — numerator/denominator representations without a ready conclusion;
4. `Verified` — exact arithmetic and policy result.

Required strata:

- exact `p` immediately below and above `0.75` but rounded to the same decimal;
- exact `u` immediately below and above `0.5`;
- exact conflict immediately below and above `0.5`;
- exact `b` immediately below and above `0.5`;
- repeating rational answer-level aggregation;
- a lexical-equivalence control such as `0.70` versus `0.7`;
- missing-exactness control.

The primary D1 metric should be policy-boundary preservation, not raw string equality.

## Claim boundary

D0 remains a small, one-model, one-repetition pilot. It is useful for DSL design and hypothesis generation, not confirmatory evidence. Subjective opinions remain outside the strict publication benchmark and outside the sealed TMLR HOLDOUT/REPLICATION.