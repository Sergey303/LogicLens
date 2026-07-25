# A0 architecture exit criteria

Status: verification gate for milestone A0.

The A0 architecture is ready to merge when all criteria below are satisfied.

## Canonical data model

- The active graph is a set of normalized triples.
- A canonical fact is represented by `fact(FactId, Subject, Predicate, Object)`.
- `FactId` is deterministic from the versioned canonical byte encoding defined in ADR-0001.
- Repeated archival occurrences attach several origins to one fact.
- Base facts and derived results are represented separately.
- Derived results expose rule identity and evidence fact IDs and are read-only.

## Runtime changes

- The only external base-data primitives are `AddFact` and `DeleteFact`.
- A replacement is one atomic delta containing delete plus add.
- `ApplyDelta` contains `CommandId` and `ExpectedRevision`.
- Replaying a completed command is idempotent.
- A semantic no-op does not increment the revision.
- Failure changes neither graph, journal nor revision.
- Crash-safe persistence details are intentionally deferred to ENG-24.

## Graph traversal

- `subgraph1` and `subgraph2` are aliases over one bounded traversal engine.
- The result separates a normalized graph slice from path-sensitive occurrences.
- Repeated semantic paths to one node are preserved.
- Cycles terminate and remain visible as references.
- Incoming and outgoing facts preserve their original direction.
- Traversal limits and truncation are visible in diagnostics.
- Fact visibility and traversal eligibility are independent.
- `rdf:type`, technical, provenance and UI/profile predicates remain visible but are not followed by default.
- Ordinary unknown IRI predicates are followed by default unless explicitly excluded or classified as non-traversable.
- Query overrides are explicit, bounded and deterministic.

## UI contract

- React depends only on UI Document v0, not on the domain ontology.
- The trusted vocabulary is closed and versioned.
- Any entity and predicate can be rendered by the generic fallback.
- Every visible base value carries the complete base fact source required for editing.
- Derived values cannot be marked editable by the JSON Schema.
- Unknown and technical facts remain inspectable.
- Arbitrary HTML, JavaScript and unknown component properties are rejected.
- Rich components are deferred to later contract versions.

## Epoch and resolver boundaries

- Epoch ID and runtime revision are distinct.
- Builder writes only to a candidate epoch workspace.
- Search writes only to an isolated request workspace.
- Neither resolver mutates the active epoch or graph directly.
- Candidate activation requires deterministic validation.

## Consistency gate

- README, architecture-v0, ADR-0001, ADR-0002, ADR-0003, ADR-0004 and the JSON Schema use the same terminology.
- Known unresolved implementation questions are assigned to later Linear issues rather than hidden in architecture prose.
- ENG-23 is allowed to implement only the contracts accepted here; changing them requires a new ADR or an explicit amendment.

## Result

Passing this gate means that A0 defines a sufficiently small and internally consistent architecture for the zero-epoch vertical slice. It does not claim that performance, crash safety, LLM quality or rich UI components have already been validated.
