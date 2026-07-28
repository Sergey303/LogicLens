# Epistemic Compiler Lab agent instructions

## Isolation

All work for this research stays inside `EpistemicCompilerLab/` unless the task explicitly asks for a repository-level link.

Do not modify the main LogicLens application, its React renderer, epochs, UI Document contracts or Builder/Search implementation.

## Current scope

The current task is E4: run a controlled local Codex→Qwen teacher loop after the deterministic SWI-Prolog MVP, representation comparison and benchmark-v1 planner experiments.

Do not add a web proxy, persistent service, authentication layer, model training or production sandbox unless a later task explicitly requires it.

## Sources of truth

Use this order:

1. original files under `sources/`;
2. verified Prolog tests and benchmark oracle;
3. facts and rules under `prolog/`;
4. the current task;
5. prompts and explanatory documents.

A successful Prolog proof establishes a consequence of loaded facts and rules. It does not prove that the source was extracted correctly.

## Roles

### Student

- reads only the representation assigned to the current mode;
- asks for missing obligatory fields;
- runs the smallest permitted CLI query in CLI modes;
- treats `unknown` as missing knowledge;
- opens evidence or exceptions only when needed;
- does not modify knowledge files.

### Teacher

- reproduces the student's TRAIN error;
- receives only aggregate DEV metrics;
- never receives HOLDOUT questions, answers or diagnostics;
- locates the earliest faulty layer before editing;
- checks original evidence;
- makes the smallest coherent change allowed by the current track;
- does not encode case IDs or full benchmark questions into candidates;
- records a short testable hypothesis, expected effect and risk;
- stops when no safe reusable improvement is supported.

### Trusted evaluator

- stores raw model output before scoring;
- validates change-track isolation and anti-memorization rules;
- runs Prolog regression tests for every candidate;
- selects the best epoch by DEV, then TRAIN, then smaller candidate size;
- evaluates HOLDOUT exactly once after model selection;
- preserves rejected candidates and runner failures as experiment evidence.

## Benchmark isolation

- Never include expected benchmark fields in a student prompt.
- Use expected fields only in deterministic validation and scoring after the student response is stored.
- Teacher optimization may use labeled TRAIN cases, but never DEV or HOLDOUT case content.
- Keep questions, model settings and scoring fixed while changing one factor.
- Preserve raw model responses; do not repair them before scoring.
- Treat malformed JSON, invalid candidates and regression failures as experiment results.
- Do not claim publication-grade improvement from the 18-case engineering pilot.

## User launch convention

Commands sent to the user must work from any PowerShell location.

Use the absolute launcher path:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' <action>
```

The launcher validates the checkout, enters `D:\projects\ChatPilotGroup\LogicLens`, performs the action and restores the caller's previous location.

## Change discipline

- Prefer explicit predicates and small modules.
- Keep source evidence addressable from derived facts.
- Do not mix changes to knowledge, prompts and model settings outside the declared combined ablation.
- Run the `tests` launcher action before accepting a knowledge change.
- Use the `doctor` launcher action to verify deterministic assets and the CLI smoke test.
- Use `runner-check` before a model experiment.
- Preserve JSON CLI statuses and field meanings.
- Keep generated model outputs under `EpistemicCompilerLab/experiments/model-runs/`; they are ignored by Git by default.
- Record only reviewed aggregate findings in append-only `experiments/runs.jsonl`.
- Emit `[CGR_ARTIFACT]` for complete run packages instead of pasting large logs.
