# ADR-0004: Traversal edge eligibility

- Status: Proposed
- Linear: ENG-35
- Amends: ADR-0002
- Depends on: ADR-0001

## Context

ADR-0002 originally described graph distance through IRI-valued facts:

```prolog
fact(_, Subject, Predicate, iri(Object)).
```

Taken literally, this makes every IRI object a traversal neighbor. That is incorrect for generic pages:

- `rdf:type` would expand every entity into its class resource;
- technical and provenance links could pull implementation metadata into normal subgraphs;
- a fact may need to remain visible without becoming an expansion edge.

The problem was found while verifying the ENG-29 zero-epoch fixture. The fixture expected class facts to remain visible, but not to create class-node occurrences.

## Decision

LogicLens separates **visible incident facts** from **eligible traversal edges**.

### 1. Every incident fact remains visible

When a node is expanded, all permitted incident base facts are assigned to the earliest layer and remain available to the view:

```prolog
visible_incident_fact(Node, Direction, FactId, Subject, Predicate, Object).
```

This includes:

- literals;
- `rdf:type`;
- technical facts;
- provenance facts exposed by the selected view mode;
- IRI-valued facts that are not eligible for traversal.

Visibility and traversal eligibility are independent decisions.

### 2. Only eligible IRI facts create occurrences

A neighboring node and path occurrence are created only through:

```prolog
traversal_edge(
    Policy,
    FactId,
    Subject,
    Predicate,
    Object,
    Direction
).
```

Conceptually:

```prolog
traversal_edge(Policy, FactId, S, P, O, Direction) :-
    fact(FactId, S, P, iri(O)),
    predicate_traversal_mode(Policy, P, follow),
    direction_allows(Policy, Direction).
```

A non-eligible IRI fact still appears in `slice_fact`, but its object does not enter `slice_node` and no occurrence is created from that fact.

### 3. Default policy is deny-by-category, not allow-by-ontology

Unknown domain predicates must continue to work. Therefore the default is:

```text
follow ordinary known IRI predicates
follow ordinary unknown IRI predicates
do not follow explicitly non-traversable categories
```

The default non-traversable categories are:

```text
rdf:type
technical predicates
provenance predicates
UI/profile predicates
ontology-schema predicates when ontology data is exposed beside the data graph
```

This is a denylist by semantic category, not a whitelist of known predicates. A new unknown relation is therefore traversable unless it is marked technical or explicitly excluded.

### 4. Required default examples

```prolog
predicate_traversal_mode(default, rdf:type, no_follow).
predicate_traversal_mode(default, Predicate, no_follow) :-
    technical_predicate(Predicate).
predicate_traversal_mode(default, Predicate, no_follow) :-
    provenance_predicate(Predicate).
predicate_traversal_mode(default, Predicate, follow) :-
    ordinary_relation_predicate(Predicate).
```

`ordinary_relation_predicate/1` includes unknown IRI-valued predicates unless another rule classifies them as non-traversable.

### 5. Query options may narrow or deliberately expand the policy

A query may provide bounded overrides:

```text
includePredicates
excludePredicates
followTypeLinks
followTechnicalLinks
```

Defaults:

```text
followTypeLinks = false
followTechnicalLinks = false
```

Explicit exclusions win over inclusions. Global node, fact, occurrence and depth limits still apply.

The first implementation may expose only `excludePredicates` and the two booleans. The policy model is defined now so later Builder/Search behavior does not require changing graph semantics.

### 6. Layer semantics remain unchanged

- Every incident fact becomes visible at the earliest layer when its subject or object node is expanded.
- Only eligible traversal edges affect distance and occurrences.
- A non-followed IRI object can still be rendered as a `ResourceLinkValue`.
- Opening that link as a new page is navigation, not continuation of the current subgraph expansion.

### 7. Example: rdf:type

Base fact:

```prolog
fact(f_type, person_1, rdf:type, iri(fog:person)).
```

For `subgraph1(person_1)` under the default policy:

```text
slice_fact contains f_type
slice_node does not contain fog:person because of f_type
occurrences contain no fog:person occurrence through f_type
```

The UI may still display the type label and allow navigation to the class resource.

### 8. Example: unknown relation

Base fact:

```prolog
fact(f_related, org_a, 'urn:logiclens:test:related', iri(org_b)).
```

Unless the predicate is classified as technical or excluded:

```text
slice_fact contains f_related
slice_node contains org_b
an occurrence for org_b is created
```

This preserves generic behavior for unrecognized domain relations.

### 9. Example: technical IRI

Base fact:

```prolog
fact(f_source, person_1, system:source_document, iri(document_1)).
```

Under the default policy:

```text
slice_fact contains f_source in the technical section
no document_1 occurrence is created
```

A technical inspection query may opt in explicitly.

## Invariants

1. Every active fact selected by the view policy remains inspectable whether or not it is traversable.
2. Traversal eligibility never changes FactId or base graph contents.
3. `rdf:type` does not create a neighbor under the default policy.
4. An unknown ordinary IRI predicate remains traversable by default.
5. A technical or provenance predicate does not create a neighbor by default.
6. Direction, cycle and global-limit rules from ADR-0002 apply after eligibility filtering.
7. The same policy and overrides produce deterministic nodes, facts and occurrences.

## Verification cases

1. `rdf:type` appears in facts but creates no class occurrence.
2. A literal fact appears in facts and creates no node.
3. A known ordinary IRI predicate creates a neighbor.
4. An unknown ordinary IRI predicate creates a neighbor.
5. A technical IRI predicate remains visible but creates no neighbor.
6. A provenance IRI predicate remains visible but creates no neighbor.
7. `followTypeLinks=true` deliberately creates a class occurrence.
8. `excludePredicates` suppresses traversal without suppressing fact visibility.
9. An explicit include cannot override an explicit exclude.
10. Cycle detection operates on the filtered edge set.
11. Incoming and outgoing modes apply after eligibility classification.
12. Diagnostics report explicit policy limits or overrides when they materially change the result.

## Rejected alternatives

### Follow every IRI-valued fact

Rejected because schema and implementation metadata become accidental domain topology.

### Allowlist only ontology-declared object properties

Rejected because unknown domain predicates would lose generic traversal and Builder/Search could not inspect newly imported relations before ontology updates.

### Hide non-traversable facts

Rejected because visibility and expansion solve different problems. Hiding would violate inspectability and the generic fallback contract.

## Consequences

- ADR-0002 distance is now measured over eligible traversal edges, not all IRI-valued facts.
- The fixture can assert that `rdf:type` is visible without treating class IRIs as ordinary neighbors.
- Unknown relations remain useful in the generic system.
- Technical metadata stays available without dominating subgraph size.
- Builder and Search must use the same explicit policy rather than inventing traversal rules per request.
