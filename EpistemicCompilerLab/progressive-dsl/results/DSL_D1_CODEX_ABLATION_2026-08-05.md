# DSL-D1 exact-rational boundary ablation — 2026-08-05

## Status

The separate exact-rational opinion pilot completed successfully with 11 frozen cases, 4 conditions and 44 Codex calls.

- LogicLens checkout: `afef0a51d4a0420dd9ad27cbb224fb7cb498455e`
- Codex CLI: `0.145.0`
- SWI-Prolog: `10.0.2`
- Model selection: account default
- Repetitions: 1
- Frozen opinions: `sha256:efa8664833f621bfca077c26f73c926782b3275be9b369678b47b0da8d359e6f`
- Frozen cases: `sha256:f2efb45fabb580d76e30ae376b8740478fbb3b63b3d11b375954965eac222947`
- Prompt: `sha256:010367760b2b921ed37f4fdcb73d4288a96b719e57389627bef1d453b5be79cb`
- Response schema: `sha256:39fd8b7dd24dd17805bd7a4e2f92dc442275d2258e645d674f30358a712d70f0`

The frozen contract, offline 44-call fake-provider run and real Python/SWI-Prolog cross-verification all completed before the real model calls.

## Primary result

| Condition | Task conclusion | Exact boundary preservation | Four exact pairs distinguished |
|---|---:|---:|---:|
| Scalar | 0/11 = 0% | 0/9 = 0% | 0/4 |
| Rounded Raw | 6/11 = 54.5% | 4/9 = 44.4% | 0/4 |
| Exact Raw | 11/11 = 100% | 9/9 = 100% | 4/4 |
| Verified DSL-D1 | 11/11 = 100% | 9/9 = 100% | 4/4 |

The four paired strata were:

1. exact projected probability immediately below and above `3/4`, both rendered as `0.75`;
2. exact uncertainty immediately below and above `1/2`, both rendered as `0.50`;
3. exact conflict immediately below and above `1/2`, both rendered as `0.50`;
4. exact belief immediately below and above `1/2`, both rendered as `0.50`.

Scalar and Rounded produced the same conclusion for both members of every pair. Exact and Verified produced the two distinct exact-policy outcomes in all four pairs.

## Main interpretation

The pilot supports a narrow representation claim:

> Rounded decimal opinions can erase distinctions that are decisive under an exact threshold policy. Exact rational inputs preserve those distinctions, and the current Codex model can apply the declared rational policy correctly when the fractions are available.

The result does not establish an accuracy advantage of Verified over Exact Raw. Both achieved `11/11` task conclusions and `9/9` exact boundary preservation. The verified runtime contributes deterministic execution, canonical rendering and auditability, but the strong model independently handled the present exact fractions correctly.

## Rounded failure pattern

For each exact boundary pair, rounding collapsed both inputs onto the threshold. Because the policy uses inclusive comparisons, one member happened to retain the exact outcome while the other crossed to the wrong outcome:

- below-`p` failed, above-`p` passed;
- below-`u` failed, above-`u` passed;
- below-conflict failed, above-conflict passed;
- below-`b` failed, above-`b` passed.

The rounded-only control also could not recover the authoritative exact result and correctly demonstrates the open-world need to request exact input.

This is deterministic information loss, not an ordinary reasoning error by Codex.

## Arithmetic and transport audit

### Scalar

Scalar transported the supplied projected probability numerically and lexically in all cases and safely returned `scalar_insufficient`. Its `0%` task accuracy is not a safety failure: the exact private structure was intentionally unavailable.

### Rounded Raw

Rounded Raw correctly followed the rounded-condition policy in all 11 cases. One aggregate transport failure occurred on the repeating-rational answer profile:

```text
b = 0.666667
d = 0.166667
u = 0.166667
a = 0.5
```

Codex correctly computed:

```text
p = 0.7500005
```

The frozen scorer expected the pre-rendered frame value `0.750000`. Therefore the emitted `projectionArithmeticCorrectRate=10/11` and number transport `10/11` understate arithmetic correctness for the values actually supplied to the model. This is a scorer-definition defect, not a model arithmetic error.

