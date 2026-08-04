#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import source_proposal as sp
from capsule import canonical_json, domain_hash, schema_check, sha256
from source_proposal.common import write_workspace
from source_proposal.pdf_link import (
    PDF_RECORD_DOMAIN,
    fragments_from_ir,
    load_pdf_schemas,
    parse_pdf_with_poppler,
    resolve_pdf_seed,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def make_pdf(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET\n".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(content))
        content.extend(f"{index} 0 obj\n".encode("ascii"))
        content.extend(obj)
        content.extend(b"\nendobj\n")
    xref = len(content)
    content.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    return bytes(content)


def build_world(root: Path) -> Path:
    world = root / "world"
    capsule = world / "capsules" / "role-boundaries"
    module = world / "modules" / "fixture"
    write_json(world / "world.json", {
        "schemaVersion":"0.1","worldId":"management","title":"Management","description":"PDF contract fixture","languages":["en"],
        "semantic":{"vocabulary":"semantic/vocabulary.json","predicates":"semantic/predicates.json","roles":"semantic/roles.json","competencies":"semantic/competencies.json"},
        "capsules":[{"id":"management.role-boundaries","path":"capsules/role-boundaries"}],
        "modules":[{"id":"management.fixture","path":"modules/fixture"}],
        "tracks":[{"id":"fixture-track","title":"Fixture","moduleIds":["management.fixture"]}]})
    write_json(world / "semantic" / "vocabulary.json", {"schemaVersion":"0.1","concepts":[{"id":"outcome.product_value","kind":"management_outcome","labels":{"en":"product value"}}]})
    write_json(world / "semantic" / "predicates.json", {"schemaVersion":"0.1","predicates":[{"id":"owns_outcome","arguments":[{"name":"role","type":"role"},{"name":"outcome","type":"management_outcome"}],"valueSpace":"strict_claim","world":"open","negation":"explicit_evidence"}]})
    write_json(world / "semantic" / "roles.json", {"schemaVersion":"0.1","roles":[{"id":"role.product_owner","title":"Product Owner"}]})
    write_json(world / "semantic" / "competencies.json", {"schemaVersion":"0.1","competencies":[]})
    write_json(capsule / "capsule.json", {"schemaVersion":"0.1","capsuleId":"management.role-boundaries","version":"0.1.0","worldId":"management","title":"Role boundaries","description":"fixture","languages":["en"],"status":"draft","sourceManifest":"sources/manifest.json","preparedFiles":[],"ruleFiles":[],"learningFiles":[],"testFiles":[],"exports":{"predicates":[],"profiles":[]},"requires":{"capsuleContract":"0.1","epistemicDsl":"0.1"}})
    write_json(capsule / "sources" / "manifest.json", {"schemaVersion":"0.1","capsuleId":"management.role-boundaries","sources":[{"id":"scrum-guide-2020","kind":"pdf-document","title":"The Scrum Guide","locator":"https://example.com/scrum-guide.pdf","version":"2020-11","language":"en","license":{"id":"CC-BY-SA-4.0","status":"confirmed","attribution":"Ken Schwaber and Jeff Sutherland"},"snapshotPolicy":"ephemeral-read","reader":{"kind":"poppler-layout"}}]})
    write_json(module / "module.json", {"schemaVersion":"0.1","moduleId":"management.fixture","version":"0.1.0","worldId":"management","title":"Fixture module","usesCapsules":[{"id":"management.role-boundaries","version":"0.1.0"}],"supportedTracks":["fixture-track"],"entry":"entry.md","sequence":["sequence.json"],"scenarios":["scenario.json"],"rubrics":["rubric.json"],"completionPolicy":{"requiresCorrectionCycle":True,"allMandatoryCriteria":True,"minimumScore":75}})
    (module / "entry.md").write_text("# Fixture\n", encoding="utf-8")
    for name in ("sequence", "scenario", "rubric"):
        write_json(module / f"{name}.json", {"schemaVersion":"0.1"})
    return world


def main() -> int:
    if not shutil.which("pdftotext") or not shutil.which("pdfinfo"):
        raise SystemExit("Poppler is required for pdf_link_contract_test.py")
    schemas = sp.load_schemas(ROOT / "contracts")
    pdf_schemas = load_pdf_schemas(ROOT / "contracts")
    quote = "The Product Owner is accountable for maximizing the value of the product."
    pdf = make_pdf(quote)

    with tempfile.TemporaryDirectory(prefix="logiclens-pdf-test-") as temp_name:
        root = Path(temp_name)
        world = build_world(root)
        proposal = root / "proposal"
        proposal.mkdir()
        ir = parse_pdf_with_poppler(content=pdf, proposal_id="scrum-guide-2020-v0", source_id="scrum-guide-2020", source_uri="https://example.com/scrum-guide.pdf", content_hash=sha256(pdf), poppler_prefix=None)
        ir["irHash"] = domain_hash(b"LogicLensCanonicalDocumentIr\0", {key:value for key,value in ir.items() if key != "irHash"})
        schema_check(ir, pdf_schemas["documentIr"], "fixture document IR")
        document_path = proposal / "document" / "canonical-document-ir.json"
        document_path.parent.mkdir(parents=True)
        document_path.write_bytes(canonical_json(ir))
        record = {"schemaVersion":"0.1","proposalId":"scrum-guide-2020-v0","worldId":"management","capsuleId":"management.role-boundaries","sourceId":"scrum-guide-2020","title":"The Scrum Guide","locator":"https://example.com/scrum-guide.pdf","license":{"id":"CC-BY-SA-4.0","status":"confirmed","attribution":"Ken Schwaber and Jeff Sutherland"},"retentionPolicy":"no-source-retention","sourceManifestHash":sha256(b"fixture\n"),"pdf":{"contentHash":sha256(pdf),"bytes":len(pdf),"mediaType":"application/pdf","finalUrl":"https://example.com/scrum-guide.pdf"},"processor":ir["processor"],"documentIr":{"path":"document/canonical-document-ir.json","hash":sha256(document_path.read_bytes()),"pageCount":1,"blockCount":len(ir["pages"][0]["blocks"])}}
        record["snapshotHash"] = domain_hash(PDF_RECORD_DOMAIN, record)
        schema_check(record, pdf_schemas["pdfRecord"], "fixture PDF record")
        record_path = proposal / "snapshot" / "pdf-link-record.json"
        record_path.parent.mkdir(parents=True)
        record_path.write_bytes(canonical_json(record))
        fragments = fragments_from_ir(ir, record["snapshotHash"])
        fragments_path = proposal / "fragments" / "fragments.jsonl"
        fragments_path.parent.mkdir(parents=True)
        fragments_path.write_bytes(b"".join(canonical_json(item) for item in fragments))
        workspace = {"schemaVersion":"0.1","proposalId":"scrum-guide-2020-v0","worldId":"management","capsuleId":"management.role-boundaries","sourceId":"scrum-guide-2020","stage":"fragmented","artifacts":{"snapshot":{"metadataPath":"snapshot/pdf-link-record.json","hash":record["snapshotHash"],"retentionPolicy":"no-source-retention","documentIrPath":"document/canonical-document-ir.json","documentIrHash":sha256(document_path.read_bytes())},"fragments":{"path":"fragments/fragments.jsonl","count":len(fragments),"hash":sha256(fragments_path.read_bytes())}}}
        write_workspace(proposal, workspace, schemas)
        seed = {"schemaVersion":"0.1","seedId":"scrum-guide-product-owner-v0","proposalId":"scrum-guide-2020-v0","sourceId":"scrum-guide-2020","assertions":[{"assertionId":"scrum.po.product-value.support","target":{"predicate":"owns_outcome","arguments":["role.product_owner","outcome.product_value"]},"stance":"support","dependencyGroup":"scrum.guide.2020.product_owner","scope":{"framework":"Scrum","version":"2020-11"},"generalisability":"context-dependent","evidence":[{"pageNumber":1,"quote":quote}],"reviewNote":"The fixture directly states Product Owner accountability for product value."}],"abstentions":[]}
        seed_path = root / "seed.json"; write_json(seed_path, seed)
        resolved = root / "resolved"
        resolve_pdf_seed(proposal_root=proposal, seed_path=seed_path, output=resolved, schemas=schemas, pdf_schemas=pdf_schemas)
        sp.prepare_extraction(world_root=world, proposal_root=proposal, prompt_path=ROOT / "prompts" / "generic" / "source-assertion-proposer.md", schemas=schemas, contracts_root=ROOT / "contracts")
        sp.import_assertion_proposal(world_root=world, proposal_root=proposal, candidate_path=resolved / "assertion-candidate.json", schemas=schemas, contracts_root=ROOT / "contracts")
        sp.import_grounding_review(proposal_root=proposal, review_path=resolved / "grounding-review.json", schemas=schemas)
        package_root = root / "package"
        package = sp.execute_gate(proposal_root=proposal, output=package_root, swipl="swipl", timeout_seconds=20, schemas=schemas)
        sp.verify_package(package_root=package_root, swipl="swipl", timeout_seconds=20, schemas=schemas)
        paths = {item["path"] for item in package["files"]}
        forbidden = {"document/canonical-document-ir.json","fragments/fragments.jsonl","extraction/extraction-request.json"}
        if paths & forbidden or any(path.endswith(".pdf") for path in paths):
            raise AssertionError(f"no-source-retention violated: {sorted(paths & forbidden)}")
        if "evidence/selected-fragments.jsonl" not in paths:
            raise AssertionError("selected evidence was not retained")
    print("PDF link contract verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
