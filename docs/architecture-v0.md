# LogicLens architecture v0

Status: accepted baseline under continuous verification.

Detailed decisions live in ADRs. This document defines how they fit together and the boundaries of the first research system.

## 1. Purpose

LogicLens studies whether graph data can be imported once into an explicit Prolog model and then queried, transformed, edited, and rendered through reproducible logical rules.

LLM resolvers do not replace the logical layer:

- Builder proposes verified reusable rules for a candidate next epoch;
- Search creates isolated question-specific Prolog and UI artifacts;
- stable runtime views continue to work without an LLM call.

Archive FOG files and cassettes are never modified after the initial import.

## 2. Primary invariants

1. FOG files and cassettes are immutable archival inputs.
2. The active editable model is the canonical LogicLens graph.
3. React knows the UI component ontology, not domain types.
4. Unknown domain predicates still have a generic representation.
5. Fact visibility and graph traversal eligibility are separate decisions.
6. Base editing uses only atomic `AddFact` and `DeleteFact` operations.
7. Derived results are read-only unless a future explicit inverse rule exists.
8. Builder never modifies the active epoch directly.
9. Search artifacts are isolated from active epoch rules and data.
10. Stable pages are reproducible from epoch, revision, view input, and UI contract version.
11. Generated rules enter an epoch only after deterministic validation.

## 3. System layers

```text
archival FOG/cassettes
        |
        | one-time import
        v
epoch snapshot: canonical facts + origins
        |
        + runtime delta journal
        v
active base graph in SWI-Prolog
        |
        + static rules
        + traversal policy
        + type profiles
        + verified derived predicates
        v
view predicates
        v
validated UI Document
        v
universal React renderer
```

LLM-assisted flows operate beside the stable runtime:

```text
Builder: current epoch + structural delta -> candidate next epoch
Search: Russian question + current epoch -> isolated temporary query and view
```

## 4. Epoch and revision

An epoch is a reproducible package, not a timestamp.

```text
epochs/
  epoch-000/
    manifest.json
    data/
      facts.pl
      origins.pl
    ontology/
      types.pl
      predicates.pl
      labels.pl
    rules/
      00-base/
      10-graph/
      20-type-profiles/
      30-generated/
    views/
      bindings.pl
      visibility.pl
    tests/
      unit/
      golden/
```

The manifest pins at least:

```json
{
  "epoch": 0,
  "parentEpoch": null,
  "baseRevision": 0,
  "engineCommit": "git-sha",
  "uiContractVersion": "0.1",
  "ontologyHash": "sha256:...",
  "dataHash": "sha256:...",
  "rulesHash": "sha256:..."
}
```

- **Epoch** changes when stable data snapshots, rules, profiles, or bindings change.
- **Revision** changes after a state-changing runtime `ApplyDelta`.

A stable entity page is identified by:

```text
EpochId + Revision + ViewProfile + EntityId
```

A Search result additionally includes its isolated request/run identity.

## 5. Canonical graph

[ADR-0001](adr/0001-canonical-fact-model.md) defines:

```prolog
fact(FactId, Subject, Predicate, Object).
fact_origin(FactId, OriginId).
origin(OriginId, Origin).
```

The active graph is a set of normalized triples.

- repeated archival occurrences attach several origins to one fact;
- `FactId` is deterministic from the versioned canonical byte encoding;
- file order and Prolog/JSON formatting do not affect identity;
- derived results are not inserted as editable base facts;
- derived values expose rule identity and evidence FactIds.

## 6. Runtime persistence and editing

Runtime state consists of:

1. the selected epoch snapshot;
2. an ordered append-only state-change journal;
3. accepted-command receipts keyed by `CommandId`;
4. the current revision.

External base-data primitives:

```text
AddFact(Subject, Predicate, Object)
DeleteFact(FactId)
```

Atomic command:

```text
ApplyDelta(CommandId, ExpectedRevision, AddFact[], DeleteFact[])
```

A replacement is delete plus add in one command.

- replaying a completed command is idempotent;
- a command containing only no-ops does not change revision;
- a failed command changes neither graph, journal, receipts, nor revision;
- crash-safe write ordering is verified separately in ENG-24.

The first version does not validate predicate domain/range or cardinality and does not edit ontology labels or constraints. It performs only structural and persistence validation.

## 7. Traversal and subgraphs

[ADR-0002](adr/0002-layered-subgraphs-and-occurrences.md) defines layered normalized subgraphs and path-sensitive occurrences.

```prolog
subgraph1(Entity, Options, Result).
subgraph2(Entity, Options, Result).
```

Both aliases use one bounded generic engine. A result contains:

- unique nodes and facts;
- earliest fact layers;
- path-sensitive occurrences;
- occurrence-to-fact references;
- cycle and limit diagnostics.

