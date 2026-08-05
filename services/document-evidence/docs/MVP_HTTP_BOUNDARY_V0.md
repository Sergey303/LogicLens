# MVP HTTP boundary v0

Status: service boundary verified; ENG-148 end-to-end proof implemented and awaiting execution.

## Consumer contract

Consumers use [`document-evidence-v1.json`](../openapi/document-evidence-v1.json) and the isolated
`DocumentEvidence.Client` project. They do not reference Application, Postgres, LocalStorage, AppForge
generated entities, database tables, or object keys.

The first versioned operations are:

```text
PUT /api/v1/workspaces/{workspaceId}/documents/{documentId}/revisions
GET /api/v1/workspaces/{workspaceId}/documents/{documentId}
GET /api/v1/workspaces/{workspaceId}/revisions/{revisionId}/fragments
```

Upload uses a raw request body. `X-Actor-Id`, `X-File-Name`, `Idempotency-Key`, `X-Source-Kind`,
`Content-Type`, and optional `Content-Length` are explicit parts of the contract.

## Trusted upload ordering

The HTTP application adapter routes upload bytes through `SecureDocumentUploadService`:

```text
authorization
  -> hourly actor/workspace request quota
  -> safe display-name normalization
  -> bounded in-memory quarantine
  -> media/signature validation
  -> independent workspace daily byte quota
  -> idempotent immutable upload lifecycle
  -> minimal audit record
```

The audit DTO has no object key, local path, display name, or idempotency key.

## Executable contracts

- Security contracts prove denial before body read or storage, signature and quota ordering, safe
  names, independent hourly/daily buckets, and minimal audit fields.
- Generated client contracts prove versioned routes, raw bytes, required headers, typed errors,
  typed JSON anchors, and caller-owned stream lifetime.
- Real HTTP contracts start ASP.NET on an ephemeral loopback port and exercise upload, metadata, and
  fragment operations through the generated client.

Run from the repository worktree:

```powershell
.\services\document-evidence\verify-service-boundary.ps1
```

The accepted local proof on `c9d8a3e0329cac4244bc1383bdfa200038096450` built four projects with
zero warnings and ran upload-security, generated-client, and real-HTTP contracts successfully.

## ENG-148 deterministic demo

`DocumentEvidence.EndToEndDemo` now performs this route:

```text
reproducible PDF bytes
  -> secure HTTP upload through generated client
  -> LocalImmutableObjectStore revision
  -> real Poppler page-grounded extraction
  -> typed fragment retrieval through generated client
  -> selected-only source-fragment-v0 export
  -> deterministic proposal and grounding review
  -> real SWI-Prolog gate
  -> verified decision receipt
```

The consumer never sees the service database, object key, or local blob path. The verifier runs the
complete route twice and rejects any difference in the full artifact-tree SHA-256:

```powershell
.\services\document-evidence\verify-eng-148-demo.ps1
```

## Remaining MVP work

The ENG-148 host proves the full user route but remains a contract/demo composition root. Production
still needs PostgreSQL-backed quota and audit state, signed read-plan revalidation, revocation
invalidation, outbox dispatch, and the deployable service composition root.
