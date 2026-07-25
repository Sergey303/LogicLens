# ADR-0003: Minimal trusted UI Document

- Status: Proposed
- Linear: ENG-22
- Depends on: ADR-0001 and ADR-0002

## Context

React must render data independently of the domain ontology. The first architecture draft listed tables, trees, graphs, timelines, images, and other components before any experiment demonstrated that they were required.

A smaller trusted core can display every base fact, nested subgraph occurrences, and the Prolog artifacts central to the research.

## Decision

UI Document v0 contains a minimal closed vocabulary.

### Structural components

```text
Page
Section
```

`Section` may contain another `Section`, allowing `subgraph2` and later bounded hierarchical views without introducing a separate tree component.

### Data components

```text
Property
TextBlock
RawProlog
Diagnostic
```

### Property value kinds

```text
TextValue
ResourceLinkValue
```

`Property` contains an array of values, so a separate `PropertyList` is unnecessary. `Section` replaces both `Group` and nested layout containers.

## 1. Root contract and context

```json
{
  "schemaVersion": "0.1",
  "epoch": 0,
  "revision": 17,
  "context": {
    "kind": "entity",
    "entityId": "person:1"
  },
  "page": {
    "kind": "page",
    "id": "page:person:1",
    "title": "Иван",
    "sections": []
  },
  "diagnostics": []
}
```

Contexts:

```text
entity — stable entity page
query  — Search result without one mandatory root entity
```

A UI Document is immutable for its `(EpochId, Revision)` pair.

## 2. Generic entity fallback

Every entity is renderable without a type-specific profile.

The generic resolver:

1. selects the preferred label using the language policy;
2. obtains outgoing and incoming base facts;
3. groups facts by `(direction, predicate)`;
4. resolves a predicate label or falls back to a compact identifier;
5. maps literals to `TextValue`;
6. maps IRIs to `ResourceLinkValue`;
7. places technical predicates in a collapsed technical section rather than dropping them;
8. optionally adds a `RawProlog` section for research inspection.

No base fact may disappear merely because its type or predicate is unknown.

## 3. Nested sections and occurrence context

A section used for a subgraph occurrence may carry:

```json
{
  "occurrence": {
    "occurrenceId": "occ:study:isi",
    "nodeId": "organization:isi",
    "depth": 1,
    "parentOccurrenceId": "occ:root",
    "viaFactId": "f:sha256:study",
    "direction": "outgoing",
    "state": "expanded"
  }
}
```

This is view context, not duplicated graph data. The same `nodeId` may appear in several sections with different `occurrenceId` values.

Maximum nesting depth is enforced before React.

## 4. Property component

```json
{
  "kind": "property",
  "id": "property:out:fog:name",
  "predicate": "fog:name",
  "label": "Имя",
  "direction": "outgoing",
  "values": []
}
```

Directions:

```text
outgoing
incoming
derived
```

Values are grouped by predicate. Sorting, grouping, and path merging are view rules, not React behavior.

## 5. Base and derived sources

Each displayed data value declares its source.

A base source contains the complete canonical fact snapshot, not only `FactId`:

```json
{
  "kind": "base",
  "fact": {
    "factId": "f:sha256:...",
    "subject": "person:1",
    "predicate": "fog:name",
    "object": {
      "kind": "literal",
      "lexical": "Иван",
      "literalKind": "language",
      "language": "ru",
      "datatype": null
    }
  },
  "origins": ["o_archive_1"]
}
```

The full fact makes outgoing and incoming edits unambiguous and lets React assemble transparent `DeleteFact + AddFact` deltas without guessing the triple from layout context.

A derived source contains rule identity and evidence:

```json
{
  "kind": "derived",
  "ruleId": "rule:sbras_academician",
  "evidenceFactIds": ["f:sha256:1", "f:sha256:2"]
}
```

A value is editable only when its source is `base` and the server sets `editable: true`. The schema requires `editable: false` for derived sources.

## 6. Literal shape

The UI literal mirrors ADR-0001:

```text
plain
language
datatype
```

Examples:

```json
{
  "kind": "text",
  "text": "Иван",
  "literalKind": "language",
  "language": "ru",
  "datatype": null,
  "editable": true,
  "source": {}
}
```

Rules:

- `plain`: language and datatype are null;
- `language`: language is present and datatype is null;
- `datatype`: datatype is present and language is null.

The lexical representation is displayed without trimming or normalization. A datatype may influence a later editor, but v0 may still use a text input.

## 7. Resource link value

```json
{
  "kind": "resourceLink",
  "targetId": "organization:isi",
  "label": "ИСИ СО РАН",
  "editable": true,
  "source": {}
}
```

For an outgoing property, `targetId` usually corresponds to the fact object. For an incoming property it usually corresponds to the fact subject. The complete fact snapshot in `source` remains authoritative.

When no label exists, `label` is the compact target identifier. The link remains usable.

