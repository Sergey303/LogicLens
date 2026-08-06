# Proposal — Relational Data-Layer Comparator for Codex/AppForge → Qwen

Status: **design input for the next WP-004 producer session; not a frozen mode contract**  
Date: 2026-08-07  
Parent package: `WP-004 / ENG-156`  
Related implementation work: AppForge production-package generation and the earlier Qwen/Codex/static-rule comparison track.

## 1. Motivation

The flagship comparison must test a strong conventional alternative to the custom Prolog/verified-frame pipeline:

> A stronger model compiles the same source knowledge into a relational database, read-only views or stored procedures, data-loading artifacts and a typed query catalogue; a fixed-weight Qwen model is then told how to query that interface and produces the final answer.

This comparator matters because a positive M6 result is less informative if the same benefit can be obtained with a standard generated PostgreSQL service. It can falsify claims that the effect depends on Prolog, a custom epistemic compiler or the full decision-frame representation.

## 2. Scientific boundary

The scientific variable is **where executable semantics and query responsibility are placed**, not whether AppForge is used.

AppForge may generate part of the implementation, but it must not become the treatment label. The publication contract must define an implementation-neutral `Relational Knowledge Package`. A small dedicated PostgreSQL generator may be used first; AppForge may be a second implementation or scaffolding provider.

No claim may say that AppForge itself improves reasoning unless AppForge versus another generator is separately randomized and powered. That comparison is outside the flagship scope.

## 3. Relational Knowledge Package contract

For every source package, the builder produces hash-frozen artifacts:

```text
schema and migrations
canonical data loader and seed manifest
read-only tables/views/materialized views
read-only stored procedures or parameterized query endpoints
typed query catalogue with names, arguments and result schemas
source/provenance mapping for every returned row
generator manifest and versions
Qwen query guide
negative/security tests
```

The package must satisfy:

- same source assertions, versions, scopes and provenance available to the other modes;
- deterministic rebuild from source package and generator hashes;
- no student/model outputs used during generation;
- no HOLDOUT or REPLICATION outcomes visible to Codex/AppForge;
- no final natural-language answer embedded in schema names, comments, guide text or seed values;
- no write-capable student credential;
- no arbitrary network or filesystem access;
- every query result traceable to source rows and procedure/view versions;
- malformed or unauthorized calls remain failures, not silently repaired answers.

## 4. Candidate modes

The identifiers below are reserved proposals only. The next WP-004 producer must reconcile them with the final mode registry and power budget.

### M15 — Relational Query Agent

Visible to Qwen:

- user question;
- typed read-only query catalogue;
- Codex-generated frozen guide explaining how to choose an endpoint and populate arguments;
- response schema.

Execution:

1. Qwen emits a typed procedure/query call, not unrestricted SQL by default.
2. A read-only adapter validates and executes it against PostgreSQL.
3. Typed rows plus provenance are returned to Qwen.
4. Qwen renders the final answer.

This mode measures the complete conventional data-layer agent bundle: generated relational representation, teacher explanation, query selection, deterministic execution and rendering.

### M16 — Relational Result Interface

Visible to Qwen:

- user question;
- independently selected and executed relational query result;
- typed rows and provenance;
- response schema.

Qwen does not create the database query. An outcome-blind frozen query mapper or adjudicated query registry chooses the correct read-only endpoint before model execution.

This mode separates failures of Qwen query formation from the value of the relational representation and returned result.

### DEV-only guide ablation

Before confirmatory freeze, compare M15 with an otherwise identical variant that receives the query catalogue but not the Codex-generated explanatory guide.

The guide/no-guide comparison is DEV-only unless WP-006 power and WP-007 feasibility explicitly authorize it. Its purpose is to estimate the marginal value of the teacher explanation without adding another headline claim.

## 5. Mandatory contrasts

### M15 versus M16 — query-generation responsibility

Question:

> Does performance loss arise because Qwen must formulate/select the database query?

Interpretation:

- M16 much better than M15: bottleneck is query formation or tool use;
- M15 approximately equals M16: Qwen can use the typed relational interface reliably;
- both weak: relational representation/result interface is insufficient for the task.

### M16 versus M6 — relational result versus epistemic decision frame

Question:

> Does the explicit four-state decision contract add value beyond conventional typed database results?

Interpretation:

