# Dependency and Clean-Room Audit Plan — Path B

Status: **WP-005 producer remediation candidate; pending independent Mutation and Dependency Auditor re-review**

## 1. Objective

Demonstrate that validation Path B can be built and executed from the written semantic contract and allowed B-oracle packet without importing, calling, reading, copying or learning expected results from production Path A, outcome gold, generated frames, prompts, teacher artifacts, model outputs or sealed outcomes.

A different module name inside the same unrestricted checkout is not independence. PASS requires static dependency evidence, physical isolation, dynamic access evidence, canary detection, trusted audit tooling, negative controls and reproducible clean-room execution.

## 2. Normative companion artifacts

- `ORACLE_PACKET_CONTRACT.json` — allowed/forbidden oracle and scorer surfaces;
- `AUDIT_TOOL_TRUST_MANIFEST.json` — audit-tool roles, observation channels, positive/negative controls and blind-spot policy;
- `HUMAN_AUDIT_PROTOCOL.json` — deterministic quantitative human-audit design;
- `MUTATION_MATRIX.yaml` — semantic/independence mutation contract;
- `INVARIANT_COVERAGE_MATRIX.csv` — invariant → vectors → mutations → scorer fields.

A disagreement between prose and these frozen machine-readable contracts blocks PASS.

## 3. Threat model

The audit must detect at least:

- direct or transitive imports of production packages;
- subprocess, FFI, RPC or Prolog calls into A;
- copied production predicates, policy functions or serializer logic;
- generated expected frames or production-derived expected-output fixtures;
- direct B-oracle access to outcome-gold fields;
- access to prompts, teacher proposals, raw model outputs or aggregate metrics;
- undeclared RAG/search/cache/HOME leakage;
- sealed-data access before authorization;
- network retrieval of forbidden repository content;
- hidden dependency through build scripts, environment variables, editable installs, plugin discovery, shared caches, symlinks or FFI libraries;
- post-model modification of acceptable alternatives or gold;
- a report that incorrectly promotes gold-query execution agreement into natural-question/query-formation validation.

## 4. Allowed clean-room packet

The B-oracle build manifest may contain only exact hash-frozen entries required by `ORACLE_PACKET_CONTRACT.json`, including:

- `SEMANTIC_SPEC.md`;
- `SEMANTIC_REGISTRY.json`;
- `POLICY_TABLE.json`;
- publication schemas and identifier/type/alias registries;
- source assertions and strict rules for the authorized non-sealed case packet;
- explicit normalized query for the current gold-query/oracle-ceiling execution;
- deterministic conformance/property generators authored from the specification;
- Path B source/tests and dedicated dependency lock;
- mutation and audit tooling required for the clean-room run.

The B-oracle packet **must not contain** expected status/action/conclusion/warnings/evidence/provenance/proof/frame, student/model outputs or production frames.

Query adjudication and outcome gold are separate registries. An explicit frozen query may be supplied to a gold-query execution; outcome gold remains unavailable until B output is frozen and the B-scorer phase begins.

Every allowed entry records repository-relative path, SHA-256, role, origin and executable/non-executable status. No glob, parent-directory mount or implicit package path is allowed.

## 5. Audit-tool trust boundary

The audit tool is itself a critical artifact. Final trust acceptance requires:

- audit-tool producer distinct from Path B implementer;
- independent Dependency Auditor distinct from both;
- frozen tool source/dependency/canary/denylist/negative-control hashes;
- recorded platform/runtime and effective privileges;
- positive controls proving the detector does not merely always fail;
- every required observation channel in `AUDIT_TOOL_TRUST_MANIFEST.json` classified `observed_pass`, `observed_fail` or `not_observable`;
- a non-empty known-blind-spots report.

`not_observable` is not PASS. A required unobservable channel must be covered by a second independently frozen observer/environment or it blocks acceptance.

Audit tooling may see forbidden-path canaries/metadata only to detect access; it must not expose sealed semantic content to B, producer or scorer.

## 6. Static audit

Before build, the auditor must:

1. resolve the complete import/dependency graph from Path B and its lockfile;
2. reject editable/local dependencies outside the packet;
3. scan source, generated code, bytecode, binaries and lockfiles for forbidden package names, paths, symbols, hashes and canaries;
4. compare source/build chunks against a production/generated-frame denylist using independently frozen detection rules;
5. inspect build scripts, plugin discovery, dynamic imports, reflection, FFI, subprocess and environment-variable access;
6. prove no production Prolog file or predicate registry is bundled;
7. prove no outcome-gold registry is mounted to the B-oracle phase;
8. verify conformance tests derive expected values from the written semantic contract/manual pre-model vectors rather than A output;
9. emit a machine-readable dependency graph and zero-forbidden-edge assertion.

A suspicious match is adjudicated before execution; it is not silently ignored.

## 7. Physical isolation

Build and run B in a fresh environment where:

- only the exact allowed packet is mounted read-only;
- production source, outcome gold, generated frames, prompts, model outputs, teacher artifacts, experiment logs, caches and sealed paths are absent, not merely ignored;
- network is disabled;
- package installation uses the frozen lock and local/hash-pinned artifacts only;
- HOME, temporary directories and language caches start empty;
- inputs are read-only and outputs are restricted to an explicit directory;
- no repository-level `.pth`, editable install, global module path or inherited plugin registry is available;
- environment variables are allowlisted and recorded;
- symlinks/mounts are resolved and checked against packet boundaries;
- process tree, imports, file opens, DNS/socket attempts, dynamic-library loads and executable loads are logged.

