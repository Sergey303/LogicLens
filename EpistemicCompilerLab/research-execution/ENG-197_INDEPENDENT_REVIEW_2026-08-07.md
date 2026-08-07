# ENG-197 — Independent Causal and Database Systems Review

Date: 2026-08-07  
Decision: **REVISE**  
Reviewer: **OpenAI GPT-5.6 Sol — Independent Causal and Database Systems Reviewer**  
Reviewer session: `ChatGPT ENG-197 independent review / 2026-08-07`  
Producer recorded in handoff: `OpenAI GPT-5.6 Thinking — Relational Comparator Architect` / `ChatGPT ENG-197 producer / 2026-08-07`  
Reviewed implementation merge: `26c599dd0791dbae77d29bcc0acabc71bfe15419`  
Reviewed producer handoff commit: `9f9f56ae497fd4042d01d188ac6ca770b51b2f3a`

## 1. Scope reviewed

- Linear `ENG-197` acceptance and producer comment;
- `relational-comparator/contract.json` and README;
- call/result schemas;
- synthetic source, M16 registry and evaluator expectations;
- deterministic generator and generated SQL/package manifest;
- typed adapter, reference oracle and `verify.py`;
- feasibility input for WP-006/WP-007;
- current WP-004 M6/M14 mode contract;
- target-paper publication strict subset;
- existing GitHub workflow evidence on the producer head.

No HOLDOUT or REPLICATION content was accessed.

## 2. Confirmed strengths

- M15/M16 are correctly labeled **trusted-execution comparators**, not M14/B* candidates.
- Semantic ownership is explicit: PostgreSQL owns retrieval, closure, status and action; Qwen owns rendering, with M15 additionally owning query formation.
- The typed-call shape has no free-SQL field and uses parameter binding.
- One-row result policy rejects zero/multiple rows instead of truncating after outcomes.
- Evaluator expected statuses are separated from generator-visible source data.
- Generated files are deterministic for the committed synthetic source and generator.
- Failure layers and STOP/PIVOT interpretations are conceptually well separated.
- The producer correctly disclosed the absence of a live PostgreSQL measurement rather than presenting it as a PASS.

## 3. Blocking findings

### B1 — PostgreSQL semantics are not actually executed by the verification

`verify_runtime_semantics()` calls the Python `reference_oracle.resolve()` and compares that result with evaluator expectations. It never runs `generated/schema.sql`, `seed.sql`, `permissions.sql` or `resolve_claim()` in PostgreSQL.

`verify_sql_contract()` only checks strings such as `WITH RECURSIVE`, `STABLE`, grants and absence of DML tokens. The SQL implementation could therefore be semantically wrong while all seven producer checks still pass.

Required correction:

- instantiate a clean pinned PostgreSQL engine;
- apply schema, seed and permissions from the committed package;
- execute every prototype typed call through the real adapter/DB path;
- compare canonical DB result bytes against an independently defined expected/oracle record;
- run negative permission tests using the actual runtime credential/role;
- make this live test part of a clean-checkout reviewer command or CI job.

### B2 — M15 query formation has an unresolved visibility contradiction

M15 declares Qwen-visible input as question + catalogue + guide + response schema. The endpoint requires `proposition_id`, `scope_id` and `version`.

The frozen guide says those identifiers are “supplied by the experiment adapter”, but they are not declared as M15-visible inputs. If the adapter supplies the correct target identifiers, it has already performed a material part of query formation. If it does not, Qwen cannot infer opaque IDs such as `p-allowed` from the natural-language question using the current visible contract.

Required correction:

- freeze exactly who maps question/entity text to proposition/scope/version identifiers;
- either expose a lossless identifier mapping/catalogue to Qwen and count that information/tokens, or define a separate deterministic interpretation layer held equal across M15/M16/M6;
- test M15 question-to-typed-call formation without using the M16 case registry or evaluator fields;
- classify wrong target/argument selection as `query_formation`, not adapter/DB failure.

### B3 — The relational representation is not yet source-equivalent to the publication strict subset

The publication contract includes explicit positive/negative evidence, dependency groups, safe strict logical rules, version/scope, provenance and proof/evidence trace. Existing strict cases include multi-premise `all`/`any` rules and an `oppose` head.

The current relational prototype represents only:

