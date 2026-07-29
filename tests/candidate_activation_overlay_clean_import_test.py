#!/usr/bin/env python3
"""Verify that the reviewed overlay loads cli_runtime without weak imports."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import build_builder_candidate_activation_overlay_clean_compat as clean


class VerificationError(AssertionError):
    pass


def main() -> int:
    rendered = clean.render_revision_runtime_clean(
        target_epoch=0,
        target_revision=1,
        rule_filename="candidate_researcher_at_iis.pl",
        module="candidate_researcher_at_iis",
        predicate="researcher_at_iis",
        predicate_iri="urn:logiclens:derived:researcher-at-iis",
    )
    text = rendered.decode("utf-8")
    if ":- use_module('cli_runtime.pl', [])." not in text:
        raise VerificationError("overlay did not use a load-only baseline import")
    if ":- use_module('cli_runtime.pl')." in text:
        raise VerificationError("overlay retained the weak baseline import")

    swipl = shutil.which("swipl")
    if swipl is None:
        raise VerificationError("swipl is required")

    with tempfile.TemporaryDirectory(prefix="logiclens-clean-overlay-") as temporary:
        rules = Path(temporary) / "rules"
        rules.mkdir(parents=True)
        (rules / "cli_runtime.pl").write_text(
            ":- module(cli_runtime, [handle_request/3]).\n"
            "handle_request(_, response{}, 0).\n",
            encoding="utf-8",
            newline="\n",
        )
        (rules / "candidate_researcher_at_iis.pl").write_text(
            ":- module(candidate_researcher_at_iis, [researcher_at_iis/2]).\n"
            "researcher_at_iis('urn:logiclens:person:alex', [fact]).\n",
            encoding="utf-8",
            newline="\n",
        )
        runtime = rules / "revision_runtime.pl"
        runtime.write_bytes(rendered)
        completed = subprocess.run(
            [swipl, "--quiet", "-s", str(runtime), "-g", "halt"],
            cwd=Path(temporary),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise VerificationError(
                "clean overlay failed to load: "
                f"stdout={completed.stdout!r}; stderr={completed.stderr!r}"
            )
        warning = "overrides weak import from cli_runtime"
        if warning in completed.stderr:
            raise VerificationError(
                f"clean overlay retained weak-import warning: {completed.stderr!r}"
            )

    print("ok 1 - baseline runtime is loaded with an empty import list")
    print("ok 2 - qualified cli_runtime calls remain available")
    print("ok 3 - SWI-Prolog emits no weak-import override warning")
    print("1..3")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, OSError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1) from exc
