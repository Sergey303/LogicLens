"""Canonical document IR extraction for the PDF link contract fixture."""

from __future__ import annotations

from typing import Any

import capsule
from source_proposal import pdf_link


def extract_document_ir(
    pdf: bytes,
    proposal_id: str,
    source_id: str,
    source_uri: str,
) -> dict[str, Any]:
    """Extract and domain-hash canonical IR from deterministic PDF bytes."""
    document_ir = pdf_link.parse_pdf_with_poppler(
        content=pdf,
        proposal_id=proposal_id,
        source_id=source_id,
        source_uri=source_uri,
        content_hash=capsule.sha256(pdf),
        poppler_prefix=None,
    )
    document_ir["irHash"] = capsule.domain_hash(
        b"LogicLensCanonicalDocumentIr\0",
        {key: value for key, value in document_ir.items() if key != "irHash"},
    )
    return document_ir
