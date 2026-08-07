# Routing equivalence and mutation tests

## Mandatory clean checks

`prototype/verify.py --require-swipl` must:

1. validate the canonical IR against `TEACHER_ROUTING_IR.schema.json`;
2. validate registry identity/version/handle uniqueness;
3. prove graph reachability and acyclicity;
4. regenerate `generated/policy.pl` byte-for-byte;
5. check all synthetic TRAIN/DEV cases;
6. exhaustively enumerate the complete frozen feature space and require decision-graph = SWI-Prolog routing;
7. scan Qwen-visible surfaces and policy explanation for case/question leakage;
8. verify canonical IDs are absent from Qwen-visible surfaces;
9. verify neutral/adapted schema surfaces do not change IDs, handles, versions or capability semantics;
10. run fail-closed mutation tests.

## Mutation set

- wrong branch destination → at least one expected route changes and the case test fails;
- missing feature → graph execution rejects malformed vector;
- invalid/ambiguous goal → outside-schema goal is rejected; declared `other` routes to clarification;
- stale capability version → registry-policy version check fails;
- unavailable capability → runtime rejects the leaf instead of choosing another capability;
- leaf/case leak → injected case ID in visible label is detected;
- missing node → graph validation fails;
- policy cycle → graph validation fails before execution;
- generated Prolog drift → byte-for-byte regeneration fails;
- schema-label-only change → routing output remains identical, establishing it as a separate presentation factor.

Because canonical routing is a deterministic graph rather than an unordered rule set, overlapping branches are structurally eliminated: each condition has exactly one true and one false successor. Exhaustive enumeration is the guard against accidental multi-policy ambiguity after lowering.

## Reviewer evidence

CI must record Python version, SWI-Prolog version, artifact hashes, exhaustive vector count, case count, and mutation-test count in a machine-readable report.
