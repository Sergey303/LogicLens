# Decision graph contract

The canonical policy is a typed, single-entry acyclic decision graph stored in `prototype/policy.ir.json`.

## Boundary

Condition nodes may read only the frozen feature vector:

- `goal_class`;
- `has_scope`;
- `has_version`;
- `asks_write`;
- `requires_strict_policy`.

Action nodes may reference only `canonical_id` + frozen version from the capability registry. The graph cannot carry SQL, Prolog goals, Python code, prompts, expected answers, case IDs, or result values.

## Determinism and ownership

The graph is the normative routing representation for the ENG-200 prototype. One feature vector reaches exactly one action or fails closed. The graph selects a capability; it does not execute domain semantics.

The feature extractor is an upstream independent component in the eventual experiment. This prototype starts from typed features so routing-policy performance is not confounded with natural-language feature extraction.

## M19

A deterministic executor traverses the graph before Qwen acts. Qwen receives no policy text and cannot change the selected capability.

## M20

Qwen receives the frozen neutral capability catalogue and a frozen explanation of the same accepted policy. Qwen selects a capability handle. The adapter maps that opaque handle to the internal canonical capability ID. Qwen never receives internal canonical IDs.

## Schema-surface control

Neutral labels/descriptions are the primary surface. A schema-adapted surface is an explicitly separate DEV-only factor. Policy bytes, capability IDs, handles, versions, and semantics remain identical.

This prevents a tool-naming improvement from being misreported as a routing-policy effect.

## Fail closed

Cycles, missing nodes, unknown features, stale versions, unavailable capabilities, undeclared capability IDs, and malformed feature vectors are errors. They are never repaired after observing outcomes.
