# DSL-D2 dependency-aware fusion ablation — 2026-08-06

## Status

The separate dependency-aware fusion pilot completed successfully with 11 frozen cases, 4 conditions and 44 Codex calls.

- LogicLens checkout: `95c0eea`
- Codex CLI: `0.145.0`
- SWI-Prolog: `10.0.2`
- Model selection: account default
- Repetitions: 1
- Frozen reports: `sha256:e0b8f561ba45eafe1d12ce3278c46edcf700356b02f674246ac93ed6e7b41c91`
- Frozen cases: `sha256:3e82d4e2348826a034946bd7f00c042ba706f161cf1b01b9bf5f87beded2616f`
- Prompt: `sha256:82433b5717a12d55ada2d6e0ca05cc44a1855cb08e33860549bdd64a8a6c4ee5`
- Response schema: `sha256:179a0e72847c5121a3a858ced23a497c3fd29b980f7cf3d51157eab35fc38ac3`

The frozen contract and the 44-call fake-provider contract completed before the real run. All 11 generated frames report:

```text
engine = python+swipl
verifiedArithmetic = true
verifiedOperatorPlan = true
verifiedPolicy = true
verifiedAgainstPrologKernel = true
```

All provider event logs contain only one `agent_message` and no command, file, MCP or web tool calls.

## Primary causal result

The key pair used identical evidence counts and differed only in declared dependency groups.

```text
dependent duplicate
same dependency group
-> average within group
-> R=3, S=0
-> qualified_uncertain
```

```text
independent corroboration
different dependency groups
-> cumulative across groups
-> R=6, S=0
-> assert_with_evidence
```

| Condition | Dependent duplicate | Independent corroboration | Pair distinguished |
|---|---|---|---:|
| Metadata absent | request dependency metadata | request dependency metadata | no |
| Naive independent | assert with evidence | assert with evidence | no |
| Raw declared groups | qualified uncertain | assert with evidence | yes |
| Verified DSL-D2 | qualified uncertain | assert with evidence | yes |

This is the main positive D2 finding.

Explicit dependency metadata plus the declared fusion policy prevented duplicate amplification. The naive-independent condition counted a dependent duplicate as independent corroboration and crossed the decision threshold. The metadata-absent condition correctly failed closed instead of inferring independence from identifiers, provenance or wording.

## Outcome accuracy

### Verified DSL-D2

Verified transported all 11 authoritative conclusions, actions, canonical operator plans, exact values and required warning IDs correctly.

```text
task conclusions:       11/11
condition conclusions:  11/11
canonical operator plan:11/11
exact value transport:  11/11
probability safety:     11/11
```

### Raw declared groups

Raw selected all 11 dependency-aware conclusions correctly and computed all complete exact profiles correctly.

```text
task conclusions:       11/11
condition conclusions:  11/11
complete arithmetic:    10/10 computable frames
```

For six homogeneous multi-report cases it returned the generic plan label `average_then_cumulative` instead of the specialized label `average_within_group` or `cumulative_across_groups`. Its natural-language explanation and exact numbers nevertheless showed the correct operation:

- same-group reports were averaged without amplification;
- different singleton groups were cumulatively combined;
- the mixed case used averaging followed by cumulative combination.

Therefore the emitted canonical-plan score `5/11` is valid as a label-transport metric, but the emitted `dependencySafetyRate=5/11` is too strict. It conflates canonical enum choice with dependency-safe arithmetic and conclusion. A post-run semantic audit gives:

```text
canonical operator label exact: 5/11
operator semantics correct:      11/11
dependency-aware conclusion:     11/11
```

The current pilot does not establish an accuracy advantage of Verified over Raw declared groups for final conclusions. Verified contributes canonical representation, deterministic execution and auditability.

### Naive independent

The naive baseline followed its explicitly incorrect assumption and returned the condition-specific conclusion in all 11 cases. It over-amplified dependent evidence in at least these cases:

- dependent duplicate;
- triple dependent dashboard reports;
- report with missing dependency metadata.

It did not distinguish the key dependent/independent pair. This is the intended failure mode.

### Metadata absent

For every multi-report case Codex refused to fuse without dependency groups. It correctly explained that independence cannot be inferred from report IDs, provenance or natural language.

The emitted condition score is `10/11`, but the remaining case exposes an oracle-order bug rather than a model error. In `incompatible-base-rate`, the condition hides dependency groups and contains multiple reports. The prompt requires requesting dependency metadata first. Codex did that. The condition-frame generator instead checked base-rate compatibility before metadata completeness and expected `request_compatible_base_rates`.

