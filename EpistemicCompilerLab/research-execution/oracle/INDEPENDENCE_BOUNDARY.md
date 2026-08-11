# Independence Boundary — Production Path A and Validation Path B

Status: **WP-005 R2 lifecycle remediation candidate; independent Mutation and Dependency Auditor re-review required**

## 1. Paths, authorities and claim surfaces

```text
A = production interpretation/query/compiler + SWI-Prolog + production policy/frame serializer
Gold = blind human query/outcome adjudication under frozen semantic/policy contracts
B-oracle = clean-room formal executor + policy/frame constructor
B-scorer = clean-room field scorer activated only after gold/B consistency and scorer freeze
```

B implements `SEMANTIC_SPEC.md`, `SEMANTIC_REGISTRY.json` and `POLICY_TABLE.json`; it must not imitate observed A outputs.

`ORACLE_LIFECYCLE_CONTRACT.json` is the machine-readable lifecycle mirror of the authoritative `context-packets/WP-005/ACCEPTANCE.v1.3.yaml` `freeze_order`. `ORACLE_PACKET_CONTRACT.json` is normative for data visibility. Any lifecycle mismatch among acceptance, lifecycle, gold protocol, packet activation rules or this boundary blocks producer handoff.

Outcome gold is the **expected-value authority for scoring**. B-oracle is an independently implemented consistency check, not a second authority that may vote with or overwrite gold.

Four claim tracks remain separate: gold-query execution, natural-question query scoring, production end-to-end, and oracle-frame renderer ceiling.

## 2. Allowed B-oracle packet

B-oracle may receive only read-only, hash-frozen:

- source assertions and strict rules;
- one explicit normalized query for the gold-query/oracle-ceiling execution being run;
- `SEMANTIC_SPEC.md`;
- `SEMANTIC_REGISTRY.json`;
- `POLICY_TABLE.json`;
- public JSON schemas;
- type/identifier/alias registries required to validate the query/source packet.

The query-adjudication registry is already frozen before B execution and may supply the explicit `normalized_query` for an authorized execution. **The independently adjudicated outcome-gold registry is also already frozen at that point, but it is not mounted, readable, importable or otherwise visible to B-oracle while B computes.**

Shared executable semantic helpers are prohibited.

## 3. One fail-closed lifecycle: blind gold first, isolated B second

The previous architecture allowed ambiguous ordering between gold construction and B execution. That ambiguity is prohibited in this version.

The exact lifecycle is:

1. `semantic_spec_registry_policy_hashes_frozen`;
2. `source_rule_packet_hashes_frozen`;
3. `blind_query_adjudication_completed`;
4. `query_adjudication_registry_hash_frozen`;
5. `blind_outcome_gold_adjudication_completed`;
6. `outcome_gold_registry_hash_frozen`;
7. `isolated_B_oracle_computes_without_outcome_gold_mount`;
8. `B_oracle_output_hash_frozen`;
9. `B_vs_outcome_gold_consistency_checked`;
10. `scorer_source_and_hash_frozen`;
11. `first_scored_model_output_may_exist`.

This order intentionally distinguishes **temporal freeze** from **runtime visibility**: outcome gold is frozen before B runs so it cannot be repaired from B, while physical isolation prevents B from reading the frozen answers.

After B output is frozen, a separate consistency phase may compare B against outcome gold. An unexplained disagreement blocks scorer activation and benchmark freeze. B may not override gold, and gold may not be repaired from B. A legitimate gold/specification defect requires a versioned correction under the frozen governance rules; it is never resolved by majority vote between A, B and gold.

Only after `B_vs_outcome_gold_consistency_checked` may scorer source/hash freeze and later score raw model responses against the frozen outcome-gold authority. The frozen B result remains independent consistency evidence and layer-diagnostic material, not the scorer's expected-value source.

Injecting `outcome_gold_registry`, `expected_status`, `expected_positive_evidence_roots`, `expected_negative_evidence_roots`, `expected_proof_normal_form`, `expected_frame`, student output, production frame or outcome metrics into a B-oracle packet is a hard independence failure before execution.

## 4. Forbidden to B-oracle

B-oracle must not read, import, call, copy, translate or dynamically load:

