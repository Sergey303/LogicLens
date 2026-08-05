# Document Evidence Service

This directory is the future separately deployable service for document ingestion, storage,
revisioning, deterministic parsing, canonical fragments, and protected byte access.

Read first:

- [service-specific agent rules](AGENTS.md);
- [architecture contract](../../docs/architecture/DOCUMENT_EVIDENCE_SERVICE_V0.md);
- [AppForge generation boundary](../../docs/architecture/APPFORGE_GENERATION_BOUNDARY_V0.md);
- [MVP HTTP boundary](docs/MVP_HTTP_BOUNDARY_V0.md);
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

`src/DocumentEvidence.Application` owns stable contracts and access-first policy.
`src/DocumentEvidence.GeneratedAdapter` maps AppForge JSON and validates generation receipts.
`src/DocumentEvidence.LocalStorage` provides content-addressed immutable objects with create-once
promotion, duplicate convergence, hash verification, root containment, and webroot isolation.

`src/DocumentEvidence.Postgres` implements Npgsql 10 lifecycle transactions against PostgreSQL 17:

- locked document rows serialize revision numbers;
- revision, job, document pointer, and handwritten outbox share one transaction;
- processing transitions use compare-and-swap over state, availability, attempt, and lease;
- outbox failure rolls back every generated-table change.

The outbox schema is [`db/001_document_evidence_outbox.sql`](db/001_document_evidence_outbox.sql).

## Page-grounded PDF evidence

`src/DocumentEvidence.Pdf` validates bytes before Poppler, calls `pdfinfo` and
`pdftotext -bbox-layout -enc UTF-8`, and emits canonical pages and blocks with reading order, bbox,
word IDs, normalized text, parser provenance, and stable hashes. Empty native-text PDFs fail closed.
LLMs and OCR are excluded from trusted extraction.

Processing completion persists parser manifest, fragments, job success, and outbox atomically. Protected
byte reads execute:

```text
authorization -> workspace/revision metadata -> revocation -> immutable bytes
```

`PdfSourceProposalBridge` exports only selected blocks to `source-fragment-v0`. The same JSONL fixture is
checked by C#, JSON Schema, grounding review, package retention checks, and real SWI-Prolog. Full PDF
bytes, canonical IR, and the complete fragment set are excluded.

Accepted PDF evidence:

- [`poppler-page-grounded-adapter-v1.json`](evidence/poppler-page-grounded-adapter-v1.json);
- [`pdf-source-proposal-bridge-v1.json`](evidence/pdf-source-proposal-bridge-v1.json).

## Deterministic OOXML adapters

`src/DocumentEvidence.Ooxml` is the shared trusted DOCX/XLSX package boundary. It enforces compressed,
entry-count, per-entry, and total uncompressed byte limits; rejects unsafe or duplicated part names;
parses XML with DTD and external resolution disabled; rejects external relationships; accepts safe
package-absolute OPC targets; validates content types; separates raw artifact SHA-256 from semantic
package identity; and canonicalizes core timestamps to UTC.

`src/DocumentEvidence.Docx` emits paragraph and table-cell blocks with section, body, paragraph, table,
row, and column anchors. `src/DocumentEvidence.Xlsx` preserves workbook sheet order and cell anchors
while keeping formula, raw, cached, and display values separate. Formula evaluation, OCR, and model
extraction are excluded.

Both adapters map into `ProcessingCompletionPayload`. Semantic package identity drives stable fragment
IDs while raw artifact identity remains in the parser manifest. Selected PDF, DOCX, and XLSX evidence
uses one `source-fragment-v0` contract with strict format-specific anchor branches.

A byte-identical EngDoc Sentinel XLSX fixture proves the real openpyxl package, source SHA-256, scenario
values, C# JSONL export, typed proposal, direct grounding, selected-only retention, SWI-Prolog, and
package verification.

Accepted OOXML evidence:

- [`ooxml-adapter-scope-v0.json`](evidence/ooxml-adapter-scope-v0.json);
- [`ooxml-adapter-acceptance-v0.json`](evidence/ooxml-adapter-acceptance-v0.json).

The final committed DOCX proof runs locally because the LogicLens Actions token cannot read the
neighboring private repository. See
[`EngDoc DOCX local acceptance gate`](docs/ENGDOC_DOCX_LOCAL_GATE.md) and run:

```powershell
.\services\document-evidence\verify-engdoc-docx.ps1
```

The ignored proof is written to
`.artifacts\document-evidence\engdoc-docx-local-proof-v0.json`.

## Remaining implementation plan

1. Execute the SHA-verified committed DOCX gate and retain its proof for ENG-145.
2. Add outbox dispatch and an S3-compatible immutable object store.
3. Prove AppForge upgrade migration continuity without dropping seeded data (ENG-152).
4. Complete production quotas, audit, read plans, and revocation invalidation.
5. Verify deterministic OpenAPI client regeneration and complete the ENG-148 demo receipt.

The vertical slice is document bytes -> immutable revision -> deterministic fragments -> permitted
retrieval -> selected evidence -> typed proposal -> verified SWI-Prolog decision frame. Models cannot
enter trusted extraction or accept their own proposals.
