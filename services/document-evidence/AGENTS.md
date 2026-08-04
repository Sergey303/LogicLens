# Document Evidence Service agent rules

The root [`AGENTS.md`](../../AGENTS.md) remains authoritative. These rules narrow work under this
service directory.

## Isolation

- Treat this directory as an independently deployable service.
- Do not add direct project references from product applications into its persistence layer.
- Consumers use generated OpenAPI clients and versioned events.
- Do not import product catalogue or capsule-activation domain models.

## Trusted core

The trusted core is deterministic:

- authorization and quota checks;
- safe byte ingestion;
- hashing and immutable storage;
- format validation;
- parser adapters;
- canonical document IR;
- artifact manifests;
- revision and revocation state.

LLM or OCR outputs are proposals or derived artifacts with explicit provenance. They never replace
original bytes or deterministic anchors.

## Module boundaries

Keep handwritten modules separate from generated clients and contracts:

```text
src/
  Api/
  Application/
  Domain/
  Infrastructure/
  FormatAdapters/
  Generated/
tests/
  Contract/
  Integration/
  Security/
```

No handwritten file exceeds 150 lines and no handwritten C# `partial` declaration is allowed.

## Required tests

Every format adapter needs:

- accepted minimal fixture;
- malformed signature or container fixture;
- oversized or bounded-resource fixture;
- deterministic regeneration check;
- stable source-anchor check;
- revocation and access-denial checks.

Storage implementations share one contract suite. Access must be rejected before byte lookup or
streaming when the caller lacks permission.
