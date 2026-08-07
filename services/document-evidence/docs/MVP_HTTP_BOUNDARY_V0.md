# MVP HTTP boundary v0

Status: service boundary and ENG-148 deterministic end-to-end route verified. Signed read-plan HTTP/client implementation is complete and awaiting strict proof.

## Consumer contract

Consumers use [`document-evidence-v1.json`](../openapi/document-evidence-v1.json) and the isolated
`DocumentEvidence.Client` project. They do not reference Application, Postgres, LocalStorage, AppForge
generated entities, database tables, or object keys.

The versioned operations are:

```text
PUT  /api/v1/workspaces/{workspaceId}/documents/{documentId}/revisions
GET  /api/v1/workspaces/{workspaceId}/documents/{documentId}
GET  /api/v1/workspaces/{workspaceId}/revisions/{revisionId}/fragments
POST /api/v1/workspaces/{workspaceId}/revisions/{revisionId}/read-plans
GET  /api/v1/read-plans/content
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

## Signed read plan

A read plan is short-lived, actor-bound, HMAC-protected, and contains revision identity and immutable
object metadata but no storage key or path. Issuance executes:

```text
authorization -> revision metadata -> revocation/supersede check -> signed plan
```

Execution never accepts the token in a URL. The generated client sends it only in the bounded
`X-Read-Plan-Token` request header, and the OpenAPI generator fails closed if that credential drifts
to another location or a credential-bearing `relativeUrl` reappears. Infrastructure must redact this
header anywhere request headers are logged.

The service executes:

```text
signature/expiry/actor check
  -> authorization revalidation
  -> fresh revision metadata
  -> revocation/supersede and snapshot revalidation
  -> immutable bytes
```

The returned stream owns the HTTP response lifetime. Closing the caller stream releases the response;
the response is not disposed before the caller can read it. Token-bearing issue responses use
`Cache-Control: no-store`; binary content responses use `Cache-Control: private, no-store` so a shared
HTTP cache cannot reuse one actor's revision bytes for another request.

## Executable contracts

- Application contracts prove authorization ordering, expiry, actor binding, stale snapshot rejection,
  and revocation/supersede failure before object access.
- Security contracts prove token tamper rejection and bounded HMAC payload validation.
- The OpenAPI validator proves header-only bounded credential transport and rejects a URL-bearing token
  contract.
- Generated client contracts prove header-only token transport and response-owned streaming.
- Real HTTP contracts exercise issue/content routes and prove read-plan responses are non-cacheable.
- PostgreSQL contracts derive supersede state from the current document revision and preserve
  workspace isolation.

Run against an already configured PostgreSQL connection:

```powershell
.\services\document-evidence\verify-service-boundary.ps1
```

For a complete local proof without reusing a developer database, Docker can provide an isolated
`postgres:17-alpine` on a dynamically allocated host port. The runner restores the previous connection
environment and removes the container in `finally`:

```powershell
.\services\document-evidence\verify-service-boundary-local-postgres.ps1
```

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

The verifier runs the complete positive route twice and rejects any difference in the full
artifact-tree SHA-256. It also proves that absent and ambiguous evidence fail closed before trusted
proposal output is created.

Complete accepted proof for tested commit `ea21acc5e7ba273d6e531d026978375299c36f00`:

- deterministic tree SHA-256:
  `sha256:c348ee34e62044e3f3849176837d9f0ff05d5943c7706b6b43d8e0530afa11f0`;
- gate status: `passed`;
- decision status: `verified`;
- unknown/conflicting evidence: rejected with no trusted output;
- `modelOutputAcceptedAutomatically=false`;
- `consumerReadsDatabase=false` and `consumerReadsBlobPath=false`.

Machine-readable evidence:

- [`eng-148-e2e-proof-v1.json`](../evidence/eng-148-e2e-proof-v1.json) — accepted positive route;
- [`eng-148-e2e-proof-v2.json`](../evidence/eng-148-e2e-proof-v2.json) — complete acceptance.

## Remaining MVP work

ENG-148 is complete. The read-plan HTTP/client slice awaits strict proof. Production still needs
PostgreSQL-backed quota and audit state, complete preview/retrieval invalidation, outbox dispatch, and
the deployable service composition root.
