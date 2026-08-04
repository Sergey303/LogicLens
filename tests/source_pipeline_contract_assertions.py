"""Negative and fallback assertions for the text source proposal contract."""

from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TAMPER_ACCEPTED = "tampered package verified"
LINK_ONLY_ACCEPTED = "link-only source was snapshotted"


def skip_swipl_gate(*_args: object, **_kwargs: object) -> None:
    """Replace the Prolog subprocess only when SWI-Prolog is not installed."""


def assert_tamper_is_rejected(
    source_proposal: object,
    root: Path,
    schemas: dict,
) -> None:
    """Prove package verification detects generated Prolog modification."""
    generated = root / "package/files/generated/source_proposal.pl"
    text = generated.read_text(encoding="utf-8")
    assert "claim_status" in text
    assert "contributes_to" in text
    generated.write_text(text + "% tampered\n", encoding="utf-8")
    try:
        source_proposal.verify_package(
            package_root=root / "package",
            swipl=None,
            timeout_seconds=5,
            schemas=schemas,
        )
    except source_proposal.SourcePipelineError:
        return
    raise AssertionError(TAMPER_ACCEPTED)


def assert_link_only_is_rejected(
    source_proposal: object,
    root: Path,
    repository: Path,
    world: Path,
    schemas: dict,
) -> None:
    """Prove a link-only declaration cannot be snapshotted as source bytes."""
    try:
        source_proposal.snapshot_source(
            world_root=world,
            capsule_id="management.role-boundaries",
            source_id="link-only",
            proposal_id="link-only-v0",
            output=root / "link",
            repository_root=repository,
            allow_network=False,
            max_bytes=100_000,
            schemas=schemas,
            contracts_root=REPOSITORY_ROOT / "contracts",
        )
    except source_proposal.SourcePipelineError:
        return
    raise AssertionError(LINK_ONLY_ACCEPTED)
