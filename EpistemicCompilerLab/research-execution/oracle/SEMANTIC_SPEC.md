# Independent Oracle Semantic Specification — Path B

Status: **WP-005 producer remediation candidate; TRAIN/DEV semantics only; independent re-review required**

This document is the normative human-readable semantic contract for Path B. Machine-readable normative details live beside it in:

- `SEMANTIC_REGISTRY.json` — canonicalization, type/scope/version/time, rule, evidence and proof normal forms;
- `POLICY_TABLE.json` — exact status/query-outcome → action/conclusion/warning policy;
- `ORACLE_PACKET_CONTRACT.json` — B-oracle, query-adjudication, outcome-gold and B-scorer data surfaces;
- `CONFORMANCE_VECTORS.json` and `INVARIANT_COVERAGE_MATRIX.csv` — positive/negative/mutation/scorer coverage.

If prose and a machine-readable normative artifact disagree, validation fails and WP-005 returns to REVISE; neither representation silently wins.

## 1. Scientific boundary

Path B answers one narrow question: given independently normalized source assertions, strict rules and a normalized query, what semantic result follows under the frozen specification, and does a raw response match independently frozen query/outcome gold field by field?

Path B is **not** a second copy of production Path A and must not read A output to compute its own output. Agreement with A is evidence only after both outputs are frozen independently.

Four tracks are reported separately:

1. **gold-query execution** — pre-model adjudicated normalized query → A/B formal execution + policy comparison;
2. **natural-question query scoring** — raw student query/interpretation → frozen query alternatives; this track does not use B-oracle outcome as query gold;
3. **production end-to-end** — production extraction/query/execution; no Path-B independence claim is made for this track;
4. **oracle-frame renderer ceiling** — frozen B-oracle frame → renderer; this validates rendering only, not interpretation/query/execution.

Cross-track promotion is forbidden. In particular, A/B agreement on a gold query is not evidence that a student or production extractor formed the right query.

## 2. Data objects

### 2.1 Source assertion

A source assertion contains:

```text
assertion_id      unique canonical identifier
source_id         canonical identifier
locator           source-bound immutable locator
predicate         registered canonical predicate ID
arguments[]       typed ordered values
scope             {jurisdiction, domain, tenant}; each canonical ID or null
version           exact registered opaque version ID
effective_from    inclusive UTC instant or null
effective_to      exclusive UTC instant or null
polarity          positive | negative
```

The assertion ID is provenance identity, not proposition identity. Two byte-equivalent assertions with distinct IDs are two provenance roots but do not create a new truth status merely by duplication. Absence of an assertion is never negative evidence.

### 2.2 Strict rule

A strict rule contains a unique canonical `rule_id`, typed positive premises, one typed head with explicit positive/negative polarity, and equality-only scope/version constraints over already bound values.

Publication Path B v1 has no priorities, defaults, defeaters, exceptions, negation-as-failure, probabilistic weights or hidden procedural callbacks. Every variable in a head or constraint must be bound by a positive premise. A rule that violates this range-restriction is invalid source input.

### 2.3 Normalized query

A normalized query contains exactly predicate, ordered typed arguments, scope, version and `query_time` when bounded effective intervals can apply. Unknown predicates, aliases, versions or identifiers are not guessed.

## 3. Canonicalization

Path B must implement `SEMANTIC_REGISTRY.json` exactly.

### 3.1 Identifiers

Canonical IDs are ASCII and match `^[a-z][a-z0-9_.-]*$`. Equality is exact UTF-8 byte equality after schema validation. There is no implicit case folding. Aliases are resolved only through an explicitly frozen alias table before execution; an unknown alias is invalid.

### 3.2 Scalar values

Strings use Unicode NFC. Integers are mathematical JSON integers and are never parsed from strings or booleans. A declared `number` may accept an integer value but not a string. Booleans have no numeric coercion. Instants are frozen as UTC RFC3339 second precision `YYYY-MM-DDTHH:MM:SSZ`.

### 3.3 Canonical JSON

UTF-8, object keys sorted lexicographically by Unicode code point, separators `,` and `:` with no whitespace, no trailing newline. Arrays preserve order unless the field is explicitly a set field; set fields are deduplicated and sorted by their declared canonical key before serialization.

