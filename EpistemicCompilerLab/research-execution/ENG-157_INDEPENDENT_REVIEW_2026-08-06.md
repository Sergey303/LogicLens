# ENG-157 / WP-005 — Independent Mutation and Dependency Review

Date: 2026-08-06  
Decision: **REVISE**  
Reviewer role: Mutation and Dependency Auditor  
Gate impact: `GATE-001` and downstream `WP-105` remain blocked.

## 1. Scope reviewed

- Linear `ENG-157` and producer handoff;
- `oracle/SEMANTIC_SPEC.md`;
- `oracle/INDEPENDENCE_BOUNDARY.md`;
- `oracle/MUTATION_MATRIX.yaml`;
- `oracle/DEPENDENCY_AUDIT_PLAN.md`;
- `handoffs/WP-005.json`;
- normative oracle/scorer and source/case protocols;
- `scripts/validate_oracle_boundary.py`.

## 2. Confirmed strengths

- Independence is defined as physical and behavioral separation, not a package-name claim.
- Shared executable semantic helpers and production predicates are prohibited.
- Clean-room packet, frozen lock, no network, empty caches, dynamic traces and output allowlists are required.
- Circularity canaries cover production code, generated frames, prompts, model outputs, metrics and sealed paths.
- Ten injected forbidden-behavior negative controls are required together with positive controls.
- The mutation matrix covers status, explicit negation, query, scope/version, clarification, evidence, provenance, proof, policy, frame, rendering, gold governance and infrastructure.
- Every critical survivor and every unexplained A/B disagreement blocks freeze.
- Gold and acceptable alternatives are intended to freeze before model outputs.
- The producer correctly states that WP-005 designs independence but does not prove a future implementation independent.

## 3. Blocking findings

### B1 — Oracle and scorer are not separated from gold visibility

The boundary allows Path B to receive “source-bound annotated case inputs and adjudicated gold records.” It does not specify which gold fields are hidden from the reference oracle computation.

If B can read adjudicated expected status, action, conclusion, evidence roots or frame fields, it can reproduce gold without independently executing the semantics. That would pass A/B agreement while providing no independent implementation evidence.

Required correction: define at least three explicit components and manifests:

1. **B-oracle input packet:** source assertions, independently adjudicated interpretation/query where appropriate, schemas, type registry and declarative policy specification — no expected status/action/frame/proof values;
2. **Gold registry:** independently annotated/adjudicated expected query alternatives and expected semantic outcomes, inaccessible to B-oracle during computation;
3. **B-scorer:** receives frozen oracle/gold expectations and raw student response only after both are hashed.

Specify separate gold-query and natural-question tracks. In the gold-query track the query may be shared; in the extracted-query track student interpretation/query is scored against pre-model adjudicated alternatives, but B-oracle still must not read the expected final frame while computing it.

### B2 — The semantic specification is not yet independently implementable

The current prose gives the central four-state truth table and broad invariants, but leaves implementation-critical semantics underspecified:

- proposition canonicalization and identifier equality;
- type coercion and normalization;
- scope/version/effective-time compatibility;
- rule ordering and duplicate-rule semantics;
- evidence-root minimality versus completeness;
- proof graph canonical form and deterministic ordering;
- policy table identifiers and exact mappings;
- invalid-query, clarification and runtime-error outcome contracts;
- warning obligations;
- exact acceptable-alternative normal form and equivalence relation.

Two honest independent implementers can disagree without either violating the prose.

Required correction:

- add machine-readable declarative policy tables and registries;
- define canonicalization algorithms in implementation-independent pseudocode;
- provide positive and negative conformance vectors for every invariant;
- mark unresolved semantics as Blockers rather than letting A/B convergence define them post hoc;
- ensure future WP-101 owns final semantic versioning and WP-005 binds to its reviewed hashes.

### B3 — Post-model acceptable-alternative loophole

`SEMANTIC_SPEC.md` permits an alternative after model runs when an “outcome-blind bug review proves equivalence.” Once model outputs exist, adding an acceptable alternative creates an avoidable researcher-degree-of-freedom even if the reviewer is nominally blinded.

Required correction:

- prohibit addition of semantic alternatives after the first model output is generated;
- allow only scorer implementation bug fixes that do not change the frozen expected semantic set;
- if a true gold ambiguity is discovered after outputs exist, version the affected benchmark and invalidate its confirmatory status rather than expanding acceptance in place.

### B4 — Shared annotation fields can erase layer independence

The allowed shared packet does not distinguish raw source assertions from adjudicated interpretation/query fields. Sharing a complete gold interpretation/query with both A and B is valid for a formal-execution-only track, but cannot validate source/question interpretation or query formation independence.

Required correction:

Define separate evaluation paths and claims:

- source-bound gold query → independent A/B execution;
- natural question → student extraction/query scoring against frozen adjudicated alternatives;
- production extraction/query → production frame;
- oracle frame → renderer ceiling.

Never report one track as evidence for another layer.

### B5 — Mutation adequacy is counted, not semantically mapped

The 39-mutation matrix is broad, but the package does not provide a coverage map from every publication-critical semantic invariant and score field to:

- at least one positive vector;
- at least one invalid/negative vector;
- at least one mutation;
- expected A result;
- expected B result;
- expected field-level scorer outcome.

Required correction: add a machine-readable invariant-to-test coverage matrix. Mutation count alone is not evidence of semantic completeness.

### B6 — Human audit sampling is not specified quantitatively

The plan says to sample every domain/status/difficulty/source/mutation family but does not define sample size, selection seed, reviewer count, disagreement recording or acceptance threshold.

Required correction: freeze a stratified human-audit sampling and adjudication protocol before Path B evaluation. Any stratum with no audited case is not covered by the human validation claim.

### B7 — Independence audit toolchain needs its own trust boundary

The plan requires similarity scanners, dependency graphing, dynamic traces and canary scanning, but does not state:

- who authors/reviews the audit tooling;
- how its rules and denylist are frozen;
- how false-negative behavior is tested beyond ten examples;
- whether audit tooling can access sealed content;
- how platform limitations in environment-variable/file/network tracing are handled.

Required correction: define an independently reviewed audit-tool manifest, hashes, privileges, negative-control coverage and known blind spots. “Where platform permits” must not silently become PASS for an unobserved channel.

### B8 — No committed semantic validator

`validate_oracle_boundary.py` is a generic artifact wrapper. It does not validate mutation IDs/coverage, forbidden/allowed surfaces, oracle-versus-scorer packets, alternative freeze, clean-room controls, STOP rules or cross-file consistency.

Required correction: commit a non-mutating validator and reviewer command that fails on B1–B8 and produces a machine-readable report.

## 4. Acceptance boundary

WP-005 may be accepted after it proves that an implementer can build B-oracle from a packet that excludes expected final semantic outcomes, while a separately frozen scorer evaluates raw student outputs against independently governed gold/reference results.

The future implementation must still undergo the complete dependency, mutation, differential and human audits. Acceptance of this design will not by itself certify implementation independence.

## 5. Decision

**REVISE.** Preserve the physical clean-room design, canaries, negative controls, mutation freeze and zero-disagreement rule. Close oracle/gold/scorer visibility, semantic completeness, track separation, post-model alternative governance, coverage mapping, human sampling, audit-tool trust and semantic validation before re-review.
