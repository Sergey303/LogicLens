#!/usr/bin/env python3
from __future__ import annotations

import shutil

import pdf_link_contract_test as base
from source_proposal.pdf_link import parse_pdf_with_pypdf


def parse_with_pypdf(
    *,
    content: bytes,
    proposal_id: str,
    source_id: str,
    source_uri: str,
    content_hash: str,
    poppler_prefix: str | None,
):
    del poppler_prefix
    return parse_pdf_with_pypdf(
        content=content,
        proposal_id=proposal_id,
        source_id=source_id,
        source_uri=source_uri,
        content_hash=content_hash,
    )


def main() -> int:
    original_parser = base.parse_pdf_with_poppler
    original_which = shutil.which

    def fake_which(name: str, *args, **kwargs):
        if name in {"pdftotext", "pdfinfo"}:
            return f"contract-stub-{name}"
        return original_which(name, *args, **kwargs)

    base.parse_pdf_with_poppler = parse_with_pypdf
    shutil.which = fake_which
    try:
        result = base.main()
    finally:
        base.parse_pdf_with_poppler = original_parser
        shutil.which = original_which

    print("pypdf fallback contract verification passed")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