### 3.4 Proposition identity

Proposition identity excludes polarity and is canonical JSON over exactly `predicate, arguments, scope, version`. Arguments remain ordered. Scope dimensions serialize in fixed order `jurisdiction, domain, tenant`. Equality is byte equality of canonical JSON.

## 4. Scope, version and effective time

For every non-null query scope dimension, an assertion/rule dimension must equal it exactly. A null query dimension is an explicit wildcard for that dimension; rules cannot invent a scope value.

Version IDs are opaque registered identifiers. Version comparison is exact equality only; lexical or semantic-version ordering is forbidden unless a future versioned semantic contract explicitly adds it.

Effective intervals are half-open: `effective_from <= query_time < effective_to`. Null `effective_from` means unbounded past; null `effective_to` means unbounded future. An assertion outside the interval is excluded from derivation. An unknown query version is `invalid_query`, not `unknown`.

Cross-scope fusion is forbidden when the query specifies incompatible non-null dimensions.

## 5. Formal execution algorithm

For a structurally valid query:

1. Validate all source assertions/rules against frozen registries and types. Invalid source packets fail before semantic execution.
2. Normalize source assertions/rules/query.
3. Remove assertions/rules incompatible with query scope, exact version or effective time.
4. Seed a finite relation `D` with every eligible assertion as `(proposition_normal_form, polarity, derivation)`.
5. Repeatedly consider every strict rule under every type-valid substitution whose positive premises are already derivable. Add the normalized head proposition/polarity plus a proof node when not already represented by the same canonical proof node.
6. Continue to the least monotone fixpoint: stop only when no new normalized proposition+polarity pair or canonical proof node is added.
7. Let `P=1` iff at least one positive derivation exists for the queried proposition. Let `N=1` iff at least one negative derivation exists.
8. Map `(P,N)` to status exactly:

| P | N | status |
|---|---|---|
| 1 | 0 | `supported` |
| 0 | 1 | `refuted` |
| 1 | 1 | `conflicting` |
| 0 | 0 | `unknown` |

Evaluation order, duplicate rule order and duplicate derivation count cannot alter this table.

## 6. Evidence-root semantics

For one derivation, its leaf roots are the sorted unique source assertion IDs reachable from its proof tree.

For one polarity, `*_evidence_roots` is the sorted set union of the leaf-root sets of **every valid derivation of that polarity** under the frozen finite closure.

This is a completeness contract, not a minimal-explanation contract. Path B v1 makes no claim that the returned root union is a minimal sufficient subset.

Consequences: duplicate derivations cannot change status; an omitted valid root is wrong; an unloaded/fabricated root is wrong; a conflicting result must preserve both positive and negative root sets.

## 7. Proof normal form

Proof nodes are either source assertion nodes or rule-application nodes as defined in `SEMANTIC_REGISTRY.json`.

For each node, compute `node_id = SHA256(canonical_json(node_fields_without_node_id))`. For a rule node, premise node IDs are sorted before hashing. The final proof graph consists of a node array sorted by node ID and directed edges `[premise_node_id, rule_node_id]` sorted lexicographically.

Every edge must resolve. Cycles are invalid. Proof roots are sorted node IDs whose conclusions equal the queried proposition and polarity. Equivalent derivations normalize to the same node/edge bytes when their semantic content is equal.

## 8. Query outcomes distinct from semantic status

The implementation must never overload `unknown` to mean parser/runtime failure.

- `valid`: a normalized registered query is ready for semantic execution;
- `needs_clarification`: in the natural-question track, a mandatory entity/predicate/argument/scope/version field is unresolved or multiple non-equivalent frozen query alternatives remain; no guessed query/status is produced;
- `invalid_query`: schema/registry/type/arity/version error in an explicit query; no semantic status is produced;
- `runtime_error`: implementation/infrastructure failure after a valid query; it never maps to one of the four semantic statuses.

Natural questions with missing mandatory fields produce clarification; explicit malformed gold queries produce invalid-query failure. These are separate evaluator strata.

## 9. Decision policy

After a `valid` query receives a semantic status, apply exactly one mapping from `POLICY_TABLE.json`. Policy cannot rewrite status.

