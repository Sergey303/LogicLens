# Local Semantic Claims pilot runner v0

Status: research-only execution helper for the frozen measured pilot.

This runner executes the 15 commands from `semantic-claims-gate-a-pilot-v0` on a local
Ollama instance. It does not retry an attempted `runId`, does not repair model output,
and does not promote claims into Dataset Profile, Presentation Planner, UI Document, or
the active epoch.

## Why a separate runner exists

The experiment plan requires every case/seed combination to remain in the denominator.
A naïve shell loop can accidentally rerun failures, overwrite partial directories, or
stop before producing the final accounting report. The runner therefore uses a staging
protocol:

1. an unattempted run writes to `.<runId>.in-progress`;
2. success or failure receives an immutable `execution.json` record;
3. the staging directory is renamed to the final `<runId>` directory;
4. an existing final directory is skipped forever by this pilot version;
5. a staging directory left by interruption is finalized as incomplete without retry;
6. after all runs, the ordinary trusted aggregator writes the measured report.

A new retry policy would need a new experiment version and new run IDs.

## Execute or resume the pilot

First create the fixed plan as documented in
`docs/runbooks/semantic-claims-llm-experiment.md`. Then run:

```powershell
python .\tools\run_semantic_claims_llm_pilot.py `
  --plan .\artifacts\semantic-claims-pilot\plan.json `
  --runs-root .\artifacts\semantic-claims-pilot\runs `
  --report .\artifacts\semantic-claims-pilot\report-001.json `
  --timeout-seconds 600
```

The default endpoint is `http://127.0.0.1:11434/api/chat`. Only the loopback endpoint
accepted by the bounded producer is allowed.

The command continues after individual runner failures so the final report can account
for every planned run. It exits with:

- `0` when all 15 runs verify as valid;
- `2` when a report was written but at least one run is missing, incomplete, or invalid;
- `1` when the plan, endpoint, output paths, or runner setup fail before a report can be
  safely produced.

## Resume behavior

Running the command again with the same `runs-root`:

- skips every existing final run directory;
- converts an abandoned `.in-progress` directory into an incomplete final attempt;
- executes only run IDs that have never produced either directory.

Use a new report filename on each collection attempt. Existing reports are never
overwritten.

## Execution record

Each attempted run receives `execution.json` with:

- the exact non-shell subprocess argument list;
- case, seed, endpoint, and timeout;
- return code and outcome;
- captured stdout/stderr, bounded to one million characters each;
- truncation flags;
- a domain-separated artifact hash.

This record explains infrastructure failure but does not replace verification of
`request.json`, raw Ollama response, candidate, or evaluation. The trusted experiment
report is still computed only from the bounded producer artifacts.

## CI boundary

CI never invokes Ollama. It tests command construction, failed-attempt finalization,
interruption recovery, no-retry behavior, and refusal to overwrite an existing report.
These are orchestration tests, not measured model results.