Correct prompt-consistent interpretation:

```text
multi-report metadata-absent safety: 10/10 request dependency metadata
single-report case:                  1/1 compute without fusion
condition behavior:                  11/11
```

## Scorer audit

The original records and `summary.json` remain immutable. The following findings are post-run audit notes and must not be presented as silent score rewriting.

### 1. Canonical label versus operator semantics

The prompt defines the two-stage algorithm but does not define the exact specialization rule for the enum labels:

```text
average_within_group
cumulative_across_groups
average_then_cumulative
```

Raw often used the general two-stage label while executing the correct specialized arithmetic. Future scoring must report separately:

- canonical operator-label exactness;
- operator-semantic correctness;
- arithmetic correctness;
- conclusion correctness.

`dependencySafety` must not require an exact canonical label when the executed dependency semantics are equivalent.

### 2. Metadata precedence

For `metadata_absent`, multiple reports must first fail closed on missing dependency metadata. Base-rate compatibility cannot authorize fusion and should not override the missing-metadata gate. The condition-frame oracle currently uses the opposite order for one case.

### 3. Single-source naive label

The naive condition-frame generator rewrites every computable frame to `naive_cumulative`, including the single-report control. Codex returned `single_source`, which is the more accurate operator description because no fusion occurred.

### 4. Partial values in blocked frames

The old `exactValueTransport` metric requires all exact fields to equal the blocked frame, usually empty strings. Codex sometimes returned valid accessible partial values:

- a common base rate even though dependency fusion was blocked;
- fused `R,S,b,d,u,conflict` while leaving projected probability empty when base rates were incompatible.

These are not full fused opinions and must not be scored as full-frame transport. Future schemas should distinguish:

- supplied source values;
- partial pre-policy aggregates;
- authoritative fused opinion;
- unavailable fields.

### 5. Action labels in the naive baseline

Several naive responses selected the correct conclusion but used `answer_with_prior_warning` rather than the canonical assert action because they emphasized that the independence assumption was intentionally unreliable. Conclusion accuracy and action-label fidelity should remain separate.

## Additional strata

The run also correctly handled:

- three dependent copies without evidence amplification under declared groups;
- mixed dependent and independent groups using average-then-cumulative;
- dependent conflict and independent conflict while preserving conflict separately from uncertainty;
- missing dependency metadata with fail-closed behavior;
- incompatible base rates without inventing a common prior;
- an answer-level proposition using `opinionSubjectLevel=answer`;
- independent negative evidence producing qualified refutation.

## Latency and token observations

| Condition | Mean latency | Mean input tokens | Mean output tokens |
|---|---:|---:|---:|
| Metadata absent | 12.56 s | 15,802.1 | 334.1 |
| Naive independent | 16.38 s | 15,533.6 | 483.1 |
| Raw declared | 15.44 s | 15,564.2 | 468.0 |
| Verified | 13.79 s | 15,825.4 | 356.8 |

Verified was about `1.65 s` faster than Raw declared in this single run and produced fewer output tokens. This is descriptive pilot evidence, not a population estimate.

## Scientific conclusion

DSL-D2 supports the following narrow pilot claim:

> Under an explicitly declared local fusion policy, dependency metadata prevents duplicated evidence from being treated as independent corroboration. A fixed strong language model can also execute the current policy correctly from raw exact reports when dependency groups are available.

The observed hierarchy is:

```text
metadata absent -> safe abstention
naive independence -> duplicate amplification risk
raw declared groups == verified frame for conclusions
verified frame > raw declared groups for canonical transport and auditability
```

D2 does not prove that asserted dependency groups reflect real causal independence. It does not validate the local fusion formula outside the pilot, establish calibrated real-world probability or provide confirmatory evidence for the strict TMLR flagship.

## Project consequence

The opinion-layer pilots have now isolated three representation risks:

1. scalar compression loses uncertainty, base-rate and conflict structure;
2. decimal rounding can erase policy-boundary distinctions;
3. missing dependency structure can amplify duplicated evidence.

In D0, D1 and D2, complete Raw input matched Verified on final conclusions for the current strong Codex model. Further opinion-layer micro-ablation has diminishing value for the flagship question. The next research effort should return to the publication critical path: fixed-weight small-model factor ablation on the strict epistemic benchmark, where the primary hypothesis concerns compiled verified frames versus contextual teaching.