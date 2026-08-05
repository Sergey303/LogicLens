# MVP HTTP boundary v0

Status: implemented, verification pending on the consolidated branch head.

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

## Remaining MVP work

The current loopback host is a contract proof, not the deployable composition root. The next slice
connects these endpoints to the production PostgreSQL/generated boundary, immutable store, PDF worker,
and outbox dispatcher, then records the complete PDF -> client fragment -> proposal -> SWI decision
receipt for ENG-148.
