from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from capsule import canonical_json, sha256
from .acquire import SafeRedirectHandler, validate_public_https_url
from .common import SourcePipelineError
from .pdf_common import PDF_MEDIA_TYPES


def fetch_pdf(url: str, max_bytes: int) -> tuple[bytes, dict[str, Any]]:
    validate_public_https_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "LogicLensPdfLinkPipeline/0.1",
            "Accept": "application/pdf",
            "Accept-Encoding": "identity",
        },
    )
    try:
        opener = urllib.request.build_opener(SafeRedirectHandler())
        with opener.open(request, timeout=45) as response:
            final_url = response.geturl()
            validate_public_https_url(final_url)
            media_type = response.headers.get_content_type().lower()
            content = response.read(max_bytes + 1)
    except (OSError, urllib.error.URLError) as exc:
        raise SourcePipelineError(f"cannot fetch PDF source: {exc}") from exc
    if len(content) > max_bytes:
        raise SourcePipelineError("PDF source exceeds maximum size")
    if media_type not in PDF_MEDIA_TYPES and not content.startswith(b"%PDF-"):
        raise SourcePipelineError(f"source is not a PDF: {media_type}")
    if not content.startswith(b"%PDF-"):
        raise SourcePipelineError("PDF magic header is missing")
    return content, {
        "mode": "ephemeral-network",
        "mediaType": "application/pdf",
        "sourceBytes": len(content),
        "finalUrl": final_url,
    }


def parse_pdf_with_poppler(
    *,
    content: bytes,
    proposal_id: str,
    source_id: str,
    source_uri: str,
    content_hash: str,
    poppler_prefix: str | None,
) -> dict[str, Any]:
    pdfinfo = resolve_executable("pdfinfo", poppler_prefix)
    pdftotext = resolve_executable("pdftotext", poppler_prefix)
    version = poppler_version(pdftotext)
    configuration = {
        "adapter": "poppler-layout",
        "pdftotextArgs": ["-layout", "-enc", "UTF-8"],
        "blockSegmentation": "blank-line-v1",
    }
    configuration_hash = sha256(canonical_json(configuration))

    with tempfile.TemporaryDirectory(prefix="logiclens-pdf-") as temp_name:
        temp = Path(temp_name)
        pdf_path = temp / "source.pdf"
        text_path = temp / "source.txt"
        pdf_path.write_bytes(content)
        info = run_process([pdfinfo, str(pdf_path)], cwd=temp)
        run_process(
            [pdftotext, "-layout", "-enc", "UTF-8", str(pdf_path), str(text_path)],
            cwd=temp,
        )
        text = text_path.read_text(encoding="utf-8", errors="strict")

    page_count = parse_pdfinfo_int(info, "Pages")
    width, height = parse_page_size(info)
    page_texts = text.replace("\r\n", "\n").replace("\r", "\n").split("\f")
    if page_texts and not page_texts[-1].strip():
        page_texts.pop()
    if page_count != len(page_texts):
        raise SourcePipelineError(
            f"Poppler page count mismatch: pdfinfo={page_count}, pdftotext={len(page_texts)}"
        )

    pages: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for page_number, page_text in enumerate(page_texts, 1):
        blocks = page_blocks(source_id, page_number, page_text, version)
        if not blocks:
            warnings.append(
                {
                    "code": "empty-text-page",
                    "message": "Poppler produced no usable native text for this page.",
                    "severity": "warning",
                    "pageNumber": page_number,
                }
            )
        pages.append(
            {
                "pageNumber": page_number,
                "width": width,
                "height": height,
                "unit": "point",
                "textLayerQuality": 1.0 if blocks else 0.0,
                "blocks": blocks,
                "readingOrder": [block["blockId"] for block in blocks],
            }
        )

    if not any(page["blocks"] for page in pages):
        raise SourcePipelineError(
            "PDF has no usable native text; OCR/Docling fallback is required and is not enabled in v0"
        )

    return {
        "contractVersion": "0.1",
        "proposalId": proposal_id,
        "sourceId": source_id,
        "artifact": {
            "sha256": content_hash,
            "mediaType": "application/pdf",
            "sizeBytes": len(content),
            "sourceUri": source_uri,
            "retained": False,
        },
        "processor": {
            "name": "poppler-layout",
            "version": version,
            "configurationHash": configuration_hash,
        },
        "pages": pages,
        "warnings": warnings,
    }


def resolve_executable(name: str, prefix: str | None) -> str:
    if prefix:
        candidate = Path(prefix) / name
        if candidate.is_file():
            return str(candidate)
    resolved = shutil.which(name)
    if not resolved:
        raise SourcePipelineError(f"required Poppler executable not found: {name}")
    return resolved


def poppler_version(pdftotext: str) -> str:
    result = subprocess.run(
        [pdftotext, "-v"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )
    output = (result.stderr or result.stdout).splitlines()
    match = re.search(r"version\s+([^\s]+)", output[0] if output else "", re.I)
    return match.group(1) if match else "unknown"


def run_process(arguments: list[str], *, cwd: Path) -> str:
    try:
        result = subprocess.run(
            arguments,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SourcePipelineError(f"PDF parser process failed: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-2000:]
        raise SourcePipelineError(f"PDF parser process failed: {detail}")
    return result.stdout


def parse_pdfinfo_int(info: str, name: str) -> int:
    match = re.search(rf"^{re.escape(name)}:\s*(\d+)\s*$", info, re.M)
    if not match:
        raise SourcePipelineError(f"pdfinfo did not report {name}")
    return int(match.group(1))


def parse_page_size(info: str) -> tuple[float, float]:
    match = re.search(r"^Page size:\s*([0-9.]+)\s+x\s+([0-9.]+)\s+pts", info, re.M)
    if not match:
        return 1.0, 1.0
    return float(match.group(1)), float(match.group(2))


def page_blocks(source_id: str, page_number: int, text: str, processor_version: str) -> list[dict[str, Any]]:
    normalized = text.replace("\u00a0", " ").strip("\n")
    groups = [group.strip() for group in re.split(r"\n\s*\n", normalized) if group.strip()]
    if not groups and normalized.strip():
        groups = [line.strip() for line in normalized.splitlines() if line.strip()]
    blocks: list[dict[str, Any]] = []
    for ordinal, group in enumerate(groups, 1):
        clean = re.sub(r"[ \t]+", " ", group).strip()
        if not clean:
            continue
        content_hash = hashlib.sha256(clean.encode("utf-8")).hexdigest()
        block_id = f"{source_id}:p{page_number:04d}:b{ordinal:04d}:{content_hash[:12]}"
        blocks.append(
            {
                "blockId": block_id,
                "kind": classify_block(clean),
                "text": group,
                "normalizedText": clean,
                "language": None,
                "source": {
                    "method": "native",
                    "processorName": "poppler-layout",
                    "processorVersion": processor_version,
                },
                "confidence": 1.0,
                "attributes": {},
            }
        )
    return blocks


def classify_block(text: str) -> str:
    first = text.splitlines()[0].strip()
    if first.startswith(("•", "- ", "* ", "●")):
        return "list"
    if len(first) <= 120 and not first.endswith((".", ";", ":")) and len(text.splitlines()) <= 2:
        return "heading"
    return "paragraph"
