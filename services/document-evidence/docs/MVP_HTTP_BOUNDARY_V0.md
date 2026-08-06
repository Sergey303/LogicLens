# MVP HTTP boundary v0

Status: service boundary and ENG-148 deterministic end-to-end route verified, including fail-closed unknown and conflicting evidence.

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

The accepted local service-boundary proof built four projects with zero warnings and ran
upload-security, generated-client, and real-HTTP contracts successfully.

## ENG-148 deterministic demo

`DocumentEvidence.EndToEndDemo` performs this route:

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
complete positive route twice and rejects any difference in the full artifact-tree SHA-256. It then
proves that an absent quote and ambiguous matching fragments fail closed before any trusted proposal
output is created:

```powershell
.\services\document-evidence\verify-eng-148-demo.ps1
```

Complete accepted proof for tested commit `ea21acc5e7ba273d6e531d026978375299c36f00`:

- repository guard: 20 files;
- Ruff: passed for all four ENG-148 Python files;
- .NET build: zero warnings and zero errors;
- two complete HTTP/Poppler/SWI-Prolog runs;
- deterministic tree SHA-256:
  `sha256:c348ee34e62044e3f3849176837d9f0ff05d5943c7706b6b43d8e0530afa11f0`;
- gate status: `passed`;
- decision status: `verified`;
- unknown evidence: rejected with no trusted output;
- conflicting grounding: rejected with no trusted output;
- `modelOutputAcceptedAutomatically=false`;
- `consumerReadsDatabase=false` and `consumerReadsBlobPath=false`;
- CGR process exit code: `0`.

Machine-readable evidence:

- [`eng-148-e2e-proof-v1.json`](../evidence/eng-148-e2e-proof-v1.json) — accepted positive route;
- [`eng-148-e2e-proof-v2.json`](../evidence/eng-148-e2e-proof-v2.json) — complete positive and fail-closed acceptance.

## Remaining MVP work

ENG-148 is complete. The host remains a contract/demo composition root. Production still needs
PostgreSQL-backed quota and audit state, signed read-plan revalidation, revocation invalidation,
outbox dispatch, and the deployable service composition root.
