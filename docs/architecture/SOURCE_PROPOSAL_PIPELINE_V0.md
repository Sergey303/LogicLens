# Source Proposal Pipeline v0

Status: executable vertical slice  
Owner: LogicLens  
Domain content owner: capsule repositories such as `CTO-Practical-Simulation`

## Purpose

The source proposal pipeline converts one declared source into a reviewed, executable proposal without silently modifying accepted capsule knowledge.

```text
source manifest
  -> immutable text snapshot
  -> addressable fragments
  -> typed assertion proposal
  -> source-grounding review
  -> generated Prolog and tests
  -> mandatory SWI-Prolog execution gate
  -> non-active proposal package
```

A passed package is evidence that the proposal is structurally valid, source-addressable and executable. It is not evidence that the source is true, that the assertion is universally applicable, or that the proposal has been promoted into an active capsule.

## Trust boundaries

- Source acquisition is separate from semantic extraction.
- Link-only and restricted sources cannot be snapshotted.
- Network acquisition requires explicit `--allow-network`, HTTPS, a public destination address, an allow-listed textual media type and a byte limit.
- Repository sources require an explicit `repositoryPath`; a URL alone is not treated as a local file.
- A model may propose assertions but cannot accept them.
- Accepted assertions require exact addressable evidence quotes from candidate fragments.
- Inference is not accepted as a source assertion; it must become a reviewed rule.
- Agent reviews are marked `provisional`; human reviews are marked `human-reviewed`.
- Passing the execution gate never activates or merges a proposal.

## Workspace stages

### 1. Snapshot

```powershell
python tools/source_pipeline.py snapshot `
  --world-root <world> `
  --capsule <capsule-id> `
  --source <source-id> `
  --proposal-id <proposal-id> `
  --repository-root <domain-repository> `
  --output <workspace>
```

The output contains canonical source text, snapshot metadata, source-manifest hash, source content hash and a workspace hash. No retrieval timestamp or machine path enters the deterministic snapshot.

### 2. Fragment

```powershell
python tools/source_pipeline.py fragment --proposal <workspace>
```

Markdown headings become addressable sections. Oversized sections are split deterministically. Every fragment records source and snapshot identity, heading path, line range, text and text hash.

### 3. Prepare extraction

```powershell
python tools/source_pipeline.py prepare `
  --world-root <world> `
  --proposal <workspace>
```

The request includes only allow-listed predicates, typed role and concept identifiers, frozen fragments and the generic source-proposer prompt. The weak or strong model must return `assertion-proposal-v0` JSON.

### 4. Import assertion proposal

```powershell
python tools/source_pipeline.py propose `
  --world-root <world> `
  --proposal <workspace> `
  --candidate <assertions-proposal.json>
```

The importer rejects unknown predicates, wrong arity, unknown typed IDs, unknown fragments, unsafe dependency groups, duplicate assertion IDs and unsupported fields such as naked confidence values.

### 5. Source-grounding review

```powershell
python tools/source_pipeline.py review `
  --proposal <workspace> `
  --review <source-grounding-review.json>
```

There must be exactly one decision per proposed assertion. `accept` requires:

- `direct` or `paraphrase` grounding;
- at least one exact quote;
- every quote to occur in an allowed candidate fragment;
- a review note.

`inference` and `unsupported` cannot be accepted as source assertions.

### 6. SWI-Prolog gate

```powershell
python tools/source_pipeline.py gate `
  --proposal <workspace> `
  --output <proposal-package> `
  --swipl swipl
```

The gate includes accepted assertions only, generates ordinary SWI-Prolog, computes expected strict statuses and adds an open-world `unknown` test. SWI-Prolog must load the generated package and pass all generated tests. Syntax-only success is insufficient.

The resulting package contains canonical snapshots, fragments, extraction request, proposal, review, approved assertion JSONL, Prolog, tests, gate report, hashes and lock. `activation` remains `not-performed`.

### 7. Verify

```powershell
python tools/source_pipeline.py verify `
  --package <proposal-package> `
  --swipl swipl
```

Verification checks the package and lock hashes, exact file set, every file hash, review hash and optionally re-executes the SWI-Prolog tests.

## Promotion boundary

v0 deliberately has no automatic promotion command. A later contract must compare accepted capsule assertions with the gated proposal, preserve provenance and dependency groups, run the full capsule regression suite and require an explicit promotion decision.

## Weak-model contract

The proposer must:

- use only supplied fragments;
- preserve source scope;
- cite fragment IDs;
- abstain when unsupported;
- avoid probabilities and confidence values;
- avoid converting recommendations or course goals into world facts;
- avoid treating absence as opposition.

The model produces a proposal, never accepted knowledge.
