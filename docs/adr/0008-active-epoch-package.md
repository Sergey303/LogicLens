# ADR-0008: Portable active epoch package

- Status: Proposed
- Linear: ENG-40
- Depends on: ADR-0005, ADR-0006, ADR-0007
- Scope: assembly and verification of the active epoch-000 runtime package

## Context

The zero epoch now has separately verified layers:

- deterministic canonical facts and origins;
- deterministic ontology labels;
- reviewed label, generic-view, traversal, and CLI rules;
- a closed JSON process contract.

Those layers are still assembled ad hoc in CI. A directory copied from the repository is not yet a defined active epoch because it can contain source inputs, stale generated files, incomplete manifests, and files whose relation to the accepted contracts is unclear.

## Decision

### 1. One command builds the package

The supported command is:

```bash
python tools/build_active_epoch.py \
  --repository-root . \
  --output artifacts/epoch-000 \
  --engine-commit <source-commit>
```

The output directory must be absent or empty. The builder refuses to write into the reviewed source directory `epochs/epoch-000`.

The builder invokes the existing data and ontology compilers and then assembles their outputs with reviewed runtime files. It does not implement a second FOG importer, ontology parser, or traversal engine.

### 2. Package contents are runtime-complete and source-free

The package contains:

```text
manifest.json
entry.pl
contracts/prolog-cli-v0.schema.json
data/
  epoch_data.pl
  facts.generated.pl
  origins.generated.pl
ontology/
  ontology_data.pl
  ontology.generated.pl
rules/
  cli_runtime.pl
  generic_view.pl
  label_rules.pl
  subgraph.pl
  traversal_policy.pl
  view_policy.pl
metadata/
  data.manifest.json
  ontology.manifest.json
smoke/
  health.request.json
  entity-view.request.json
  subgraph.request.json
```

It does not contain archival FOG, source XML, build directories, test archives, temporary paths, or .NET binaries.

The package needs SWI-Prolog at runtime but does not need .NET, the repository checkout, or original source inputs.

### 3. The active manifest is the package authority

The top-level manifest pins:

- epoch and base revision;
- source/engine commit;
- data and ontology compiler commits;
- UI, CLI, fact, data, ontology-label, and OccurrenceId contract versions;
- `dataHash` and `ontologyHash` from the specialized generators;
- `rulesHash` over the reviewed runtime Prolog files;
- SHA-256 for every package file except the top-level manifest;
- `packageHash` over every package file except the top-level manifest.

Paths are sorted with ordinal semantics. Aggregate hashes use a versioned domain prefix and length-prefixed UTF-8 paths and raw file bytes.

### 4. The manifest does not hash itself

`manifest.json` is deliberately absent from its own `files` map and from `packageHash`.

`engineCommit`, `dataCompilerCommit`, and `ontologyCompilerCommit` describe the source revision used to generate the package. A later commit or release may store the package without creating an impossible self-reference.

### 5. Verification is portable, not repository-relative

CI builds the package twice from the same source revision and requires byte-identical directory trees.

The verifier then:

1. recomputes every per-file hash;
2. recomputes `rulesHash` and `packageHash`;
3. rejects FOG, XML, `bin`, `obj`, and symlinks;
4. copies the package to a new temporary directory;
5. runs `health`, `entity-view`, and `subgraph` through `entry.pl` from that copied directory.

The final smoke stage does not read the repository, invoke a compiler, or access source archives.

## Rejected alternatives

### Copy `epochs/epoch-000` directly

Rejected because the source directory mixes reviewed loaders/rules, committed fixture data, tests, and a partial stage manifest. Direct copying does not prove that generated ontology and data belong to the same active package.

### Put source XML and FOG into the package

Rejected because the active epoch is the imported logical model. Carrying archival inputs would blur the one-time import boundary and make runtime reproducibility depend on import tools.

### Include `manifest.json` in its own hash

Rejected because it creates an impossible fixed-point/self-reference requirement.

### Add another combined importer

Rejected because it would duplicate already verified data and ontology semantics. The active builder orchestrates the existing compilers and verifies their manifests instead.

## Consequences

- epoch-000 becomes a copyable runtime unit rather than a repository layout convention;
- all stable runtime inputs are covered by one manifest;
- data, ontology, and rule changes become observable through separate and aggregate hashes;
- deployment can consume a CI artifact without .NET or archival source data;
- later epoch activation can preserve the same package boundary while changing the internal generation pipeline.
