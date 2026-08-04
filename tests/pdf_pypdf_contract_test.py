#!/usr/bin/env python3
from __future__ import annotations

import shutil

import pdf_link_contract_test as base
from source_proposal.pdf_link import (
    fragments_from_ir,
    parse_pdf_with_pypdf,
)


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


def verify_evidence_unit_segmentation() -> None:
    quote = (
        "The Product Owner is accountable for maximizing the value of the "
        "product resulting from the work of the Scrum Team."
    )
    text = (
        "Product Owner\n"
        "Unrelated introductory sentence.\n"
        "The Product Owner is accountable for maximizing the value of the "
        "product resulting from the work of\n"
        "the Scrum Team. How this is done may vary widely across "
        "organizations.\n"
        "Unrelated trailing sentence.\n"
    )
    ir = {
        "proposalId": "segmentation-v0",
        "sourceId": "scrum-guide-2020",
        "pages": [
            {
                "pageNumber": 6,
                "blocks": [
                    {
                        "blockId": (
                            "scrum-guide-2020:p0006:b0001:"
                            "000000000000"
                        ),
                        "kind": "paragraph",
                        "text": text,
                        "normalizedText": text,
                    }
                ],
            }
        ],
    }
    fragments = fragments_from_ir(
        ir,
        "sha256:" + ("0" * 64),
    )
    matches = [
        item
        for item in fragments
        if quote in item["text"]
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected one quote fragment, received {len(matches)}"
        )
    if matches[0]["text"] != quote:
        raise AssertionError(
            "review quote was retained with unrelated page text"
        )
    if any(len(item["text"]) > 500 for item in fragments):
        raise AssertionError(
            "evidence unit segmentation retained an oversized fixture unit"
        )


def main() -> int:
    verify_evidence_unit_segmentation()

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
