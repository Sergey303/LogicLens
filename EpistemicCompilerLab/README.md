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
- [`runner/README.md`](runner/README.md) — five-mode local-model experiment;
- [`tests/`](tests/) — Prolog regression tests;
- [`cases/`](cases/) — benchmark-v0 and scoring contract;
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
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' tests
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' oracle
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' runner-check
```

## CPU-safe local-model baseline

The first GPU attempt on the development workstation failed while allocating a CUDA host buffer. The baseline therefore creates a separate Ollama profile with `num_gpu=0`, `num_ctx=2048` and `num_batch=64`. The source model remains unchanged.

Check the derived profile and JSON response:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' ollama-smoke 'qwen2.5-coder:7b'
```

Run and score all nine Markdown cases:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' representation-baseline markdown 'qwen2.5-coder:7b'
```

The command creates a timestamped JSONL run and summary under `experiments/model-runs/`. It prints both the base model and the derived execution model. Partial results are preserved and scored if a later model stage fails.

Allowed modes are `markdown`, `compact-json`, `prolog-text`, `cli` and `cli-tails`.

Lower-level `representation-run` expects an execution-model name, such as `epistemic-qwen2.5-coder-7b:cpu-v1`, rather than automatically creating a profile.

`unknown` means the loaded knowledge is insufficient. It never means `false`.
