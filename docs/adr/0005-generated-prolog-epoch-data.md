# ADR-0005: Generated Prolog epoch data

- Status: Proposed
- Linear: ENG-36
- Depends on: ADR-0001
- Scope: generated base-data package of epoch 000 and later epochs

## Context

LogicLens imports archival FOG once and then treats the canonical graph as the active data model. SWI-Prolog must receive that graph in a deterministic, inspectable form.

Two boundaries must remain clear:

1. parsing FOG is a C# import responsibility;
2. querying and deriving views from canonical facts is a Prolog responsibility.

SWI-Prolog therefore does not parse FOG in the zero epoch. C# generates Prolog data files from the already verified canonical graph.

## Decision

### 1. C# generates Prolog data files

```text
FOG archives
  -> FogSubsetImporter
  -> CanonicalGraph
  -> PrologEpochWriter
  -> generated epoch data
```

Generated files are build artifacts with committed golden copies for the zero-epoch fixture. They are never edited manually.

### 2. Identifiers are atoms; lexical text is strings

Canonical identifiers are emitted as quoted Prolog atoms:

```prolog
'f:sha256:...'
'urn:logiclens:person:alex'
'http://fogid.net/o/name'
```

Literal lexical values and archival source text are emitted as Prolog strings:

```prolog
"Алексей Ветров"
"fixtures/zero-epoch/archive/cassette-a.fog"
"logiclens-zero-epoch-a"
```

This distinction is intentional:

- identifiers participate in predicate matching and indexing;
- arbitrary textual values must not permanently grow SWI-Prolog's global atom table;
- conversion from a string to an atom is allowed only inside a bounded rule that demonstrably requires it.

### 3. Canonical fact terms

```prolog
fact(FactId, Subject, Predicate, iri(Resource)).
fact(FactId, Subject, Predicate, literal(Lexical, plain)).
fact(FactId, Subject, Predicate, literal(Lexical, lang(Language))).
fact(FactId, Subject, Predicate, literal(Lexical, datatype(Datatype))).
```

Examples:

```prolog
fact(
    'f:sha256:54e98ac97c4d7e3c953f2cd19a84bdfa2ce5b19af180762864da3b42e5d5b69d',
    'urn:logiclens:person:alex',
    'http://fogid.net/o/name',
    literal("Алексей Ветров", lang('ru'))
).

fact(
    'f:sha256:238f6c6e82b7f18c30dfeeab73add225f27d2498473db0460cc4fbb091d3e2ab',
    'urn:logiclens:student:study',
    'http://fogid.net/o/from-date',
    literal("2010-09-01", datatype('http://www.w3.org/2001/XMLSchema#date'))
).
```

Language tags are already normalized by ADR-0001 and remain atoms. Datatype and resource identifiers are atoms.

### 4. Provenance terms

```prolog
fact_origin(FactId, OriginId).
origin(OriginId, archival(SourcePath, SourceDbId, EntityId)).
```

Example:

```prolog
origin(
    'origin:fixture-a:person-alex',
    archival(
        "fixtures/zero-epoch/archive/cassette-a.fog",
        "logiclens-zero-epoch-a",
        'urn:logiclens:person:alex'
    )
).
```

`OriginId`, `EntityId`, and `FactId` are identifiers. `SourcePath` and `SourceDbId` are source metadata strings.

### 5. File layout

```text
epochs/
  epoch-000/
    manifest.json
    data/
      epoch_data.pl
      facts.generated.pl
      origins.generated.pl
```

`facts.generated.pl` and `origins.generated.pl` contain only generated clauses and comments. They do not declare a module.

`epoch_data.pl` is handwritten and stable:

```prolog
:- module(epoch_data, [fact/4, fact_origin/2, origin/2]).
:- include('facts.generated.pl').
:- include('origins.generated.pl').
```

This keeps module ownership in a reviewed file while allowing deterministic replacement of generated clauses.

### 6. Deterministic ordering and encoding

- UTF-8 without BOM;
- LF line endings;
- one clause per logical item;
- facts sorted by `FactId` using ordinal string order;
- `fact_origin/2` sorted by `FactId`, then `OriginId`;
- `origin/2` sorted by `OriginId`;
- exactly one trailing LF;
- no timestamps in generated Prolog files.

The same canonical graph, origin set, writer version, and compiler inputs must produce byte-identical files.

### 7. Escaping

The writer never concatenates raw values into executable Prolog source.

Quoted atoms escape at least:

```text
\  -> \\
'  -> \'
LF -> \n
CR -> \r
TAB -> \t
```

Quoted strings escape at least:

```text
\  -> \\
"  -> \"
LF -> \n
CR -> \r
TAB -> \t
```

Other Unicode characters are written directly as UTF-8. Control characters outside the supported escaped set are rejected until a verified encoding is added.

Generated files must be loaded by SWI-Prolog during CI; text comparison alone is insufficient validation.

### 8. Manifest and self-reference

The epoch manifest records the compiler revision that produced the data package, not the commit that later stores the generated files.

```json
{
  "epoch": 0,
  "stage": "data-generated",
  "factContractVersion": "1",
  "factIdEncodingVersion": 1,
  "prologDataContractVersion": "1",
  "compilerCommit": "git-sha-used-to-run-the-writer",
  "factCount": 29,
  "originCount": 10,
  "files": {
    "data/facts.generated.pl": "sha256:...",
    "data/origins.generated.pl": "sha256:..."
  },
  "dataHash": "sha256:..."
}
```

This avoids an impossible manifest self-reference. A compiler commit may generate files that are committed by a later commit.

The complete active epoch manifest will add ontology and rules hashes after ENG-37/ENG-38. Until then `stage` remains `data-generated` and the package is not an active application epoch.

### 9. Verification

ENG-36 passes only when CI proves all of the following:

1. FOG fixture import still produces the expected canonical graph.
2. Generation is byte-identical across two runs.
3. Committed generated files equal a fresh generation.
4. SWI-Prolog loads `epoch_data.pl` without warnings or errors.
5. `aggregate_all(count, fact(_,_,_,_), 29)` succeeds.
6. every `fact_origin/2` references an existing fact and origin.
7. every fact has at least one origin.
8. strings containing quotes, slashes, backslashes, tabs, and newlines round-trip through SWI-Prolog tests.

## Rejected alternatives

### Parse FOG directly in Prolog

Rejected for v0 because it duplicates the verified import semantics, FactId calculation, and XML subset validation.

### Store all lexical values as atoms

Rejected because large and diverse text would permanently grow the atom table.

### Emit one monolithic generated module

Rejected because it mixes reviewed module declarations with regenerated data and makes accidental manual edits harder to detect.

### Serialize canonical data only as JSON

Rejected as the primary epoch format because the research requires inspectable and directly queryable Prolog data. JSON may remain an interchange and diagnostic representation.

## Consequences

- FOG parsing has one implementation.
- Prolog data is readable, directly queryable, and deterministic.
- arbitrary text does not become global atoms.
- later process or API boundaries can change without changing the fact terms.
- generated data remains auditable through file hashes and committed golden packages.
