# Document Evidence Service

This directory is the future separately deployable service for document ingestion, storage,
revisioning, deterministic parsing, canonical fragments, and protected byte access.

Read first:

- [service-specific agent rules](AGENTS.md);
- [architecture contract](../../docs/architecture/DOCUMENT_EVIDENCE_SERVICE_V0.md);
- [AppForge generation boundary](../../docs/architecture/APPFORGE_GENERATION_BOUNDARY_V0.md);
- [product platform direction](../../docs/architecture/PRODUCT_PLATFORM_V0.md);
- [PDF Link Pipeline v0](../../docs/architecture/PDF_LINK_PIPELINE_V0.md);
- [Source Proposal Pipeline v0](../../docs/architecture/SOURCE_PROPOSAL_PIPELINE_V0.md);
- [operational AppForge model](spec/document-evidence.md).

## Generate the replaceable CRUD contour

```powershell
.\services\document-evidence\generate-appforge.ps1 `
  -AppForgeRoot D:\projects\ChatPilotGroup\AppForge
```

The wrapper generates a production PostgreSQL backend under `Generated/`, verifies its manifest,
records AppForge/source hashes, and builds the generated solution. Generated output is never edited
by hand. Use `-SkipBuild` only for a generation-only diagnostic run.

The generated controllers are not the public service boundary yet. Workspace/object authorization,
safe upload, immutable bytes, processing jobs, parser adapters, and source anchors remain
handwritten modules around the generated persistence contour.

## Initial implementation plan

1. Generate and verify the operational CRUD contour from the Markdown model.
2. Isolate generated persistence/API behind handwritten application interfaces.
3. Add content-addressed local storage, then an S3-compatible implementation.
4. Port PDF contracts and tests from LogicLens without coupling to capsule activation.
5. Port multi-format adapters and reproducible fixtures from EngDoc Essential.
6. Add ChatPilot-derived access, filename, signature, quota, and storage-root guards.
7. Add durable processing jobs, manifests, hashes, and revocation invalidation.
8. Integrate LogicLens through generated clients and typed source anchors.

The first vertical slice is PDF upload or registered link -> immutable revision -> deterministic
fragments -> permitted retrieval. Model-based assertion proposals remain outside this service.