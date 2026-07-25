# Benchmark cases

`benchmark-v0.jsonl` is the first fixed case set for comparing knowledge representations.

Each line is one independent JSON object. The benchmark preserves the same domain meaning while changing only the representation available to the student.

## Required fields

- `id` — stable unique case identifier;
- `questionRu` — user-facing Russian question;
- `expectedAction` — `query` or `ask_user`;
- `expectedStatus` — `success`, `unknown` or `need_user`;
- `requiresTail` — `null`, `evidence` or `exceptions`;
- `tailEntity` — the entity that owns the required tail, or `null`.

Query cases also contain:

- `query.operation`;
- `query.arguments`;
- `expectedMaterial` when a unique material must be returned.

Clarification cases contain `expectedField`.

A tail is not implicitly owned by `expectedMaterial`. A result may select one entity while its explanation or exception list belongs to the rule, replacement target or source assertion represented by another entity.

Do not require a tail for a direct answer when the compact result and proof already contain enough information. For example, selecting `asd2` for revision A after the transition is already justified by `rule:revision_a_exception`; the `exceptions` tail is reserved for a separate request to inspect the exception set.

## CLI result contract

Every `current-material` response has a `solutions` array:

- `success` contains one or more solution objects;
- `unknown` contains `solutions: []`;
- consumers must not infer array contents from a missing property.

This stable shape keeps PowerShell, future gateways and student tools independent of runtime-specific missing-property behaviour.

## Representation modes

Run the same cases with:

1. original Markdown source;
2. compact JSON knowledge;
3. Prolog source read without execution;
4. SWI-Prolog CLI;
5. CLI plus targeted optional tails.

The question text, model settings and scoring rules remain fixed within one comparison.

## Scoring

Record separately:

- correct action selection;
- correct final status;
- correct material when applicable;
- correct decision to open or not open a tail;
- correct tail entity;
- unnecessary CLI calls and tails;
- semantic query errors;
- final-answer accuracy.

`need_user` is an expected translator decision, not a Prolog result. `unknown` is an expected knowledge result and must not be rewritten as `false`.
