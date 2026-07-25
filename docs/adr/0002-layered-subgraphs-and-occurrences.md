# ADR-0002: Layered subgraphs and repeated-path occurrences

- Status: Proposed
- Linear: ENG-21
- Depends on: ADR-0001

## Context

LogicLens needs reusable `subgraph1(Entity)` and `subgraph2(Entity)` predicates for generic pages and for LLM-generated views.

A normalized graph must not duplicate nodes or facts. A useful page, however, may need to show the same resource more than once when it is reached through different meaningful relations. For example, one person may both study and work at the same institute.

A plain node set loses path meaning. A plain tree duplicates data and can expand forever on cycles.

## Decision

A subgraph result has two coordinated representations:

1. a normalized graph slice with unique nodes and facts;
2. a path-sensitive occurrence structure used to compose the page.

```text
SubgraphResult = GraphSlice + Occurrences + OccurrenceFacts
```

## 1. Public predicates

```prolog
subgraph1(Entity, Options, Result) :-
    subgraph(Entity, 1, Options, Result).

subgraph2(Entity, Options, Result) :-
    subgraph(Entity, 2, Options, Result).
```

The numeric predicates are aliases. One generic engine implements traversal for all depths and entity types.

Type-specific names may be generated as thin wrappers only:

```prolog
person_subgraph2(Entity, Options, Result) :-
    entity_type(Entity, 'fog:person'),
    subgraph2(Entity, Options, Result).
```

They must not copy traversal logic.

## 2. Distance

Graph distance counts only resource-to-resource links.

```prolog
fact(_, Subject, Predicate, iri(Object)).
```

Literals are properties of an expanded node and do not become graph nodes.

Traversal supports:

```text
outgoing
incoming
both
```

The default generic entity page uses `both`. Edge direction is always preserved in the result even when distance is computed over both directions.

## 3. Layer semantics

Layer numbers describe when facts become visible while expanding from the root.

- layer 0: the root node;
- layer 1: facts exposed by expanding the root;
- layer 2: new facts exposed by expanding nodes at minimum distance 1;
- layer N: new facts exposed by expanding nodes at minimum distance N-1.

A fact is assigned to its earliest possible layer and appears once in the normalized fact set.

Therefore `subgraph2(Root)` contains:

```text
all layer-1 facts
+
all layer-2 facts not already present in layer 1
```

This is the precise meaning of “include subgraph1(root), then expand its neighboring nodes without repeating subgraph1(root).”

## 4. Normalized graph slice

Conceptual Prolog terms:

```prolog
slice_node(NodeId, MinimumDistance).
slice_fact(FactId, Layer, Subject, Predicate, Object).
```

Properties:

- each `NodeId` occurs once;
- each `FactId` occurs once;
- `MinimumDistance` is the shortest resource-link distance from the root;
- a node can have several path occurrences despite one normalized node record;
- labels are resolved by language rules and are not counted as traversal edges.

## 5. Occurrences preserve path meaning

Conceptual term:

```prolog
occurrence(
    OccurrenceId,
    NodeId,
    Depth,
    ParentOccurrenceId,
    ViaFactId,
    Direction,
    State
).
```

`OccurrenceId` identifies a path position, not a graph node. It is deterministic from the root and ordered path of `(FactId, Direction)` pairs.

States:

```text
expanded
boundary
cycle_reference
limited
```

The same node may therefore have several occurrences:

```text
root person
  -- studied_at --> ISI occurrence A
  -- worked_at  --> ISI occurrence B
```

Both occurrences refer to one normalized ISI node.

## 6. Facts exposed by an occurrence

```prolog
occurrence_fact(OccurrenceId, FactId).
```

An occurrence at depth `D` may expose facts assigned to layer `D + 1`.

Facts from earlier layers are not emitted again under a child occurrence. This avoids repeating the root's `subgraph1` inside every child expansion.

The same newly exposed fact may be referenced by several occurrences at the same depth when those paths genuinely converge. The normalized `slice_fact` remains unique; only presentation references repeat.

## 7. Cycle handling

Cycles are checked per path, not globally.

When following an edge would reach a node already present in the current occurrence path:

- create a `cycle_reference` occurrence;
- preserve the edge and target node;
- do not expand that occurrence further.

This preserves evidence of the cycle without infinite recursion.

Global limits are also mandatory:

