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

`FactId` is derived from the canonical encoding of `(Subject, Predicate, Object)`.

Conceptually:

```text
FactId = sha256(canonical(Subject, Predicate, Object))
```

This gives:

- idempotent import;
- stable links from UI documents and proof evidence;
- deterministic replay;
- natural duplicate elimination.

The exact textual encoding and hash representation must be covered by golden tests before implementation is considered complete.

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

The active graph is materialized as `fact/4`. Changes are additionally appended to a journal:

```prolog
change(ChangeId, Revision, Actor, Timestamp, Operations).
```

where operations contain only:

```prolog
add(FactId, Subject, Predicate, Object).
delete(FactId).
```

The active graph may be updated immediately after a successful atomic write. On restart it can be reconstructed from the epoch snapshot plus the ordered journal.

### 6. Editing API

```text
ApplyDelta(
    ExpectedRevision,
    AddFact[],
    DeleteFact[]
)
```

`AddFact` carries `(Subject, Predicate, Object)`. The server computes `FactId`.

`DeleteFact` carries `FactId` and, for optimistic concurrency diagnostics, may also carry the triple last seen by the client.

Replacement is one atomic delta:

```text
DeleteFact(oldFactId)
AddFact(subject, newPredicate, newObject)
```

The whole delta succeeds or fails. The revision increments once.

### 7. Add and delete semantics

- Adding a triple already present is an idempotent no-op.
- Deleting an absent `FactId` is an idempotent no-op only when the request uses the current revision; with a stale revision the entire delta is rejected.
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
2. `FactId` is a pure deterministic function of the normalized triple.
3. Every active fact has at least one origin.
4. A derived result cannot be edited as a base fact.
5. An applied delta changes the revision exactly once.
6. A failed delta changes neither graph, journal, nor revision.
7. Replaying a snapshot and journal yields the same active graph and revision.
8. React never invents `FactId`; it receives it from the server.

## JSON boundary

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

Add operation:

```json
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
```

Delete operation:

```json
{
  "factId": "f:sha256:..."
}
```

## Verification cases

1. Import the same triple from two documents: one fact, two origins.
2. Import the same triple twice from one document: one fact, one deduplicated origin.
3. Add an existing triple: no new fact, journal records either a no-op result or no operation according to the final API policy.
4. Delete a fact with two origins: the visible triple disappears as a whole.
5. Re-add the deleted triple: the same deterministic `FactId` returns.
6. Replace a literal: old fact absent, new fact present, one revision increment.
7. Replace a predicate: old fact absent, new fact present, one revision increment.
8. Apply a stale delta: no graph, journal, or revision changes.
9. Rebuild from snapshot and journal: byte-order-independent equality of the normalized graph.
10. Produce a derived result: every evidence ID resolves to an active base fact.

## Rejected alternatives

### One assertion record per source occurrence

Rejected for v0 because it exposes archival multiplicity as editable data and makes deletion of one visible property ambiguous. It may later be added below the canonical graph if source-occurrence editing becomes a real requirement.

### `DeleteFact(Subject, Predicate, Object)` only

Rejected as the primary API because the client already receives a stable `FactId`; using it avoids normalization differences and improves concurrency diagnostics.

### Negative facts as the active model

Rejected for v0. Tombstones are useful in an overlay system, but LogicLens currently owns the active Prolog model after one-time import. A materialized graph plus append-only journal is simpler. Epoch creation provides compaction.

## Consequences

- The first version is a graph editor, not an archival assertion editor.
- Duplicate FOG occurrences remain inspectable through origins but are not separately editable.
- The effective graph requires no extra duplicate-elimination layer.
- Epoch snapshots can be compact and deterministic.
- Later source-specific editing can add an assertion-occurrence layer without changing UI facts or derived predicate contracts.