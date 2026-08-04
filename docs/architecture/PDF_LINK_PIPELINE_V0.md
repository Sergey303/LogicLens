# Ephemeral PDF Link Pipeline v0

Status: executable vertical slice  
Owner: LogicLens  
Domain content owner: capsule repositories such as `CTO-Practical-Simulation`

## Purpose

The PDF link pipeline reads a declared public PDF by URL, fingerprints and parses it, creates page/block-addressable evidence, and then hands the result to the existing source proposal pipeline.

The original PDF is never committed, packaged, or uploaded as an Actions artifact.

```text
public HTTPS PDF
  -> bounded temporary download
  -> MIME and PDF magic validation
  -> SHA-256 fingerprint
  -> native-text adapter (Poppler or pypdf)
  -> Canonical Document IR
  -> page/block fragments
  -> assertion seed or model proposal
  -> source-grounding review
  -> SWI-Prolog execution gate
  -> selected-evidence-only package
  -> temporary workspace deletion
```

## Source declaration

```json
{
  "id": "scrum-guide-2020",
  "kind": "pdf-document",
  "title": "The Scrum Guide",
  "locator": "https://scrumguides.org/docs/scrumguide/v2020/2020-Scrum-Guide-US.pdf",
  "version": "2020-11",
  "language": "en",
  "license": {
    "id": "CC-BY-SA-4.0",
    "status": "confirmed",
    "attribution": "Ken Schwaber and Jeff Sutherland, The Scrum Guide"
  },
  "snapshotPolicy": "ephemeral-read",
  "reader": {
    "kind": "auto-layout"
  }
}
```

Reader modes:

- `auto-layout`: use Poppler when both `pdfinfo` and `pdftotext` are available; otherwise use the pinned pure-Python parser;
- `poppler-layout`: require Poppler and fail when it is unavailable;
- `pypdf-layout`: require `pypdf` and never start a system PDF process;
- `docling-http`: reserved by the manifest contract, but not enabled by the v0 runtime.

Install the portable parser dependency with:

```powershell
py -3 -m pip install -r requirements-pdf.txt
```

An optional `expectedSha256` pins a known revision. A mismatch stops the pipeline and requires an explicit new source revision.

## Trust and retention boundary

The reader must:

- accept only credential-free public HTTPS URLs;
- reject private, loopback and link-local destinations, including redirects;
- enforce a byte limit;
- require PDF media type or PDF magic bytes;
- calculate SHA-256 before semantic processing;
- use memory or a temporary directory for source bytes;
- delete temporary PDF bytes after parsing;
- never copy the PDF into a proposal workspace or package.

A temporary workspace may contain full Canonical Document IR and fragments while a proposal is being prepared and reviewed. It must be created outside the repository and deleted after the gate.

## Canonical Document IR

The contract is adapted from the EngDoc Sentinel document boundary:

```text
Document
  Page
    Block
      text
      normalized text
      kind
      reading order
      parser provenance
      confidence
```

Both native-text adapters produce page dimensions, blocks, reading order and explicit processor provenance. Geometry is optional. The processor name and pinned version are included in the IR and PDF link record, so Poppler and pypdf results cannot be confused.

## CLI

```powershell
python tools/pdf_link_pipeline.py ingest `
  --world-root <world> `
  --capsule <capsule-id> `
  --source <pdf-source-id> `
  --proposal-id <proposal-id> `
  --output <temporary-workspace>
```

Use `--poppler-prefix <directory>` when Poppler is installed outside `PATH`. On Windows the resolver checks both extensionless names and `.exe` files.

The command directly creates a source-proposal workspace at stage `fragmented`.

A deterministic seed can resolve page-specific exact quotes into generated candidate and review files:

```powershell
python tools/pdf_link_pipeline.py resolve-seed `
  --proposal <temporary-workspace> `
  --seed <pdf-proposal-seed.json> `
  --output <temporary-resolution>
```

The normal source pipeline continues from there:

```powershell
python tools/source_pipeline.py prepare ...
python tools/source_pipeline.py propose ...
python tools/source_pipeline.py review ...
python tools/source_pipeline.py gate ...
python tools/source_pipeline.py verify ...
```

## Package retention

For `no-source-retention` workspaces, the gate excludes:

- original PDF bytes;
- Canonical Document IR;
- the full fragment set;
- the full extraction request containing all source text.

The package retains only:

- PDF link record and fingerprint;
- selected evidence fragments used by accepted assertions;
- exact grounding review quotes;
- assertion proposal;
- generic prompt and extraction metadata without source text;
- approved assertions;
- generated Prolog and PlUnit tests;
- gate report and hashes.

Verification rejects a PDF package containing `.pdf`, full IR, full fragments, or the full extraction request.

## Current parser limit

Poppler and pypdf extract only an existing text layer. They are not OCR systems. A scanned or otherwise textless PDF fails safely and requires a future OCR/Docling adapter; an empty text layer is never silently accepted as evidence.
