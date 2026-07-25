# Epistemic Compiler Lab

`EpistemicCompilerLab/` is an independent research area inside the LogicLens repository.

The main LogicLens project uses LLM and Prolog to build React views over graph data. This lab studies a different, more abstract problem: how a slow compound teacher system can compile documents and verified knowledge into representations that a fast local student model can query, understand and improve.

## Research question

Can a strong or slow teacher system improve a weak local LLM by choosing:

- which knowledge to encode as facts, rules or external evidence;
- which representation and language the student receives;
- which optional knowledge tails the student should open;
- which diagnostic question to ask after an error;
- whether to fix a fact, rule, prompt, translation or training example?

## MVP boundary

The first executable slice contains repository-local sources, Prolog knowledge, short-lived SWI-Prolog CLI calls, JSON results, separate teacher/student prompts, optional evidence tails and regression tests.

It does not include React, LogicLens epochs, UI Document generation, a web proxy, a persistent Prolog service or production sandboxing.

## Structure

- [`AGENTS.md`](AGENTS.md) — local work rules;
- [`prompts/student.md`](prompts/student.md) — fast student contract;
- [`prompts/teacher.md`](prompts/teacher.md) — slow teacher contract;
- [`prolog/knowledge.pl`](prolog/knowledge.pl) — executable fixture knowledge;
- [`prolog/entry.pl`](prolog/entry.pl) — JSON CLI;
- [`sources/materials.md`](sources/materials.md) — original fixture evidence;
- [`tests/knowledge_tests.pl`](tests/knowledge_tests.pl) — regression tests;
- [`cases/README.md`](cases/README.md) — benchmark-v0 contract and scoring;
- [`cases/benchmark-v0.jsonl`](cases/benchmark-v0.jsonl) — fixed representation cases;
- [`experiments/README.md`](experiments/README.md) — controlled comparison protocol;
- [`experiments/runs.jsonl`](experiments/runs.jsonl) — confirmed environment and experiment runs.

## Windows setup

Install the Windows 64-bit stable build from:

`https://www.swi-prolog.org/download/stable`

Open a new PowerShell window and verify:

```powershell
swipl --version
```

The repository scripts also search the registry and standard installation folders when `PATH` is not yet refreshed.

## Run from any directory

The launcher validates the checkout and temporarily enters `D:\projects\ChatPilotGroup\LogicLens`.

Update `main` and verify everything:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' sync-doctor
```

Other actions:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' doctor
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' tests
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' cases
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' oracle
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' query current-material b 20260810
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' query expand asd100500 evidence
```

The doctor validates benchmark-v0, executes its deterministic Prolog oracle, runs all PL-Unit tests and performs a JSON CLI smoke test.

`unknown` means the loaded knowledge is insufficient. It never means `false`.
