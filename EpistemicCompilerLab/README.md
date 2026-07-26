# Epistemic Compiler Lab

`EpistemicCompilerLab/` is an independent research area inside the LogicLens repository.

The main LogicLens project uses LLM and Prolog to build React views over graph data. This lab studies a different problem: how a slow teacher can compile verified knowledge into representations that a fast local student model can query and improve.

## Research question

Can a strong teacher improve a weak local LLM by choosing:

- which knowledge becomes facts, rules or evidence;
- which representation the student receives;
- which optional tails the student should open;
- which diagnostic question follows an error;
- whether to fix a fact, rule, prompt, translation or example?

## Boundary

The lab contains repository-local sources, Prolog knowledge, short-lived SWI-Prolog CLI calls, JSON results, teacher/student prompts, optional evidence tails, regression tests and a local Ollama representation runner.

It does not include React, LogicLens epochs, UI Document generation, a web proxy, a persistent Prolog service, model training or production sandboxing.

## Structure

- [`AGENTS.md`](AGENTS.md) — local work rules;
- [`prolog/`](prolog/) — executable fixture knowledge and JSON CLI;
- [`sources/`](sources/) — original fixture evidence;
- [`representations/`](representations/) — alternative knowledge forms;
- [`runner/README.md`](runner/README.md) — local-model experiments;
- [`tests/`](tests/) — Prolog regression tests;
- [`cases/benchmark-v0.jsonl`](cases/benchmark-v0.jsonl) — immutable first comparison;
- [`cases/benchmark-v1.jsonl`](cases/benchmark-v1.jsonl) — teacher-frame contract;
- [`cases/BENCHMARK_V1.md`](cases/BENCHMARK_V1.md) — v1 rationale and semantics;
- [`experiments/`](experiments/) — protocol and append-only run ledger.

## Windows setup

Install the stable Windows x64 SWI-Prolog build from:

`https://www.swi-prolog.org/download/stable`

Then verify:

```powershell
swipl --version
ollama list
```

## Run from any directory

The launcher validates the checkout and temporarily enters `D:\projects\ChatPilotGroup\LogicLens`.

Update `main` and verify the deterministic lab:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' sync-doctor
```

Other deterministic actions:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' cases
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' cases-v1
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' tests
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' oracle
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' runner-check
```

## Benchmark versions

V0 is preserved exactly as the first five-mode baseline. It revealed that Prolog text improved status/action accuracy, while raw-question planning limited CLI execution.

V1 separates material selection, clarification, explanation and exception inspection. A teacher frame contains normalized intent and only values present in the question. Hidden expected plans are used solely for validation and scoring. They cannot introduce revision, date, entity or tail kind absent from that frame.

## CPU-safe local-model experiments

The first GPU attempt on the development workstation failed while allocating a CUDA host buffer. Experiments therefore create a separate Ollama profile with `num_gpu=0`, `num_ctx=2048` and `num_batch=64`. The source model remains unchanged.

Check the derived profile and JSON response:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' ollama-smoke 'qwen2.5-coder:7b'
```

Run one v0 representation and print failed-case diagnostics:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' representation-baseline markdown 'qwen2.5-coder:7b'
```

Run the historical v0 suite over all five representations:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' representation-suite 'qwen2.5-coder:7b'
```

The suite stores one JSONL run and summary per mode plus `comparison.json` and `comparison.csv` under a timestamped directory in `experiments/model-runs/`. Results remain local and are ignored by Git until aggregate findings are reviewed and copied into the append-only ledger.

Allowed v0 modes are `markdown`, `compact-json`, `prolog-text`, `cli` and `cli-tails`.

`unknown` means the loaded knowledge is insufficient. It never means `false`.
