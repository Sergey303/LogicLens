# Routing equivalence and mutation tests

## Mandatory clean checks

`prototype/verify.py --require-swipl` must:

1. validate the standalone feature contract and require the policy to reference its exact ID/SHA-256;
2. validate the canonical IR against `TEACHER_ROUTING_IR.schema.json`;
3. validate the capability registry against `ROUTING_CAPABILITY_REGISTRY.schema.json`;
4. validate every referenced input/result JSON schema;
5. validate registry identity/version/handle uniqueness, budgets, failure semantics, provenance and no side effects;
6. prove graph reachability and acyclicity;
7. regenerate `generated/policy.pl` byte-for-byte;
8. regenerate both Qwen-visible catalogues byte-for-byte;
9. check all synthetic TRAIN/DEV cases;
10. exhaustively enumerate the complete frozen feature space and require decision-graph = SWI-Prolog routing;
11. require exact typed-feature input equality for the M19/M20/direct-Qwen primary contrast;
12. adversarially test that `requires_strict_policy` is not a global capability-label proxy;
13. scan Qwen-visible surfaces and policy explanation for case/question leakage;
14. verify canonical capability IDs are absent from Qwen-visible surfaces;
15. verify neutral/adapted schema surfaces differ only in label/description;
16. run named fail-closed mutation tests;
17. validate the top-level ENG-200 freeze manifest.

## Named mutation set

The machine-readable report must record names, not only a count:

- `missing_feature`;
- `invalid_goal`;
- `stale_capability_version`;
- `unavailable_capability`;
- `missing_node`;
- `policy_cycle`;
- `wrong_branch`;
- `case_id_leak_detected`;
- `canonical_capability_id_leak_detected`;
- `schema_surface_identity_preserved`.

The explicit leakage verifier must inject both a benchmark case ID and an internal canonical capability ID and prove that the shared scanner rejects both.

Because canonical routing is a deterministic graph rather than an unordered rule set, overlapping branches are structurally eliminated: each condition has exactly one true and one false successor. Exhaustive enumeration is the guard against accidental multi-policy ambiguity after lowering.

## Reviewer evidence

CI must record Python version, SWI-Prolog version, artifact hashes, feature-contract ID/hash, freeze-manifest hash, exhaustive vector count, case count, named mutation results, and typed capability-contract validation in a machine-readable report.
