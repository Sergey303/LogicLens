# LogicLens

LogicLens is a research system for building stable and query-specific interfaces over graph data through Prolog rules and LLM resolvers.

## Core idea

1. Archive cassettes and FOG files are imported once into Prolog data files.
2. A zero epoch contains imported facts, ontology labels, static rendering rules and the fixed React component ontology.
3. Later epochs add verified derived predicates, visibility rules and bindings between Prolog results and UI components.
4. `Builder` creates candidate epochs with Qwen2.5-Coder 7B or Codex and validates them through SWI-Prolog.
5. `Search` turns a natural-language question into temporary Prolog queries, result facts, view bindings and a dynamically assembled page.

## Planned layers

- archived source data;
- canonical Prolog facts and provenance;
- derived predicates and view rules;
- UI ontology and universal React renderer;
- epoch builder;
- query-specific search resolver;
- atomic editing through `AddFact` and `DeleteFact`.

## Independent research

- [`EpistemicCompilerLab/`](EpistemicCompilerLab/) — isolated experiments on compound teachers, weak local students, adaptive knowledge representations and SWI-Prolog execution. It does not define the main LogicLens UI architecture.

## Architecture

- [Architecture v0](docs/architecture-v0.md)
- [ADR-0001: Canonical fact, provenance, and change model](docs/adr/0001-canonical-fact-model.md)
- [ADR-0002: Layered subgraphs and repeated-path occurrences](docs/adr/0002-layered-subgraphs-and-occurrences.md)
- [ADR-0003: Minimal trusted UI Document](docs/adr/0003-minimal-ui-document.md)
- [ADR-0004: Traversal edge eligibility](docs/adr/0004-traversal-edge-eligibility.md)
- [ADR-0005: Generated Prolog epoch data](docs/adr/0005-generated-prolog-epoch-data.md)
- [ADR-0007: Restricted Prolog CLI](docs/adr/0007-prolog-cli-and-traversal-execution-contract.md)
- [ADR-0008: Portable active epoch package](docs/adr/0008-active-epoch-package.md)
- [ADR-0009: Crash-safe runtime state log](docs/adr/0009-crash-safe-runtime-state-log.md)
- [ADR-0010: Provider-neutral Builder candidate package](docs/adr/0010-builder-candidate-package.md)
- [ADR-0011: Reproducible Builder experiment envelope](docs/adr/0011-builder-experiment-envelope.md)
- [ADR-0020: Transactional runtime selection](docs/adr/0020-transactional-runtime-selection.md)
- [UI Document v0 JSON Schema](contracts/ui-document-v0.schema.json)
- [Epoch candidate v0 JSON Schema](contracts/epoch-candidate-v0.schema.json)
- [Builder task v0 JSON Schema](contracts/builder-task-v0.schema.json)
- [Builder run v0 JSON Schema](contracts/builder-run-v0.schema.json)
- [Builder provider experiment runbook](docs/runbooks/builder-provider-experiment.md)
- [A0 architecture exit criteria](docs/verification/a0-exit-criteria.md)
- [ENG-23 zero-epoch vertical slice plan](docs/plans/eng-23-zero-epoch-vertical-slice.md)

## Run the selected transactional runtime

A normal launcher must resolve the immutable package selected by `deployment/current.json`; it does not open `active-epoch` directly.

```powershell
python .\tools\run_transactional_runtime.py `
  --deployment-root .\artifacts\builder\eng-107-activation-002\deployment `
  request `
  --command health
```

Run the API and React application through the same verified pointer:

```powershell
python .\tools\run_logiclens.py `
  --deployment-root .\artifacts\builder\eng-107-activation-002\deployment
```

Finite verification mode builds the application, starts it against the selected package, checks the vertical slice and stops it:

```powershell
python .\tools\run_logiclens.py `
  --deployment-root .\artifacts\builder\eng-107-activation-002\deployment `
  --verify-only `
  --no-browser
```

The launcher validates pointer, journal, attestation and package hashes before starting SWI-Prolog. See [ADR-0020](docs/adr/0020-transactional-runtime-selection.md).

## Run the zero epoch fixture

With Python 3.12+, .NET 8, Node.js 24, npm, SWI-Prolog 9.0.4 and Git available on `PATH`:

```powershell
python .\tools\run_zero_epoch.py
```

This command is retained for the historical revision 0.0 fixture. It prepares a fresh portable epoch, builds the API and React renderer, starts both services, verifies the complete path and opens the entity page. See the [zero-epoch local runbook](docs/runbooks/zero-epoch-local-run.md).

CI uses the same fixture entry point in finite verification mode:

```powershell
python .\tools\run_zero_epoch.py --verify-only --no-browser
```

## Current executable foundation

ENG-30 adds the minimal .NET 8 canonical-fact foundation and a zero-dependency verifier.

```powershell
dotnet build .\LogicLens.sln
dotnet run --project .\tests\LogicLens.Core.Verification\LogicLens.Core.Verification.csproj
```

See [ENG-30 canonical facts and FactId v1](docs/development/eng-30-canonical-facts.md).

ENG-36 adds deterministic generation of Prolog epoch data:

```powershell
dotnet run --project .\tools\LogicLens.EpochCompiler\LogicLens.EpochCompiler.csproj -- `
  --output .\epochs\epoch-000 `
  --compiler-commit <git-sha>
```

The generated package is accepted only after byte-for-byte regeneration and SWI-Prolog tests.

ENG-24 adds the crash-safe runtime `ApplyDelta` store. Its verifier exercises idempotency, revision conflicts, replay, incomplete tails, durable-crash recovery, corruption rejection and one-writer enforcement:

```powershell
dotnet run --project .\tests\LogicLens.State.Verification\LogicLens.State.Verification.csproj
```

The runtime store is not connected to the HTTP editing surface or the active SWI graph yet.

ENG-46 adds the trusted provider-neutral input for Builder experiments. First build a portable baseline, then validate a proposal into an isolated candidate package and deterministic comparison report:

```powershell
python .\tools\build_active_epoch.py `
  --repository-root . `
  --output .\artifacts\epoch-000 `
  --engine-commit <git-sha>

python .\tools\build_epoch_candidate.py `
  --baseline .\artifacts\epoch-000 `
  --proposal .\fixtures\builder-candidate\valid `
  --schema .\contracts\epoch-candidate-v0.schema.json `
  --output .\artifacts\candidate-fixture `
  --report .\artifacts\candidate-fixture-comparison.json
```

The candidate contract is additive and cannot activate or replace the active epoch.

ENG-47 freezes one identical task and evidence workspace for Qwen and Codex, imports both through ENG-46, checks a hidden oracle and writes comparable run records:

```powershell
python .\tools\builder_experiment.py prepare `
  --baseline .\artifacts\epoch-000 `
  --task .\experiments\builder\eng-26-researcher-at-iis `
  --task-schema .\contracts\builder-task-v0.schema.json `
  --candidate-schema .\contracts\epoch-candidate-v0.schema.json `
  --output .\artifacts\builder-workspace
```

Use the [Builder provider experiment runbook](docs/runbooks/builder-provider-experiment.md) for the local Ollama/Qwen run, Codex proposal import and final comparison. Fixture runs prove the pipeline but are never reported as real provider results.

## Project tracking

Architecture verification and implementation tasks are tracked in the Linear project `LogicLens` inside ChatPilotGroup.
