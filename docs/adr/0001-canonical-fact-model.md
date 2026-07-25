# ADR-0001: Canonical fact, provenance, and change model

- Status: Proposed
- Linear: ENG-20
- Scope: zero epoch and later runtime deltas

## Context

LogicLens imports archival FOG/cassette data once and then treats the Prolog representation as the active data model. The first version needs a small model that supports:

- an RDF-like graph;
- stable fact identity;
- multiple archival origins for the same triple;
- `AddFact` and `DeleteFact` as the only editing primitives;
- atomic replacement as delete plus add;
- provenance for derived results;
- deterministic reconstruction from an epoch snapshot and its delta journal.

The initial candidate `fact(Subject, Predicate, Object, Provenance)` mixed the graph fact with one source occurrence. A later candidate introduced an assertion ID for every occurrence. That preserves every occurrence, but makes the editor operate on an assertion multiset rather than on the graph visible to the user.

## Decision

### 1. The canonical data model is a set of triples

Identical normalized triples are one canonical fact, even when they occur in several FOG documents.

```prolog
fact(FactId, Subject, Predicate, Object).
fact_origin(FactId, OriginId).
origin(OriginId, Origin).
```

`FactId` identifies the triple, not an individual source occurrence.

### 2. Fact IDs are deterministic

`FactId` is derived from the canonical encoding of `(Subject, Predicate, Object)`:

```text
FactId = "f:sha256:" + lowercaseHex(sha256(CanonicalFactBytes))
```

Canonical bytes use LogicLens encoding version 1, not Prolog source text, JSON formatting, or `write_canonical/1` output.

Each field is UTF-8 encoded and preceded by its byte length as an unsigned big-endian 64-bit integer. The stream is:

```text
ASCII "LogicLensFact\0"
version byte 0x01
field(Subject)
field(Predicate)
object tag
object fields
```

Object tags:

```text
0x01: IRI       -> field(Resource)
0x02: plain     -> field(Lexical)
0x03: language  -> field(lowercaseLanguageTag), field(Lexical)
0x04: datatype  -> field(Datatype), field(Lexical)
```

Rules:

- prefixes are expanded before hashing;
- resource and datatype identifiers are hashed exactly as imported after prefix expansion;
- lexical literal text is not trimmed, case-folded, or Unicode-normalized;
- language tags are lowercased;
- no locale-sensitive conversion is allowed;
- a future incompatible encoding increments the version byte.

This custom encoding is deliberately simple to reproduce in C#, Prolog tests, and other tools. Golden byte and hash vectors are required.

### 3. Subjects and predicates are resource identifiers; objects are tagged

```prolog
fact(FactId, Subject, Predicate, iri(Resource)).
fact(FactId, Subject, Predicate, literal(Lexical, plain)).
fact(FactId, Subject, Predicate, literal(Lexical, lang(Language))).
fact(FactId, Subject, Predicate, literal(Lexical, datatype(Datatype))).
```

Examples:

```prolog
fact(f_1, 'person:1', 'rdf:type', iri('fog:person')).
fact(f_2, 'person:1', 'fog:name', literal('Иван', lang(ru))).
fact(f_3, 'person:1', 'fog:birthDate', literal('1987-12-11', datatype('xsd:date'))).
```

The tagged literal form prevents invalid combinations such as simultaneously assigning a language and a non-language datatype.

### 4. Duplicate source occurrences become multiple origins

```prolog
fact(f_name, 'person:1', 'fog:name', literal('Иван', lang(ru))).
fact_origin(f_name, o_archive_1).
fact_origin(f_name, o_archive_2).
```

The UI normally shows one value and may show that it has two archival origins.

Source-specific deletion is intentionally outside the first version. `DeleteFact` removes the graph fact as a whole from the effective state.

### 5. Active state and history are separate

The active graph is materialized as `fact/4`. State-changing deltas are additionally appended to a journal:

```prolog
change(ChangeId, BeforeRevision, AfterRevision, Actor, Timestamp, Operations).
```

Operations contain only:

```prolog
add(FactId, Subject, Predicate, Object).
delete(FactId).
```

The active graph may be updated immediately after a successful durable write. On restart it can be reconstructed from the epoch snapshot plus the ordered journal.

Accepted commands also have an idempotency receipt keyed by `CommandId`. Receipt persistence and crash-safe ordering are specified by ENG-24 rather than by the fact model.

### 6. Editing API

```text
ApplyDelta(
    CommandId,
    ExpectedRevision,
    AddFact[],
    DeleteFact[]
)
```

`AddFact` carries `(Subject, Predicate, Object)`. The server canonicalizes it and computes `FactId`.

`DeleteFact` carries `FactId` and, for optimistic concurrency diagnostics, may also carry the triple last seen by the client.

Replacement is one atomic delta:

```text
DeleteFact(oldFactId)
AddFact(subject, newPredicate, newObject)
```

The whole state-changing delta succeeds or fails. Its revision increments exactly once.

### 7. Add, delete, and no-op semantics

