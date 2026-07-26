# Builder provider experiment runbook

This runbook prepares one frozen task, runs local Qwen through Ollama and Codex through the Codex CLI, validates both through the same trusted pipeline, and compares successful runs.

The commands do not activate an epoch.

## Prerequisites

- Python 3.12+
- .NET 8
- SWI-Prolog 9.0.4
- Git
- for Qwen: local Ollama with `qwen2.5-coder:7b`
- for Codex: Codex CLI installed, `codex login` completed, and an explicit available model identifier

Run commands from the repository root.

## Fast path: run the real pair with one command

Choose a new empty output directory and pass the exact Codex model identifier used for the experiment:

```powershell
python .\tools\run_builder_provider_pair.py `
  --output .\artifacts\builder\eng-48-real-pair `
  --codex-model gpt-5.6
```

The command builds one baseline, prepares one frozen workspace, runs Qwen through loopback Ollama, runs Codex through `codex exec`, imports both proposals through the same trusted validator and hidden oracle, and writes the comparison. It never activates a candidate.

The Codex adapter runs with an ephemeral session, read-only sandbox, no approvals, no user configuration, no project rules, and a strict output schema. The complete provider input is passed through stdin, so Windows command-line length does not truncate it. Any Codex tool invocation or frozen-workspace change rejects the run.

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

Run Codex non-interactively against the same frozen workspace. The model identifier is required so the retained provider metadata cannot silently follow a changing local default:

```powershell
python .\tools\run_builder_codex.py `
  --workspace .\artifacts\builder\workspace `
  --output .\artifacts\builder\codex-provider `
  --run-id codex-run-001 `
  --model gpt-5.6
```

Use an actually available model and retain its exact identifier. The adapter writes only the three task-declared proposal files, preserves the final JSON response and Codex JSONL events, records elapsed time, and leaves unknown subscription cost absent so trusted import represents it as `null`.

Do not copy `oracle.json` into the Codex workspace. Do not edit the task or evidence after the workspace is prepared. The adapter rejects a Codex run that invokes tools or changes any frozen-workspace byte.

Import the proposal:

```powershell
python .\tools\builder_experiment.py import-run `
  --baseline .\artifacts\builder\active-epoch `
  --task $Task `
  --task-schema .\contracts\builder-task-v0.schema.json `
  --candidate-schema .\contracts\epoch-candidate-v0.schema.json `
  --run-schema .\contracts\builder-run-v0.schema.json `
  --workspace .\artifacts\builder\workspace `
  --proposal .\artifacts\builder\codex-provider\proposal `
  --raw-output .\artifacts\builder\codex-provider\raw\provider-output.json `
  --output .\artifacts\builder\codex-run-001 `
  --run-id codex-run-001
```

Trusted import retains the final Codex response as raw provider evidence. The separate JSONL event stream remains beside the provider proposal for audit and must never contain credentials or API keys.

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
