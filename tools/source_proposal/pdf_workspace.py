from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from capsule import (
    canonical_json,
    domain_hash,
    normalized_text,
    schema_check,
    sha256,
    validate_world,
)
from .common import (
    MAX_FRAGMENT_CHARS,
    SAFE_ID,
    SourcePipelineError,
    prepare_empty_directory,
    write_workspace,
)
from .pdf_common import PDF_IR_DOMAIN, PDF_RECORD_DOMAIN
from .pdf_parser import SUPPORTED_PDF_READERS, fetch_pdf, parse_pdf


LIST_ITEM = re.compile(r"^(?:[•●▪◦*-]|\d+[.)])\s+")
SENTENCE_BOUNDARY = re.compile(
    r'(?<=[.!?])\s+(?=(?:["“‘(\[]?[A-Z0-9]))'
)


def ingest_pdf_link(
    *,
    world_root: Path,
    capsule_id: str,
    source_id: str,
    proposal_id: str,
    output: Path,
    max_bytes: int,
    poppler_prefix: str | None,
    schemas: dict[str, dict[str, Any]],
    pdf_schemas: dict[str, dict[str, Any]],
    contracts_root: Path,
) -> dict[str, Any]:
    if not SAFE_ID.fullmatch(proposal_id):
        raise SourcePipelineError("proposal ID is not a safe identifier")
    if max_bytes < 1 or max_bytes > 64 * 1024 * 1024:
        raise SourcePipelineError(
            "max bytes must be between 1 and 67108864"
        )

    world = validate_world(world_root, contracts_root)
    capsule = world["capsules"].get(capsule_id)
    if capsule is None:
        raise SourcePipelineError(f"unknown capsule: {capsule_id}")
    source = next(
        (
            item
            for item in capsule["sources"]["sources"]
            if item["id"] == source_id
        ),
        None,
    )
    if source is None:
        raise SourcePipelineError(f"unknown source: {source_id}")
    if (
        source.get("kind") != "pdf-document"
        or source.get("snapshotPolicy") != "ephemeral-read"
    ):
        raise SourcePipelineError(
            "PDF link ingestion requires kind=pdf-document "
            "and snapshotPolicy=ephemeral-read"
        )
    if source["license"]["status"] == "restricted":
        raise SourcePipelineError("restricted PDF source cannot be read")

    reader_kind = source.get("reader", {}).get("kind")
    if reader_kind not in SUPPORTED_PDF_READERS:
        raise SourcePipelineError(
            f"unsupported PDF reader.kind: {reader_kind}"
        )

    content, acquisition = fetch_pdf(source["locator"], max_bytes)
    expected = source.get("expectedSha256")
    content_hash = sha256(content)
    if expected is not None and expected != content_hash:
        raise SourcePipelineError(
            f"PDF hash mismatch: expected {expected}, "
            f"received {content_hash}; treat it as a new revision"
        )

    root = prepare_empty_directory(output)
    ir = parse_pdf(
        content=content,
        proposal_id=proposal_id,
        source_id=source_id,
        source_uri=acquisition["finalUrl"],
        content_hash=content_hash,
        reader_kind=reader_kind,
        poppler_prefix=poppler_prefix,
    )
    schema_check(
        ir,
        pdf_schemas["documentIr"],
        "canonical document IR",
    )
    ir["irHash"] = domain_hash(
        PDF_IR_DOMAIN,
        {
            key: value
            for key, value in ir.items()
            if key != "irHash"
        },
    )
    schema_check(
        ir,
        pdf_schemas["documentIr"],
        "canonical document IR",
    )

    document_dir = root / "document"
    fragment_dir = root / "fragments"
    snapshot_dir = root / "snapshot"
    document_dir.mkdir(parents=True)
    fragment_dir.mkdir(parents=True)
    snapshot_dir.mkdir(parents=True)

    ir_relative = "document/canonical-document-ir.json"
    ir_bytes = canonical_json(ir)
    (root / ir_relative).write_bytes(ir_bytes)

    source_manifest_hash = sha256(
        canonical_json(capsule["sources"])
    )
    record: dict[str, Any] = {
        "schemaVersion": "0.1",
        "proposalId": proposal_id,
        "worldId": world["manifest"]["worldId"],
        "capsuleId": capsule_id,
        "sourceId": source_id,
        "title": source["title"],
        "locator": source["locator"],
        "license": deepcopy(source["license"]),
        "retentionPolicy": "no-source-retention",
        "sourceManifestHash": source_manifest_hash,
        "pdf": {
            "contentHash": content_hash,
            "bytes": len(content),
            "mediaType": "application/pdf",
            "finalUrl": acquisition["finalUrl"],
        },
        "processor": deepcopy(ir["processor"]),
        "documentIr": {
            "path": ir_relative,
            "hash": sha256(ir_bytes),
            "pageCount": len(ir["pages"]),
            "blockCount": sum(
                len(page["blocks"])
                for page in ir["pages"]
            ),
        },
    }
    record["snapshotHash"] = domain_hash(
        PDF_RECORD_DOMAIN,
        record,
    )
    schema_check(
        record,
        pdf_schemas["pdfRecord"],
        "PDF link record",
    )
    record_relative = "snapshot/pdf-link-record.json"
    (root / record_relative).write_bytes(
        canonical_json(record)
    )

    fragments = fragments_from_ir(
        ir,
        record["snapshotHash"],
    )
    fragments_relative = "fragments/fragments.jsonl"
    fragment_bytes = b"".join(
        canonical_json(fragment)
        for fragment in fragments
    )
    (root / fragments_relative).write_bytes(fragment_bytes)

    workspace: dict[str, Any] = {
        "schemaVersion": "0.1",
        "proposalId": proposal_id,
        "worldId": world["manifest"]["worldId"],
        "capsuleId": capsule_id,
        "sourceId": source_id,
        "stage": "fragmented",
        "artifacts": {
            "snapshot": {
                "metadataPath": record_relative,
                "hash": record["snapshotHash"],
                "retentionPolicy": "no-source-retention",
                "documentIrPath": ir_relative,
                "documentIrHash": sha256(ir_bytes),
            },
            "fragments": {
                "path": fragments_relative,
                "count": len(fragments),
                "hash": sha256(fragment_bytes),
            },
        },
    }
    return write_workspace(root, workspace, schemas)