```text
maxDepth
maxNodes
maxFacts
maxOccurrences
maxResultsPerPredicate
```

A limit produces `limited` state and diagnostics rather than silent truncation.

## 8. Example

Base facts:

```prolog
fact(f_study, person_1, studied_at, iri(isi)).
fact(f_work,  person_1, worked_at,  iri(isi)).
fact(f_part,  isi,       part_of,    iri(sbras)).
fact(f_name,  isi,       name,       literal('ИСИ СО РАН', lang(ru))).
```

`subgraph1(person_1)`:

```text
unique nodes:
  person_1 depth 0
  isi      depth 1

unique facts, layer 1:
  f_study
  f_work

occurrences:
  isi via f_study
  isi via f_work
```

The label of `isi` is resolved as support metadata and does not increase distance.

`subgraph2(person_1)` additionally contains layer 2:

```text
f_part
f_name
sbras depth 2
```

The root facts `f_study` and `f_work` are not repeated inside either ISI child expansion. Both ISI occurrences may reference the same layer-2 facts when the view intentionally renders both semantic paths.

## 9. Serialization contract

```json
{
  "root": "person_1",
  "maxDepth": 2,
  "direction": "both",
  "nodes": [
    {
      "id": "person_1",
      "minimumDistance": 0
    },
    {
      "id": "isi",
      "minimumDistance": 1,
      "label": "ИСИ СО РАН"
    },
    {
      "id": "sbras",
      "minimumDistance": 2
    }
  ],
  "facts": [
    {
      "factId": "f_study",
      "layer": 1
    },
    {
      "factId": "f_work",
      "layer": 1
    },
    {
      "factId": "f_part",
      "layer": 2
    }
  ],
  "occurrences": [
    {
      "occurrenceId": "o_study",
      "nodeId": "isi",
      "depth": 1,
      "parentOccurrenceId": "root",
      "viaFactId": "f_study",
      "direction": "outgoing",
      "state": "expanded"
    },
    {
      "occurrenceId": "o_work",
      "nodeId": "isi",
      "depth": 1,
      "parentOccurrenceId": "root",
      "viaFactId": "f_work",
      "direction": "outgoing",
      "state": "expanded"
    }
  ],
  "occurrenceFacts": [
    {
      "occurrenceId": "o_study",
      "factIds": ["f_part"]
    },
    {
      "occurrenceId": "o_work",
      "factIds": ["f_part"]
    }
  ],
  "diagnostics": []
}
```

## 10. Rendering policy

The data contract permits repeated occurrences. A view profile decides whether to:

- render every semantic occurrence;
- merge occurrences of one node and list relation paths;
- render one primary occurrence with aliases;
- show normalized graph, tree, table, or timeline components.

Traversal must not make this UI decision.

Generic pages use a conservative default:

- group direct root facts by predicate;
- show the same target under each distinct root predicate;
- merge repeated child expansions when they would display identical layer-2 facts;
- expose all paths in technical details.

## 11. Verification cases

1. One direct outgoing link.
2. One direct incoming link.
3. One literal property: included as a fact, no new node.
4. Two different predicates to the same node: one node, two occurrences.
5. Two paths converge at depth 2: one normalized node, multiple occurrences.
6. Self-loop: one cycle reference, no recursion.
7. Two-node cycle: preserved edge, bounded expansion.
8. A fact incident to two frontier nodes: one normalized fact.
9. Layer 2 excludes every layer-1 fact.
10. Outgoing, incoming, and both modes retain original edge direction.
11. Limits produce explicit diagnostics.
12. Serialization order is deterministic after sorting by layer, node ID, fact ID, and occurrence path.

## Rejected alternatives

### Unique nodes and facts only

Rejected because it cannot explain why the same node is relevant through different relations.

### Occurrence tree only

Rejected because it duplicates graph data, complicates editing and provenance, and grows rapidly on converging paths.

### Global visited-node suppression

Rejected because the first path would erase later meaningful paths to the same node.

### Expand cycles until max depth

Rejected because repeated cycle copies add no new information and inflate LLM context and UI output.

## Consequences

- Prolog queries and editing use normalized `FactId` values.
- React views may preserve semantic repetition without duplicating data records.
- `subgraph1` and `subgraph2` become stable aliases over one generic traversal engine.
- Builder and Search can choose presentation policies without redefining graph semantics.
- The result is larger than a plain graph slice but remains bounded and serializable.