- M16 matches or exceeds M6: do not claim Prolog or the full epistemic frame is necessary; narrow to a broader executable-interface result;
- M6 exceeds M16 under matched information and output obligations: evidence supports marginal value of the explicit epistemic status/policy/frame contract;
- deterministic template rendering also matches both: the LLM renderer is unnecessary for the tested task class.

### M15 versus its no-guide DEV ablation — teacher explanation

Question:

> Does Codex's explanation of the generated query interface help fixed-weight Qwen use it?

This is a bounded contextual-teaching result. It is not evidence of weight learning or general skill transfer.

### M16 versus M14 — conventional execution versus non-executed source context

This is a secondary bundle comparison. It estimates the value of relational compilation plus deterministic execution, not a single causal factor.

M15 or M16 versus Raw Prolog alone is diagnostic and must never be the headline causal comparison.

## 6. Matching and anti-confounding requirements

The next producer must freeze:

- the exact source-information equivalence audit;
- whether relational procedures implement rules, policies or only retrieval;
- a common output contract;
- model profile and decoding;
- read-only tool budget and retry policy;
- query catalogue size and visibility;
- token accounting for the guide, catalogue and returned rows;
- maximum result-row policy without outcome-dependent truncation;
- provenance completeness;
- failure classification by query formation, execution, result transport and rendering.

If stored procedures compute status/action/conclusion, M15/M16 are trusted-execution comparators, not non-compiled baselines and are ineligible for M14/B* selection.

If they only retrieve source rows, they do not test an alternative semantic runtime and must be described as retrieval/query-interface controls.

## 7. Implementation choice

Recommended first implementation:

- PostgreSQL;
- a small deterministic generator from the frozen publication case/source contract;
- migrations plus seed/load manifest;
- parameterized read-only functions or views exposed through a typed JSON tool adapter;
- no generated admin UI;
- no unrestricted SQL from Qwen in the confirmatory path.

AppForge may provide:

- entity and EF/PostgreSQL scaffolding;
- migrations;
- generated service/controller contracts;
- typed TypeScript/JSON bindings;
- manifests and reproducible package identity.

AppForge should not own the scientific semantics unless its generated procedures/views are themselves reviewed against the written relational contract. A simpler generator is preferable if AppForge introduces unrelated frontend, CRUD or deployment surface into the experiment.

## 8. Security and validity controls

- Qwen receives a least-privilege read-only credential or, preferably, only a typed tool endpoint.
- SQL injection, DDL/DML and undeclared procedures are rejected.
- Query text/call arguments, result bytes and database execution plan identifiers are stored before scoring.
- Database contents and procedure definitions are immutable during a run block.
- Result limits must be semantically lossless for accepted scenarios; oversized cases fail benchmark construction before split assignment.
- No procedure or view name may leak the expected status or conclusion.
- The independent scorer must distinguish query error, database-runtime error, wrong result use and renderer error.

## 9. Decision and pivot rules

- If M16 is non-inferior to M6, remove claims that the custom epistemic frame or Prolog-specific execution is necessary.
- If M15 is weak but M16 is strong, characterize query formation as the bottleneck and avoid blaming the relational runtime.
- If the Codex guide is the only source of improvement, report a bounded interface-teaching effect rather than a compilation effect.
- If a simple relational package matches M6 at materially lower cost, the engineering recommendation should prefer the simpler conventional system even if the research paper retains a narrower behavioral finding.
- If relational semantics cannot represent the frozen rule/status subset without hidden bespoke code, disclose that limitation and do not present it as a fair conventional baseline.

## 10. Scope and sequencing

This proposal does not authorize a new confirmatory mode automatically.

Required sequence:

1. next WP-004 producer formalizes the relational contract and causal role;
2. build a small TRAIN/DEV-only prototype;
3. test source equivalence, query correctness, leakage and result-size feasibility;
4. WP-006 evaluates the statistical consequence of adding M15/M16;
5. WP-007 evaluates calls, tokens, database build/runtime and annotation cost;
6. independent reviewer chooses one of:
   - include M15 and M16 in confirmatory falsification subset;
   - include only M16 as the strongest conventional execution comparator;
   - retain both as DEV-only diagnostics;
   - reject the comparator as invalid or infeasible with recorded reasons.

No mode is added after HOLDOUT access.
