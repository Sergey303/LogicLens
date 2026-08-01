# Deterministic Semantic Claims baseline v0

Status: research-only Gate A control.

This baseline establishes what LogicLens can infer without an LLM, task-text parsing,
or domain-specific code. It uses only:

- exact ontology labels already present in the frozen case;
- literal datatypes attached to canonical facts.

It produces a candidate Semantic Claims artifact and a separate evaluation artifact.
Oracle claims are never read while generating the candidate. They are used only by the
trusted evaluator after candidate bytes have been frozen and verified.

## Supported label rules

Version 0 deliberately uses a small exact label table:

- `Редакция`, `Код` → `display_role / identifier`;
- `Название` → `display_role / display_label`;
- `Описание` → `display_role / description`;
- `Статус`, `Состояние` → `value_role / status`;
- `Материал` → `value_role / category`;
- `Температура` → `value_role / measurement`;
- `Цена` → `value_role / monetary_amount`;
- `Возраст` → `value_role / age`;
- `Действует с` → `value_role / time_value`.

A generic label `Дата` combined with `xsd:date` or `xsd:dateTime` yields only
`possible time_value`. It must not become `supported`, and the baseline does not invent
a second interpretation such as `publication_time`.

Predicates without a recognized ontology label remain in
`unclassifiedPredicateIds`. In particular, the opaque-predicate benchmark case must
remain unclassified. This is the intended lower bound against which a later LLM claim
producer will be measured.

## Candidate artifact

`tools/semantic_claims_baseline.py create` records:

- frozen benchmark and case hashes;
- producer identity and algorithm version;
- the exact allowed input families;
- `task.textUsed = false`;
- generated claims and inspectable evidence;
- unclassified predicate IDs;
- canonical JSON and a domain-separated artifact hash.

The verifier reconstructs the candidate from the frozen case. Changes to claims,
status, evidence, ordering, unclassified predicates, producer identity, or bytes fail
closed.

## Evaluation artifact

The evaluator scores exact tuples:

```text
(dataElement.kind, dataElement.id, facet, role)
```

It records:

- exact-role TP, FP, FN, precision, recall, and F1;
- per-role metrics and macro-F1;
- ambiguity detection from `possible` status;
- false-supported count;
- machine-checkable evidence validity;
- oracle and candidate claim counts.

Claim IDs are intentionally excluded from semantic scoring. Status remains separately
observable through ambiguity and false-supported metrics.

## Frozen benchmark result

For the five semantic-planning-v0 cases, algorithm version 1 must produce:

- exact-role TP: 14;
- exact-role FP: 0;
- exact-role FN: 4;
- aggregate exact-role F1: 0.875;
- false-supported claims: 0;
- evidence validity: 16 / 16;
- opaque-predicate candidate claims: 0.

These values are a control result, not a product quality target. A later LLM producer
must be evaluated with the same scorer and must add value specifically on opaque and
ambiguous inputs without increasing false-supported claims or invalid evidence.

## Run locally

```bash
python tools/semantic_claims_baseline.py create \
  --case-id opaque-revision-comparison \
  --output /tmp/opaque.candidate.json

python tools/semantic_claims_baseline.py verify \
  --artifact /tmp/opaque.candidate.json

python tools/semantic_claims_baseline.py evaluate \
  --candidate /tmp/opaque.candidate.json \
  --output /tmp/opaque.evaluation.json

python tools/semantic_claims_baseline.py verify-evaluation \
  --candidate /tmp/opaque.candidate.json \
  --artifact /tmp/opaque.evaluation.json
```

This stage does not change the planner, UI Document, React renderer, active epoch, or
transactional runtime.
