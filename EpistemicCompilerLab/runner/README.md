# Representation runner v0

This runner compares one weak Ollama-compatible local model across five knowledge representations while keeping benchmark questions, model settings and scoring fixed.

## Modes

1. `markdown` — the model receives only `sources/materials.md` and the question;
2. `compact-json` — the model receives only `representations/knowledge.compact.json` and the question;
3. `prolog-text` — the model reads `prolog/knowledge.pl` without executing it;
4. `cli` — the model first translates the question into `current-material`, the runner executes it, and the model finalizes from the compact JSON result;
5. `cli-tails` — as above, with a separate model decision about opening one `evidence` or `exceptions` tail.

The benchmark's `expected*` fields are used only by `score-representation.ps1`. They are never included in model prompts.

## Result contract

Each JSONL line stores:

- run, commit, model, seed, temperature and prompt hashes;
- case ID and question;
- planner and tail-planner decisions when applicable;
- exact CLI calls and returned JSON;
- opened tails;
- normalized final answer;
- token counters and elapsed time;
- raw model responses for audit;
- a runner error when transport or schema handling failed.

A malformed answer affects its case but does not erase earlier results. The runner writes each case immediately and reports the number of runner errors after all cases.

## Local outputs

Generated model runs belong under `experiments/model-runs/`. Raw runs and summaries are ignored by Git because they may be large and model-specific. Preserve important aggregate findings separately in the append-only `experiments/runs.jsonl` after review.

## Ollama

The selected model must already appear in Ollama's `/api/tags` response. The runner uses `/api/chat` with:

- `format=json`;
- deterministic seed by default (`42`);
- temperature `0` by default;
- no remote API or web proxy.

List installed models locally with `ollama list` before the first run.
