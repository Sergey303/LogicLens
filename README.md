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
- [UI Document v0 JSON Schema](contracts/ui-document-v0.schema.json)
- [A0 architecture exit criteria](docs/verification/a0-exit-criteria.md)
- [ENG-23 zero-epoch vertical slice plan](docs/plans/eng-23-zero-epoch-vertical-slice.md)

## Run the zero epoch

With Python 3.12+, .NET 8, Node.js 24, npm, SWI-Prolog 9.0.4 and Git available on `PATH`:

```powershell
python .\tools\run_zero_epoch.py
```

The command prepares a fresh portable epoch, builds the API and React renderer, starts both services, verifies the complete path and opens the entity page. See the [zero-epoch local runbook](docs/runbooks/zero-epoch-local-run.md).

CI uses the same entry point in finite verification mode:

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

## Project tracking

Architecture verification and implementation tasks are tracked in the Linear project `LogicLens` inside ChatPilotGroup.
