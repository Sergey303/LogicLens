#!/usr/bin/env python3
"""Compatibility entry that loads cli_runtime without importing handle_request/3."""
from __future__ import annotations

import build_builder_candidate_activation_overlay as base


_OLD_IMPORT = b":- use_module('cli_runtime.pl').\n"
_CLEAN_IMPORT = b":- use_module('cli_runtime.pl', []).\n"
_ORIGINAL_RENDER_REVISION_RUNTIME = base.render_revision_runtime


def render_revision_runtime_clean(**kwargs) -> bytes:
    """Render the reviewed wrapper with a load-only baseline-module import."""
    content = _ORIGINAL_RENDER_REVISION_RUNTIME(**kwargs)
    if content.count(_OLD_IMPORT) != 1:
        raise base.ActivationOverlayError(
            "expected exactly one baseline runtime import in the rendered overlay"
        )
    cleaned = content.replace(_OLD_IMPORT, _CLEAN_IMPORT, 1)
    if b"overrides weak import" in cleaned:
        raise base.ActivationOverlayError("rendered overlay contains warning text")
    return cleaned


def install() -> None:
    base.render_revision_runtime = render_revision_runtime_clean


install()

# Re-export the public operations used by scripts and tests.
ActivationOverlayError = base.ActivationOverlayError
create_overlay = base.create_overlay
verify_overlay = base.verify_overlay
write_overlay = base.write_overlay
compute_overlay_hash = base.compute_overlay_hash
read_declared_overlay_files = base.read_declared_overlay_files
main = base.main


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ActivationOverlayError, OSError, ValueError) as exc:
        print(f"Activation overlay failed: {exc}", file=base.sys.stderr)
        raise SystemExit(1) from exc
