# Document Evidence Service v0

Status: proposed shared-service baseline.
Consumers: LogicLens, product applications, and EngDoc Essential.

## Purpose

Provide one secure, reproducible document lifecycle instead of copying upload, storage, parsing,
and source-fragment logic into each product.

## Ownership

The service owns:

- document identity, workspace ownership, and revisions;
- safe upload and source-link registration;
- immutable original bytes and content hashes;
- processing state and idempotent jobs;
- deterministic format adapters and canonical document IR;
- page, sheet, section, cell, and text-fragment anchors;
- derived previews and extraction artifacts;
- access checks, retention, revocation, and audit events;
- signed download or read plans.

It does not own:

- domain assertions or their acceptance;
- product catalogue entities;
- capsule activation or active epochs;
- Prolog rules and decisions;
- RAG ranking policy outside document candidate retrieval;
- final user-facing answers.

## Service boundary

Consumers use a versioned HTTP/OpenAPI contract and events. They never read the service database,
object-store keys, or local file paths directly. Generated clients are isolated from handwritten
application modules.

Every request carries a `workspaceId`; application-level authorization is checked before metadata,
fragments, plans, or bytes are returned.

## Storage

- PostgreSQL stores metadata, lifecycle, revisions, access policy, and artifact records.
- Original and derived bytes use S3-compatible object storage; local filesystem is allowed in dev.
- Objects are content-addressed by SHA-256 and never overwritten.
- Display names are metadata, not storage paths.
- A revision points to one immutable original and its deterministic artifacts.

## Ingestion pipeline

```text
create upload intent
  -> authorize workspace and quota
  -> receive bytes into quarantine
  -> normalize display name
  -> verify size, media allowlist, signature, and container structure
  -> calculate SHA-256
  -> persist immutable object and revision
  -> enqueue idempotent processing job
  -> run format adapter
  -> produce canonical document IR and fragments
  -> verify hashes and artifact manifest
  -> publish processing result
```

A model is not part of the trusted ingestion path. Model-based extraction creates proposals in a
separate worker and cannot modify accepted document IR.

## Initial formats

1. PDF, reusing LogicLens page-grounded PDF contracts and Poppler verification.
2. DOCX, validating OOXML package structure before extraction.
3. XLSX, preserving workbook, sheet, cell, formula/value, and canonicalized metadata.
4. TXT, Markdown, HTML, and CSV through deterministic text/table adapters.
5. Images only when an explicit OCR adapter and confidence/provenance contract are accepted.

EngDoc Essential is the preferred source for multi-format canonicalization and technical-document
fixtures. LogicLens remains the source for proposal, provenance, and SWI-Prolog execution gates.

## Security requirements adopted from ChatPilot

- Check object-level access before lookup or byte streaming.
- Normalize path-like names to safe base names and enforce length limits.
- Validate magic/signature bytes; do not trust `Content-Type` or extension alone.
- Validate structured containers such as OOXML.
- Apply short-window rate limits and independent daily quotas before storage.
- Reject storage roots inside a web root and reject traversal in configured paths.
- Revalidate access when issuing download plans and when executing them.
- Invalidate fragments, previews, and search candidates after revocation or revision change.

## Reliability

- Upload completion, processing requests, and event publication require idempotency keys.
- Processing uses durable jobs/outbox semantics with leases, retries, and terminal failure states.
- Artifact generation is reproducible; manifests pin parser version and every artifact hash.
- A successful parser run does not accept semantic assertions.

## MVP API surface

- create and complete upload intent;
- register a permitted source link;
- read document and revision metadata;
- list processing state and artifacts;
- retrieve permitted fragments by typed anchor;
- issue a signed download/read plan;
- revoke or supersede a revision;
- request deterministic reprocessing with a pinned adapter version.

## Extraction plan

Implement the service as a separate project under `services/document-evidence/` first. Keep its API,
database schema, and object storage independent so it can be extracted to a dedicated repository
without changing consumers.
