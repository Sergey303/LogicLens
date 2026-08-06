# Mode Contracts — WP-004

`modes.yaml` is the normative W0 causal-design contract for M0–M14.

A later runtime implementation may add machine-specific manifests, but may not change visible/hidden inputs, authoritative fields, renderer identity, matching rules or eligibility without a pre-HOLDOUT reviewed revision.

## Primary interpretation

`M6 − M14` is a **multi-component deployed-interface bundle effect**. It compares trusted execution plus a verified result interface with the strongest full-information matched non-compiled source interface. It is not, by itself, a single-factor estimate of solver execution, typed structure, conclusion fields or rendering.

Component interpretation requires the frozen M9–M13 contrasts.

## Factor interpretation

- M0–M5 and M14 do not receive an authoritative computed result.
- M6 is the deployable compiled verified-interface treatment.
- M7 is a gold renderer ceiling, not a deployable system.
- M8 is a strong-model ceiling, not an eligible baseline.
- M9 isolates typed structure while preserving all verified semantic values.
- M10 tests whether the status label alone explains the benefit.
- M11 removes the LLM renderer while keeping the same semantic frame.
- M12 removes only `allowedConclusion` from M6 and marks the field absent.
- M13 mutates exactly one preregistered field per run.
- M14 instantiates the frozen globally selected B* without a computed result and retains its complete source representation.

## Lossless token matching

Length matching may never weaken a control by deleting information.

For every scenario and model profile:

1. serialize the full unpadded inputs for the compared LLM modes;
2. compute token counts with the frozen model-profile tokenizer;
3. set the common envelope to the maximum count;
4. add frozen scenario-independent neutral padding only to shorter modes;
5. preserve exact unpadded and padded byte/token manifests.

Forbidden operations include truncation, assertion/rule removal, outcome-dependent summarization, informative padding and post-HOLDOUT matching repair.

A scenario that cannot fit the lossless envelope plus frozen output reserve is rejected during benchmark construction before split assignment; it is never removed after outcomes are visible.

## Baseline robustness

The headline uses one globally DEV-selected B* to prevent outcome-driven comparator switching. A mandatory secondary sensitivity selects the strongest eligible baseline separately for each frozen model profile using the same DEV-only ranking. Failure against a profile-specific strongest control forces claim narrowing for that profile.

## Freeze rule

No mode may be added or semantically changed after HOLDOUT access. Any implementation mismatch is a protocol deviation and invalidates affected confirmatory blocks.
