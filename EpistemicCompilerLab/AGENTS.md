# Epistemic Compiler Lab agent instructions

## Isolation

All work for this research stays inside `EpistemicCompilerLab/` unless the task explicitly asks for a repository-level link.

Do not modify the main LogicLens application, its React renderer, epochs, UI Document contracts or Builder/Search implementation.

## Current scope

The current task is the teacher–student SWI-Prolog research MVP.

Do not add a web proxy, persistent service, authentication layer or production sandbox unless a later task explicitly requires it.

## Sources of truth

Use this order:

1. original files under `sources/`;
2. verified Prolog tests;
3. facts and rules under `prolog/`;
4. the current task;
5. prompts and explanatory documents.

A successful Prolog proof establishes a consequence of loaded facts and rules. It does not prove that the source was extracted correctly.

## Roles

### Student

- reads approved knowledge;
- runs the smallest useful CLI query;
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

## Change discipline

- Prefer explicit predicates and small modules.
- Keep source evidence addressable from derived facts.
- Do not mix changes to knowledge, prompts and model settings in one experiment unless their interaction is being measured.
- Run all Prolog tests before accepting a knowledge change.
- Preserve JSON CLI statuses and field meanings.
- Keep generated or temporary experiment output out of the main LogicLens project paths.