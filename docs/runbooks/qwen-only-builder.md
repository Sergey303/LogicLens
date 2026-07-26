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
  --output .\artifacts\builder\qwen-attempt-001 `
  --qwen-model qwen2.5-coder:7b `
  --context-tokens 16384 `
  --output-tokens 2048
```

`16384` context tokens and `2048` output tokens are the reviewed defaults and
may be omitted. The accepted ranges are `4096..32768` and `256..8192`.

The runner:

1. builds a fresh portable active epoch;
2. prepares the frozen public Builder workspace;
3. calls only the loopback Ollama adapter;
4. sends `options.num_ctx` and `options.num_predict` explicitly;
5. sends an exact JSON Schema in Ollama `format`, requiring exactly the three
   task-declared file keys and string contents;
6. repeats the schema and short mandatory language, file, test and UI contract
   after all public evidence;
7. preserves the raw request and raw model response;
8. imports a syntactically valid proposal through the unchanged trusted
   candidate validator and hidden oracle;
9. writes `qwen-only-summary.json` with both reviewed token budgets.

## Why both token budgets are explicit

The frozen ENG-26 request is much larger than Ollama's common default context.
A real earlier run retained a roughly 28,000-character request but reported
`prompt_eval_count` around 2050. Ollama had silently discarded the beginning,
including the SWI-Prolog-not-Perl contract, and Qwen repeated its earlier Perl
answer.

A later full-context run returned malformed JSON with an unterminated file
content string. The output log alone could not distinguish a generation limit
from incorrect escaping. The adapter therefore now:

- supplies an exact JSON Schema instead of generic JSON mode;
- fixes the maximum generated token count explicitly;
- checks Ollama completion metadata;
- records structured diagnostics without modifying the model response.

If the reported prompt token count leaves fewer than 512 reviewed tokens for
the answer, the adapter preserves the response, writes
`raw/adapter-result.json` with `status: context-limited`, and fails the run as an
infrastructure problem.

If Ollama reports an output-length stop, the adapter writes
`status: output-limited` with `done_reason`, `eval_count`, and the reviewed
output budget. This is also an infrastructure failure.

If `message.content` is malformed JSON, the raw response is preserved and the
adapter writes `status: invalid-json` with completion metadata, content byte
length, and JSON line, column and character position. The adapter never closes
strings, inserts braces, repairs escaping, or otherwise changes model output.
Malformed JSON remains a measured model rejection.

## Result states

- `passed`: the proposal passed candidate validation and the hidden oracle;
- `rejected`: Qwen received the reviewed request and returned a preserved
  response, but adapter validation, candidate validation, or the hidden oracle
  rejected it;
- `infrastructure-failed`: preparation failed, no provider response was
  preserved, the prompt reached the configured context boundary, or generation
  reached the reviewed output limit.

A genuine rejection is a measured model result and returns exit code `0`.
Infrastructure failure returns a non-zero exit code.

## Artifacts

```text
qwen-attempt-001/
  active-epoch/
  workspace/
  qwen-provider/
    proposal/                 # present only when adapter parsing passed
    raw/request.json
    raw/provider-output.json
    raw/adapter-result.json   # only for classified adapter failures
  qwen-run-001/               # present only after trusted import passed
  qwen-only-summary.json
```

Do not edit or reuse an existing attempt directory. Keep rejected,
context-limited and output-limited raw responses as evidence and run the next
attempt in a new directory.

## Prompt boundary for the 7B model

The frozen task prompt explicitly states that `.pl` means SWI-Prolog, never
Perl. It also supplies syntax-only contracts for `epoch_data:fact/4`, `iri/1`,
language literals, `sort/2`, plunit, and the trusted UI binding shape. A compact
version of the same mandatory constraints is placed at the end of the provider
request so it remains visible after the evidence.

For plunit, distinguish directives from test cases:

```prolog
:- begin_tests(module_name).
:- use_module('../rules/candidate_rule.pl').

test(case_name) :-
    assertion(true).

:- end_tests(module_name).
```

`begin_tests/1`, `use_module/1`, and `end_tests/1` are directives. A test case
is an ordinary clause and must not be written as `:- test(...)`. The trusted
validator deliberately keeps `test` outside its directive allowlist.

These instructions clarify the programming-language, file and transport
contracts only. They do not expose the hidden oracle, bypass validation, or
provide provider-specific acceptance exceptions.
