# ENG-197 — M15 identifier visibility and query-responsibility contract

Status: **frozen remediation producer contract; TRAIN/DEV only**.

## Adjudication

`M15 Relational Query Agent` is **DEV-only by default** and is not eligible for confirmatory inclusion in the current WP-004 candidate registry.

Reason: the frozen relational package currently exposes one semantic endpoint, `resolve_claim`. With only one endpoint, M15 cannot support a meaningful endpoint-selection estimand. Treating formatting of a predetermined call as tool/query selection would overstate the treatment.

`M16 Relational Result Interface` is the only ENG-197 mode that may become a WP-004 falsification candidate after live PostgreSQL execution, lossless-subset, freeze-manifest and independent-review gates pass.

## M15 DEV-only visible input

For diagnostics, M15 receives exactly:

- the natural-language question;
- the neutral typed catalogue;
- the frozen query guide;
- the response/call schema;
- independently prepared **opaque visible identifiers** required to instantiate the call: `proposition_id`, `scope_id`, `version`.

The identifier values are prepared without outcome/status/action information and are byte-identical to the values used by M16 for the same scenario. They are not inferred by a hidden semantic service.

M15 does **not** receive:

- expected status/action/conclusion;
- evaluator-only case labels;
- a preselected endpoint field in the question payload;
- SQL text;
- production/Prolog output;
- HOLDOUT/REPLICATION content.

## What M15 may measure

With the current single-endpoint catalogue, M15 may only be reported as a DEV diagnostic of:

- typed-call construction/argument placement;
- schema-following failure;
- query-guide usability.

It may **not** be reported as evidence for capability/endpoint routing or teacher policy selection.

A future M15 version can test query/endpoint selection only after a separately frozen catalogue contains at least two semantically distinct read-only endpoints, each has independently adjudicated routing ground truth, and WP-004 versions the treatment before HOLDOUT.

## Failure accounting

Keep separate:

- `identifier_preparation` — upstream, held equal M15/M16;
- `typed_call_construction` — M15 responsibility;
- `adapter_validation`;
- `db_execution`;
- `result_transport`;
- `rendering`.

A wrong or malformed M15 call is never repaired by selecting the M16 call.
