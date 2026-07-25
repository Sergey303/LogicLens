# Zero-epoch fixture

This fixture is the smallest archival input used to verify the LogicLens zero epoch.

It is intentionally separate from the large historical files in `data/`:

- the historical files remain untouched archival inputs;
- the fixture is small enough for deterministic golden tests;
- the fixture uses real types and predicates from `data/Ontology.xml`;
- only the `urn:logiclens:test:` namespace is synthetic and exists to verify unknown-predicate fallback, technical-field handling, repeated paths, and cycles.

## Files

```text
archive/cassette-a.fog
archive/cassette-b.fog
expected/origins.json
expected/normalized-facts.json
expected/fact-id-v1-golden.json
expected/view-expectations.json
```

`expected/origins.json` fixes stable fixture-only origin identifiers. Production origin identity may later use another deterministic scheme, but ENG-29 must not depend on an undocumented naming guess.

## Covered cases

- person, organization, participation, education, document and authority entities;
- Russian, English, untagged and datatype literals;
- Russian-first language selection;
- English and untagged fallback;
- unknown predicate rendering;
- one configured technical predicate;
- incoming and outgoing links;
- one canonical fact with two archival origins;
- two semantic routes from one person to the same organization;
- a two-node cycle;
- depth-1 and depth-2 traversal;
- raw source inspection.

## Main entities

```text
urn:logiclens:person:alex
urn:logiclens:org:iis
urn:logiclens:org:lab
urn:logiclens:org:archive
urn:logiclens:participation:work
urn:logiclens:student:study
urn:logiclens:document:paper
urn:logiclens:authority:paper-author
```

## Important expectations

For `urn:logiclens:person:alex` with traversal direction `both`:

- participation, student and authority records are distance 1 through incoming facts;
- IIS is distance 2 through both `in-org` and `learning-org`;
- the two IIS occurrences remain distinct while the normalized IIS node and facts remain unique;
- the paper is distance 2 through the authority record.

For `urn:logiclens:org:lab`:

- `urn:logiclens:org:archive` is distance 1;
- expanding it exposes a relation back to the root;
- this produces a cycle reference rather than recursive expansion.

## Verified consistency

The fixture is designed so a standard XML parser and the RDF/XML subset mapping produce exactly 29 unique canonical triples. The expected graph and FactId v1 vectors were generated independently from the XML and compared before review.

## Archival immutability

Tests and tools may read files under `archive/`, but must never rewrite them. Generated Prolog, normalized JSON and runtime state belong outside this directory.
