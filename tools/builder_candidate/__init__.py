"""Provider-neutral candidate epoch packaging and verification."""

from __future__ import annotations

import re

from . import cli as _cli


# A Prolog directive starts a source line with `:-`. A rule body separator such
# as `candidate(X) :- epoch_data:fact(...)` must never be classified as a
# directive merely because the body begins with an identifier.
_cli.DIRECTIVE_NAME = re.compile(
    r"^\s*:-\s*([A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
_cli.USE_MODULE = re.compile(
    r"^\s*:-\s*use_module\s*\((.*?)\)\s*\.",
    re.MULTILINE | re.DOTALL,
)
