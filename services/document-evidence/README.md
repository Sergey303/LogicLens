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

## Page-grounded PDF evidence vertical slice

`src/DocumentEvidence.Pdf` is a deterministic trusted adapter. It:

- validates byte limits, `%PDF-` signature, and optional pinned SHA-256 before Poppler;
- calls `pdfinfo` and `pdftotext -bbox-layout -enc UTF-8` through a narrow process port;
- emits canonical pages and blocks with reading order, bbox, word IDs, normalized text, and hashes;
- records artifact, parser version, parser configuration, and IR hashes;
- rejects PDFs with no usable native text instead of silently inventing evidence;
- contains no LLM or OCR path in trusted extraction.

Processing completion converts extracted blocks into deterministic fragment IDs and contiguous sequence
numbers. PostgreSQL atomically persists parser manifest, fragments, job success, and outbox event. A
stale lease leaves job, revision, fragments, and outbox unchanged.

Protected byte reads execute in this order:

```text
authorization -> workspace/revision metadata -> revocation -> immutable bytes
```

Denied access stops before metadata lookup. Revocation stops before object lookup. Physical storage keys
never cross the application boundary.

`PdfSourceProposalBridge` exports only selected blocks to the existing `source-fragment-v0` contract.
The fragment retains page, bbox, word IDs, Poppler version, artifact hash, and canonical text hash. The
same JSONL fixture is checked by C# and then passed through JSON Schema, grounding review, package
retention checks, and the real SWI-Prolog gate. Full PDF bytes, canonical IR, and the complete fragment
set are excluded from the accepted package.

Accepted PDF evidence:

- [`poppler-page-grounded-adapter-v1.json`](evidence/poppler-page-grounded-adapter-v1.json);
- [`pdf-source-proposal-bridge-v1.json`](evidence/pdf-source-proposal-bridge-v1.json).

## Deterministic OOXML adapters

`src/DocumentEvidence.Ooxml` is the shared trusted package boundary for DOCX and XLSX. It:

- enforces compressed, entry-count, per-entry, and total uncompressed byte limits;
- rejects unsafe, escaping, and case-insensitively duplicated part names;
- parses XML with DTD and external resolution disabled;
- rejects external trusted relationships;
- validates required content-type overrides;
- separates raw artifact SHA-256 from canonical package-entry SHA-256;
- canonicalizes core metadata timestamps to UTC.

`src/DocumentEvidence.Docx` emits stable paragraph and table-cell blocks with section, body, paragraph,
table, row, and column anchors. `src/DocumentEvidence.Xlsx` preserves workbook sheet order and stable
cell anchors while keeping formula, raw, cached, and display values separate. ISO date cells are
canonicalized to UTC. Formula evaluation, OCR, and model-based extraction are excluded from the trusted
adapters.

The initial EngDoc Sentinel provenance and reused deterministic patterns are recorded in
[`ooxml-adapter-scope-v0.json`](evidence/ooxml-adapter-scope-v0.json).

## Remaining implementation plan

1. Complete and validate deterministic DOCX/XLSX adapters and retained-evidence bridge (ENG-145).
2. Add outbox dispatch and an S3-compatible immutable object store.
3. Prove AppForge upgrade migration continuity without dropping seeded data (ENG-152).
4. Add quota, audit, protected download response, and revocation invalidation guards.
5. Publish versioned service clients and events for LogicLens and EngDoc Essential.

The vertical slice is document bytes -> immutable revision -> deterministic fragments -> permitted
retrieval -> selected evidence -> typed proposal -> verified SWI-Prolog decision frame. Models cannot
enter trusted extraction or accept their own proposals.
