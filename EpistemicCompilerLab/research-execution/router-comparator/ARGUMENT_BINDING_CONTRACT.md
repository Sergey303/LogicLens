# Argument binding contract

Status: frozen ENG-200 boundary contract.

## Decision

ENG-200 is a **capability-selection-only** experiment.

The router outputs exactly one capability identity (or an explicit clarification/reject capability). It does not create, infer, repair, or optimize tool arguments.

## Independent held-equal binder

After route selection, an independently frozen binder maps pre-existing structured case fields into the selected capability's input schema.

The binder:

- is identical for M19, M20, direct-Qwen selection, human/static routing, and tree/Prolog representation checks;
- receives no teacher explanation, model output confidence, expected epistemic status, final answer, or correctness signal;
- cannot change the selected capability;
- validates output against the selected capability's frozen input schema;
- fails closed on missing, ambiguous, extra, or invalid arguments;
- records a separate `argument_binding` error layer;
- cannot retry by selecting a different capability.

For the primary route-selection comparison, argument values come from independently prepared structured case metadata. Raw natural-language argument extraction is outside ENG-200 and, if studied, must be a separate DEV-only treatment.

## Causal interpretation

Because argument binding is held equal and downstream of route selection, M19-vs-M20 can be interpreted as deterministic policy execution versus Qwen following the same frozen policy, rather than as a comparison of argument-generation ability.

Any future condition that lets Qwen or Codex form arguments as part of routing is a new treatment and requires a new mode contract and separate scoring.