| outcome/status | action | allowed conclusion | mandatory warning |
|---|---|---|---|
| needs clarification | `request_clarification` | none | `clarification_required` |
| invalid query | `reject_query` | none | `invalid_query` |
| runtime error | `report_runtime_error` | none | `runtime_error` |
| supported | `answer_supported` | `affirm` | none |
| refuted | `answer_refuted` | `deny` | none |
| conflicting | `abstain_conflict` | none | `conflicting_evidence` |
| unknown | `abstain_unknown` | none | `insufficient_evidence` |

The publication subset currently defines no additional source-validity warning types. Adding one requires a new policy version before model-output access.

## 10. Gold and acceptable alternatives

### 10.1 No oracle-from-gold circularity

The B-oracle does not receive expected status/action/conclusion/evidence/provenance/proof/frame fields. `ORACLE_PACKET_CONTRACT.json` makes these fields structurally forbidden in the B-oracle packet.

Independently adjudicated outcomes live in `outcome_gold_registry`, inaccessible during B computation. Only after the B result hash and both registry hashes are frozen may the B-scorer receive raw student output + frozen B output + frozen gold registries.

### 10.2 Query alternatives

Natural-question query alternatives live separately in a pre-model `query_adjudication_registry`. B may execute one of these normalized queries only as an explicit gold-query/oracle-ceiling input. This does not validate student query formation.

### 10.3 Alternative normal form

Acceptable alternatives use exact canonical JSON normalization from `SEMANTIC_REGISTRY.json`. There is no fuzzy or embedding-based scoring-time equivalence.

### 10.4 Post-model discovery

After the first model output exists, no new acceptable query/outcome alternative may be appended in place. If a previously unknown legitimate ambiguity is discovered, the current benchmark version loses confirmatory eligibility; a new benchmark version, registries, hashes and reviewer decision are required. Bug fixes are allowed only when the expected semantic alternative set is byte-identical.

## 11. Field-level scorer

For a schema-valid raw response, score at least these booleans independently:

`schema_valid`, `query_predicate`, `query_arguments`, `query_arity`, `scope_version`, `clarification`, `status`, `action`, `allowed_or_forbidden_conclusion`, `evidence_roots`, `provenance`, `proof_trace`, `warnings`, `language_or_rendering_contract`.

The composite publication correctness endpoint is true only when every publication-critical applicable field is true. A non-applicable field is determined only by the frozen track/query-outcome contract, never by model output.

Malformed output is incorrect. Forbidden tool use or exhausted infrastructure retry is an infrastructure failure and cannot be silently excluded or imputed as correct.

## 12. Conformance and mutation coverage

Every publication-critical invariant is mapped in `INVARIANT_COVERAGE_MATRIX.csv` to at least one positive vector, one negative/invalid vector, one mutation ID, expected Path A result, expected Path B result and expected field-level scorer detection. `CONFORMANCE_VECTORS.json` is frozen before model runs. Any invariant without complete coverage blocks WP-005 semantic validation.

## 13. Human audit

`HUMAN_AUDIT_PROTOCOL.json` freezes a 120-case non-sealed TRAIN/DEV sample, deterministic seed `157005`, 30 cases per status, coverage requirements over domain/status/difficulty/source-family/mutation-family, two blind reviewers per case, third-party adjudication and quantitative thresholds. Failure triggers REVISE and full versioned repeat; cases are not replaced to improve agreement.

## 14. Error attribution

Every failure is attributed to exactly one primary layer where possible: source normalization/registry; natural-question interpretation; query formation; formal execution; decision policy; frame serialization; renderer; scorer/gold governance; infrastructure. When multiple fields fail, retain all field failures and identify the earliest causally sufficient layer; do not collapse the raw evidence.

## 15. STOP conditions

Stop benchmark freeze or confirmatory work if:

- B-oracle can observe expected outcome/frame or model output;
- A/B disagree on a publication-critical invariant without a pre-model adjudicated semantic resolution;
- any critical invariant lacks positive+negative+mutation+scorer coverage;
- any critical mutation survives;
- a required audit observation channel is unobservable and unmitigated;
- human audit thresholds fail;
- acceptable alternatives are changed in place after model outputs;
- `unknown`, `invalid_query`, `needs_clarification` or `runtime_error` are conflated.
