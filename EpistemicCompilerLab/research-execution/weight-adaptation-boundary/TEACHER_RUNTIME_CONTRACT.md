# ENG-202 — Codex teacher runtime and budget contract

Status: producer design candidate. No teacher corpus has been generated.

## Model/runtime identity

The local Codex CLI is invoked without an unsupported guessed `--codex-model` override. Before any W-C corpus generation, the producer must record:

- Codex CLI version and executable hash where available;
- resolved provider/model identifier reported by the runtime;
- request API/runtime metadata exposed by Codex;
- teacher system/instruction/template SHA-256;
- generation start/end timestamps;
- per-attempt input/output token accounting when exposed.

`codex_cli_default` is **not** treated as an immutable scientific model identity. If the runtime cannot expose a stable resolved model identifier, the run must record `teacher_model_reproducibility: limited` and ENG-202 cannot claim exact teacher-model reproducibility. A model/runtime change during corpus generation invalidates that corpus version.

No fallback teacher/model may be silently substituted after failures.

## Visibility

Core W-C teacher input is limited to:

- TRAIN `input_text`;
- frozen TRAIN `teacher_evidence_view`;
- target schema;
- frozen teacher instructions.

The teacher must not receive adjudicated `gold_target`, internal IDs, DEV/HOLDOUT/REPLICATION content, student outputs, scores or aggregate model outcomes.

## Frozen budget

For each frozen TRAIN record:

- maximum successful semantic generation responses: `1`;
- maximum provider attempts: `2`;
- attempt 2 is permitted only when attempt 1 failed before producing a semantic response, and must use the byte-identical frozen request;
- no retry is permitted after a refusal, schema-invalid semantic response, budget violation or successful semantic response;
- maximum teacher-visible input tokens per attempt: `4096`;
- maximum generated output tokens for the single semantic response: `256`.

For a corpus with `N` frozen TRAIN records, the planned worst-case audit budget is therefore:

- successful generation responses: at most `N`;
- provider attempts: at most `2 * N`;
- input-token ceiling across attempts: `8192 * N`;
- successful semantic output-token ceiling: `256 * N`.

Every attempt is retained in the audit ledger, including an infrastructure-failed first attempt. The exact observed token usage is retained. If the runtime cannot enforce a hard token limit, observed usage must be validated against the ceiling; a semantic response exceeding the per-attempt/output ceiling is rejected rather than truncated or repaired.

## Determinism and failures

If the runtime exposes temperature, seed or sampling controls, freeze them before generation and record them. If it does not, preserve every request/response hash and report teacher stochasticity as an external-source limitation.

Malformed schema output, content-policy refusal, timeout or provider error remains in the generation ledger. A malformed/refused semantic response cannot be retried or manually repaired within the same candidate corpus. Only a pre-semantic transport/infrastructure failure is retryable once with the byte-identical request.

## No outcome-directed regeneration

Teacher targets are generated before student training outcomes are observed. No target may be regenerated because W-C underperforms, because a DEV error is discovered, or because another arm performs better.
