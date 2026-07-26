# Qwen-only Builder runbook

This path runs one real LogicLens Builder attempt with local `qwen2.5-coder:7b`
through Ollama. It does not invoke Codex, does not weaken the trusted candidate
validator, and never activates a candidate epoch.

## Prerequisites

- Python 3.12+
- .NET 8
- SWI-Prolog 9.0.4
- Git
- local Ollama with `qwen2.5-coder:7b`

Run the command from the repository root.

## One-command run

Choose a new empty output directory for every attempt:

```powershell
python .\tools\run_builder_qwen_only.py `
  --output .\artifacts\builder\eng-52-qwen-001 `
  --qwen-model qwen2.5-coder:7b
```

The runner:

1. builds a fresh portable active epoch;
2. prepares the frozen public Builder workspace;
3. calls only the loopback Ollama adapter;
4. preserves the raw request and raw model response;
5. imports a syntactically valid proposal through the unchanged trusted
   candidate validator and hidden oracle;
6. writes `qwen-only-summary.json`.

## Result states

- `passed`: the proposal passed candidate validation and the hidden oracle;
- `rejected`: Qwen returned a preserved response, but the adapter, candidate
  validator, or hidden oracle rejected it;
- `infrastructure-failed`: no provider response was preserved or a required
  preparation stage failed.

A rejection is a measured model result and returns exit code `0`.
Infrastructure failure returns a non-zero exit code.

## Artifacts

```text
eng-52-qwen-001/
  active-epoch/
  workspace/
  qwen-provider/
    proposal/                 # present only when adapter parsing passed
    raw/request.json
    raw/provider-output.json
  qwen-run-001/               # present only after trusted import passed
  qwen-only-summary.json
```

Do not edit or reuse an existing attempt directory. Keep rejected raw responses
as evidence and run the next attempt in a new directory.

## Prompt boundary for the 7B model

The frozen task prompt explicitly states that `.pl` means SWI-Prolog, never
Perl. It also supplies syntax-only contracts for `epoch_data:fact/4`, `iri/1`,
language literals, `sort/2`, plunit, and the trusted UI binding shape.

These instructions clarify the programming-language and file contracts only.
They do not expose the hidden oracle, bypass validation, or provide
provider-specific acceptance exceptions.
