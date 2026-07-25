# Representation runner v0

This runner compares one weak Ollama-compatible local model across five knowledge representations while keeping benchmark questions, model settings and scoring fixed.

## Modes

1. `markdown` — the model receives only `sources/materials.md` and the question;
2. `compact-json` — the model receives only `representations/knowledge.compact.json` and the question;
3. `prolog-text` — the model reads `prolog/knowledge.pl` without executing it;
4. `cli` — the model translates the question into `current-material`, the runner executes it, and the model finalizes from the JSON result;
5. `cli-tails` — as above, with a separate decision about opening one `evidence` or `exceptions` tail.

The benchmark's `expected*` fields are used only by `score-representation.ps1`. They are never included in model prompts.

## Result contract

Each JSONL line stores the run identity, commit, model, prompt hashes, case, decisions, exact CLI calls, opened tails, normalized answer, token counters, elapsed time, raw model responses and any runner error.

A malformed answer affects its case but does not erase earlier results. Each case is written immediately.

## Local outputs

Generated files belong under `experiments/model-runs/` and are ignored by Git. Preserve reviewed aggregate findings in the append-only `experiments/runs.jsonl`.

## Ollama execution profile

The one-command baseline creates a separate local profile derived from the requested base model. Version `cpu-v1` uses:

- `num_gpu 0` — CPU execution, avoiding CUDA host-buffer allocation;
- `num_ctx 2048` — fixed experiment context;
- `num_batch 64` — bounded prompt-processing batch;
- temperature `0` and seed `42` in every API call.

For base model `qwen2.5-coder:7b`, the generated profile is:

`epistemic-qwen2.5-coder-7b:cpu-v1`

The base model is not modified or duplicated. Ollama creates another model configuration referencing it. The profile name is stored as the executed model in JSONL, while the baseline command prints both base and execution names.

CPU-safe and future GPU runs are different experimental conditions and must not be combined in one comparison.

The runner uses only the local `/api/chat` and `/api/tags` endpoints. List source models with `ollama list`.