- one source ID per assertion;
- no dependency group;
- unary positive implication edges;
- direct negative evidence only at the queried proposition;
- no rule/proof lineage in the returned result.

That is a useful toy kernel, but it is not yet evidence that the **same frozen source knowledge** can be represented losslessly by the strongest pure relational comparator. Using it against M6 could weaken M16 by construction.

Required correction:

- define an implementation-neutral relational mapping for every field/rule type admitted by the frozen confirmatory strict subset;
- preserve dependency groups and full provenance;
- represent the accepted strict rule forms, including polarity/head stance and required multi-premise semantics;
- preserve rule/proof lineage sufficiently for source-equivalence auditing;
- add a machine-readable source-equivalence report comparing canonical source facts/rules/provenance against the relational package;
- reject unsupported cases before split assignment rather than silently simplifying them.

### B4 — The freeze/hash closure is incomplete

The package/handoff hashes the source, generator and generated SQL/catalogue/guide, but does not bind all scientific/runtime artifacts that can change M15/M16 semantics.

Notably missing from the frozen hash closure are the scientific contract, call schema, result schema, adapter, M16 registry, reference oracle/expected records and verification/security tests.

Required correction:

- create one top-level immutable manifest hashing every artifact that affects visibility, query formation, execution, transport, scoring boundary or security;
- include contract and schema versions plus generator identity;
- validate the manifest from a clean checkout;
- regenerate the producer handoff from those exact hashes.

### B5 — The required DB-result-before-scoring path is only simulated

`make_pre_score_record()` correctly defines the intended record, but producer verification feeds it rows produced by the Python reference oracle. There is no committed executor that runs the parameterized PostgreSQL call and stores the actual typed call/result bytes before renderer/scorer access.

Required correction:

- add the minimal real DB executor/transport seam;
- persist canonical typed call and actual PostgreSQL result bytes before rendering/scoring;
- freeze query-formation failure and DB/transport failure record schemas;
- demonstrate that scorer fields cannot enter the pre-score record.

### B6 — Feasibility acceptance is not complete

`FEASIBILITY_INPUT.json` contains useful static arithmetic, but the required values for catalogue/guide/result tokens, clean DB build time, query latency, database storage and M16 registry annotation/adjudication cost are still placeholders. WP-007 is currently Backlog and explicitly blocked by ENG-197 and other W0 work.

The Linear acceptance for ENG-197 requires calls, tokens, DB build time, storage and annotation cost to be passed to WP-006/WP-007. That criterion is not yet satisfied by measured values.

Required correction:

- collect the declared measurements on frozen model/tokenizer and PostgreSQL profiles;
- record units, environment/version and uncertainty;
- pass measured inputs to WP-006/WP-007;
- only then adjudicate `M15+M16`, `M16 only`, DEV-only or rejection for confirmatory inclusion.

## 4. Non-blocking hardening

- Validate the semantic pairing `supported→accept`, `refuted→reject`, `unknown/conflicting→review` at the result boundary, not only membership of each enum independently.
- Prefer a runtime DB identity that cannot issue arbitrary table queries if the typed-function boundary is meant to be defense in depth; document how the NOLOGIN reader role is actually assumed by the executor.
- Add exact evidence/provenance expectations for the recursive case, not status/action only.
- Keep AppForge explicitly replaceable; do not expand scope into UI/CRUD generation for this experiment.

## 5. Scientific interpretation retained

The proposed causal role remains valid in principle:

- `M15 vs M16` can estimate query-formation/tool-use cost once the M15 identifier visibility contract is frozen;
- `M16 vs M6` can test conventional relational trusted execution versus the explicit epistemic decision-frame interface once source/policy equivalence is demonstrated;
- if M16 is non-inferior to M6, claims that Prolog or the full custom epistemic frame is necessary must be removed;
- if a fair relational package matches M6 at lower cost, the engineering recommendation should prefer the simpler system.

## 6. Decision

**REVISE.** Do not add M15 or M16 to confirmatory execution yet.

For the next review, the minimum evidence is:

1. live PostgreSQL execution and permission tests;
2. resolved M15 identifier/query-formation visibility contract;
3. lossless mapping/equivalence for the frozen strict subset;
4. complete artifact hash manifest;
5. actual DB pre-score transport record path;
6. measured WP-006/WP-007 feasibility inputs.

Until these are closed, M15/M16 may remain design/prototype material only; they are not accepted confirmatory comparators.