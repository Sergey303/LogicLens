# Decision graph contract

The canonical policy is a typed, single-entry acyclic decision graph stored in `prototype/policy.ir.json`.

## Independent feature boundary

The normative feature definitions live in `ROUTING_FEATURE_CONTRACT.json`, not inside the teacher policy. The policy references that contract by ID and SHA-256.

Condition nodes may read only the frozen feature vector:

- `goal_class`;
- `has_scope`;
- `has_version`;
- `asks_write`;
- `requires_strict_policy`.

The feature vector is independently supplied and validated before routing. For the primary M19-vs-M20/direct-Qwen comparison, the same canonical serialized feature bytes are used in all three arms. Raw-question feature extraction is a separate DEV-only ablation.

`requires_strict_policy` is an output-obligation feature: it means the request explicitly requires strict four-state epistemic handling, conflict preservation, or an auditable policy trace. It must not be defined as “use Prolog” or any other implementation choice.

## Boundary

Action nodes may reference only `canonical_id` + frozen version from the capability registry. The graph cannot carry SQL, Prolog goals, Python code, prompts, expected answers, case IDs, result values, or bound tool arguments.

## Determinism and ownership

The graph is the normative routing representation for the ENG-200 prototype. One feature vector reaches exactly one action or fails closed. The graph selects a **capability only**; it does not execute domain semantics or bind arguments.

Argument binding is performed after route selection by the same independently frozen adapter in M19, M20, and direct-Qwen routing. Binding failures are scored separately and cannot trigger rerouting.

## M19

A deterministic executor traverses the graph using the frozen typed feature vector before Qwen acts. Qwen receives no policy text and cannot change the selected capability.

## M20

Qwen receives the exact same typed feature vector, the frozen neutral capability catalogue, and a frozen explanation of the same accepted policy. Qwen selects a capability handle. The adapter maps that opaque handle to the internal canonical capability ID. Qwen never receives internal canonical IDs.

## Direct-Qwen baseline

Direct Qwen receives the exact same typed feature vector and neutral capability catalogue as M20, but no teacher policy/explanation. This isolates the value of the teacher-generated routing policy.

## Schema-surface control

Neutral labels/descriptions are the primary surface. A schema-adapted surface is an explicitly separate DEV-only factor. Policy bytes, capability IDs, handles, versions, typed I/O schemas, budgets, failure semantics, and capability semantics remain identical.

## Fail closed

Cycles, missing nodes, unknown features, stale versions, unavailable capabilities, undeclared capability IDs, malformed feature vectors, invalid schema references, and argument-binding failures are errors. They are never repaired after observing outcomes.
