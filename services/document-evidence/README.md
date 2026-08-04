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

`src/DocumentEvidence.GeneratedAdapter` is the replaceable infrastructure edge. It maps AppForge JSON,
checks document/revision/workspace identity, validates the generation receipt, and exposes an
`IHttpClientBuilder` for service credentials, retries, and telemetry.

```csharp
services
    .AddAppForgeGeneratedOperationalStore(generatedApiBaseAddress, receiptPath)
    .AddHttpMessageHandler<DocumentEvidenceServiceCredentialHandler>();
```

## Implemented immutable lifecycle contracts

`src/DocumentEvidence.LocalStorage` implements a local content-addressed object store:

- addressing uses only lowercase SHA-256, never display names or caller paths;
- bytes are fsynced to random staging files before promotion;
- POSIX `link(2)` or Windows `CreateHardLinkW` provides create-once promotion;
- concurrent duplicate writes converge to one object without overwrite;
- duplicate and read paths verify size and SHA-256;
- storage roots cannot overlap a configured web root or escape through input.

The application layer also defines:

- deterministic revision manifests with canonical JSON and SHA-256 identity;
- replay-safe upload completion that checks idempotency before reading bytes;
- one coarse repository operation for revision, processing job, and outbox atomicity;
- immutable processing-job transitions for lease, expiry reclaim, retry backoff, success, and terminal failure;
- stale-token and expired-lease rejection.

Application, generated-adapter, and local-storage contract runners are mandatory in Repository quality
and build on .NET 10 with warnings as errors.

## Remaining implementation plan

1. Implement the PostgreSQL transaction behind `IDocumentLifecycleRepository`.
2. Add leased-job compare-and-swap persistence and outbox dispatch.
3. Add an S3-compatible immutable object-store implementation.
4. Port PDF contracts and tests without coupling to capsule activation.
5. Port deterministic DOCX and XLSX adapters from EngDoc Essential.
6. Add access, filename, signature, quota, revocation, audit, and protected download guards.
7. Integrate LogicLens and EngDoc Essential through versioned generated clients.

The first vertical slice remains PDF upload or registered link -> immutable revision -> deterministic
fragments -> permitted retrieval -> LogicLens typed proposal. Model-based assertion proposals remain
outside the document service and cannot accept themselves.
