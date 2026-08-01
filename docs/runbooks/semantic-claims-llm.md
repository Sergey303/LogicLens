# Bounded LLM Semantic Claims producer v0

Status: research-only Gate A experiment boundary.

This tool lets a local Ollama model propose Semantic Claims for the frozen
`semantic-planning-v0` benchmark. It does not generate UI, choose a component,
compute a Dataset Profile, or enter the active epoch.

## Trust boundary

The model receives only:

- task language, goal, text, and visible questions;
- canonical facts with fixture-local FactIds;
- visible ontology labels and definitions.

The request never contains `answerKey`, `oracleSemanticClaims`,
`oracleDatasetProfile`, or `expectedPresentation`. The prompt and exact JSON Schema
are preserved in `request.json`.

The model response is untrusted. Trusted code checks:

- every visible predicate is either claimed or explicitly unclassified;
- no invented predicate, FactId, label, datatype, task substring, or neighboring
  predicate reference exists;
- facets and statuses use the closed v0 values;
- roles are bounded lower-snake-case strings but are not normalized through a role
  allowlist;
- `supported` and `possible` claims contain machine-checkable evidence;
- alternatives are valid, symmetric, and refer to the same data element;
- malformed JSON is rejected without repair;
- output-limited generations are infrastructure failures.

A trusted importer assigns deterministic claim IDs, preserves model order, creates a
domain-hashed candidate artifact, and invokes the same
`semantic_claims_baseline.evaluate_claims` scorer used by the deterministic control.

## CI versus measured experiments

CI does not call Ollama. It verifies the response contract, prompt boundary, negative
cases, deterministic importer, scorer integration, and an explicitly synthetic
transport replay. That replay is not a model result and must not be reported as LLM
accuracy.

A measured run exists only after `run` preserves a real loopback Ollama response in a
new output directory. Never edit or reuse a run directory. Keep rejected responses as
experimental evidence.

## Run one local experiment

```powershell
python .\tools\semantic_claims_llm.py run `
  --case-id opaque-revision-comparison `
  --model qwen2.5-coder:7b `
  --seed 0 `
  --context-tokens 2048 `
  --output-tokens 1024 `
  --output .\artifacts\semantic-claims\opaque-seed-0
```

Only HTTP loopback endpoints with path `/api/chat` are accepted. The default is
`http://127.0.0.1:11434/api/chat`. The request also fixes the CPU-safe derived
Ollama profile `num_gpu=0` and `num_batch=64`; it does not modify the base model.

The output directory contains:

```text
request.json
raw-ollama-response.json
model-response.json
candidate.json
evaluation.json
```

## Offline import

A preserved raw response can be imported without another model call:

```powershell
python .\tools\semantic_claims_llm.py import `
  --case-id opaque-revision-comparison `
  --request .\request.json `
  --raw-response .\raw-ollama-response.json `
  --model-response .\model-response.json `
  --candidate .\candidate.json `
  --evaluation .\evaluation.json
```

Then verify the immutable boundary:

```powershell
python .\tools\semantic_claims_llm.py verify `
  --request .\request.json `
  --raw-response .\raw-ollama-response.json `
  --model-response .\model-response.json `
  --candidate .\candidate.json
```

## Promotion gate

This PR establishes transport and scoring only. No LLM result is promoted to Dataset
Profile or Presentation Planner. Before that boundary is generalized, measured runs
must beat the deterministic baseline specifically on opaque predicates while keeping:

- evidence validity at 100% for the frozen pilot;
- false-supported claims at zero for the frozen pilot;
- ambiguous time semantics non-supported;
- complete predicate accounting;
- stable results across declared seeds.
