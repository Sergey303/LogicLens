from __future__ import annotations

from pathlib import Path
from typing import Any

from capsule import json_object

PDF_RECORD_DOMAIN = b"LogicLensPdfLinkRecord\0"
PDF_IR_DOMAIN = b"LogicLensCanonicalDocumentIr\0"
PDF_SEED_DOMAIN = b"LogicLensPdfProposalSeed\0"
PDF_MEDIA_TYPES = {"application/pdf", "application/octet-stream"}
MAX_PDF_BYTES = 32 * 1024 * 1024


def load_pdf_schemas(contracts_root: Path) -> dict[str, dict[str, Any]]:
    return {
        "pdfRecord": json_object(contracts_root / "pdf-link-record-v0.schema.json", "PDF link record schema"),
        "documentIr": json_object(contracts_root / "canonical-document-ir-v0.schema.json", "canonical document IR schema"),
        "seed": json_object(contracts_root / "pdf-proposal-seed-v0.schema.json", "PDF proposal seed schema"),
    }
