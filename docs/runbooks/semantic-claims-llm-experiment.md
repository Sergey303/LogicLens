# Measured Semantic Claims pilot plan v0

Status: research-only measurement protocol.

This layer turns bounded local Ollama runs into one reproducible Gate A report. It does
not call a model in CI and it does not promote any model output into Dataset Profile,
Presentation Planner, UI Document, React, or the active epoch.

## Fixed pilot matrix

The pilot is intentionally small and immutable:

- model: `qwen2.5-coder:7b`;
- temperature: `0`;
- context: `2048` tokens;
- maximum output: `1024` tokens;
- CPU-safe derived profile: `num_gpu=0`, `num_batch=64`;
- cases: all five frozen `semantic-planning-v0` cases;
- seeds: `0`, `1`, and `2`;
- planned runs: 15.

The plan binds every case and request to frozen manifest, case, and request hashes. A
new model, token budget, case set, or seed set requires a new plan version rather than
editing this pilot.

## No cherry-picking

Every planned run must appear in the final report as exactly one of:

- `valid` — request, raw Ollama response, parsed response, candidate, and evaluation all
  verify;
- `missing` — the run directory is absent;
- `incomplete` — the directory exists but one or more required files are absent;
- `invalid` — an artifact, hash, request, producer identity, or evaluation fails
  verification.

Missing, incomplete, and invalid runs remain in the report. They cannot be silently
excluded from the denominator or replaced with a successful retry under the same
`runId`.

## Create and verify the plan

```powershell
python .\tools\semantic_claims_llm_experiment.py create-plan `
  --output .\artifacts\semantic-claims-pilot\plan.json

python .\tools\semantic_claims_llm_experiment.py verify-plan `
  --plan .\artifacts\semantic-claims-pilot\plan.json
```

Generate the exact 15 local commands:

```powershell
python .\tools\semantic_claims_llm_experiment.py commands `
  --plan .\artifacts\semantic-claims-pilot\plan.json `
  --runs-root .\artifacts\semantic-claims-pilot\runs
```

Each command creates a new immutable run directory containing:

```text
request.json
raw-ollama-response.json
model-response.json
candidate.json
evaluation.json
```

Do not edit a run directory after creation. Infrastructure failures should be preserved
as missing, incomplete, or invalid evidence until a separately versioned rerun policy is
approved.

## Collect the report

```powershell
python .\tools\semantic_claims_llm_experiment.py collect `
  --plan .\artifacts\semantic-claims-pilot\plan.json `
  --runs-root .\artifacts\semantic-claims-pilot\runs `
  --output .\artifacts\semantic-claims-pilot\report.json

python .\tools\semantic_claims_llm_experiment.py verify-report `
  --plan .\artifacts\semantic-claims-pilot\plan.json `
  --runs-root .\artifacts\semantic-claims-pilot\runs `
  --report .\artifacts\semantic-claims-pilot\report.json
```

The report records every run, aggregate exact-role TP/FP/FN/F1, per-case results,
contract evidence validity, false-supported safety, and claim-signature stability across
all three declared seeds.

## Baseline comparison

The plan freezes the already measured deterministic control:

- all cases: TP 14, FP 0, FN 4, exact-role F1 `0.875`;
- opaque case: TP 0, FP 0, FN 3, exact-role F1 `0.0`.

`opaqueBeatsDeterministicBaseline` can become true only after all 15 runs verify. A
partial report never claims improvement even when its available runs look favorable.

## Safety and interpretation

The pilot signals are descriptive research signals, not promotion authority:

- all contract evidence must remain valid;
- false-supported claims must remain zero;
- every case must have all three seeds;
- claim signatures must be stable across those seeds;
- `automaticPromotionAllowed` is always `false`.

Even a complete passing report remains too small for production promotion. It can only
justify the next controlled experiment or a decision to stop/simplify the direction.

## CI boundary

CI creates and verifies the fixed plan, emits all 15 commands, and collects an empty
report containing 15 explicit `missing` records. This proves accounting and report
replay without calling Ollama. The empty CI report and any synthetic fixture are not
measured LLM results.
