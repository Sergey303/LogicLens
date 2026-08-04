# Document Evidence Service

This directory is the future separately deployable service for document ingestion, storage,
revisioning, deterministic parsing, canonical fragments, and protected byte access.

Read first:

- [service-specific agent rules](AGENTS.md);
- [architecture contract](../../docs/architecture/DOCUMENT_EVIDENCE_SERVICE_V0.md);
- [AppForge generation boundary](../../docs/architecture/APPFORGE_GENERATION_BOUNDARY_V0.md);
- [product platform direction](../../docs/architecture/PRODUCT_PLATFORM_V0.md);
- [PDF Link Pipeline v0](../../docs/architecture/PDF_LINK_PIPELINE_V0.md);
- [Source Proposal Pipeline v0](../../docs/architecture/SOURCE_PROPOSAL_PIPELINE_V0.md).

## Generated package

AppForge consumes [`spec/document-evidence.md`](spec/document-evidence.md) and writes the complete
replaceable production package under the ignored local `Generated/` directory:

```text
Generated/
  backend/          EF Core/PostgreSQL/API and migrations
  backend-contract/ canonical JSON contract
  frontend/         TypeScript bindings and React/PrimeReact resources
  frontend-app/     production Vite app and dist
  deploy/           Docker Compose production preset
  manifest/         package manifest and LogicLens receipt
  docs/             generated package runbook
```

Generate it from this repository with:

```powershell
.\services\document-evidence\generate-appforge.ps1 `
  -AppForgeRoot D:\projects\ChatPilotGroup\AppForge
```

The generated React application is an internal administration surface, not the final evidence UX.
Do not edit or commit files under `Generated/`; change the Markdown model or AppForge and regenerate.
The accepted first production trial is recorded in
[`evidence/appforge-production-trial-v0.json`](evidence/appforge-production-trial-v0.json).

## Implemented handwritten boundary

`src/DocumentEvidence.Application` contains stable handwritten contracts, access policy ports, and
the facade. It has no EF Core, AppForge DTO, generated namespace, database-path, or blob-path dependency.
Authorization runs before any generated metadata or fragment lookup.

`src/DocumentEvidence.GeneratedAdapter` is the replaceable infrastructure edge. It:

- maps AppForge JSON into handwritten records;
- verifies document, revision, and workspace identity before returning data;
- paginates fragments through the generated list contract without truncation;
- rejects inconsistent generated responses as contract violations;
- validates `logiclens-generation-receipt.json` and registers immutable generator identity for diagnostics;
- exposes `IHttpClientBuilder` so a host can add service credentials, retries, and telemetry.

```csharp
services
    .AddAppForgeGeneratedOperationalStore(generatedApiBaseAddress, receiptPath)
    .AddHttpMessageHandler<DocumentEvidenceServiceCredentialHandler>();
```

Application and adapter contract runners live under `tests/` and are mandatory in Repository quality.

## Remaining implementation plan

1. Add content-addressed local storage, then an S3-compatible implementation.
2. Add idempotent upload completion, outbox, leased processing jobs, retries, and terminal states.
3. Port PDF contracts and tests from LogicLens without coupling to capsule activation.
4. Port multi-format adapters and reproducible fixtures from EngDoc Essential.
5. Add ChatPilot-derived access, filename, signature, quota, and storage-root guards.
6. Add revocation invalidation, protected download plans, manifests, and hashes.
7. Integrate LogicLens and EngDoc Essential through versioned generated service clients.

The first vertical slice is PDF upload or registered link -> immutable revision -> deterministic
fragments -> permitted retrieval -> LogicLens typed proposal. Model-based assertion proposals remain
outside the document service and cannot accept themselves.
