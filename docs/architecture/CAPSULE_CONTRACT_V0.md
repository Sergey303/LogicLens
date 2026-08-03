# LogicLens Capsule Contract v0

Status: proposed executable vertical slice  
Contract version: `0.1`

## Purpose

A capsule is a versioned, source-grounded, reproducible package of knowledge for one bounded topic. It contains domain data and rules but no universal runtime code and no learner state.

The contract separates:

- original or linked sources;
- prepared assertions and concepts;
- executable domain rules;
- learning material;
- tests and expected frames;
- a deterministic compiled package.

LogicLens owns the contract, compiler, validation and runtime. A domain repository owns capsule content.

## Capsule versus module

A **capsule** answers: “What verified knowledge, evidence, rules and tests are available for this topic?”

A **learning module** answers: “In what order and through which activities should a learner acquire and demonstrate that knowledge?”

One module may use several capsules. One capsule may be reused by several modules and role tracks.

## Required authoring layout

```text
<capsule>/
  capsule.json
  sources/
    manifest.json
  prepared/
    *.json
    *.jsonl
  rules/
    *.pl
    *.json
  learning/
    *.md
    *.json
    *.jsonl
  tests/
    *.json
    *.jsonl
```

Only files declared by `capsule.json` enter a compiled package. Undeclared files are ignored by compilation and should be reported by stricter future validators.

## Trust boundary

A capsule is untrusted authoring input. It may not:

- execute processes or network calls through Prolog;
- select an active LogicLens epoch;
- write outside its compilation output;
- invent missing provenance;
- treat missing support as opposition;
- treat two evidence records as independent without a dependency group.

Compilation performs:

1. JSON Schema validation;
2. safe relative-path validation;
3. source-manifest and provenance validation;
4. JSONL validation;
5. static Prolog safety checks;
6. canonical JSON/JSONL serialization;
7. generation of canonical Prolog assertions;
8. per-file hashing;
9. deterministic package hashing;
10. lock creation.

## Domain data layers

### Sources

`sources/manifest.json` records source identity, locator, licence status and snapshot policy. A locator may be an external URL or a repository path. Link-only sources remain references; the compiler does not silently download them.

### Prepared assertions

Each assertion has:

- a stable `assertionId`;
- a typed target predicate and arguments;
- explicit `support` or `oppose` stance;
- one or more source references;
- a dependency group;
- a generalisability level.

Absence is never compiled as negative evidence.

### Rules

Prolog rule files contain domain derivations, applicability checks, conflict rules and decisions. The first contract permits declarative Prolog only and rejects obvious process, filesystem, network and mutation primitives.

### Learning material

Learning files contain overviews, questions, misconceptions, scenario fragments and domain additions to generic LogicLens prompts.

### Tests

Tests must include positive and negative or unknown cases. A future validated status will require executable SWI-Prolog tests; v0 already packages test data deterministically.

## Compiled package

`python tools/capsule.py compile` produces:

```text
<output>/
  capsule-package.json
  capsule.lock.json
  files/
    capsule/...
    world/semantic/...
    generated/assertions.pl
```

`capsule-package.json` lists every canonical file and SHA-256 digest. `capsule.lock.json` binds the package to:

- world and capsule identities;
- capsule version;
- source-manifest hash;
- prepared-data hash;
- semantic-model hash;
- rules hash;
- package hash.

The package contains no timestamps, machine paths or provider secrets.

## Weak-model boundary

A weak model should not edit compiled facts or perform epistemic arithmetic. It receives a typed request or a verified frame and may:

- choose an allowed query;
- ask for missing mandatory input;
- request an optional evidence tail;
- render a verified result;
- play a constrained stakeholder role.

Final `pass/fail` remains a deterministic or separately reviewed evaluation result.
