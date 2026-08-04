# LogicLens agent contract

This file is the root instruction and documentation entry point for repository work.
More specific `AGENTS.md` files may narrow these rules inside their directories.

## Current architecture direction

- New knowledge authoring uses [Epistemic DSL v0](docs/architecture/EPISTEMIC_DSL_V0.md).
- Reusable verified knowledge is packaged through the
  [Capsule Contract v0](docs/architecture/CAPSULE_CONTRACT_V0.md).
- Runtime reasoning remains in SWI-Prolog and returns verified decision frames.
- New product work must not introduce dependencies on cassettes, FOG, XML ontologies,
  or Polar.DB. Existing references are historical until migrated.
- Operational application data uses PostgreSQL through EF Core unless an accepted ADR says otherwise.
- Local model calls use Ollama behind a narrow typed client boundary.

## Repository discipline

- Work on a task branch or worktree; never develop directly on `main`.
- Keep each commit coherent and independently reviewable.
- Do not mix generated-code changes with handwritten behavior changes.
- Do not rewrite unrelated files while fixing a local problem.
- Preserve public contracts unless the same change updates schemas, tests, and documentation.

## File size and decomposition

- New or modified handwritten files must contain no more than 150 physical lines.
- Generated files are excluded only when their path or suffix identifies them as generated.
- Do not use handwritten C# `partial` declarations to bypass the limit.
- Split by responsibility, public contract, or feature boundary instead of numbered fragments.
- A long existing file may remain untouched, but any substantial edit must first extract a coherent module.

## Generated-code boundary

- Generated code belongs under a `Generated/` directory or uses a recognised generated suffix.
- Handwritten projects may reference generated projects or public generated namespaces only.
- Generated projects must not depend on handwritten application projects.
- Never hand-edit generated output; change the schema, template, or generator and regenerate.
- AppForge output must remain a replaceable module, not the owner of domain decisions.

## Quality gate

Before committing changed files:

```powershell
python .\tools\quality\repository_guard.py --staged
ruff check <changed-python-files>
ruff format --check <changed-python-files>
```

CI applies the same rules to the pull-request diff. See
[Quality gates](docs/development/QUALITY_GATES.md).

## Documentation tree

Every new or modified Markdown file must be reachable through Markdown links from this file.
Do not create orphan decision records or status notes.

- [Repository overview](README.md)
- [Documentation map](docs/README.md)
  - [Linear project entry](docs/project/LINEAR.md)
  - [Product platform direction](docs/architecture/PRODUCT_PLATFORM_V0.md)
  - [Shared document evidence service](docs/architecture/DOCUMENT_EVIDENCE_SERVICE_V0.md)
  - [AppForge generation boundary](docs/architecture/APPFORGE_GENERATION_BOUNDARY_V0.md)
  - [Epistemic DSL v0](docs/architecture/EPISTEMIC_DSL_V0.md)
  - [Capsule Contract v0](docs/architecture/CAPSULE_CONTRACT_V0.md)
  - [Source Proposal Pipeline v0](docs/architecture/SOURCE_PROPOSAL_PIPELINE_V0.md)
  - [PDF Link Pipeline v0](docs/architecture/PDF_LINK_PIPELINE_V0.md)
  - [Quality gates](docs/development/QUALITY_GATES.md)
- [Document evidence service workspace](services/document-evidence/README.md)
  - [Service-specific agent rules](services/document-evidence/AGENTS.md)
- [Epistemic Compiler Lab rules](EpistemicCompilerLab/AGENTS.md)

## Shared document service boundary

The document evidence service is a separate deployable process used by LogicLens,
product applications, and EngDoc Essential.

It owns safe ingestion, immutable blobs, document revisions, deterministic extraction,
canonical fragments, processing state, access checks, retention, and source anchors.
It does not own domain assertions, capsule activation, Prolog decisions, product catalogues,
or final natural-language answers.

Consumers use generated OpenAPI clients and events. They do not read the service database or
blob paths directly. See the [service architecture](docs/architecture/DOCUMENT_EVIDENCE_SERVICE_V0.md).

## Model trust boundary

- A model may interpret a request, retrieve candidate evidence, propose typed records, or render a
  verified frame.
- A model may not accept its own proposal, activate a capsule, invent provenance, or strengthen a
  deterministic conclusion.
- RAG returns candidate source fragments, not accepted facts.
- RLM loops must be bounded, tool-allowlisted, logged, and terminate in a typed request or proposal.

## Testing expectations

- Every defect fix adds the narrowest useful regression test.
- Contract changes include positive, negative, unknown, and conflict cases when applicable.
- Document processing tests use reproducible fixtures and stable hashes.
- A green parser test does not prove semantic correctness; provenance and review gates remain required.