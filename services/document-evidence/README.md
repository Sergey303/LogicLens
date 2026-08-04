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
replaceable production package under `Generated/`:

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
Do not edit files under `Generated/`; change the Markdown model or AppForge and regenerate.

## Handwritten implementation plan

1. Compose the generated operational package behind a handwritten service facade.
2. Add content-addressed local storage, then an S3-compatible implementation.
3. Add idempotent upload completion, outbox, leased processing jobs, retries, and terminal states.
4. Port PDF contracts and tests from LogicLens without coupling to capsule activation.
5. Port multi-format adapters and reproducible fixtures from EngDoc Essential.
6. Add ChatPilot-derived access, filename, signature, quota, and storage-root guards.
7. Add revocation invalidation, protected download plans, manifests, and hashes.
8. Integrate LogicLens and EngDoc Essential through versioned generated service clients.

The first vertical slice is PDF upload or registered link -> immutable revision -> deterministic
fragments -> permitted retrieval -> LogicLens typed proposal. Model-based assertion proposals remain
outside the document service and cannot accept themselves.
