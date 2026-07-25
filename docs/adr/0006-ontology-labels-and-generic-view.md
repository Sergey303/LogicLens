# ADR-0006: Ontology labels and generic entity view

- Status: Proposed
- Linear: ENG-37
- Depends on: ADR-0001, ADR-0003, ADR-0005
- Scope: zero-epoch labels and root entity card before traversal

## Context

LogicLens needs a useful page for every entity before type-specific profiles, Builder, Search, or rich UI components exist.

The source ontology is not a FOG cassette. It uses a compact custom XML vocabulary such as:

```xml
<Class rdf:about="...">
  <label xml:lang="ru">...</label>
</Class>

<ObjectProperty rdf:about="..." priority="m">
  <label xml:lang="ru">...</label>
  <inverse-label xml:lang="ru">...</inverse-label>
</ObjectProperty>
```

Treating this as ordinary entity data would mix schema metadata with the active graph. Parsing it inside runtime Prolog would also duplicate source-format concerns. The ontology therefore receives its own one-time compiler and generated Prolog package.

## Decision

### 1. Ontology labels are a separate generated package

```text
data/Ontology.xml
  -> LogicLens.OntologyCompiler
  -> epochs/epoch-000/ontology/ontology.generated.pl
```

The compiler extracts only metadata required by the zero-epoch UI:

- term identifier;
- term kind;
- forward labels;
- inverse labels;
- optional priority.

It does not import domain/range/cardinality as validation rules in v0.

### 2. Generated ontology terms

```prolog
ontology_term(Resource, Kind).
ontology_label(Resource, Direction, Language, Text).
ontology_priority(Resource, Priority).
```

Kinds:

```text
class
datatype_property
object_property
enumeration_type
```

Directions:

```text
forward
inverse
```

Language is an atom such as `ru`, `en`, or `plain`. Label and priority values are strings.

Examples:

```prolog
ontology_term('http://fogid.net/o/person', class).
ontology_label('http://fogid.net/o/person', forward, ru, "Персона").
ontology_label('http://fogid.net/o/person', forward, en, "Person").

ontology_term('http://fogid.net/o/participant', object_property).
ontology_label(
    'http://fogid.net/o/participant',
    inverse,
    ru,
    "участник в орг."
).
ontology_priority('http://fogid.net/o/participant', "m").
```

Generated metadata is loaded by a reviewed module:

```prolog
:- module(ontology_data, [
    ontology_term/2,
    ontology_label/4,
    ontology_priority/2
]).
```

### 3. Runtime labels have two sources

Resource titles are selected from active graph name facts:

```prolog
fact(_, Resource, 'http://fogid.net/o/name', literal(Text, LanguageKind)).
```

Ontology labels are used for:

- predicates;
- class resources;
- other ontology terms.

A resource name from active data has priority over an ontology label because it describes the concrete entity rather than its type.

### 4. Language policy

Default Russian UI order:

```text
ru -> en -> plain -> first stable available
```

The requested language list may be changed by options, but `plain` and deterministic final fallback remain.

“First stable” means the candidate with the lowest deterministic key, not source-file order. Candidate order uses language, text, and source identity.

Alternate labels are not deleted. The generic view selects one display label while source facts remain represented in property groups.

### 5. Predicate labels depend on direction

Outgoing relation:

```text
ontology inverse? no
use forward label
```

Incoming relation:

```text
use inverse label when available
otherwise forward label
otherwise compact identifier
```

Direction remains a separate field in the view model even when an inverse label is used.

### 6. Compact identifier fallback

When no selected data or ontology label exists, LogicLens displays the final non-empty segment after `#`, `/`, or `:`.

Examples:

```text
http://fogid.net/o/name             -> name
urn:logiclens:test:internal-code    -> internal-code
urn:logiclens:person:alex           -> alex
```

The complete identifier remains available in the view model.

### 7. Generic root entity view

The zero-epoch root card is constructed from incident facts only. Traversed neighbor expansion belongs to ENG-38.