def fragments_from_ir(
    ir: dict[str, Any],
    snapshot_hash: str,
) -> list[dict[str, Any]]:
    fragments: list[dict[str, Any]] = []
    ordinal = 0
    heading_path: list[str] = []

    for page in ir["pages"]:
        for block in page["blocks"]:
            text = (
                block.get("text")
                or block.get("normalizedText")
                or ""
            )
            units = evidence_units(text)

            for unit_index, unit in enumerate(units, 1):
                unit_text = unit["text"]
                if unit["kind"] == "heading":
                    heading_path = [unit_text]

                chunks = split_oversized_unit(unit_text)
                for chunk_index, chunk in enumerate(chunks, 1):
                    ordinal += 1
                    block_ordinal = (
                        block["blockId"]
                        .split(":b", 1)[1]
                        .split(":", 1)[0]
                    )
                    suffix = ""
                    if len(units) > 1:
                        suffix += f":u{unit_index:03d}"
                    if len(chunks) > 1:
                        suffix += f":c{chunk_index:03d}"
                    fragment_id = (
                        f"{ir['sourceId']}"
                        f"#p-{page['pageNumber']:04d}"
                        f"-b-{block_ordinal}{suffix}"
                    )
                    fragment = {
                        "schemaVersion": "0.1",
                        "fragmentId": fragment_id,
                        "proposalId": ir["proposalId"],
                        "sourceId": ir["sourceId"],
                        "snapshotHash": snapshot_hash,
                        "ordinal": ordinal,
                        "headingPath": list(heading_path),
                        "lineStart": unit["lineStart"],
                        "lineEnd": unit["lineEnd"],
                        "pageNumber": page["pageNumber"],
                        "blockIds": [block["blockId"]],
                        "text": chunk,
                        "textHash": sha256(
                            normalized_text(chunk)
                        ),
                    }
                    fragments.append(fragment)

    return fragments


def evidence_units(text: str) -> list[dict[str, Any]]:
    lines = (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .splitlines()
    )
    units: list[dict[str, Any]] = []
    paragraph: list[str] = []
    paragraph_start: int | None = None
    paragraph_end: int | None = None

    def emit(value: str, start: int, end: int, kind: str) -> None:
        for sentence in split_sentences(value):
            units.append(
                {
                    "text": sentence,
                    "lineStart": start,
                    "lineEnd": end,
                    "kind": kind,
                }
            )

    def flush_paragraph() -> None:
        nonlocal paragraph, paragraph_start, paragraph_end
        if paragraph:
            emit(
                " ".join(paragraph),
                paragraph_start or 1,
                paragraph_end or paragraph_start or 1,
                "paragraph",
            )
        paragraph = []
        paragraph_start = None
        paragraph_end = None

    for line_number, raw_line in enumerate(lines, 1):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            flush_paragraph()
            continue

        if LIST_ITEM.match(line):
            flush_paragraph()
            emit(line, line_number, line_number, "list")
            continue

        if is_heading_line(line):
            flush_paragraph()
            emit(line, line_number, line_number, "heading")
            continue

        if paragraph_start is None:
            paragraph_start = line_number
        paragraph_end = line_number
        paragraph.append(line)

        if line.endswith((".", "!", "?", ";", ":")):
            flush_paragraph()

    flush_paragraph()

    if not units:
        normalized = re.sub(r"\s+", " ", text).strip()
        if normalized:
            emit(normalized, 1, max(1, len(lines)), "paragraph")

    return units


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    return [
        item.strip()
        for item in SENTENCE_BOUNDARY.split(normalized)
        if item.strip()
    ]


def split_oversized_unit(text: str) -> list[str]:
    if len(text) <= MAX_FRAGMENT_CHARS:
        return [text]
    chunks: list[str] = []
    remaining = text
    while len(remaining) > MAX_FRAGMENT_CHARS:
        boundary = remaining.rfind(" ", 0, MAX_FRAGMENT_CHARS + 1)
        if boundary < MAX_FRAGMENT_CHARS // 2:
            boundary = MAX_FRAGMENT_CHARS
        chunks.append(remaining[:boundary].strip())
        remaining = remaining[boundary:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def is_heading_line(line: str) -> bool:
    if len(line) > 80 or len(line.split()) > 10:
        return False
    if line.endswith((".", "!", "?", ";", ":")):
        return False
    if LIST_ITEM.match(line):
        return False
    return True
