# Failure, Retry, Exclusion and Block-Rerun Rules — WP-006

Status: **producer statistical contract; pending independent review**

## 1. Default rule

Every planned scenario/mode/paraphrase/repetition remains in the denominator. Scientific or model failures are outcomes, not exclusions.

Count incorrect:

- timeout after allowed attempts;
- provider/runtime error after allowed attempts;
- empty output;
- malformed JSON;
- response-schema invalidity;
- forbidden tool call;
- mandatory-language violation;
- missing mandatory contract field;
- unexpected model artifact or hidden-input access;
- process crash attributable to the evaluated mode;
- inability to token-match M14 under the frozen rule.

No semantically wrong or malformed response is retried.

## 2. Retry contract

Freeze per model/runtime before confirmatory execution:

```text
max attempts
retryable infrastructure error codes
per-attempt timeout
backoff schedule
cold/warm-state rule
```

Only failures demonstrably outside model semantics are retryable. All attempts and event logs are retained. Analysis uses the final allowed attempt while also reporting attempt-level failure counts.

## 3. No post-outcome exclusions

Never exclude because a case is difficult, ambiguous after seeing outputs, unfavorable, inconsistent with pilots, a model family performs poorly, a mode times out often, or a source/rule/status stratum reverses the effect.

A source/case defect discovered after execution is handled by the frozen adjudication rule and reported. It is not silently repaired or removed.

## 4. Pre-execution eligibility failures

Before model execution, a scenario may be marked `not_executed_protocol_invalid` only when an independent outcome-blind audit proves:

- source rights prohibit the declared use;
- required source bytes are unavailable or hash-drifted;
- annotation/adjudication is incomplete;
- the case violates the frozen schema or leakage grouping;
- no valid query/frame normal form exists under the written semantic spec;
- a canary or sealed-path violation occurred.

The scenario remains in the completeness report, with immutable reason and timing. Replacement, if allowed, must be generated from the predeclared reserve pool without seeing model outcomes.

## 5. Infrastructure-wide outage

A complete randomized block may be rerun only when:

- the outage affects all modes in the block or makes paired comparison impossible;
- the trigger matches a preregistered infrastructure code;
- no partial scientific scores from that block were inspected;
- the entire block, including successes, is rerun under the same frozen configuration;
- old and new raw artifacts remain available;
- an independent operations reviewer approves the rerun.

Partial favorable reruns are forbidden.

## 6. Mode/config drift

If a frozen model, prompt, schema, tokenizer, source, compiler, scorer, mode transformation or hardware/runtime contract drifts:

- STOP the affected batch;
- quarantine outputs;
- determine scope before scores are inspected;
- do not merge old/new versions;
- rerun every affected mode symmetrically only after reviewed versioning;
- publish the deviation and both artifact chains.

## 7. Scorer bug after HOLDOUT

A scorer correction requires:

1. written bug and affected fields;
2. proof no hypothesis, threshold, acceptable alternative or favorable rule changed;
3. version/hash bump;
4. independent review;
5. symmetric rerun of scoring for every affected mode and split;
6. publication of old and corrected results.

If scientific choice changed, the confirmatory claim is invalidated rather than repaired.

## 8. Missingness reporting

Report by mode, model, domain and failure category:

- planned observations;
- attempted observations;
- successful schema-valid outputs;
- retries;
- timeouts/provider/runtime failures;
- malformed/schema failures;
- forbidden tool/artifact violations;
- scenario-level failures after aggregation.

No complete-case-only primary analysis is permitted.

## 9. STOP conditions

STOP or invalidate the affected confirmatory route when hidden gold is exposed, raw output storage fails before scoring, frozen hashes drift, sealed data leak, retries depend on semantic correctness, partial results influence remaining execution, or failure handling cannot be applied symmetrically.
