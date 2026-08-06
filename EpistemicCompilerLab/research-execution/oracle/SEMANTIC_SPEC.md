# Implementation-Independent Semantic Specification — Path A / Path B

Status: **WP-005 producer specification; pending independent review**

## 1. Purpose

This document is the only normative semantic description shared by production path A and validation path B. Neither implementation is authoritative by itself. Confirmatory gold is accepted only after independent annotation/adjudication, property tests, mutation tests, human audit, and explained A/B agreement.

## 2. Typed objects

### Source assertion

A source assertion contains:

- stable `assertion_id`;
- subject, predicate and ordered typed arguments;
- explicit polarity: `positive` or `negative`;
- source/version/scope/effective-time fields;
- addressable provenance;
- dependency group where required;
- annotation state and adjudication record.

Absence of an assertion is never negative evidence.

### Interpretation

Interpretation contains only values licensed by the user question and frozen source vocabulary. It records ambiguous/missing required fields and may require clarification. It may not silently add an entity, version, scope, predicate or argument.

### Query

A query contains a declared predicate, ordered typed arguments, version/scope and requested decision contract. Invalid arity, unknown identifiers, incompatible scope or unresolved mandatory ambiguity produce a rejected query or clarification action—not a guessed query.

### Derived status

Let `P` mean at least one valid positive derivation and `N` at least one valid negative derivation for the same normalized proposition, scope and version.

| P | N | status |
|---|---|---|
| true | false | `supported` |
| false | true | `refuted` |
| true | true | `conflicting` |
| false | false | `unknown` |

`unknown` is open-world insufficiency, never `false`. `conflicting` preserves both derivation sets and may not be silently resolved.

### Decision policy

Policy is a frozen deterministic function of valid query, status, request type, version/scope and declared warnings. It returns:

- `action`;
- `allowedConclusion` or an explicit absence;
- clarification requirements;
- forbidden conclusions;
- mandatory warning/provenance/proof obligations.

Policy does not alter source assertions or status.

### Decision frame

A frame contains separately addressable:

- normalized query;
- status;
- positive and negative evidence roots;
- proof trace;
- action;
- allowed conclusion;
- scope/version;
- warnings;
- provenance;
- policy/rule/schema versions.

A frame is invalid if required fields are absent, evidence/proof identifiers are unresolvable, or fields contradict each other.

### Student response

Raw response is stored before validation. The scorer parses it only through the frozen response schema. Timeout, exhausted retry, empty output, malformed JSON, forbidden tool call or schema failure is incorrect.

## 3. Rule semantics

Only safe strict rules in the frozen publication subset are allowed.

- Variables in a derived head or negative/support condition must be range-restricted by positive typed premises.
- Rule application preserves argument order, scope/version compatibility and provenance roots.
- Explicit negation is data, not negation-as-failure.
- No closed-world completion is permitted.
- Duplicate derivations may be preserved for audit but cannot change Boolean existence of P or N.
- Dependency metadata cannot be inferred from names or wording.
- Any exception/priority mechanism must be explicitly specified before implementation; otherwise conflicting derivations remain `conflicting`.

## 4. Normal forms and acceptable alternatives

Before model runs, annotation/adjudication may enumerate multiple valid queries or frames. Each receives a semantic normal form:

```text
predicate
ordered typed arguments
scope
version
status
normalized evidence-root sets
policy action
forbidden/allowed conclusion class
```

An alternative is accepted only when listed before model execution or when an outcome-blind bug review proves equivalence under this normal form. A model-produced alternative is never accepted merely because it appeared.

## 5. Scoring decomposition

Path B emits field booleans for:

```text
schema_valid
query_predicate
query_arguments
query_arity
scope_version
clarification
status
action
allowed_or_forbidden_conclusion
evidence_roots
provenance
proof_trace
warnings
language_or_rendering_contract
```

Composite exact epistemic contract accuracy is the conjunction of mandatory field booleans under the frozen scenario/paraphrase aggregation rule.

Error buckets remain distinct:

```text
source annotation/extraction
question interpretation
query formation
formal execution
decision policy
frame serialization
renderer
infrastructure
```

## 6. Gold construction

Gold is created from source-bound annotation and independent adjudication before student outputs are available. Gold construction may use source documents, frozen schemas, this specification, annotation forms and adjudication records. It may not use production-generated frames, student prompts, student responses, aggregate model metrics or favorable pilot behavior.

## 7. Required invariants

- Same normalized proposition and compatible scope/version are required before combining evidence.
- Status truth table above is exhaustive and deterministic.
- Evidence roots are subsets of loaded addressable assertions/rules.
- Every proof edge resolves to an existing premise/rule and terminates.
- Action/conclusion obey the policy table and status.
- Clarification is mandatory when required interpretation fields are unresolved.
- Forbidden conclusions are never accepted by fluent wording.
- Formal correctness is relative to loaded validated assertions/rules, not world truth.

## 8. Freeze and disagreement

Before HOLDOUT, freeze hashes for semantic spec, schemas, Path B, scorer, mutation report, A/B differential report and human audit. Every unexplained A/B disagreement blocks confirmatory freeze. Resolution must identify annotation error, A error, B error or underspecified semantics and produce a reviewed version bump.
