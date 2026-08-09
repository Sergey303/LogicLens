# ENG-202 — Distillation data contract

Status: producer design candidate; TRAIN generation/training only.

## Unit of supervision

Every row represents one independently grouped TRAIN example and contains evaluator-side metadata plus a student-visible input/target pair. Internal identifiers never become model text.

Required evaluator-side fields:

- `record_id`: opaque random internal identifier, never teacher/student visible;
- `split`: exactly `TRAIN`;
- `source_family_id`: grouping key used for split/leakage audits, never inserted into target;
- `input_text`;
- `gold_target`;
- `teacher_target` for W-C only;
- `target_schema_id`;
- `source_refs`;
- SHA-256 of canonical input and each target;
- tokenizer revision;
- token counts computed with that tokenizer;
- generation provenance for teacher targets.

## Student-visible corpus

W-B rows contain only the frozen inference/training template plus `input_text` and `gold_target`.

W-C rows contain the identical template plus `input_text` and `teacher_target`.

Neither arm receives `record_id`, split name, source-family identifier, evaluator notes, hidden labels, expected scores, DEV/HOLDOUT/REPLICATION references or teacher metadata.

## Teacher contract

The teacher may see only TRAIN material supplied by the frozen teacher workspace. It cannot query DEV, HOLDOUT, REPLICATION, future source families, student outputs or aggregate outcome reports.

For core W-C, the teacher must output exactly the same target schema used by W-B. Free-form chain-of-thought, rationale, Python/Prolog trace or extra commentary is rejected from W-C and belongs only to separately frozen W-D.

Teacher calls, request/response hashes, model identifier, token counts, temperature/seed when exposed, errors and retries are retained. Failed calls are not silently regenerated under a different prompt/model/budget.

## Budget matching

Primary matching variable: **effective supervised target tokens** under the exact frozen tokenizer revision.

Before any training, a deterministic corpus builder constructs matched W-B/W-C views. For each source-family stratum it uses the same records and applies the same maximum target-token cap. Total effective target tokens must be equal across W-B/W-C; if exact equality is impossible because targets tokenize differently, deterministic end truncation is applied to the longer arm under the frozen output schema. Any truncation that makes a target schema-invalid rejects the candidate corpus instead of repairing it manually.

The training manifest additionally fixes equal optimizer steps, batches, sequence length, adapter capacity and seeds.

## Content integrity

Canonical UTF-8 LF text is hashed with SHA-256. Corpus generation produces an immutable manifest with ordered record hashes and aggregate hash. Changes to any input/target/provenance field create a new corpus version.

## Prohibited leakage

Reject a corpus if model-visible text contains or encodes:

- internal case IDs or source-family IDs;
- expected metric/scorer outputs;
- DEV/HOLDOUT/REPLICATION examples or identifiers;
- hidden answer tables;
- future source-family names learned after the TRAIN freeze;
- post-hoc student/model failure annotations;
- instructions derived from confirmatory outcomes.

Unknown overlap is not treated as safe. If a required leakage check cannot be run, the report records `unknown` and the corpus is not eligible for confirmatory use.

## No retroactive repair

After any HOLDOUT access, no TRAIN target may be repaired from model outputs, scorer failures or HOLDOUT-derived patterns. Before HOLDOUT, any TRAIN repair is a new versioned corpus and requires the same leakage checks and matched-arm regeneration.
