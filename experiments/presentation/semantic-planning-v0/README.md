# Semantic planning benchmark v0

Status: frozen research fixture set.

This directory is the first replayable benchmark for the research gate described in
`docs/research/semantic-presentation-planning-v1.md`.

It does not add a production Semantic IR contract, a planner implementation, a rich UI
component, or an LLM invocation path. The files freeze inputs and oracle boundaries
before implementation begins.

## What is frozen

Each case contains six independent boundaries:

1. task and answer key;
2. canonical facts with stable fixture-local `factId` values;
3. ontology evidence visible to a resolver;
4. oracle semantic claims;
5. oracle deterministic dataset profile;
6. acceptable presentation decisions and required rejection reasons.

The `fixture:*` identifiers are benchmark-local opaque FactIds. They intentionally do
not claim to be production FactId v1 hashes. Future import tooling may translate them
into production canonical facts while preserving the frozen references inside the
benchmark envelope.


## Vocabulary boundary

The `facet`, `role`, component, and rejection-reason strings are frozen oracle labels
for this research set; they are not an already accepted production enum. A future
schema must explicitly accept, map, or reject each value. A runner must not silently
normalize `publication_time`, `monetary_amount`, `age`, or any other role into a broader
role because that would erase the interpretation boundary the case is intended to test.

## Cases

1. `clear-revision-comparison` — positive table case with explicit labels and datatypes.
2. `opaque-revision-comparison` — positive case where predicate names and labels do not
   reveal their roles; the task and neighboring facts are required evidence.
3. `ambiguous-time-excluded` — a table remains useful, but an ambiguous time-like field
   must be excluded from the primary view and retained in the generic fallback.
4. `lookalike-incomparable-records` — equal-looking numeric records must not be forced
   into a comparison table when their meanings are temperature, price, and age.
5. `single-entity-generic-fallback` — a rich comparison view is rejected because there
   is only one entity.

## Replay order

A future runner must support these replays without changing the case files:

```text
canonicalFacts
  -> oracleSemanticClaims
  -> oracleDatasetProfile
  -> expectedPresentation
```

Later measured runs may replace one boundary at a time:

```text
model semantic claims + trusted profile + planner
oracle semantic claims + trusted profile + planner
oracle semantic claims + oracle profile + planner
oracle presentation decision + UI compiler
golden UI Document + React renderer
```

## Mutation policy

The set is append-only after merge. Corrections require a new benchmark version or an
explicit replacement case with a new `caseId`. Existing case bytes and their hashes in
`manifest.json` must not be rewritten silently.
