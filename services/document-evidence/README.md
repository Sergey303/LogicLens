# Document Evidence Service

This directory is the future separately deployable service for document ingestion, storage,
revisioning, deterministic parsing, canonical fragments, and protected byte access.

Read first:

- [service-specific agent rules](AGENTS.md);
- [architecture contract](../../docs/architecture/DOCUMENT_EVIDENCE_SERVICE_V0.md);
- [AppForge generation boundary](../../docs/architecture/APPFORGE_GENERATION_BOUNDARY_V0.md);
- [PDF Link Pipeline v0](../../docs/architecture/PDF_LINK_PIPELINE_V0.md);
- [Source Proposal Pipeline v0](../../docs/architecture/SOURCE_PROPOSAL_PIPELINE_V0.md).

## Generated package

AppForge consumes [`spec/document-evidence.md`](spec/document-evidence.md) and writes the replaceable
production package under ignored local `Generated/`:

```text
Generated/
  backend/          EF Core/PostgreSQL/API and migrations
  backend-contract/ canonical JSON contract
  frontend/         TypeScript bindings and React/PrimeReact resources
  frontend-app/     production Vite app and dist
  deploy/           Docker Compose production preset
  manifest/         package manifest and LogicLens receipt
```

```powershell
.\services\document-evidence\generate-appforge.ps1 `
  -AppForgeRoot D:\projects\ChatPilotGroup\AppForge
.\services\document-evidence\verify-generated-package.ps1
```

Do not edit or commit `Generated/`. Accepted generation evidence:

- [`appforge-production-trial-v0.json`](evidence/appforge-production-trial-v0.json);
- [`appforge-lifecycle-package-v1.json`](evidence/appforge-lifecycle-package-v1.json);
- [`strict-generated-package-proof-v1.json`](evidence/strict-generated-package-proof-v1.json).

The accepted lifecycle package is a fresh-schema proof. Upgrade migration continuity is ENG-152.

## Handwritten boundary and lifecycle

`src/DocumentEvidence.Application` owns stable contracts and access-first policy. It has no EF Core,
AppForge DTO, generated namespace, database-path, or blob-path dependency.

`src/DocumentEvidence.GeneratedAdapter` maps AppForge JSON, checks document/revision/workspace identity,
validates generation receipts, and exposes an `IHttpClientBuilder` for credentials and telemetry.

`src/DocumentEvidence.LocalStorage` provides content-addressed immutable local objects:

- lowercase SHA-256 addressing, never display names or caller paths;
- fsynced random staging files;
- POSIX `link(2)` or Windows `CreateHardLinkW` create-once promotion;
- concurrent duplicate convergence without overwrite;
- size/hash verification on duplicate writes and reads;
- storage-root containment and webroot isolation.

`src/DocumentEvidence.Postgres` implements Npgsql 10 lifecycle transactions against PostgreSQL 17:

- locked document rows serialize revision numbers;
- revision, job, document pointer, and handwritten outbox share one transaction;
- unique conflicts become replay only after reading the original completion;
- processing transitions use compare-and-swap over state, attempt, availability, lease, and error;
- outbox failure rolls back every generated-table change.

The outbox schema is [`db/001_document_evidence_outbox.sql`](db/001_document_evidence_outbox.sql).

## Page-grounded PDF adapter

`src/DocumentEvidence.Pdf` is a deterministic trusted adapter. It:

- validates byte limits, `%PDF-` signature, and optional pinned SHA-256 before Poppler;
- calls `pdfinfo` and `pdftotext -bbox-layout -enc UTF-8` through a narrow process port;
- emits canonical pages and blocks with reading order, bbox, word IDs, normalized text, and hashes;
- records artifact, parser version, parser configuration, and IR hashes;
- rejects PDFs with no usable native text instead of silently inventing evidence;
- retains only explicitly selected blocks for downstream packages;
- contains no LLM or OCR path in trusted extraction.

Validation includes fake-process security/determinism contracts and a real Ubuntu Poppler integration.
The accepted real proof is
[`poppler-page-grounded-adapter-v1.json`](evidence/poppler-page-grounded-adapter-v1.json).

## Remaining implementation plan

1. Persist PDF fragments and parser manifests through processing completion.
2. Bridge retained PDF evidence into the source-proposal/SWI-Prolog gate.
3. Prove revocation and access denial before byte lookup or streaming.
4. Add outbox dispatch and an S3-compatible immutable object store.
5. Prove AppForge upgrade migration continuity without dropping seeded data (ENG-152).
6. Port deterministic DOCX and XLSX adapters from EngDoc Essential.
7. Add quota, audit, protected download, and revocation invalidation guards.

The vertical slice remains PDF upload or registered link -> immutable revision -> deterministic fragments
-> permitted retrieval -> LogicLens typed proposal. Models cannot enter trusted extraction or accept their
own proposals.