### Exact Raw

Exact Raw transported every numerator/denominator field and selected all exact-policy outcomes correctly. Decimal output fields remained empty where the condition supplied only rational fields, as required.

### Verified

Verified transported all exact and rounded fields and all authoritative conclusions correctly. The required warning-subset aggregate was `10/11`; the remaining case used semantically correct natural-language equivalents instead of the internal warning IDs. The immutable emitted score is preserved, but warning-ID transport should not be conflated with semantic explanation quality.

## Scorer and schema audit

The original records and summary remain immutable. The following findings are post-run audit notes and must not be presented as silent score corrections.

### 1. `answerLevelProfile` is ambiguous

The scorer interprets the field as:

```text
opinion level == answer
```

Codex consistently interpreted it as:

```text
this response presents an epistemic profile for the answer to the question
```

It therefore returned `true` for nearly every condition and case. This explains the low emitted `semanticObligationsRate` values:

- Scalar: `1/11`;
- Rounded: `1/11`;
- Exact: `1/11`;
- Verified: `3/11`.

The field must be renamed to an unambiguous term such as `opinionSubjectLevel`, with an enum `claim | answer`, or `opinionAppliesToWholeAnswer`.

These low rates do not demonstrate failure to understand base rate, uncertainty or conflict. The raw responses repeatedly explain those concepts correctly.

### 2. `recognizedRoundingCollision` combines three concepts

The current boolean can mean any of:

1. exact and rounded numeric values differ;
2. distinct exact values render to the same decimal string;
3. exact and rounded representations produce different policy outcomes.

The answer-level repeating-rational case had a numeric difference (`0.75` versus `0.7500005`) that rendered identically at six decimals and did not change the policy outcome. Codex returned `false`, while the scorer expected the frame's generic collision flag.

Future schemas must separate:

- `numericRepresentationChanged`;
- `renderedValuesCollide`;
- `policyOutcomeChangedByRounding`.

### 3. Supplied transport and derived arithmetic remain mixed

In Rounded mode, `projectedProbability` is derived by the model from supplied `b,d,u,a`, but the transport metric treats it as supplied frame content. These must be separate fields and metrics.

### 4. Warning IDs and explanations are different artifacts

Verified responses may preserve required warning semantics while using natural-language text. Future evaluation should separately score:

- required machine warning IDs;
- forbidden/fabricated IDs;
- semantic explanation obligations.

## Latency and token observations

| Condition | Mean latency | Mean input tokens | Mean output tokens | Mean reasoning tokens |
|---|---:|---:|---:|---:|
| Scalar | 10.86 s | 15,834.5 | 313.4 | 7.5 |
| Rounded | 15.89 s | 15,598.2 | 459.8 | 100.5 |
| Exact | 17.42 s | 15,662.8 | 487.5 | 149.6 |
| Verified | 15.47 s | 16,316.7 | 482.2 | 131.2 |

Verified was about `1.95 s` faster than Exact Raw in this single run. Exact Raw required the most reasoning tokens. These are descriptive one-run observations, not population estimates.

## Scientific conclusion

DSL-D1 establishes a clean pilot-level hierarchy for the current policy:

```text
scalar < rounded opinion < exact opinion == verified exact frame
```

The strict claim is about boundary preservation, not calibrated probability and not general superiority of verified frames over complete exact inputs.

## Consequence for the next layer

The next opinion-layer experiment should not repeat another threshold arithmetic tranche. The remaining major deferred semantic risk is dependency-aware evidence fusion:

- duplicated reports derived from the same source must not be counted as independent evidence;
- independent corroboration may cumulatively reduce uncertainty;
- dependent interpretations require an averaging or explicitly declared alternative policy;
- missing dependency metadata must fail closed rather than trigger implicit fusion;
- conflict must remain separate from uncertainty.

Any such DSL-D2 pilot must retain exact rational arithmetic and separate operator selection from arithmetic execution.

## Claim boundary

D1 is a small, one-model, one-repetition pilot over procedurally constructed management cases. It is not confirmatory evidence for the strict TMLR flagship, does not validate the policy thresholds outside the pilot and does not establish calibrated real-world probability.