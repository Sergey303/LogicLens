# Product platform direction v0

Status: proposed integration baseline.

## Decision

LogicLens becomes the trusted knowledge and reasoning foundation for several product surfaces.
The first commercial vertical is a technical-product knowledge assistant; EngDoc Essential remains
the document-control vertical. They share contracts and infrastructure without becoming one UI.

## Fixed choices

- PostgreSQL is the operational application store.
- EF Core owns migrations, writes, workflow, and ordinary reads for the MVP.
- Dapper is not required until profiling or query complexity proves a specific need.
- SWI-Prolog executes strict rules, evidence selection, and decision policies.
- Epistemic DSL is the authored knowledge and uncertainty language.
- Capsules package bounded verified knowledge; active epochs select runtime versions.
- Ollama is the only model provider required for the MVP.
- RAG retrieves candidate source fragments; bounded RLM may orchestrate complex investigations.

## Explicitly removed from new product architecture

New product modules must not depend on:

- cassettes;
- FOG;
- XML ontologies;
- Polar.DB;
- a graph database as an assumed source of truth;
- autonomous LLM engineering decisions.

Historical import paths may remain while their replacement is verified.

## Runtime shape

```text
React / PrimeReact
        |
ASP.NET Core product API
        |
PostgreSQL + EF Core ---- Document Evidence Service
        |                         |
typed query / frame          blobs, revisions,
        |                    fragments, extraction
SWI-Prolog runtime
        |
verified decision frame
        |
Ollama renderer or product UI
```

## Product modules

The product application owns:

- catalogue and product identity;
- aliases and typed product attributes;
- search and comparison workflows;
- manager handoff and editorial workflow;
- user permissions and product-specific audit.

LogicLens owns:

- epistemic contracts;
- capsule compilation and validation;
- Prolog execution and evidence DAGs;
- verified decision frames;
- active epoch selection.

The document evidence service owns documents and source anchors. Its boundary is defined in
[Document Evidence Service v0](DOCUMENT_EVIDENCE_SERVICE_V0.md).

## Search composition

Search is composed, not replaced by one technique:

1. exact and normalized aliases for identifiers;
2. PostgreSQL filters for typed parameters;
3. RAG over permitted document fragments;
4. SWI-Prolog for applicability, conflicts, unknowns, and decisions;
5. optional bounded RLM for multi-step evidence gathering.

RAG scores are retrieval metadata. They are not fact confidence or probability of truth.

## Model boundary

The MVP uses two narrow interfaces:

- structured generation through Ollama `/api/chat`;
- embeddings through an Ollama embedding endpoint.

The model may interpret, propose, and render. It may not activate knowledge, calculate epistemic
values, invent provenance, or strengthen a verified conclusion.

## Deployment direction

Start as a modular product application plus separately deployable document service and SWI-Prolog
runtime. Do not introduce microservices for catalogue, comparison, or editorial workflow before a
measured scaling or ownership boundary exists.
