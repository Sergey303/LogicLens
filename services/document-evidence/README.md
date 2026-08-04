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

Verify an existing local package without regenerating it:

```powershell
.\services\document-evidence\verify-generated-package.ps1
```

The generated React application is an internal administration surface, not the final evidence UX.
Do not edit or commit files under `Generated/`; change the Markdown model or AppForge and regenerate.

Accepted evidence:

- [`appforge-production-trial-v0.json`](evidence/appforge-production-trial-v0.json) — first complete production package;
- [`appforge-lifecycle-package-v1.json`](evidence/appforge-lifecycle-package-v1.json) — lifecycle fields, fresh initial migration, and zero-warning AppForge proof.

The lifecycle proof is intentionally classified as a fresh-schema proof. Preservation of an existing
migration chain is tracked separately in ENG-152 because the proof command removed the previous local
package before generation. The CGR process itself returned exit code 1 only after all eight AppForge
stages completed: its post-proof snippet used the nonexistent PowerShell parameter
`Select-Object -Single`.

## Implemented handwritten boundary

`src/DocumentEvidence.Application` contains stable handwritten contracts, access policy ports, and
the facade. It has no EF Core, AppForge DTO, generated namespace, database-path, or blob-path dependency.
Authorization runs before any generated metadata or fragment lookup.

`src/DocumentEvidence.GeneratedAdapter` maps AppForge JSON, checks document/revision/workspace identity,
validates the generation receipt, and exposes an `IHttpClientBuilder` for credentials and telemetry.

```csharp
services
    .AddAppForgeGeneratedOperationalStore(generatedApiBaseAddress, receiptPath)
    .AddHttpMessageHandler<DocumentEvidenceServiceCredentialHandler>();
```

## Implemented immutable lifecycle

`src/DocumentEvidence.LocalStorage` implements a local content-addressed object store:

- addressing uses only lowercase SHA-256, never display names or caller paths;
- bytes are fsynced to random staging files before promotion;
- POSIX `link(2)` or Windows `CreateHardLinkW` provides create-once promotion;
- concurrent duplicate writes converge without overwrite;
- duplicate and read paths verify size and SHA-256;
- storage roots cannot overlap a configured web root or escape through input.

The application layer defines deterministic revision manifests, replay-safe upload completion,
processing-job lease/retry/terminal transitions, stale-token rejection, and coarse transaction/CAS ports.

`src/DocumentEvidence.Postgres` implements those ports with Npgsql 10 against PostgreSQL 17:

- a locked document row serializes revision numbering;
- StoredObject dedupe validates key, size, and media type;
- revision, processing job, document pointer, and handwritten outbox insert share one transaction;
- a unique conflict becomes a replay only when the original completion can be read back;
- processing transitions use compare-and-swap over state, attempt, availability, lease, and error;
- outbox failure rolls back every generated-table change.

The outbox schema is versioned in [`db/001_document_evidence_outbox.sql`](db/001_document_evidence_outbox.sql).
Repository quality runs application, generated-adapter, local-storage, and live PostgreSQL 17 integrations
with warnings as errors.

## Remaining implementation plan

1. Port the page-grounded PDF adapter and its provenance contracts.
2. Add outbox lease/dispatch and an S3-compatible immutable object store.
3. Prove AppForge upgrade migration continuity without dropping seeded data (ENG-152).
4. Port deterministic DOCX and XLSX adapters from EngDoc Essential.
5. Add access, filename, signature, quota, revocation, audit, and protected download guards.
6. Integrate LogicLens and EngDoc Essential through versioned generated clients.

The first vertical slice remains PDF upload or registered link -> immutable revision -> deterministic
fragments -> permitted retrieval -> LogicLens typed proposal. Model-based assertion proposals remain
outside the document service and cannot accept themselves.
