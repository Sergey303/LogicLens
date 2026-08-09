# Independence Boundary — Production Path A and Validation Path B

Status: **WP-005 producer remediation candidate; independent Mutation and Dependency Auditor re-review required**

## 1. Paths and claim surfaces

```text
A = production interpretation/query/compiler + SWI-Prolog + production policy/frame serializer
B-oracle = clean-room formal executor + policy/frame constructor
B-scorer = clean-room field scorer activated only after oracle/gold/scorer freeze
```

B implements `SEMANTIC_SPEC.md`, `SEMANTIC_REGISTRY.json` and `POLICY_TABLE.json`; it must not imitate observed A outputs.

The exact data surfaces are normative in `ORACLE_PACKET_CONTRACT.json`. Four claim tracks remain separate: gold-query execution, natural-question query scoring, production end-to-end, and oracle-frame renderer ceiling.

## 2. Allowed B-oracle packet

B-oracle may receive only read-only, hash-frozen:

- source assertions and strict rules;
- one explicit normalized query for the gold-query/oracle-ceiling execution being run;
- `SEMANTIC_SPEC.md`;
- `SEMANTIC_REGISTRY.json`;
- `POLICY_TABLE.json`;
- public JSON schemas;
- type/identifier/alias registries required to validate the query/source packet.

A pre-model query-adjudication registry may supply an explicit normalized query to a gold-query/oracle-ceiling execution, but **expected semantic outcomes remain in a different registry and are not visible to B-oracle**.

Shared executable semantic helpers are prohibited.

## 3. Outcome gold is not an oracle input

The previous architecture allowed “adjudicated gold records” as a shared B surface. That is prohibited in this version.

Expected fields live in a distinct `outcome_gold_registry`, including expected status/action/conclusion/warnings/evidence/provenance/proof/frame. This registry is inaccessible to B-oracle while it computes a case.

Order is fail-closed:

1. source/query/spec/policy hashes freeze;
2. B-oracle computes from its allowed packet;
3. B-oracle output bytes/hash freeze;
4. query-adjudication and outcome-gold registry hashes freeze;
5. B-scorer source/hash freezes;
6. only then may B-scorer receive raw student response + frozen B result + frozen gold registries.

Injecting `expected_status`, `expected_frame`, student output, production frame or outcome metrics into a B-oracle packet is a hard independence failure before execution.

## 4. Forbidden to B-oracle

B-oracle must not read, import, call, copy, translate or dynamically load:

- production compiler/runtime modules;
- production Prolog predicates or compiled clauses;
- production policy functions or frame serializer;
- production-generated expected frames;
- expected status/action/conclusion/evidence/provenance/proof/frame fields from gold;
- production unit-test expected outputs when derived from A;
- student prompts, model configuration prompts or teacher proposals;
- raw student/model outputs;
- aggregate DEV/HOLDOUT/REPLICATION metrics;
- sealed datasets before authorized execution;
- caches, RAG indexes, HOME caches, editable packages or logs containing forbidden artifacts.

B-scorer receives raw responses only after the freeze order in section 3 and only for scoring.

## 5. Gold-query execution is not query-formation validation

For a gold-query execution, both A and B may receive the same pre-model adjudicated normalized query. Agreement then validates only formal execution, decision policy and frame serialization under that query.

It does **not** validate:

- natural-question interpretation;
- student query formation;
- production extractor/query formation.

Natural-question query correctness is scored separately against the frozen query-adjudication registry. Production end-to-end remains its own non-independent production track. Oracle-frame→renderer validates rendering only.

Any report that promotes one track into another is invalid even when numeric agreement is perfect.

## 6. Acceptable-alternative freeze

Query alternatives and expected outcome alternatives must be frozen before the first model output exists.

After model output:

- no in-place alternative may be appended;
- scorer implementation bugs may be fixed only if the expected semantic set is byte-identical;
- a newly discovered legitimate ambiguity invalidates current confirmatory eligibility and requires a new benchmark version, new hashes and independent review.

“Outcome-blind equivalence review” is not a loophole for expanding expected answers after seeing behavior.

## 7. Clean-room roles

- Semantic-spec producer and Path A producer disclose prior roles.
- Path B implementer receives only the allowed B-oracle packet and conformance artifacts.
- Audit-tool producer must be distinct from Path B implementer for final trust acceptance.
- Mutation/Dependency Auditor is distinct from Path B implementer and audit-tool producer.
- Human adjudicators do not see A/B/model outputs.
- GATE-001 gatekeeper is a distinct session.

The producer of a critical artifact cannot independently approve it.

## 8. Physical enforcement

The final B build/run environment must:

- mount only an explicit allowed manifest;
- omit production source, generated-frame, model-output and sealed directories;
- use separate package lock/module namespace;
- disable arbitrary network access;
- expose read-only inputs and an output-only allowlist;
- trace file opens, imports, processes, dynamic libraries/FFI, network/DNS, environment reads, symlink resolution and package/cache resolution;
- scan source, built artifacts, stdout/stderr and output artifacts for forbidden paths/symbols/hashes/canaries;
- fail closed on undeclared access.

Instruction-only separation is insufficient.

`AUDIT_TOOL_TRUST_MANIFEST.json` defines the required observation channels, 16 negative controls, positive controls, independent reviewer role and blind-spot policy. A required channel that is `not_observable` cannot count as PASS; it must be covered by a second frozen observer/environment or blocks acceptance.

## 9. Circularity canaries

Place unique forbidden canaries in at least:

- production compiler source;
- generated frame directory;
- production test expected-output fixtures;
- outcome-gold registry location exposed only to scorer phase;
- model-output directory;
- teacher prompt directory;
- HOME/language cache;
- editable/local production package path.

Any forbidden canary in B-oracle source, build, logs or outputs is a hard independence failure. The audit tool must not return canary content, only detection metadata.

## 10. Human audit independence

`HUMAN_AUDIT_PROTOCOL.json` freezes a deterministic 120-case non-sealed TRAIN/DEV sample, two blind reviewers plus adjudicator, coverage strata and thresholds. Human reviewers do not use A/B/model outputs as truth.

## 11. Differential agreement

A/B agreement is field-level and only within a declared track. Reports include case/track, A and B normalized query where applicable, per-field values, evidence/proof roots, policy result, disagreement layer, resolution classification and artifact hashes.

Exact agreement is required unless the applicable alternative was frozen pre-model under `SEMANTIC_REGISTRY.json` normal form.

Every unexplained disagreement blocks freeze. Resolution must classify annotation/gold error, Path A error, Path B error, scorer error or underspecified semantics and produce a versioned reviewed change.

## 12. STOP conditions

STOP confirmatory work when:

- B-oracle can observe expected outcome/frame or raw model output;
- B requires production executable semantics;
- any forbidden dependency/access is observed;
- any required audit channel is unobservable and unmitigated;
- gold/alternatives are changed in place after model output;
- critical mutation survives;
- A/B disagreement remains unexplained;
- gold-query agreement is presented as natural-query validation;
- field-level decomposition cannot reproduce the composite endpoint.
