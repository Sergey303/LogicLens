# Mode Contracts — WP-004

`modes.yaml` is the normative W0 causal-design contract for M0–M14.

A later runtime implementation may add machine-specific manifests, but may not change visible/hidden inputs, authoritative fields, renderer identity, matching rules, or eligibility without a pre-HOLDOUT reviewed revision.

## Factor interpretation

- M0–M5 and M14 do not receive an authoritative computed result.
- M6 is the deployable compiled verified-interface treatment.
- M7 is a gold renderer ceiling, not a deployable system.
- M8 is a strong-model ceiling, not an eligible baseline.
- M9 isolates typed structure while preserving verified semantic content.
- M10 tests whether the status label alone explains the benefit.
- M11 removes the LLM renderer while keeping the exact M6 frame.
- M12 removes only `allowedConclusion` from M6 and marks the field absent.
- M13 mutates exactly one field per run.
- M14 instantiates the frozen globally selected non-compiled baseline under M6's token/output envelope.

## Freeze rule

No mode may be added or semantically changed after HOLDOUT access. Any implementation mismatch is a protocol deviation and invalidates affected confirmatory blocks.