The run must succeed for positive controls in this environment.

## 8. Circularity canaries

Generate unique high-entropy canaries and place different values in at least:

- production compiler source;
- production policy/serializer source;
- production Prolog predicates;
- generated-frame directory;
- production expected-output fixtures;
- **outcome-gold registry location available only to scorer phase**;
- student/teacher prompt directories;
- model-output and aggregate-metric directories;
- sealed-path placeholder;
- HOME/language cache;
- editable/local production package path.

Scan B source, build products, stdout/stderr, access logs and output artifacts for every canary. Any hit is a hard FAIL. Canaries are audit controls, never semantic fixtures.

## 9. Dynamic audit

Run the full Path B unit/property/conformance/mutation suite while collecting all channels required by `AUDIT_TOOL_TRUST_MANIFEST.json`, including:

- imported modules and resolved file paths;
- all file opens with mode/result;
- subprocess and executable invocations;
- FFI/dynamic library loads;
- network/socket/DNS attempts;
- environment-variable reads;
- symlink/mount resolution;
- cache/HOME/package/plugin resolution;
- stdout/stderr and output artifact hashes.

Compare the trace with the exact allowlist. Undeclared attempted access fails even if the OS denies it.

## 10. Negative and positive controls

The frozen audit-tool manifest requires 16 negative controls, including direct/transitive production imports, production Prolog subprocess, generated-frame/gold/model-output reads, network/sealed-path access, post-freeze registry write, symlink escape, HOME cache, editable package, FFI/plugin and environment-path leaks.

Every negative control must be detected for the intended reason. A detector that always fails is rejected by positive controls.

Positive controls include clean packet build, clean reference tests, allowed read-only source access, allowed output write and identical second-clean-environment reproduction.

## 11. Mutation/conformance audit

For every publication-critical invariant:

- execute its positive vector;
- execute its negative/invalid vector;
- execute every mapped critical mutation;
- record expected and actual A result, B result and field-level scorer booleans;
- preserve raw mutant and report hashes.

All critical mutations in `MUTATION_MATRIX.yaml` must be killed. No equivalent-mutant waiver may be invented after model output.

## 12. A/B differential audit

On non-sealed TRAIN/DEV only and within the declared track:

- freeze A and B outputs before resolution;
- compare normalized query where applicable, status, action, conclusion class, evidence roots, provenance, proof and warnings field by field;
- preserve both outputs and implementation hashes;
- classify every disagreement as annotation/gold error, underspecified semantics, A defect, B defect or approved pre-model alternative;
- version and rerun all affected non-sealed cases after a fix.

There is no majority vote between A and B. Any unexplained disagreement blocks freeze.

Gold-query execution agreement may validate execution/policy/frame only; it cannot be reported as query-formation accuracy.

## 13. Quantitative human audit

`HUMAN_AUDIT_PROTOCOL.json` is normative:

- sample size exactly `120` non-sealed TRAIN/DEV cases;
- deterministic seed `157005` and SHA-256 ordering;
- 30 sampled cases per semantic status;
- mandatory coverage over every observed domain, status, difficulty, source family and mutation family;
- 2 blind independent reviewers per case;
- 1 third adjudicator on disagreement;
- pre-adjudication exact-case agreement >= `0.95`;
- each mandatory stratum agreement >= `0.90`;
- zero unresolved post-adjudication disagreements;
- zero discovered semantic/scorer errors permitted for PASS.

If quotas/coverage are impossible, the protocol STOPs and is versioned before audit. Cases are not replaced because reviewers disagree. Threshold failure yields REVISE and a full new versioned 120-case audit after remediation.

## 14. Machine-readable report

The final audit report records at least:

```text
report schema/version
candidate B commit and source hashes
allowed-packet manifest hash
semantic/policy/packet-contract hashes
dedicated dependency lock hash
audit-tool source/dependency/trust-manifest hashes
static dependency graph hash
forbidden symbol/path/hash/canary registry hash
platform/runtime/container hashes
per-channel observability status
known-blind-spots report hash
positive/negative control results
dynamic access trace hash
conformance/mutation report hash
A/B differential report hash
human audit report hash
all findings and resolutions
PASS / REVISE / STOP decision
```

Raw traces, failed mutants, reviewer disagreements and blind-spot records are retained.

## 15. PASS gate

PASS requires all of:

- zero direct/transitive forbidden dependencies;
- zero forbidden oracle access to outcome gold/model/production frames;
- zero forbidden file/process/network/FFI/cache/plugin/symlink access attempts;
- zero canary hits;
- every required observation channel observable or covered by an accepted second observer;
- every negative control detected for the correct reason;
- all positive controls and second-environment reproduction pass;
- 100% critical mutation kill rate;
- complete invariant coverage matrix;
- zero unexplained A/B disagreements;
- gold/alternatives demonstrably frozen pre-model;
- human-audit thresholds satisfied;
- field-level scoring reproduces the composite endpoint.

## 16. STOP / redesign

STOP confirmatory work when any forbidden dependency/access remains, B cannot run without A, outcome gold leaks into B-oracle, a critical mutation survives, a required audit channel is unobservable and unmitigated, model behavior influenced gold, human-audit acceptance fails, or A/B semantic agreement cannot be reached without sharing executable implementation. Redesign before benchmark freeze; do not waive independence after favorable results are observed.
