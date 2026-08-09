# ENG-202 — Codex teacher runtime and budget contract

Status: producer design candidate. No teacher corpus has been generated.

## Model/runtime identity

The local Codex CLI is invoked without an unsupported guessed `--codex-model` override. Before any W-C corpus generation, the producer must record:

- Codex CLI version and executable hash where available;
- resolved provider/model identifier reported by the runtime;
- request API/runtime metadata exposed by Codex;
- teacher system/instruction/template SHA-256;
- generation start/end timestamps;
- per-request input/output token accounting when exposed.

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

- maximum teacher calls: `1`;
- maximum teacher-visible input tokens: `4096`;
- maximum generated output tokens: `256`;
- retries: only transport/infrastructure retry of the byte-identical frozen request, and it counts as an attempted call in the audit ledger even if provider billing semantics differ.

For a corpus with `N` frozen TRAIN records, the planned scientific budget is therefore:

- successful generation requests: at most `N`;
- nominal input-token ceiling: `4096 * N`;
- nominal output-token ceiling: `256 * N`.

The exact observed token usage is retained. If the runtime cannot enforce a hard input/output token limit, the producer must validate observed usage against the ceiling and reject any response exceeding it.

## Determinism and failures

If the runtime exposes temperature, seed or sampling controls, freeze them before generation and record them. If it does not, preserve every request/response hash and report teacher stochasticity as an external-source limitation.

Malformed schema output, content-policy refusal, timeout or provider error remains in the generation ledger. A malformed semantic output cannot be manually repaired; the record is rejected from that candidate corpus or the entire candidate is versioned under a predeclared deterministic rule.

## No outcome-directed regeneration

Teacher targets are generated before student training outcomes are observed. No target may be regenerated because W-C underperforms, because a DEV error is discovered, or because another arm performs better.