```prolog
entity_view(Entity, Options, View).
```

Neutral view shape:

```text
View = {
  kind: entity_view,
  entity: Entity,
  title: String,
  groups: [Group...],
  diagnostics: []
}
```

Group shape:

```text
Group = {
  direction: outgoing | incoming,
  predicate: Predicate,
  label: String,
  priority: String | null,
  technical: true | false,
  values: [Value...]
}
```

Groups are formed by `(direction, predicate)`. Each base fact belongs to exactly one group.

### 8. Outgoing and incoming display values

For an outgoing fact:

```prolog
fact(FactId, Entity, Predicate, Object)
```

- a literal displays the literal;
- an IRI displays a link to the object resource.

For an incoming fact:

```prolog
fact(FactId, Subject, Predicate, iri(Entity))
```

the displayed link points to `Subject`, while source metadata preserves the complete original triple.

### 9. Base source snapshot

Every displayed value carries:

```text
source = {
  kind: base,
  factId: FactId,
  subject: Subject,
  predicate: Predicate,
  object: canonical tagged object,
  origins: [OriginId...]
}
```

This is required even for incoming values. React and the later API never reconstruct a mutation from the displayed target alone.

### 10. Technical facts

Technical status is declared by reviewed policy rules, not inferred merely because a predicate is unknown.

```prolog
technical_predicate('urn:logiclens:test:internal-code').
```

Technical facts remain in the generic view with `technical: true`; the API later places them in a collapsed technical section.

### 11. Deterministic ordering

Groups are ordered by:

1. normal before technical;
2. ontology priority, missing last;
3. outgoing before incoming;
4. predicate identifier.

Values inside a group are ordered by `FactId`.

Origins are ordered by `OriginId`.

No ordering depends on clause, XML, hash-table, or filesystem order.

### 12. Raw Prolog is separate

`entity_view/3` does not embed executable source. A separate predicate returns a plain-text fragment of the exact incident base facts:

```prolog
entity_prolog(Entity, Text).
```

The browser will later render this as `RawProlog`; it never executes it.

## Invariants

1. Every root incident base fact appears in exactly one group.
2. A base fact is never represented only by a generated summary.
3. Incoming display reversal never changes the source triple.
4. Unknown predicates remain visible.
5. Technical predicates remain visible.
6. Entity title selection does not remove name facts from groups.
7. The same epoch, entity, and options produce structurally equal view terms.
8. Generic view construction does not use type-specific rules.
9. Ontology XML is not parsed during runtime view queries.

## Verification cases

1. Person title selects Russian name.
2. Document title falls back to English.
3. Organization title falls back to untagged text.
4. Class resource uses ontology label.
5. Unknown resource uses compact identifier.
6. Outgoing property uses forward ontology label.
7. Incoming property uses inverse label.
8. Incoming value links to the original subject and preserves the full source triple.
9. Unknown predicate uses compact identifier.
10. Technical predicate is present and marked technical.
11. Several values of one predicate share one group.
12. Every root incident fact appears exactly once.
13. Every base source lists all origins.
14. Two calls return equal normalized JSON.
15. Raw Prolog contains all and only root incident facts.

## Rejected alternatives

### Parse Ontology.xml in every Prolog process

Rejected because runtime should query a stable epoch package, not repeat source-format import.

### Add ontology labels to the active fact graph

Rejected for v0 because schema metadata and editable domain facts have different ownership and mutation rules.

### Use only forward labels for incoming relations

Rejected because the ontology already carries explicit inverse wording and the user should see the relation from the current entity’s perspective.

### Hide unknown or technical facts

Rejected because generic fallback is an inspectability guarantee.

## Consequences

- zero-epoch pages can be useful without domain-specific React code;
- the source ontology remains inspectable but separate from editable data;
- labels and grouping are deterministic and testable in SWI-Prolog;
- ENG-38 can add nested subgraphs without changing the root property/value contract;
- ENG-32 can map the neutral view to UI Document v0 without interpreting domain semantics.
