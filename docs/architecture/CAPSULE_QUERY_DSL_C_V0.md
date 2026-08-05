# Capsule Query DSL-C0

## Purpose

DSL-C0 extends the strict and logical capsule runtimes with typed numerical observations. It is designed to answer a narrow question deterministically:

> Does a packaged point or bounded observation satisfy a typed numerical comparison under explicit unit and boundary semantics?

A normal observation can be reported, but it cannot produce a strict threshold decision without an explicit probabilistic policy.

## Operations

### `observation`

Returns the packaged observation, its normalized representation, provenance, dependency group and scope.

### `numeric-comparison`

Supports:

- `lt`
- `lte`
- `gt`
- `gte`
- `between`

## Observation models

### Point

A single exact value with a declared unit.

### Bounded

A lower and upper bound with independent inclusivity flags. The runtime does not replace an interval by a midpoint or mean.

### Normal

A descriptive mean and standard deviation. DSL-C0 returns `unknown` for strict threshold decisions because a normal model has no finite strict bound and no probability policy is implied.

## Unit model

Allowlisted dimensions and base units:

| Dimension | Input units | Base unit |
|---|---|---|
| Duration | millisecond, second, minute, hour, day | second |
| Ratio | fraction, percent | fraction |
| Count | count | count |

All Python calculations use `Decimal`. Result JSON serializes normalized numbers as canonical decimal strings. SWI-Prolog receives scaled integers for independent comparison verification.

## Strict interval semantics

For a bounded observation:

- `supported` means every value in the observation interval satisfies the comparison;
- `refuted` means every value in the observation interval violates the comparison;
- `unknown` means the observation crosses or partially overlaps the decision boundary.

For `between`, inclusion and exclusion at both observation and comparison boundaries are preserved.

## Open-world behaviour

A declared metric target without a loaded observation returns:

```json
{
  "status": "unknown",
  "action": "abstain_on_numeric_decision",
  "warnings": ["missing-observation"]
}
```

Absence of a measurement is never converted into threshold failure.

## Trust boundary

The query runtime:

1. verifies the capsule package hash and file inventory;
2. validates typed target identifiers against the packaged semantic model;
3. loads only packaged observation files;
4. validates observation records and provenance references;
5. normalizes values with the allowlisted unit kernel;
6. computes the comparison in Python;
7. independently recomputes the comparison in SWI-Prolog;
8. rejects the result on disagreement.

The LLM receives the resulting frame; it is not responsible for the authoritative arithmetic.

## Experimental ablation

The management-course experiment uses three conditions:

1. **Direct** — no private measurement;
2. **Raw observation** — the same source observation and comparison, without a computed result;
3. **Verified DSL-C** — the complete deterministic frame.

This separates:

- information availability (`Direct → Raw`);
- formal numerical execution (`Raw → Verified DSL-C`);
- safe abstention from private-fact guessing;
- exact number transport from semantic interpretation.

## Deliberate boundary before DSL-D

DSL-C0 does not:

- select confidence levels;
- calculate a normal-tail decision probability;
- introduce priors;
- fuse dependent observations;
- emit belief, disbelief, uncertainty or base rate.

Those behaviours require an explicit DSL-D opinion or probabilistic decision policy. Keeping this boundary prevents the runtime or LLM from silently turning descriptive uncertainty into a fabricated probability.
