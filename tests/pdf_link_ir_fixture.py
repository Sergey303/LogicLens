"""Canonical document IR extraction for the PDF link contract fixture."""

from __future__ import annotations

from typing import Any


def extract_document_ir(
    pdf_link: Any,
    capsule: Any,
    pdf: bytes,
    data: Any,
) -> dict[str, Any]:
    """Extract and domain-hash canonical IR from deterministic PDF bytes."""
    document_ir = pdf_link.parse_pdf_with_poppler(
        content=pdf,
        proposal_id=data.PROPOSAL_ID,
        source_id=data.SOURCE_ID,
        source_uri=data.SOURCE_URI,
        content_hash=capsule.sha256(pdf),
        poppler_prefix=None,
    )
    document_ir["irHash"] = capsule.domain_hash(
        b"LogicLensCanonicalDocumentIr\0",
        {key: value for key, value in document_ir.items() if key != "irHash"},
    )
    return document_ir