- Adding a triple already present is an idempotent no-op.
- Deleting an absent `FactId` is an idempotent no-op only when the request uses the current revision; with a stale revision the entire command is rejected.
- A command containing only no-op operations is accepted, returns the unchanged revision, and does not append a state-change journal entry.
- The command result is stored as an idempotency receipt, so retrying the same `CommandId` returns the original result.
- Reusing a `CommandId` with different content is rejected.
- Deleting a fact removes it from the active graph but does not alter archived FOG files.
- Re-adding the same triple restores the same deterministic `FactId`.
- Exact duplicate facts cannot exist in the active graph.

### 8. Derived predicates are not base facts

Derived results must not be passed to `DeleteFact` or `AddFact` as though they were stored facts.

A derived result may expose evidence:

```prolog
derived_result(ResultId, RuleId, Value, EvidenceFactIds).
```

For the first version, `EvidenceFactIds` is a sorted unique list of canonical base `FactId` values. A full proof DAG is deferred until a demonstrated use case requires it.

### 9. Provenance model

An origin is metadata about how a canonical fact entered the graph.

Examples:

```prolog
origin(o_archive_1,
       archival(cassette('cassette-a'),
                document('originals/0001.fog'),
                entity('person:1'))).

origin(o_user_42,
       edit(user('sergey'),
            change(c_42),
            timestamp('2026-07-25T05:00:00Z'))).
```

The exact archival fields may expand, but the `fact/4` contract does not change.

## Invariants

1. At most one active `fact/4` exists for a normalized triple.
2. `FactId` is a pure deterministic function of the canonical triple encoding.
3. Every active fact has at least one origin.
4. A derived result cannot be edited as a base fact.
5. A state-changing delta changes the revision exactly once.
6. A no-op command leaves the revision and state-change journal unchanged.
7. A failed command changes neither graph, journal, revision, nor accepted-command receipts.
8. Replaying a snapshot and journal yields the same active graph and revision.
9. React never invents `FactId`; it receives it from the server.
10. The same `CommandId` cannot represent two different requests.

## JSON boundary

Canonical fact:

```json
{
  "factId": "f:sha256:...",
  "subject": "person:1",
  "predicate": "fog:name",
  "object": {
    "kind": "literal",
    "lexical": "Иван",
    "literalKind": "language",
    "language": "ru"
  },
  "origins": ["o_archive_1", "o_archive_2"]
}
```

Apply delta:

```json
{
  "commandId": "01J35Y7P5P7K8QY9FJ0N8W2M4C",
  "expectedRevision": 17,
  "delete": [
    {
      "factId": "f:sha256:old"
    }
  ],
  "add": [
    {
      "subject": "person:1",
      "predicate": "fog:name",
      "object": {
        "kind": "literal",
        "lexical": "Иван Иванов",
        "literalKind": "language",
        "language": "ru"
      }
    }
  ]
}
```

## Verification cases

1. Import the same triple from two documents: one fact, two origins.
2. Import the same triple twice from one document: one fact, one deduplicated origin.
3. Hash fixed canonical byte vectors in two implementations and receive identical IDs.
4. Add an existing triple: no new fact, unchanged revision, stored idempotency result.
5. Delete a fact with two origins: the visible triple disappears as a whole.
6. Re-add the deleted triple: the same deterministic `FactId` returns.
7. Replace a literal: old fact absent, new fact present, one revision increment.
8. Replace a predicate: old fact absent, new fact present, one revision increment.
9. Apply a stale delta: no graph, journal, receipt, or revision changes.
10. Retry an accepted `CommandId`: return the original result without reapplying.
11. Reuse a `CommandId` with different content: reject the request.
12. Rebuild from snapshot and journal: byte-order-independent equality of the normalized graph.
13. Produce a derived result: every evidence ID resolves to an active base fact.

## Rejected alternatives

### One assertion record per source occurrence

Rejected for v0 because it exposes archival multiplicity as editable data and makes deletion of one visible property ambiguous. It may later be added below the canonical graph if source-occurrence editing becomes a real requirement.

### `DeleteFact(Subject, Predicate, Object)` only

Rejected as the primary API because the client already receives a stable `FactId`; using it avoids normalization differences and improves concurrency diagnostics.

### Prolog term text as canonical hash input

Rejected because quoting, escaping, implementation versions, and formatting can change. Fact identity must not depend on a Prolog printer.

### Canonical JSON as hash input

Rejected for v0 because cross-language canonical JSON adds rules and dependencies not otherwise needed by the data model.

### Negative facts as the active model

Rejected for v0. Tombstones are useful in an overlay system, but LogicLens currently owns the active Prolog model after one-time import. A materialized graph plus append-only journal is simpler. Epoch creation provides compaction.

## Consequences

- The first version is a graph editor, not an archival assertion editor.
- Duplicate FOG occurrences remain inspectable through origins but are not separately editable.
- The effective graph requires no extra duplicate-elimination layer.
- Fact IDs remain stable across file order, Prolog formatting, and repeated imports.
- Epoch snapshots can be compact and deterministic.
- Later source-specific editing can add an assertion-occurrence layer without changing UI facts or derived predicate contracts.