## 8. TextBlock

`TextBlock` is plain text generated by a stable rule or Search result. Markdown and arbitrary HTML are excluded from the trusted v0 renderer.

```json
{
  "kind": "textBlock",
  "id": "summary:1",
  "text": "Найдено три связанных проекта."
}
```

When it states data-derived information, it should carry a derived source. Static explanatory text may omit a source.

## 9. RawProlog

```json
{
  "kind": "rawProlog",
  "id": "search:query",
  "title": "Запрос Prolog",
  "code": "answer_person(Person) :- ...",
  "artifactKind": "query"
}
```

Artifact kinds:

```text
query
data
view
rule
diagnostic
```

Raw Prolog is rendered as text and is never evaluated in the browser.

## 10. Diagnostic

```json
{
  "kind": "diagnostic",
  "id": "limit:1",
  "severity": "warning",
  "message": "Результат ограничен 200 узлами."
}
```

Severities:

```text
info
warning
error
```

Truncation, unsupported generated components, and fallback behavior must be visible.

## 11. Technical section policy

Technical and normally hidden facts remain accessible in a section with `presentation: technical`. React renders it collapsed by default.

This preserves inspectability without making every page visually noisy.

## 12. Validation before React

The server rejects a UI Document when any of the following is true:

1. unsupported `schemaVersion`;
2. unknown component or value kind;
3. missing or duplicate component ID;
4. section nesting exceeds configured depth;
5. component, value, or byte limits are exceeded;
6. a base fact does not exist at the declared revision;
7. a displayed base value does not correspond to its embedded fact and direction;
8. `editable: true` is set for a derived value;
9. derived evidence references missing base facts;
10. a literal kind conflicts with language or datatype fields;
11. a resource link target is structurally invalid;
12. occurrence context refers to a missing parent, node, or fact;
13. RawProlog exceeds limits or is not plain text;
14. the document contains HTML, script, executable URLs, or arbitrary React properties.

A rejected generated document falls back to the generic entity page.

## 13. Prolog representation

SWI-Prolog constructs the contract as dictionaries and serializes it to JSON:

```prolog
View = _{
    schemaVersion: "0.1",
    epoch: Epoch,
    revision: Revision,
    context: _{kind: entity, entityId: Entity},
    page: _{
        kind: page,
        id: PageId,
        title: Title,
        sections: Sections
    },
    diagnostics: Diagnostics
}.
```

The JSON schema, not ad-hoc predicate arity, is the external UI contract.

## 14. Deferred components

The following are not part of trusted UI Document v0:

```text
Table
Tree
Graph
Timeline
Image
Map
Form
Tabs
arbitrary Markdown/HTML/CSS/JS
```

They may enter a later contract version after a Builder/Search experiment demonstrates:

- a repeated need;
- a stable data contract;
- safe rendering;
- a useful fallback when unavailable.

Search may generate HTML/CSS in an isolated experimental path, but that output is not equivalent to a validated UI Document.

## 15. Verification cases

1. Unknown entity type with known predicates.
2. Unknown predicates with literals and IRIs.
3. Several values for one predicate.
4. Russian label available.
5. No Russian label, English fallback available.
6. No labels, compact identifier fallback.
7. Incoming relation has an unambiguous complete source fact.
8. Technical fact remains available in a collapsed section.
9. Base value exposes a complete fact and editability.
10. Derived value exposes rule and evidence and is schema-enforced read-only.
11. Plain, language, and datatype literals reject invalid field combinations.
12. Nested occurrence sections represent two paths to the same node.
13. Raw query, data, and view Prolog fragments render as text.
14. Invalid generated component causes generic fallback.
15. Every active root fact is represented at least once in normal or technical sections.
16. Repetition of one FactId is allowed only when tied to explicit occurrence contexts.

## Rejected alternatives

### Large component ontology in epoch 0

Rejected because it expands React and validation before the research has shown which rich representations are useful.

### Flat sections only

Rejected because `subgraph2` would either lose hierarchy or encode paths into presentation labels.

### Base source containing only FactId

Rejected because incoming links cannot be safely reconstructed for replacement without fetching or guessing the underlying triple.

### Arbitrary component props from Prolog or LLM

Rejected because it turns the UI contract into an unbounded remote code/configuration surface.

### Trusted Markdown or HTML text blocks

Rejected for v0. Plain text is sufficient for summaries and avoids a second rendering/security language.

### Hiding unknown or technical facts completely

Rejected because it violates inspectability and can conceal information from both users and architecture tests.

## Consequences

- The zero-epoch renderer remains small but can express bounded hierarchy.
- Every graph fact remains visible without type-specific React code.
- The document is self-contained enough to explain and edit outgoing and incoming facts.
- Builder and Search initially focus on composition and logic rather than visual novelty.
- Rich visualizations remain possible through explicit future contract versions and the separate experimental HTML path.