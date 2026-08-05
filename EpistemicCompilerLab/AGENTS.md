# Epistemic Compiler Lab agent instructions

## Isolation

All research work stays inside `EpistemicCompilerLab/` unless a task explicitly requires a repository-level link.

Do not modify the main LogicLens application, React renderer, epochs, UI Document contracts or Builder/Search implementation.

## Current scope

The active stage follows the completed E4 Codex→Qwen teacher-loop and compiled-frame replication. Design and test strict epistemic structures that separate source assertions, interpretation, epistemic status, decision policy and rendering.

Do not add probability, fuzzy membership, a web proxy, persistent service, authentication, model training or production sandboxing unless a later task supplies a separate benchmark and provenance contract.

The frozen compiled-frame replication v0, its cases hash and parser hash are immutable controls. New strict-epistemic work must use separate files and commands.

## Flagship publication protocol

Before changing benchmark, oracle, scorer, model runs, teacher loop, HOLDOUT, replication or manuscript artifacts, read:

1. [`scientific-roadmap/TARGET_PAPER_COMPILE_DONT_TEACH.md`](scientific-roadmap/TARGET_PAPER_COMPILE_DONT_TEACH.md);
2. [`scientific-roadmap/TARGET_PAPER_FULL_EXECUTION_PATH_AND_STRICT_AUDIT.md`](scientific-roadmap/TARGET_PAPER_FULL_EXECUTION_PATH_AND_STRICT_AUDIT.md);
3. [`scientific-roadmap/critical-protocols/README.md`](scientific-roadmap/critical-protocols/README.md);
4. the specific MUST/STOP protocol linked from that index.

The critical protocols are normative. A task, prompt or local implementation decision may not weaken them. Any benchmark-isolation violation invalidates the affected confirmatory run.

## Sources of truth

Use this order:

1. original files under `sources/`;
2. verified Prolog tests and benchmark oracle;
3. facts and rules under `prolog/`;
4. the current task;
5. prompts and explanatory documents.

A successful Prolog proof establishes a consequence of loaded facts and rules. It does not prove that source extraction was correct.

## Typed epistemic boundary

Keep these objects distinct:

- source assertion with provenance and explicit polarity;
- interpretation containing only values present in the request;
- derived epistemic status;
- decision and reason;
- natural-language rendering.

`unknown` means insufficient loaded evidence, never `false`. `refuted` requires explicit negative evidence. `conflicting` preserves incompatible positive and negative evidence instead of selecting one silently.

## Student

- reads only the representation assigned to the current mode;
- asks for missing obligatory fields;
- treats `unknown`, `refuted` and `conflicting` as different statuses;
- does not modify knowledge files;
- never receives hidden expected fields.

## Teacher

- reproduces the student's TRAIN error;
- receives only aggregate DEV metrics;
- never receives HOLDOUT or replication content during optimization;
- locates the earliest faulty layer before editing;
- checks original evidence;
- makes the smallest coherent change allowed by the current track;
- does not encode case IDs or full benchmark questions into candidates;
- records a testable hypothesis, expected effect and risk;
- stops when no safe reusable improvement is supported.

## Trusted evaluator

- stores raw model output before scoring;
- validates factor isolation and anti-memorization rules;
- runs Prolog regression tests for every knowledge or policy candidate;
- evaluates frozen hashes before model calls;
- preserves rejected candidates and runner failures as evidence;
- reports compiler, status, policy and renderer accuracy separately.

## Benchmark isolation

- Never include expected benchmark fields in a student prompt.
- Use expected fields only in deterministic scoring after raw output is stored.
- Teacher optimization may use labeled TRAIN cases, but never DEV or HOLDOUT content.
- Keep questions, model settings and scoring fixed while changing one factor.
- Preserve raw responses; do not repair them before scoring.
- Treat malformed JSON, invalid candidates and regression failures as results.
- Freeze parser, knowledge, policy, prompt, schema and cases hashes independently.
- Do not claim publication-grade improvement from one domain, model or seed.

## User launch convention

Commands must work from any PowerShell location:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' <action>
```

## Change discipline

- Prefer explicit predicates and small modules.
- Keep source evidence addressable from derived conclusions.
- Do not mix parser, knowledge, policy and renderer changes outside a declared combined ablation.
- Run `strict-epistemic-tests` before accepting strict epistemic changes.
- Use `doctor` to verify all deterministic assets.
- Use `runner-check` before model experiments.
- Preserve JSON status and field meanings.
- Keep model outputs under `experiments/model-runs/`; they are ignored by Git.
- Record only reviewed aggregate findings in the append-only run ledger.
- Emit `[CGR_ARTIFACT]` for complete packages instead of pasting large logs.
