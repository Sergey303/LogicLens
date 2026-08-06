# Dependency and Clean-Room Audit Plan — Path B

Status: **WP-005 producer plan; pending independent Mutation and Dependency Auditor review**

## 1. Objective

Demonstrate that validation path B can be built and executed from the written semantic specification and allowed data surfaces without importing, calling, reading, copying, or learning expected results from production path A, generated frames, prompts, teacher artifacts, model outputs, or sealed outcomes.

A different module name inside the same unrestricted checkout is not independence. PASS requires static dependency evidence, physical isolation, dynamic access evidence, canary detection, negative controls and reproducible clean-room execution.

## 2. Threat model

The audit must detect:

- direct or transitive imports of production packages;
- subprocess, FFI, RPC or Prolog calls into A;
- copied production predicates, policy functions or serializer logic;
- generated expected frames or production-derived test fixtures;
- access to prompts, teacher proposals, raw model outputs or aggregate metrics during gold construction;
- undeclared RAG/search/cache leakage;
- sealed-data access before authorization;
- network retrieval of forbidden repository content;
- hidden dependency through build scripts, environment variables, editable installs or shared caches;
- post-model modification of acceptable alternatives or gold.

## 3. Allowed clean-room packet

The build manifest may contain only hash-frozen:

- `oracle/SEMANTIC_SPEC.md`;
- publication JSON Schemas and identifier/type registries;
- policy tables represented as declarative data;
- source-bound annotated non-sealed cases and independent adjudication records;
- generic canonical JSON/UTF-8 rules;
- deterministic seeds and property generators authored from the specification;
- Path B source, tests and dedicated dependency lock;
- mutation matrix and audit tooling.

Every entry records repository-relative path, SHA-256, role, origin and whether it is executable. No glob or parent-directory mount is allowed.

## 4. Static audit

Before build, the auditor must:

1. resolve the complete import/dependency graph from Path B and its lockfile;
2. reject editable/local dependencies outside the packet;
3. scan source, generated code, bytecode, binaries and lockfiles for forbidden package names, paths, symbols and canaries;
4. compare chunks/hashes against production source and generated-frame denylist, with independently frozen similarity thresholds;
5. inspect build scripts, plugin discovery, dynamic imports, reflection, FFI, subprocess and environment-variable reads;
6. prove no production Prolog file or predicate registry is bundled;
7. verify tests derive expected values from the written spec/manual vectors rather than A outputs;
8. emit a machine-readable dependency graph and zero-forbidden-edge assertion.

A suspicious match is reviewed before execution; it is not silently ignored.

## 5. Physical isolation

Build and run B in a fresh environment where:

- only the exact packet is mounted read-only;
- production source, generated frames, prompts, model outputs, teacher artifacts, experiment logs, caches and sealed paths are absent, not merely ignored;
- network is disabled;
- package installation uses the frozen lock and local/hash-pinned artifacts only;
- HOME, temporary directories and language caches start empty;
- inputs are read-only and outputs are restricted to an explicit directory;
- no repository-level `.pth`, editable install, global module path or inherited plugin registry is available;
- environment variables are allowlisted and recorded;
- process tree, imports, file opens, DNS/socket attempts and executable loads are logged.

The run must succeed in this environment for positive control cases.

## 6. Circularity canaries

Generate unique high-entropy canaries and place different values in forbidden locations before the audit:

- production compiler source;
- production policy/serializer source;
- production Prolog predicates;
- generated-frame directory;
- production expected-output fixtures;
- student prompt and teacher proposal directories;
- model-output and aggregate-metric directories;
- sealed-path placeholder.

Scan B source, build products, stdout/stderr, access logs and output artifacts for every canary. Any hit is a hard FAIL. Canaries are audit controls, never semantic fixtures.

## 7. Dynamic audit

Run the full Path B unit/property/mutation suite while collecting:

- imported modules and resolved file paths;
- all file opens with mode and result;
- subprocess and executable invocations;
- FFI/library loads;
- network/socket/DNS attempts;
- environment-variable reads where platform tooling permits;
- output file hashes and process exit states.

Compare the trace with the allowlist. Undeclared attempted access fails even when the operating system denies it.

## 8. Required negative controls

The auditor injects each prohibited behavior into a disposable mutant of B and proves the audit catches it:

1. direct import of a production module;
2. transitive dependency on a production helper;
3. subprocess call to SWI-Prolog with a production predicate file;
4. dynamic import from an environment-supplied path;
5. read of a generated expected frame;
6. copy of a production canary/string into B source;
7. read of a model-output or metric file during gold construction;
8. network request for repository/raw content;
9. access to a sealed-path canary;
10. post-run modification of acceptable-alternative registry.

All negative controls must fail for the intended audit reason. A detector that always fails is rejected by the positive controls.

## 9. Positive controls

From a clean packet, B must:

- install/build using only the frozen lock;
- execute reference unit tests and property tests;
- kill every critical mutation in `MUTATION_MATRIX.yaml`;
- generate field-level scores for synthetic raw responses after gold freeze;
- reproduce identical outputs and hashes in a second clean environment;
- complete without forbidden access or canary hits.

## 10. A/B differential audit

On non-sealed TRAIN/DEV only:

- run A and B from the same source-bound case IDs;
- compare normalized query, status, action, conclusion class, evidence roots, provenance, proof and warnings field by field;
- preserve both outputs before resolution;
- classify every disagreement as annotation error, underspecified semantics, A defect, B defect or approved pre-model semantic alternative;
- version and rerun all affected non-sealed cases after a fix.

There is no majority vote between A and B. Any unexplained disagreement blocks freeze.

## 11. Human audit

Sample every domain, status, difficulty, source family and mutation family. Auditors work from source documents, annotation records, schemas and `SEMANTIC_SPEC.md`, without A output or student output. Record reviewer identity/session, decision, evidence locator, disagreement and adjudication.

## 12. Machine-readable report

The final audit report must record:

```text
report schema/version
candidate Path B commit and source hashes
allowed-packet manifest hash
dedicated lock hash
static dependency graph hash
forbidden symbol/path/hash/canary registry hash
sandbox/runtime/container hashes
positive and negative control results
dynamic access trace hash
mutation report hash
A/B differential report hash
human audit report hash
all findings and resolutions
PASS / REVISE / STOP decision
```

Raw traces and failed mutants are retained.

## 13. PASS gate

PASS requires all of the following:

- zero direct or transitive forbidden dependencies;
- zero forbidden file/process/network access attempts;
- zero canary hits;
- every negative control detected for the correct reason;
- positive controls and reproducibility rerun pass;
- 100% kill rate for critical mutations;
- zero unexplained A/B disagreements;
- gold and acceptable alternatives demonstrably frozen before model outputs;
- field-level scoring reproduces the composite endpoint.

## 14. STOP / redesign

STOP confirmatory work when any forbidden dependency/access remains, clean-room B cannot run without A, a critical mutation survives, model behavior influenced gold, or A/B semantic agreement cannot be reached without sharing executable implementation. Redesign the semantics or oracle boundary before benchmark freeze; do not waive independence after observing favorable results.
