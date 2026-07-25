# LogicLens architecture v0

Status: working architecture under verification.

## 1. Purpose

LogicLens studies whether graph data can be represented, transformed, queried, edited, and rendered through an explicit Prolog layer, while LLM resolvers create verified reusable rules or temporary question-specific views.

The system does not modify archival FOG files after the initial import.

## 2. Primary invariants

1. FOG files and cassettes are archival inputs only.
2. The active editable data model is the LogicLens Prolog graph.
3. React knows the UI component ontology, not the domain ontology.
4. Every unknown domain predicate still has a generic fallback representation.
5. Base graph editing uses only atomic `AddFact` and `DeleteFact` operations.
6. Derived results are read-only unless an explicit inverse edit rule is introduced later.
7. Builder never modifies the active epoch directly.
8. Search artifacts are isolated from active epoch rules and data.
9. Every stable page is reproducible from the epoch, runtime revision, and UI contract version.
10. Every generated rule accepted into an epoch passes deterministic validation.

## 3. System layers

```text
archival FOG/cassettes
        |
        | one-time import
        v
epoch snapshot: canonical Prolog facts + origins
        |
        + runtime delta journal
        v
active base graph in SWI-Prolog
        |
        + static rules
        + type profiles
        + generated derived predicates
        v
view predicates / UI Document
        v
universal React renderer
```

Two LLM-assisted flows operate beside the stable runtime:

```text
Builder: current epoch + structural delta -> candidate next epoch
Search: Russian question + current epoch -> isolated temporary query and view
```

## 4. Epoch package

An epoch is a reproducible package, not merely a timestamp.

Suggested layout:

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

The manifest must pin at least:

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

### Epoch and runtime revision are different

- **Epoch** changes when data is compacted and/or stable rules and profiles change.
- **Revision** changes after every state-changing runtime `ApplyDelta`.

A stable page is identified by:

```text
EpochId + Revision + ViewProfile + EntityOrQuery
```

## 5. Canonical base graph

The canonical model is defined in [ADR-0001](adr/0001-canonical-fact-model.md).

```prolog
fact(FactId, Subject, Predicate, Object).
fact_origin(FactId, OriginId).
origin(OriginId, Origin).
```

The graph is a set of normalized triples. Repeated archival occurrences attach multiple origins to one fact.

`FactId` is deterministic from a versioned, length-prefixed UTF-8 encoding of the canonical triple. It does not depend on Prolog formatting or file order.

## 6. Runtime persistence

The in-memory SWI-Prolog graph is not the sole durable copy.

Runtime state consists of:

1. the selected epoch snapshot;
2. an ordered append-only state-change journal;
3. accepted-command receipts keyed by `CommandId`;
4. the current revision.

On startup:

```text
load epoch snapshot
-> replay validated journal entries in revision order
-> verify resulting revision and graph hash
-> expose API
```

After a state-changing delta:

```text
validate CommandId and expected revision
-> prepare next graph state
-> durably write change and command receipt
-> publish graph mutation
-> increment revision once
-> rebuild affected views
```

A command containing only no-op operations leaves the revision and state-change journal unchanged but returns a stable receipt for retries.

The exact crash-safe write sequence remains part of ENG-24.

## 7. Static rule layers

### 7.1 Trusted UI Document v0

The minimal trusted contract is defined in [ADR-0003](adr/0003-minimal-ui-document.md) and [its JSON Schema](../contracts/ui-document-v0.schema.json).

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

Property value kinds:

```text
TextValue
ResourceLinkValue
```

Minimal generic rules:

- IRI object -> `ResourceLinkValue`;
- literal object -> `TextValue`;
- one predicate with several values -> one `Property` with an array of values;
- unknown predicate -> `Property` using ontology label or compact identifier;
- unknown entity type -> generic property page;
- technical facts -> collapsed technical section, never silent removal;
- generated Prolog fragment -> `RawProlog`.

`Table`, `Tree`, `Graph`, `Timeline`, `Image`, arbitrary Markdown, HTML, CSS, and JavaScript are not trusted v0 components. They may enter a later UI contract after an experiment demonstrates a stable need and safe fallback.

### 7.2 Language selection

Default order for Russian UI:

```text
Russian -> English -> untagged -> first available
```

The same rule applies to:

- resource labels;
- type labels;
- predicate labels;
- descriptions;
- generated section labels when multilingual alternatives exist.

The UI must provide access to alternate language values rather than silently discarding them.

### 7.3 Graph traversal

Traversal semantics are defined in [ADR-0002](adr/0002-layered-subgraphs-and-occurrences.md).

```prolog
subgraph1(Entity, Options, Result).
subgraph2(Entity, Options, Result).
```

Both aliases use one bounded generic engine. A result contains:

- a normalized set of unique nodes and facts;
- fact layers that exclude facts already emitted by earlier layers;
- path-sensitive node occurrences;
- links from occurrences to newly exposed facts;
- explicit cycle and limit diagnostics.