The same node may have several semantic occurrences while its normalized data remains unique.

### Traversal eligibility

[ADR-0004](adr/0004-traversal-edge-eligibility.md) amends the traversal semantics.

When a node is expanded, incident facts remain visible, but only eligible IRI facts create neighboring node occurrences.

Default policy:

```text
rdf:type              -> visible, not followed
technical predicates  -> visible, not followed
provenance predicates -> visible, not followed
UI/profile predicates -> visible, not followed
ordinary known IRI relation   -> followed
ordinary unknown IRI relation -> followed
literal value                 -> visible, never a node
```

This prevents schema and implementation metadata from becoming accidental topology while preserving generic traversal of new domain relations.

A non-followed IRI object can still be rendered as a resource link and opened as a new page. Navigation is not continuation of the current subgraph expansion.

Traversal supports `outgoing`, `incoming`, and `both`; the generic page defaults to `both` and preserves original fact direction.

## 8. Labels and generic views

Default language order for Russian UI:

```text
Russian -> English -> untagged -> first available
```

The policy applies to resource, type, predicate, description, and section labels. Alternate language values remain inspectable.

Generic view construction:

```text
base facts
-> labels and language selection
-> grouping by direction and predicate
-> traversal result
-> optional type profile
-> derived predicates
-> visibility and ordering rules
-> validated UI Document
```

Unknown types and predicates use ontology labels when available and compact identifiers otherwise. Technical facts go to a collapsed technical section rather than disappearing.

## 9. Trusted UI Document v0

[ADR-0003](adr/0003-minimal-ui-document.md) and the [JSON Schema](../contracts/ui-document-v0.schema.json) define the closed trusted vocabulary.

Structural components:

```text
Page
Section
```

Data components:

```text
Property
TextBlock
RawProlog
Diagnostic
```

Value kinds:

```text
TextValue
ResourceLinkValue
```

Every base value carries the complete base fact source required for unambiguous editing. Derived values carry rule and evidence information and cannot be editable.

Not trusted in v0:

```text
Table
Tree
Graph
Timeline
Image
Map
Form
Tabs
arbitrary Markdown/HTML/CSS/JavaScript
```

Rich components require a later versioned contract and a verified fallback.

## 10. Builder

Builder creates an `epoch-(i+1)` candidate from:

- current epoch;
- structural delta, samples, and statistics;
- allowed Prolog modules and bounded CLI tools;
- the fixed UI contract;
- a task prompt.

Initial providers:

- `qwen2.5-coder:7b` through Ollama;
- Codex through configured authorization.

Builder may propose derived predicates, profiles, visibility/order rules, component bindings, tests, and golden views.

Builder may not mutate active data, write into the active epoch, execute unrestricted shell commands, introduce unknown UI components, or activate its own candidate.

Candidate validation includes syntax/module loading, allowed calls, timeout and result limits, tests, UI schema validation, evidence checks, generic-fallback comparison, and a readable change report.

## 11. Search

Search runs for a semantic user request, not for every low-level data fetch.

Input:

```text
Russian question
+ optional starting entities
+ current EpochId and Revision
+ allowed Prolog tools
+ traversal policy
+ UI contract
```

Output workspace:

```text
query.pl
answer-data.pl
answer-view.pl
ui-document.json
run-report.json
```

Search v0 is read-only. Generated artifacts execute in isolation and never become stable epoch rules automatically.

The user may inspect:

1. result Prolog data;
2. Prolog view bindings;
3. the rendered page.

Experimental HTML/CSS or application generation may be compared separately, but it is not the trusted renderer.

Successful Search runs become evidence for future Builder proposals, not automatic production changes.

## 12. Failure behavior

- unknown type or predicate -> generic fallback;
- Builder failure -> current epoch remains active;
- Search failure -> stable epoch view plus diagnostics;
- query timeout -> terminate isolated run;
- invalid UI Document -> reject and use trusted fallback;
- stale edit revision -> reject the whole delta;
- traversal limit -> explicit diagnostic, never silent truncation;
- unsupported rich component -> trusted v0 fallback.

## 13. Verification order

1. ADR-0001 canonical fact model.
2. ADR-0002 layered subgraphs and occurrences.
3. ADR-0003 trusted UI Document v0.
4. ADR-0004 traversal edge eligibility.
5. ENG-23 zero-epoch vertical slice.
6. ENG-24 crash-safe ApplyDelta.
7. ENG-25 restricted Prolog CLI.
8. ENG-26 Builder comparison.
9. ENG-27 Search vertical slice.
10. ENG-28 benchmark protocol.

The order validates deterministic foundations before introducing LLM-generated runtime behavior.
