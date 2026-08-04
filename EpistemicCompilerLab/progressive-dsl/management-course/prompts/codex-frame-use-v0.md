# Progressive management frame-use experiment v0

Answer the management-course question in Russian and return only the JSON object required by the supplied output schema.

## Epistemic discipline

- `epistemicStatus` describes whether the proposition is supported, refuted, unknown or conflicting under the information available in this experimental condition.
- When `verifiedFrame` is present, treat it as authoritative for the loaded capsule. Do not recompute, strengthen or silently contradict it.
- `unknown` is not `false`. For `unknown`, set `abstain` to `true`, use `abstain_and_request_context`, and state what context is missing.
- `conflicting` is not ignorance. Report both sides and use `report_conflict_and_compare_models`.
- Copy `evidenceIds`, `proofNodeIds` and `warnings` only from the verified frame. Never invent identifiers.
- When no frame is present, set `usedVerifiedFrame` to `false`, leave `evidenceIds` and `proofNodeIds` empty, and answer from the public question only.
- A local or context-dependent rule must never be presented as a universal management law.
- A proof that delegation is allowed does not transfer the delegator's retained strategic accountability.

## Conclusion strength

- `assert`: supported without a material scope warning.
- `qualified`: supported or refuted, but scope, locality or another warning must be preserved.
- `abstain`: unknown.
- `report_conflict`: conflicting.

The `answer` should be concise but must preserve role boundaries, scope and any retained responsibility relevant to the question.

The experiment input is between the markers below.
