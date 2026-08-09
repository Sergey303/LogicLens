# ENG-202 — Distillation data contract

Status: producer design candidate; TRAIN generation/training only.

## Unit of supervision

Every row represents one independently grouped TRAIN example and contains evaluator-side metadata plus a student-visible input/target pair. Internal identifiers never become model text.

Required evaluator-side fields:

- `record_id`: opaque random internal identifier, never teacher/student visible;
- `split`: exactly `TRAIN`;
- `source_family_id`: grouping key used for split/leakage audits, never inserted into target;
- `input_text`;
- `teacher_evidence_view`: frozen TRAIN-only evidence/context permitted to Codex;
- `gold_target`;
- `teacher_target` for W-C only;
- `target_schema_id`;
- `source_refs`;
- SHA-256 of canonical input/evidence and each target;
- tokenizer revision;
- token counts computed with that tokenizer;
- generation provenance for teacher targets.

## Student-visible corpus

W-B rows contain only the frozen inference/training template plus `input_text` and `gold_target`.

W-C rows contain the identical template plus `input_text` and `teacher_target`.

Neither arm receives `record_id`, split name, source-family identifier, evaluator notes, hidden labels, expected scores, DEV/HOLDOUT/REPLICATION references or teacher metadata.

## Teacher contract

The teacher may see only `input_text`, `teacher_evidence_view`, the frozen target schema and teacher instructions for TRAIN records. **It must not receive `gold_target`.** It cannot query DEV, HOLDOUT, REPLICATION, future source families, student outputs or aggregate outcome reports.

For core W-C, the teacher must independently produce exactly the same target schema used by W-B. Free-form chain-of-thought, rationale, Python/Prolog trace or extra commentary is rejected from W-C and belongs only to separately frozen W-D.

Teacher calls, request/response hashes, model identifier, token counts, temperature/seed when exposed, errors and retries are retained. Failed calls are not silently regenerated under a different prompt/model/budget.

Teacher generation in core W-C may not select records using observed student weakness, choose among multiple correct teacher trajectories using student likelihood, reweight supervision spans, or regenerate a curriculum from student errors. Those are distinct distillation treatments identified in `DISTILLATION_CONTROL_BOUNDARY.md`.

## Record-set and ordering match

W-B and W-C use **exactly the same ordered evaluator-side `record_id` set for each training seed**.

Data order may not depend on `gold_target`, `teacher_target`, target length, model loss or DEV performance. The normative per-seed ordering is defined in `TRAINING_REPLICABILITY_CONTRACT.md`:

```text
order_key = SHA256(utf8(decimal_seed) || 0x00 || utf8(record_id))
sort ascending by (order_key, record_id)
```

The record ID/order manifest is evaluator-side evidence and is never student-visible.

## Target-length and compute matching

The target **content is the treatment**, so valid semantic targets must not be edited merely to equalize token totals.

Core matching rules:

1. identical grouped TRAIN record IDs;
2. identical student-visible input template;
3. identical target schema;
4. identical predeclared maximum sequence length and maximum complete-target length;
5. identical optimizer steps, effective batch/accumulation boundaries and adapter capacity;
6. one frozen loss implementation for both arms;
7. actual target-token totals and per-record target-length distributions retained for both arms.

A complete target that exceeds the predeclared maximum target length makes the candidate corpus invalid. **Do not end-truncate a semantically valid target, delete a record from only one arm, append supervised no-op padding, or manually rewrite a target to force token equality.**

If target-token totals differ because the two supervision sources produce different valid values under the same schema, the difference is reported as a property of the supervision treatment. A separately preregistered length-matched sensitivity analysis may be DEV-only; it cannot replace the core result after outcomes are observed.

## Content integrity

Canonical UTF-8 LF text is hashed with SHA-256. Corpus generation produces an immutable manifest with ordered record hashes and aggregate hash. Changes to any input/evidence/target/provenance field create a new corpus version.

The corpus manifest must separately hash:

- unordered grouped record membership;
- per-seed ordered record IDs;
- student-visible input bytes;
- W-B target bytes;
- W-C target bytes;
- tokenizer/revision used for token accounting.

## Prohibited leakage

Reject a corpus if model-visible or teacher-visible text contains or encodes:

- internal case IDs or source-family IDs;
- adjudicated `gold_target` in the W-C teacher workspace;
- expected metric/scorer outputs;
- DEV/HOLDOUT/REPLICATION examples or identifiers;
- hidden answer tables;
- future source-family names learned after the TRAIN freeze;
- post-hoc student/model failure annotations;
- instructions derived from confirmatory outcomes.

Unknown overlap is not treated as safe. If a required leakage check cannot be run, the report records `unknown` and the corpus is not eligible for confirmatory use.

Checks requiring hidden DEV/HOLDOUT/REPLICATION content are run by a sealed split custodian/scanner under a frozen procedure. It returns only report statuses and aggregate evidence; hidden examples are not exposed to the producer, teacher, corpus builder or student.

## No retroactive repair

After any HOLDOUT access, no TRAIN target may be repaired from model outputs, scorer failures or HOLDOUT-derived patterns. Before HOLDOUT, any TRAIN repair is a new versioned corpus and requires the same leakage checks and matched-arm regeneration.
