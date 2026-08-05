# Progressive management numeric-frame experiment v0

Answer the management-course question in Russian and return only the JSON object required by the supplied output schema.

## Experimental conditions

- `direct`: neither the private observation nor a verified frame is supplied. Do not guess the Northstar measurement. Return `unknown`, abstain, use empty numerical strings, `modelKind: "missing"`, `baseUnit: "none"`, and no identifiers.
- `raw`: `rawObservation` and the comparison request are supplied, but no computed result is supplied. Interpret the typed observation, convert allowlisted units when needed, preserve interval/distribution semantics, and perform the comparison yourself.
- `gold-c`: `verifiedFrame` is supplied. Treat its status, action, observation, normalized values, comparison, warnings and scope as authoritative. Do not strengthen or silently contradict it.

Set `usedVerifiedFrame` to true only for `gold-c`.
Set `usedRawObservation` to true only when the condition is `raw` and `rawObservation` is a non-null object. For the missing-observation control it must be false.

## Strict numerical semantics

- A point supports or refutes a comparison according to its exact normalized value.
- A bounded observation is `supported` only when every value in the interval satisfies the comparison.
- A bounded observation is `refuted` only when every value in the interval violates the comparison.
- When a bounded observation crosses or partially overlaps the decision boundary, return `unknown` and abstain. Never replace the interval by its midpoint or mean.
- A normal model provides a mean and standard deviation, not a strict finite bound. Without an explicit probability level and decision policy, a strict threshold conclusion is `unknown`.
- A missing observation is `unknown`, not `refuted`.
- Do not invent a probability, confidence level, z-score, credible interval or decision policy.
- Preserve inclusive/exclusive boundary meaning.
- Local observations apply only to the named snapshot and organisation.

## Canonical numeric fields

Copy canonical normalized strings from `verifiedFrame` in `gold-c`.
In `raw`, calculate the same canonical base representation:

- durations → `second`;
- ratios and percentages → `fraction`;
- counts → `count`.

Use plain decimal strings without units, exponent notation or trailing zeroes. Use the empty string for a numeric field that does not apply.

- Point: fill `normalizedPoint`.
- Bounded: fill `normalizedLower` and `normalizedUpper`.
- Normal: fill `normalizedMean` and `normalizedStandardDeviation`.
- Single threshold: fill `normalizedThresholdValue`.
- `between`: fill `normalizedThresholdLower` and `normalizedThresholdUpper`.

For a missing observation set all normalized fields to empty strings and `baseUnit` to `none`.

## Interpretation fields

- `preservedInterval` is true only when a bounded observation was kept as a bounded interval in the reasoning.
- `preservedDistribution` is true only when a normal observation was kept as a distribution and was not treated as a strict bound.
- `introducedProbabilityPolicy` must remain false unless an explicit probability policy is present in the input. This experiment never supplies one.
- `observationId` must be copied from the supplied raw observation or verified frame; otherwise use the empty string.
- Copy `warnings` exactly from the verified frame in `gold-c`. In `raw`, produce the warnings implied by the same numerical semantics. In `direct`, use an empty array.

Use these `interpretationFlags` where applicable:

- `local-snapshot-only`
- `point-comparison`
- `whole-interval-satisfies`
- `whole-interval-violates`
- `interval-crosses-threshold`
- `distribution-not-strict-bound`
- `probability-policy-missing`
- `missing-observation`
- `unit-conversion-required`
- `inclusive-range`

The prose answer must explain the actual number or interval, threshold, unit conversion, and reason for `unknown` when relevant. Merely copying flags is insufficient.

The experiment input is between the markers below.
