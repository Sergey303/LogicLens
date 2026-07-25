# Epistemic Compiler Lab agent instructions

## Isolation

All work for this research stays inside `EpistemicCompilerLab/` unless the task explicitly asks for a repository-level link.

Do not modify the main LogicLens application, its React renderer, epochs, UI Document contracts or Builder/Search implementation.

## Current scope

The current task is E2: compare one weak local model across controlled knowledge representations after the deterministic SWI-Prolog MVP and benchmark oracle have passed.

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

- reproduces the student's error;
- locates the earliest faulty layer before editing;
- checks original evidence;
- makes the smallest coherent change;
- adds a regression test;
- records model, prompt, commit and metrics.

## Benchmark isolation

- Never include `expectedAction`, `expectedStatus`, `expectedMaterial`, `expectedField`, `requiresTail` or `tailEntity` in a model prompt.
- Use expected benchmark fields only in deterministic validation and scoring after the model response is stored.
- Keep questions, model settings and scoring fixed while changing one representation.
- Preserve raw model responses; do not repair them before scoring.
- Treat malformed model JSON, bad query translation and unnecessary tails as experiment results.

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
- Do not mix changes to knowledge, prompts and model settings in one experiment unless their interaction is being measured.
- Run the `tests` launcher action before accepting a knowledge change.
- Use the `doctor` launcher action to verify deterministic assets and the CLI smoke test.
- Use `runner-check` before a model experiment.
- Preserve JSON CLI statuses and field meanings.
- Keep generated model outputs under `EpistemicCompilerLab/experiments/model-runs/`; they are ignored by Git by default.
- Record only reviewed aggregate findings in append-only `experiments/runs.jsonl`.