- production compiler/runtime modules;
- production Prolog predicates or compiled clauses;
- production policy functions or frame serializer;
- production-generated expected frames;
- the outcome-gold registry or expected status/action/conclusion/warnings/positive evidence roots/negative evidence roots/provenance/proof/frame fields from gold;
- production unit-test expected outputs when derived from A;
- student prompts, model configuration prompts or teacher proposals;
- raw student/model outputs;
- aggregate DEV/HOLDOUT/REPLICATION metrics;
- sealed datasets before authorized execution;
- caches, RAG indexes, HOME caches, editable packages or logs containing forbidden artifacts.

B-scorer receives raw responses only after the lifecycle in section 3 reaches `scorer_source_and_hash_frozen`, and only for scoring.

## 5. Gold-query execution is not query-formation validation

For a gold-query execution, both A and B may receive the same pre-model adjudicated normalized query. Agreement then validates only formal execution, decision policy and frame serialization under that query.

It does **not** validate:

- natural-question interpretation;
- student query formation;
- production extractor/query formation.

Natural-question query correctness is scored separately against the frozen query-adjudication registry. Production end-to-end remains its own non-independent production track. Oracle-frame→renderer validates rendering only.

Any report that promotes one track into another is invalid even when numeric agreement is perfect.

## 6. Acceptable-alternative freeze

Query alternatives and expected outcome alternatives must be frozen before B-oracle execution and therefore before the first model output exists.

After model output:

- no in-place alternative may be appended;
- scorer implementation bugs may be fixed only if the query/outcome-gold semantic bytes remain byte-identical;
- a newly discovered legitimate ambiguity invalidates current confirmatory eligibility and requires a new benchmark version, new blind adjudication, new hashes and independent review.

“Outcome-blind equivalence review” is not a loophole for expanding expected answers after seeing behavior.

## 7. Clean-room roles

- Semantic-spec producer and Path A producer disclose prior roles.
- Gold adjudicators are distinct from same-candidate Path A, Path B, B-scorer, teacher-target and model-output-analysis roles.
- Path B implementer receives only the allowed B-oracle packet and conformance artifacts; outcome gold is absent from the B runtime mount.
- Audit-tool producer must be distinct from Path B implementer for final trust acceptance.
- Mutation/Dependency Auditor is distinct from Path B implementer and audit-tool producer.
- Human adjudicators do not see A/B/model outputs.
- GATE-001 gatekeeper is a distinct session.

The producer of a critical artifact cannot independently approve it.

## 8. Physical enforcement

The final B build/run environment must:

- mount only an explicit allowed manifest;
- omit outcome-gold, production source, generated-frame, model-output and sealed directories;
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
- outcome-gold registry location exposed only after B execution to the consistency/scorer phases;
- model-output directory;
- teacher prompt directory;
- HOME/language cache;
- editable/local production package path.

Any forbidden canary in B-oracle source, build, logs or outputs is a hard independence failure. The audit tool must not return canary content, only detection metadata.

## 10. Human audit independence

`HUMAN_AUDIT_PROTOCOL.json` freezes a deterministic 120-case non-sealed TRAIN/DEV sample, two blind reviewers plus adjudicator, coverage strata and thresholds. Human reviewers do not use A/B/model outputs as truth.

## 11. Differential agreement

A/B agreement is field-level and only within a declared track. Gold/B consistency is separately recorded after both gold and B output hashes are frozen. Reports include case/track, normalized query where applicable, per-field values, evidence/proof roots, policy result, disagreement layer, resolution classification and artifact hashes.

Exact agreement is required unless the applicable alternative was frozen pre-B/pre-model under `SEMANTIC_REGISTRY.json` normal form.

Every unexplained disagreement blocks scorer activation/freeze. Resolution must classify annotation/gold error, Path A error, Path B error, scorer error or underspecified semantics and produce a versioned reviewed change. Neither B nor A may silently repair outcome gold.

## 12. STOP conditions

STOP confirmatory work when:

- B-oracle can observe outcome gold, expected outcome/frame or raw model output;
- B executes before blind outcome gold is frozen;
- outcome gold is repaired from B or model behavior;
- B requires production executable semantics;
- any forbidden dependency/access is observed;
- any required audit channel is unobservable and unmitigated;
- gold/alternatives are changed in place after model output;
- critical mutation survives;
- B/gold or A/B disagreement remains unexplained where the relevant contract requires agreement;
- gold-query agreement is presented as natural-query validation;
- field-level decomposition cannot reproduce the composite endpoint.
