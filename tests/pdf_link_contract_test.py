"""Exercise ephemeral PDF extraction, proposal, retention, and Prolog gates."""

from __future__ import annotations

import importlib
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POPPLER_REQUIRED = "Poppler is required for pdf_link_contract_test.py"


def main() -> int:
    """Run the PDF link vertical slice against real Poppler and SWI-Prolog."""
    sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "tools"), str(ROOT)]
    source_proposal = importlib.import_module("source_proposal")
    source_common = importlib.import_module("source_proposal.common")
    capsule = importlib.import_module("capsule")
    pdf_link = importlib.import_module("source_proposal.pdf_link")
    assertions = importlib.import_module("pdf_link_contract_assertions")
    data = importlib.import_module("pdf_link_contract_data")
    gate_fixture = importlib.import_module("pdf_link_gate_fixture")
    ir_fixture = importlib.import_module("pdf_link_ir_fixture")
    pdf_builder = importlib.import_module("pdf_fixture_builder")
    world_fixture = importlib.import_module("pdf_link_world_fixture")
    if not shutil.which("pdftotext") or not shutil.which("pdfinfo"):
        raise SystemExit(POPPLER_REQUIRED)
    schemas = source_proposal.load_schemas(ROOT / "contracts")
    pdf_schemas = pdf_link.load_pdf_schemas(ROOT / "contracts")
    pdf = pdf_builder.make_pdf(data.QUOTE)

    with tempfile.TemporaryDirectory(prefix="logiclens-pdf-test-") as temp_name:
        root = Path(temp_name)
        world = world_fixture.build_world(root)
        proposal = root / "proposal"
        proposal.mkdir()
        document_ir = ir_fixture.extract_document_ir(
            pdf,
            data.PROPOSAL_ID,
            data.SOURCE_ID,
            data.SOURCE_URI,
        )
        capsule.schema_check(document_ir, pdf_schemas["documentIr"], "fixture document IR")
        document_path = proposal / "document/canonical-document-ir.json"
        document_path.parent.mkdir(parents=True)
        document_path.write_bytes(capsule.canonical_json(document_ir))
        document_hash = capsule.sha256(document_path.read_bytes())
        record = data.record(pdf, document_ir, document_hash)
        capsule.schema_check(record, pdf_schemas["pdfRecord"], "fixture PDF record")
        record_path = proposal / "snapshot/pdf-link-record.json"
        record_path.parent.mkdir(parents=True)
        record_path.write_bytes(capsule.canonical_json(record))
        fragments = pdf_link.fragments_from_ir(document_ir, record["snapshotHash"])
        fragments_path = proposal / "fragments/fragments.jsonl"
        fragments_path.parent.mkdir(parents=True)
        fragments_path.write_bytes(
            b"".join(capsule.canonical_json(item) for item in fragments)
        )
        workspace = data.workspace(
            record["snapshotHash"],
            document_hash,
            capsule.sha256(fragments_path.read_bytes()),
            len(fragments),
        )
        source_common.write_workspace(proposal, workspace, schemas)
        seed_path = root / "seed.json"
        world_fixture.write_json(seed_path, data.seed())
        resolved = root / "resolved"
        pdf_link.resolve_pdf_seed(
            proposal_root=proposal,
            seed_path=seed_path,
            output=resolved,
            schemas=schemas,
            pdf_schemas=pdf_schemas,
        )
        package = gate_fixture.run_proposal_gate(
            world,
            proposal,
            resolved,
            root,
            schemas,
        )
        assertions.assert_selected_retention(package)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
