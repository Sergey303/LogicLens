# ADR-0011: reproducible Builder experiment envelope

- Status: Proposed
- Linear: ENG-47, child of ENG-26
- Depends on: ADR-0007, ADR-0008, ADR-0010
- Scope: frozen tasks, provider workspaces, trusted oracle, run records and Qwen/Codex comparison

## Context

ADR-0010 gives every generated candidate the same untrusted proposal and validation boundary. ENG-26 still cannot compare Qwen and Codex fairly unless both receive the same task and evidence, bind to the same active package, preserve their provider metadata, and pass an independent correctness check.

Self-authored candidate tests are necessary but insufficient. A model can produce a rule and a matching test that agree with each other while both are wrong. Provider wrappers can also accidentally leak local paths, credentials, mutable active files, different evidence, or different criteria into one run.

## Decision

### One frozen task package

A Builder experiment task is a reviewed directory:

```text
task.json
prompt.md
oracle.json
```

`task.json` conforms to `builder-task-v0.schema.json` and pins:

- task identity and objective;
- expected active epoch and revision;
- candidate, CLI and UI contract versions;
- the exact rule, test and UI paths;
- required Prolog module, predicate and arity;
- required UI predicate and trusted component;
- closed evidence requests;
- public acceptance criteria.

`taskHash` covers canonical `task.json` plus normalized `prompt.md`. It does not cover provider output or measured run data.

### Public workspace, private oracle

`prepare` verifies the active portable package first, executes the task's closed CLI requests, and creates a provider workspace containing:

```text
workspace-manifest.json
task.json
prompt.md
contracts/epoch-candidate-v0.schema.json
evidence/*.json
```

Each evidence file contains the exact CLI request and deterministic response. The workspace manifest pins the task hash, oracle hash, active package hash and every public file hash.

`oracle.json` is never copied into the provider workspace. Its hash is disclosed so all runs can prove they were evaluated against the same oracle without revealing the expected answer to the provider adapter.

### Same provider permissions

A provider receives only the frozen workspace and writes an ADR-0010 proposal. It cannot select new CLI requests through the workspace, write into the active package, change the task, choose a validator, or activate a candidate.

Qwen through Ollama uses a loopback-only adapter. The adapter sends task, prompt and public evidence to `/api/chat`, requires one JSON object with exactly the three task-declared files, retains the raw request and response, and writes an ordinary candidate proposal.

Codex writes or exports the same proposal shape. It receives no privileged importer. Both paths converge on `builder_experiment.py import-run` and then ADR-0010 validation.

### Trusted import and hidden correctness oracle

`import-run` performs this order:

1. verify the active package manifest and hashes;
2. verify task and oracle identity;
3. recompute workspace file hashes;
4. reject a changed task, evidence file or active package;
5. require exactly the task-declared proposal files;
6. invoke the ADR-0010 candidate validator;
7. require the task-specific module, predicate export and exact UI binding;
8. execute the hidden oracle over the complete derived result set;
9. create the immutable run artifact only after every check passes.

The hidden oracle checks all returned `(Person, EvidenceFactIds)` pairs, not merely one expected success. This rejects extra results, missing results, duplicated results and incorrect or unsorted evidence.

### Run artifact

A successful run directory contains:

```text
run.json
comparison.json
proposal/
candidate/
raw/                 # optional
```

`run.json` conforms to `builder-run-v0.schema.json` and pins:

- run, task and provider identity;
- task, oracle and active package hashes;
- provider model;
- CLI calls, manual fixes, elapsed time and cost, each explicitly nullable when unknown;
- raw output hash and size when retained;
- proposal, candidate, candidate-package and comparison-report hashes;
- successful candidate and oracle validation.

No absolute path, endpoint, token, credential, timestamp, process ID or temporary directory is part of the run contract.

### Comparison without invented metrics

`compare` accepts only runs with identical task, oracle and active package hashes. Runs are sorted by run ID before serialization, so command argument order cannot change the report.

Fixture runs prove the pipeline but never produce a provider recommendation.

For exactly two non-fixture runs, automatic recommendation is allowed only when all four measured values are present and one run Pareto-dominates the other across:

```text
manual fixes
CLI calls
elapsed milliseconds
cost in USD
```

If metrics are missing or trade off, `recommendedRunId` remains null and the report explicitly requires human review. Passing the oracle is a prerequisite, not a score that can compensate for a failed candidate.

### Current experiment task

ENG-26 v0 asks both providers to derive `researcher_at_iis/2` from the real epoch-000 participation structure:

```text
Person <-participant- Participation -in-org-> IIS
                              -role-> "исследователь"@ru
```

The second argument must contain the sorted FactIds for participant, organization and role evidence. This task uses facts present in epoch-000 rather than an absent academic-rank assertion.

## Verification

ENG-47 must prove:

1. preparing the same task twice yields byte-identical public workspaces;
2. the provider workspace contains three deterministic evidence responses and no oracle;
3. two distinct fixture implementations pass the same candidate validator and hidden oracle;
4. importing the same provider run twice yields byte-identical run artifacts;
5. comparison is byte-identical regardless of run argument order;
6. fixture runs never produce a recommendation;
7. a rule and self-authored test that agree on the same false answer are rejected by the hidden oracle;
8. changed evidence and a changed task are rejected after workspace preparation;
9. extra proposal files are rejected even when ADR-0010 would otherwise allow their paths;
10. runs with different task hashes cannot be compared;
11. the offline Ollama response fixture becomes a normal proposal and passes trusted import;
12. the Ollama request excludes oracle data and retained machine endpoints;
13. non-loopback Ollama endpoints are rejected;
14. the active package remains unchanged throughout successful and failed runs;
15. workspace, both fixture runs and comparison report are retained as CI artifacts.

## Rejected alternatives

### Give providers the oracle tests

Rejected because the test becomes another prompt example and no longer independently detects a self-consistent false implementation.

### Compare provider prose or patches directly

Rejected because neither proves candidate package validity, evidence correctness or identical base state.

### Record missing metrics as zero

Rejected because zero would falsely imply measured speed, cost or intervention. Unknown values remain JSON null.

### Recommend by a weighted opaque score

Rejected because weights hide trade-offs and can produce a winner from incomplete measurements. v0 uses only strict Pareto dominance.

### Let the Ollama adapter call arbitrary URLs

Rejected because the local provider path does not need remote network capability or embedded credentials. Only loopback `/api/chat` is accepted.

## Consequences

- Qwen and Codex can be run at different times while remaining comparable by immutable hashes.
- Provider adapters cannot weaken candidate validation or see the trusted oracle.
- Raw model output can be audited without making it authoritative.
- Fixture runs exercise the entire path but are clearly excluded from provider conclusions.
- ENG-26 still requires the actual Qwen and Codex runs, measurement review, repair if needed and a recommended candidate epoch.