The same target may have several occurrences through different facts, such as `studied_at` and `worked_at`, while underlying nodes and facts remain unique.

Traversal supports `outgoing`, `incoming`, and `both`; the generic page defaults to `both` while preserving original edge direction.

### 7.4 Type profiles

Type-specific predicates must be thin declarations over generic engines, not copies of traversal logic.

```prolog
type_profile('fog:person', portrait).
profile_depth(portrait, 1).
```

Generated aliases may exist for LLM readability, but duplicated implementations are prohibited.

## 8. View construction

A view is generated in layers:

```text
base facts
-> language and label rules
-> generic grouping
-> selected subgraph
-> type profile
-> derived predicates
-> visibility and ordering rules
-> validated UI Document
```

Each UI value that displays base data carries `FactId`. Derived values carry rule identity and evidence `FactId` values.

React only renders the validated UI Document and sends declared edit operations back to the server.

## 9. Editing

The editor is the same page with edit actions enabled for base facts.

Allowed primitive operations:

```text
AddFact(Subject, Predicate, Object)
DeleteFact(FactId)
```

Examples:

```text
change literal   = DeleteFact(old) + AddFact(new literal)
change link      = DeleteFact(old) + AddFact(new IRI)
change predicate = DeleteFact(old) + AddFact(new predicate)
```

These operations are enclosed in one atomic command:

```text
ApplyDelta(CommandId, ExpectedRevision, AddFact[], DeleteFact[])
```

The first version does not validate a predicate against the subject type and does not edit ontology labels, domain/range, cardinality, or constraints. It performs only technical validation required to preserve a readable Prolog state.

Visibility is not deletion of data. Visibility rules are UI facts/rules stored separately from the base graph and may themselves later use the same Add/Delete machinery with a different target namespace.

## 10. Builder resolver

Builder creates `epoch-(i+1)` candidates from:

- epoch `i`;
- accumulated structural delta;
- samples and statistics;
- allowed Prolog modules and CLI tools;
- the fixed UI component contract;
- a task prompt.

Supported providers initially:

- `qwen2.5-coder:7b` through Ollama;
- Codex through its configured authorization.

Builder may propose:

- complex derived predicates;
- type profiles;
- visibility and ordering rules;
- bindings to UI components;
- tests and golden views.

Builder may not:

- write into the active epoch;
- mutate active data;
- execute unrestricted shell commands;
- introduce unknown UI components;
- activate its own candidate.

Candidate validation must include:

1. Prolog syntax and module loading;
2. allowed imports and predicates;
3. query timeout and bounded result size;
4. tests for every generated rule;
5. UI Document schema validation;
6. evidence availability for derived results;
7. comparison against generic fallback views;
8. a human-readable change report.

## 11. Search resolver

Search runs for a semantic user request, not for every low-level data fetch.

Input:

```text
Russian question
+ optional starting entities
+ current EpochId and Revision
+ allowed Prolog query tools
+ UI component contract
```

Output artifacts:

```text
query.pl
answer-data.pl
answer-view.pl
ui-document.json
run-report.json
```

The user-facing result may show:

1. the Prolog result data;
2. the Prolog view binding;
3. the rendered dynamic page.

Search v0 is read-only. Generated files execute in an isolated workspace and cannot become stable epoch rules automatically.

An experimental HTML/CSS or application-generation path may be compared with the canonical Prolog-to-UI-Document path, but arbitrary generated HTML is not the trusted default renderer.

## 12. Feedback from Search to Builder

Successful Search runs are research evidence, not direct training or automatic production changes.

The system records:

- normalized intent;
- tools and predicates used;
- generated query structure;
- result and UI validity;
- user acceptance or correction;
- repeated path patterns;
- runtime and model metadata.

Builder can later propose stable predicates and profiles for repeated successful patterns.

## 13. Failure behavior

- Unknown type or predicate -> generic fallback page.
- Builder failure -> current epoch remains active.
- Search failure -> stable epoch view plus diagnostic report.
- Generated query timeout -> terminate isolated run, no active-state change.
- Invalid UI Document -> reject generated view, use generic renderer.
- Stale edit revision -> reject entire delta and return current facts.
- Unsupported rich component -> diagnostic plus trusted v0 fallback.

## 14. Verification order

1. ADR-0001 canonical fact model.
2. ADR-0002 subgraph semantics.
3. ADR-0003 fixed UI ontology and fallback view.
4. ENG-23 zero-epoch vertical slice.
5. ENG-24 crash-safe ApplyDelta.
6. ENG-25 restricted Prolog CLI.
7. ENG-26 Builder comparison.
8. ENG-27 Search vertical slice.
9. ENG-28 benchmark protocol.

This order deliberately validates deterministic foundations before introducing LLM-generated runtime behavior.