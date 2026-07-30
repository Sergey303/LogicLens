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

The lab contains repository-local sources, Prolog knowledge, short-lived SWI-Prolog CLI calls, JSON results, teacher/student prompts, optional evidence tails, regression tests and local Ollama/Codex adapters.

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
- [`cases/teacher-loop-pilot-v0.jsonl`](cases/teacher-loop-pilot-v0.jsonl) — frozen 6/6/6 optimization pilot;
- [`research/TEACHER_STUDENT_EXPERIMENT.md`](research/TEACHER_STUDENT_EXPERIMENT.md) — measurement and article protocol;
- [`experiments/`](experiments/) — protocol and append-only run ledger.

## Windows setup

Install the stable Windows x64 SWI-Prolog build from:

`https://www.swi-prolog.org/download/stable`

Then verify:

```powershell
swipl --version
ollama list
codex --version
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

The teacher-loop pilot has 18 material-selection and clarification questions: 6 TRAIN, 6 DEV and 6 HOLDOUT. Codex receives labeled TRAIN diagnostics and aggregate DEV metrics. HOLDOUT is evaluated once after selecting the best epoch and never enters the teacher prompt.

## Local providers

Ollama experiments use a derived CPU-safe profile with `num_gpu=0`, `num_ctx=2048` and `num_batch=64`. The source model remains unchanged.

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' ollama-smoke 'qwen2.5-coder:7b'
```

The Codex adapter uses stdin, ephemeral execution, a read-only sandbox, ignored user config/project rules, strict JSON Schema, retained JSONL events and rejection of all tool calls. Omit the model so the authenticated ChatGPT session selects its supported default. Pass an explicit identifier only after verifying account support.

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' codex-smoke
```

Run the paired Codex planner-v1 experiment:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' planner-v1-codex-pair
```

Run the local Codex→Qwen optimization pilot. Safe defaults are combined prompt+Prolog, one teacher epoch and `qwen2.5-coder:7b`:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' teacher-loop
```

Longer ablation examples:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' teacher-loop prompt 3
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' teacher-loop prolog 3
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' teacher-loop combined 3 'qwen2.5-coder:7b'
```

The teacher loop stores every Qwen response, Codex candidate, validation result, epoch metric, selected candidate and final holdout result. It creates a sibling ZIP and prints the ChatGptRunner `[CGR_ARTIFACT]` marker, so `Attach output` includes the full run automatically.

Run the compiled decision-frame control:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' compiled-frame
```

This control deterministically extracts revision/date, marks absent inputs, executes the verified Prolog query and gives Qwen only the resulting decision frame. It reports frame accuracy separately from Qwen rendering accuracy. The current 18-case oracle is an engineering control, not publication-grade evidence of parser generalization.

Replication v0 was generated with parser source and old questions withheld, accepted without edits, and frozen by hash before Qwen evaluation:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' compiled-frame-replication
```

Run one historical v0 Ollama representation:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' representation-baseline markdown 'qwen2.5-coder:7b'
```

Run the historical v0 five-mode Ollama suite:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' representation-suite 'qwen2.5-coder:7b'
```

Generated runs live under timestamped directories in `experiments/model-runs/`. They remain local and ignored by Git until aggregate findings are reviewed and copied into the append-only ledger.

`unknown` means the loaded knowledge is insufficient. It never means `false`.
