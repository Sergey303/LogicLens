# Builder provider experiment runbook

This runbook prepares one frozen task, runs local Qwen through Ollama or imports a Codex proposal, validates both through the same trusted pipeline, and compares successful runs.

The commands do not activate an epoch.

## Prerequisites

- Python 3.12+
- .NET 8
- SWI-Prolog 9.0.4
- Git
- for Qwen: local Ollama with `qwen2.5-coder:7b`

Run commands from the repository root.

## 1. Build the active baseline

```powershell
$Commit = git rev-parse HEAD
python .\tools\build_active_epoch.py `
  --repository-root . `
  --output .\artifacts\builder\active-epoch `
  --engine-commit $Commit
```

The output must be a fresh directory. Do not use `epochs\epoch-000` as the output.

## 2. Prepare the frozen provider workspace

```powershell
$Task = '.\experiments\builder\eng-26-researcher-at-iis'
python .\tools\builder_experiment.py prepare `
  --baseline .\artifacts\builder\active-epoch `
  --task $Task `
  --task-schema .\contracts\builder-task-v0.schema.json `
  --candidate-schema .\contracts\epoch-candidate-v0.schema.json `
  --output .\artifacts\builder\workspace
```

The workspace contains the task, prompt, candidate schema and deterministic public evidence. It intentionally does not contain `oracle.json`.

Record the printed task, oracle and active package hashes. Both providers must use this exact workspace.

## 3A. Produce the Qwen proposal through local Ollama

```powershell
python .\tools\run_builder_ollama.py `
  --workspace .\artifacts\builder\workspace `
  --output .\artifacts\builder\qwen-provider `
  --run-id qwen-run-001 `
  --model qwen2.5-coder:7b
```

The adapter accepts only a loopback Ollama `/api/chat` endpoint. It retains:

```text
qwen-provider/
  proposal/
  raw/request.json
  raw/provider-output.json
```

The raw model response is evidence, not trusted code. Import it next.

```powershell
python .\tools\builder_experiment.py import-run `
  --baseline .\artifacts\builder\active-epoch `
  --task $Task `
  --task-schema .\contracts\builder-task-v0.schema.json `
  --candidate-schema .\contracts\epoch-candidate-v0.schema.json `
  --run-schema .\contracts\builder-run-v0.schema.json `
  --workspace .\artifacts\builder\workspace `
  --proposal .\artifacts\builder\qwen-provider\proposal `
  --raw-output .\artifacts\builder\qwen-provider\raw\provider-output.json `
  --output .\artifacts\builder\qwen-run-001 `
  --run-id qwen-run-001
```

A successful import means both candidate validation and the hidden oracle passed.

## 3B. Produce and import the Codex proposal

Give Codex the contents of the frozen workspace directory. It must create only:

```text
codex-provider/
  proposal.json
  files/
    rules/candidate_researcher_at_iis.pl
    tests/candidate_researcher_at_iis_tests.pl
    ui/researcher-at-iis.json
```

Use this provider metadata in `proposal.json`:

```json
{
  "kind": "codex",
  "name": "codex",
  "model": "<actual model identifier>",
  "runId": "codex-run-001"
}
```

Do not copy `oracle.json` into the Codex workspace. Do not edit the task or evidence after the workspace is prepared.

When the proposal is ready:

```powershell
python .\tools\builder_experiment.py import-run `
  --baseline .\artifacts\builder\active-epoch `
  --task $Task `
  --task-schema .\contracts\builder-task-v0.schema.json `
  --candidate-schema .\contracts\epoch-candidate-v0.schema.json `
  --run-schema .\contracts\builder-run-v0.schema.json `
  --workspace .\artifacts\builder\workspace `
  --proposal .\artifacts\builder\codex-provider `
  --output .\artifacts\builder\codex-run-001 `
  --run-id codex-run-001
```

A raw Codex transcript may be passed through `--raw-output <file>` when a stable export is available. Never place credentials or API keys in that file.

## 4. Compare successful runs

```powershell
python .\tools\builder_experiment.py compare `
  --run-schema .\contracts\builder-run-v0.schema.json `
  --run .\artifacts\builder\qwen-run-001 `
  --run .\artifacts\builder\codex-run-001 `
  --output .\artifacts\builder\provider-comparison.json
```

The comparison refuses runs with different task, oracle or active package hashes.

A recommendation is produced only when both non-fixture runs passed and all four metrics are present, and one run is no worse on every metric while being better on at least one. Otherwise the report leaves `recommendedRunId` null and requires human review.

## 5. Record manual repair honestly

When a proposal needs a manual change:

1. preserve the original provider output;
2. copy the proposal into a new run ID;
3. increment `metrics.manualFixes`;
4. describe the repair in `notes`;
5. import the repaired proposal as a separate run;
6. compare original accepted runs and repaired runs without overwriting artifacts.

A rejected proposal has no successful `run.json`. Keep its raw provider output and validator log separately; do not manufacture a passed envelope.

## Safety checks

Stop when any of these differ between Qwen and Codex:

- `taskHash`;
- `oracleHash`;
- `basePackageHash`;
- candidate, CLI or UI contract version;
- workspace file hashes.

Do not bypass `import-run`, run provider code inside the active epoch, expose the oracle, add provider-specific validation exceptions, or activate a candidate from this workflow.
