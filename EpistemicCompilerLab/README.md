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

The first executable slice contains:

- repository-local sources and Prolog knowledge;
- short-lived SWI-Prolog CLI calls;
- JSON query results;
- separate teacher and student prompts;
- optional evidence and exception tails;
- regression tests and experiment records.

It does not include React, LogicLens epochs, UI Document generation, a web proxy, a persistent Prolog service or production sandboxing.

## Structure

- [`AGENTS.md`](AGENTS.md) — local work rules;
- [`prompts/student.md`](prompts/student.md) — fast student contract;
- [`prompts/teacher.md`](prompts/teacher.md) — slow teacher contract;
- [`prolog/knowledge.pl`](prolog/knowledge.pl) — executable fixture knowledge;
- [`prolog/entry.pl`](prolog/entry.pl) — JSON CLI;
- [`sources/materials.md`](sources/materials.md) — original fixture evidence;
- [`tests/knowledge_tests.pl`](tests/knowledge_tests.pl) — regression tests;
- [`experiments/README.md`](experiments/README.md) — controlled comparison protocol.

## Run

```powershell
swipl -q -s EpistemicCompilerLab/prolog/entry.pl -- current-material b 20260810
swipl -q -s EpistemicCompilerLab/prolog/entry.pl -- expand asd100500 evidence
swipl -q -s EpistemicCompilerLab/tests/knowledge_tests.pl -g "run_tests,halt"
```

Or use the thin wrapper:

```powershell
pwsh EpistemicCompilerLab/scripts/query.ps1 current-material b 20260810
```

`unknown` means the loaded knowledge is insufficient. It never means `false`.