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

## Architecture

- [Architecture v0](docs/architecture-v0.md)
- [ADR-0001: Canonical fact, provenance, and change model](docs/adr/0001-canonical-fact-model.md)
- [ADR-0002: Layered subgraphs and repeated-path occurrences](docs/adr/0002-layered-subgraphs-and-occurrences.md)

## Project tracking

Architecture verification and implementation tasks are tracked in the Linear project `LogicLens` inside ChatPilotGroup.