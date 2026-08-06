# Independence Boundary — Production Path A and Validation Path B

Status: **WP-005 producer architecture; pending Mutation and Dependency Auditor review**

## 1. Paths

```text
A = production canonical JSON/DSL compiler + SWI-Prolog + production policy/frame serializer
B = clean-room standalone reference oracle and field-level scorer
```

B should use a separate implementation language/runtime or, at minimum, a separately packaged pure reference implementation with no production imports. B must implement `SEMANTIC_SPEC.md`, not imitate observed A outputs.

## 2. Only allowed shared surfaces

A and B may share read-only, hash-frozen:

- written `SEMANTIC_SPEC.md`;
- publication JSON Schemas and identifier/type registries;
- source-bound annotated case inputs and adjudicated gold records;
- declared policy tables expressed as data, not production executable code;
- deterministic test seeds and generic test vectors authored from the specification;
- common serialization standards such as UTF-8 and canonical JSON rules.

Shared artifacts require hashes and provenance. Shared executable semantic helpers are prohibited.

## 3. Forbidden to B

B must not read, import, call, copy, translate or dynamically load:

- production compiler/runtime modules;
- production Prolog predicates or compiled clauses;
- production policy functions or frame serializer;
- generated expected frames from A;
- production unit-test expected outputs if derived from A;
- student prompts, model configuration prompts or teacher proposals;
- student/model raw outputs during gold creation;
- aggregate DEV/HOLDOUT/REPLICATION metrics;
- sealed datasets before authorized execution;
- caches, RAG indexes or logs containing any forbidden artifact.

B may receive raw student responses only after gold and scorer hashes are frozen, solely for field scoring.

## 4. Clean-room roles and contexts

- Semantic-spec producer and Path A producer disclose prior roles.
- Path B implementer receives only the allowed packet.
- Dependency auditor receives B source, build manifest, filesystem trace and denylist; it need not receive sealed outcomes.
- Human gold adjudicators do not see model outputs.
- Confirmatory analyst receives frozen A/B reports only after controlled unblinding.

The same unlogged session cannot act as A producer and independent B acceptor.

## 5. Physical enforcement

Path B build/run environment must:

- mount only the explicit allowed manifest;
- omit the production source tree and generated-frame directories;
- use a separate package lock and module namespace;
- disable arbitrary network access;
- expose read-only inputs and an output-only allowlist;
- log file opens/imports/process execution;
- scan source and built artifacts for forbidden paths, symbols, hashes and canaries;
- fail closed on undeclared access.

Instruction-only separation is insufficient.

## 6. Gold lifecycle

1. Annotators produce source-bound records independently.
2. Adjudicator resolves disagreements without model output.
3. Gold/acceptable alternatives are serialized and hashed.
4. B implements/scorers against the written spec.
5. Property, mutation, invalid-input and human audits pass.
6. A/B differential runs on non-sealed TRAIN/DEV.
7. Every disagreement is resolved and versioned.
8. Gold, B and scorer freeze.
9. Only then may B score raw model outputs.

## 7. Differential agreement

Agreement is field-level, not only composite. Reports include:

- scenario/case ID;
- A and B normalized queries;
- per-field frame values;
- evidence/proof roots;
- policy result;
- disagreement layer;
- resolution classification;
- artifact hashes.

Exact agreement is required unless a predeclared semantically equivalent alternative normal form applies.

## 8. Circularity canaries

Place unique forbidden canaries in:

- production compiler source;
- generated frame directory;
- production test expected-output fixtures;
- model-output directory;
- teacher prompt directory.

Any canary in B source, build, logs or outputs is a hard independence failure.

## 9. STOP conditions

STOP confirmatory work when:

- B requires production executable code to reproduce semantics;
- forbidden dependency/access is observed;
- gold is influenced by model output;
- critical mutation survives;
- A/B disagreement remains unexplained;
- acceptable alternatives are added after seeing model behavior;
- field-level decomposition cannot reproduce the composite endpoint.
