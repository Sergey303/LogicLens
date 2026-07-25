# ENG-23: zero-epoch vertical slice

## Goal

Build the smallest executable path that proves the accepted A0 contracts can work together:

```text
sample archival data
  -> one-time import
  -> canonical Prolog facts and labels
  -> generic entity view
  -> validated UI Document v0
  -> universal React renderer
```

The slice is deliberately not a production platform. It is an executable architecture test.

## Scope

### Data

Use a small synthetic or safely redistributable fixture containing:

- at least three entity types;
- literals in Russian and English;
- an untagged literal;
- an unknown predicate;
- one technical predicate;
- incoming and outgoing links;
- one repeated triple from two archival origins;
- one cycle;
- one entity reachable by two different predicates, such as `studiedAt` and `workedAt`.

The imported FOG/cassette fixture remains immutable after import.

### Prolog

Implement only:

- `fact/4`, `fact_origin/2`, `origin/2`;
- deterministic `FactId` encoding with golden vectors;
- label lookup and compact-identifier fallback;
- language selection `ru -> en -> untagged -> first available`;
- grouping by direction and predicate;
- generic entity fallback view;
- bounded traversal engine sufficient for `subgraph1` and `subgraph2`;
- plain Prolog artifact output for inspection.

### Server

Expose a narrow API:

```text
GET /api/entities/{id}/view
GET /api/entities/{id}/facts
GET /api/entities/{id}/prolog
GET /api/health
```

`GET /view` returns a server-validated UI Document v0. No LLM is involved.

### React

Implement the trusted v0 vocabulary only:

- Page;
- nested Section;
- Property;
- TextBlock;
- RawProlog;
- Diagnostic;
- TextValue;
- ResourceLinkValue.

React must not contain domain type switches such as `Person`, `Organization` or `Document`.

## Suggested repository layout

```text
src/
  LogicLens.Core/
  LogicLens.Import/
  LogicLens.Prolog/
  LogicLens.Api/
  logiclens-web/

epochs/
  epoch-000/
    manifest.json
    data/
    ontology/
    rules/
    tests/

fixtures/
  zero-epoch/

contracts/
  ui-document-v0.schema.json

tests/
  LogicLens.Core.Tests/
  LogicLens.Integration.Tests/
```

Project names remain provisional until the first scaffold proves the boundaries useful. Avoid creating separate assemblies without an actual dependency boundary.

## Implementation sequence

1. Add fixture and expected normalized facts.
2. Implement canonical object model and FactId encoder.
3. Generate Prolog files for epoch 000.
4. Load them in SWI-Prolog and expose deterministic query commands.
5. Implement generic view construction.
6. Validate output against UI Document v0 schema.
7. Implement React renderer.
8. Add navigation through resource links.
9. Add raw Prolog inspection.
10. Run golden and end-to-end tests.

## Required tests

### Canonical facts

- Same triple from two sources creates one fact with two origins.
- Prefix aliases produce the same expanded identifiers and FactId.
- Literal language tag case does not change FactId.
- Literal lexical whitespace does change FactId.
- C# and Prolog golden vectors agree.

### Language policy

- Russian is selected when present.
- English is selected when Russian is absent.
- Untagged is selected when Russian and English are absent.
- First stable value is selected only as the final fallback.
- Alternate language values remain inspectable.

### Generic UI

- Unknown type renders successfully.
- Unknown predicate renders with compact identifier.
- Incoming relation displays the other entity but preserves the complete source triple.
- Technical fact remains accessible.
- Every active base fact appears exactly once in normal or technical sections.
- Resource links navigate without React domain knowledge.

### Traversal

- Depth 1 contains root facts and direct neighbors.
- Depth 2 adds newly exposed neighbor facts without duplicating canonical facts.
- Two semantic paths to one node remain distinct occurrences.
- A cycle terminates and emits a cycle reference.
- Configured limits produce a diagnostic.

### Contract validation

- Valid generated document passes the JSON Schema and semantic validator.
- Unknown component fails.
- Derived value with `editable=true` fails.
- Missing base fact source fails.
- Duplicate component IDs fail semantic validation.

## Acceptance criteria

ENG-23 is complete when:

1. one command starts SWI-Prolog, API and React locally;
2. a known entity opens through the generic page;
3. resource navigation works;
4. all base facts remain inspectable;
5. Russian/English fallback behaves as specified;
6. `subgraph1` and `subgraph2` can be rendered with nested sections;
7. the raw Prolog data used for the page is visible;
8. the UI Document passes schema and semantic validation;
9. automated tests cover the required cases;
10. no Builder, Search or domain-specific React component is present.

## Explicit non-goals

- production FOG importer completeness;
- runtime editing and ApplyDelta persistence;
- PolarDB projection;
- Builder or Search;
- authentication and permissions;
- rich UI components;
- arbitrary HTML generation;
- performance conclusions on large datasets.

## Architecture feedback rule

When implementation reveals a contract problem, do not patch around it in React or API. Record the failing example, update the relevant ADR and schema in a separate architecture change, then continue the slice against the corrected contract.
