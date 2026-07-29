from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import apply_builder_activation_transaction as transaction
from build_builder_staged_revision import run_request

from .selection import (
    SelectedRuntimeError,
    default_contract_paths,
    resolve_selected_runtime,
)


ALLOWED_COMMANDS = frozenset(
    {
        "health",
        "inspect-facts",
        "entity-view",
        "subgraph",
        "derived-query",
    }
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve and invoke the package selected by transactional current.json."
        )
    )
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--deployment-root", required=True, type=Path)
    parser.add_argument("--pointer-schema", type=Path)
    parser.add_argument("--journal-schema", type=Path)
    parser.add_argument("--attestation-schema", type=Path)
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--timeout-ms", type=int, default=30_000)

    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("resolve")

    request = commands.add_parser("request")
    request.add_argument("--command", required=True, choices=sorted(ALLOWED_COMMANDS))
    request.add_argument("--request-id", default="selected-runtime-request")
    options = request.add_mutually_exclusive_group()
    options.add_argument("--options-json", default="{}")
    options.add_argument("--options-file", type=Path)
    return parser.parse_args()


def find_repository_root() -> Path:
    for start in (Path.cwd(), Path(__file__).resolve().parent):
        for candidate in (start, *start.parents):
            if (
                (candidate / "contracts" / "active-pointer-v0.schema.json").is_file()
                and (candidate / "tools" / "apply_builder_activation_transaction.py").is_file()
            ):
                return candidate.resolve()
    raise SelectedRuntimeError(
        "could not locate repository root; pass --repository-root explicitly"
    )


def parse_options(args: argparse.Namespace) -> dict[str, Any]:
    raw = (
        args.options_file.resolve().read_text(encoding="utf-8")
        if args.options_file is not None
        else args.options_json
    )
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise SelectedRuntimeError("request options must be one JSON object")
    return value


def main() -> int:
    args = parse_args()
    if not 100 <= args.timeout_ms <= 60_000:
        raise SelectedRuntimeError("timeout-ms must be between 100 and 60000")

    repository = (
        args.repository_root.resolve()
        if args.repository_root is not None
        else find_repository_root()
    )
    default_pointer, default_journal, default_attestation = default_contract_paths(
        repository
    )
    selected = resolve_selected_runtime(
        deployment_root=args.deployment_root,
        pointer_schema_path=args.pointer_schema or default_pointer,
        journal_schema_path=args.journal_schema or default_journal,
        attestation_schema_path=args.attestation_schema or default_attestation,
    )

    if args.action == "resolve":
        print(json.dumps(selected.as_json(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    swipl = shutil.which(args.swipl) or args.swipl
    request = {
        "protocolVersion": "0.1",
        "requestId": args.request_id,
        "command": args.command,
        "epoch": selected.epoch,
        "revision": selected.revision,
        "options": parse_options(args),
    }
    code, response, stderr = run_request(
        swipl,
        selected.package_root,
        request,
        args.timeout_ms / 1000.0,
    )
    if response.get("epoch") != selected.epoch or response.get("revision") != selected.revision:
        raise SelectedRuntimeError(
            "runtime response state differs from transactional current.json"
        )
    if code != 0 or response.get("status") != "ok":
        raise SelectedRuntimeError(
            "selected runtime rejected the request: "
            + json.dumps(response, ensure_ascii=False, sort_keys=True)
            + (f"; stderr={stderr.strip()}" if stderr.strip() else "")
        )

    envelope = {
        "schemaVersion": "0.1",
        "stage": "selected-runtime-response",
        "selection": selected.as_json(),
        "response": response,
    }
    print(json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def run_entry() -> int:
    try:
        return main()
    except (
        SelectedRuntimeError,
        transaction.ActivationTransactionError,
        OSError,
        ValueError,
    ) as exc:
        print(f"Transactional runtime launch failed: {exc}", file=sys.stderr)
        return 1
