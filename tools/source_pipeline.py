#!/usr/bin/env python3
"""Build source-grounded assertion proposals and execute their lifecycle."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from capsule import CapsuleError
from source_proposal import (
    SourcePipelineError,
    execute_gate,
    finalize_activation,
    fragment_workspace,
    import_assertion_proposal,
    import_grounding_review,
    load_schemas,
    prepare_extraction,
    snapshot_source,
    stage_activation,
    verify_package,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contracts-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "contracts",
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        default=(
            Path(__file__).resolve().parents[1]
            / "prompts"
            / "generic"
            / "source-assertion-proposer.md"
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)

    snapshot = commands.add_parser("snapshot")
    snapshot.add_argument("--world-root", required=True, type=Path)
    snapshot.add_argument("--capsule", required=True)
    snapshot.add_argument("--source", required=True)
    snapshot.add_argument("--proposal-id", required=True)
    snapshot.add_argument("--output", required=True, type=Path)
    snapshot.add_argument("--repository-root", type=Path)
    snapshot.add_argument("--allow-network", action="store_true")
    snapshot.add_argument("--max-bytes", type=int, default=4 * 1024 * 1024)

    fragment = commands.add_parser("fragment")
    fragment.add_argument("--proposal", required=True, type=Path)

    prepare = commands.add_parser("prepare")
    prepare.add_argument("--world-root", required=True, type=Path)
    prepare.add_argument("--proposal", required=True, type=Path)

    propose = commands.add_parser("propose")
    propose.add_argument("--world-root", required=True, type=Path)
    propose.add_argument("--proposal", required=True, type=Path)
    propose.add_argument("--candidate", required=True, type=Path)

    review = commands.add_parser("review")
    review.add_argument("--proposal", required=True, type=Path)
    review.add_argument("--review", required=True, type=Path)

    gate = commands.add_parser("gate")
    gate.add_argument("--proposal", required=True, type=Path)
    gate.add_argument("--output", required=True, type=Path)
    gate.add_argument("--swipl", default="swipl")
    gate.add_argument("--timeout-seconds", type=int, default=30)

    verify = commands.add_parser("verify")
    verify.add_argument("--package", required=True, type=Path)
    verify.add_argument("--swipl")
    verify.add_argument("--timeout-seconds", type=int, default=30)

    stage = commands.add_parser("stage-activation")
    stage.add_argument("--package", required=True, type=Path)
    stage.add_argument("--world-root", required=True, type=Path)
    stage.add_argument("--output-world-root", required=True, type=Path)
    stage.add_argument("--expected-current-version", required=True)
    stage.add_argument("--new-version", required=True)
    stage.add_argument("--allow-provisional", action="store_true")
    stage.add_argument("--swipl", default="swipl")
    stage.add_argument("--timeout-seconds", type=int, default=30)

    finalize = commands.add_parser("finalize-activation")
    finalize.add_argument("--source-world-root", required=True, type=Path)
    finalize.add_argument("--staged-world-root", required=True, type=Path)
    finalize.add_argument("--output-world-root", required=True, type=Path)
    finalize.add_argument("--activation-id", required=True)
    finalize.add_argument("--expected-activation-hash", required=True)
    finalize.add_argument("--approve-provisional", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schemas = load_schemas(args.contracts_root)

    if args.command == "snapshot":
        item = snapshot_source(
            world_root=args.world_root,
            capsule_id=args.capsule,
            source_id=args.source,
            proposal_id=args.proposal_id,
            output=args.output,
            repository_root=args.repository_root,
            allow_network=args.allow_network,
            max_bytes=args.max_bytes,
            schemas=schemas,
            contracts_root=args.contracts_root,
        )
        print(f"Snapshotted source: {item['sourceId']}")
        print(f"Workspace hash: {item['workspaceHash']}")
        print(f"Output: {args.output.resolve()}")
        return 0

    if args.command == "fragment":
        item = fragment_workspace(args.proposal, schemas)
        print(f"Created fragments: {item['artifacts']['fragments']['count']}")
        print(f"Workspace hash: {item['workspaceHash']}")
        return 0

    if args.command == "prepare":
        item = prepare_extraction(
            world_root=args.world_root,
            proposal_root=args.proposal,
            prompt_path=args.prompt,
            schemas=schemas,
            contracts_root=args.contracts_root,
        )
        print("Prepared assertion extraction request")
        print(f"Workspace hash: {item['workspaceHash']}")
        return 0

    if args.command == "propose":
        item = import_assertion_proposal(
            world_root=args.world_root,
            proposal_root=args.proposal,
            candidate_path=args.candidate,
            schemas=schemas,
            contracts_root=args.contracts_root,
        )
        count = item["artifacts"]["assertionProposal"]["count"]
        print(f"Imported assertion proposal: {count} assertions")
        print(f"Workspace hash: {item['workspaceHash']}")
        return 0

    if args.command == "review":
        item = import_grounding_review(
            proposal_root=args.proposal,
            review_path=args.review,
            schemas=schemas,
        )
        print(
            "Imported source-grounding review: "
            f"{item['artifacts']['review']['class']}"
        )
        print(f"Workspace hash: {item['workspaceHash']}")
        return 0

    if args.command == "gate":
        item = execute_gate(
            proposal_root=args.proposal,
            output=args.output,
            swipl=args.swipl,
            timeout_seconds=args.timeout_seconds,
            schemas=schemas,
        )
        print(f"Source proposal gate passed: {item['proposalId']}")
        print(f"Review class: {item['reviewClass']}")
        print(f"Package hash: {item['packageHash']}")
        return 0

    if args.command == "stage-activation":
        item = stage_activation(
            package_root=args.package,
            world_root=args.world_root,
            output_world_root=args.output_world_root,
            expected_current_version=args.expected_current_version,
            new_version=args.new_version,
            allow_provisional=args.allow_provisional,
            swipl=args.swipl,
            timeout_seconds=args.timeout_seconds,
            schemas=schemas,
            contracts_root=args.contracts_root,
        )
        print(f"Staged source proposal activation: {item['activationId']}")
        print(
            "Capsule version: "
            f"{item['oldCapsuleVersion']} -> {item['newCapsuleVersion']}"
        )
        print(f"Assertions: {len(item['assertionIds'])}")
        print(f"Activation hash: {item['activationHash']}")
        print(f"Output world: {args.output_world_root.resolve()}")
        return 0

    if args.command == "finalize-activation":
        item = finalize_activation(
            source_world_root=args.source_world_root,
            staged_world_root=args.staged_world_root,
            output_world_root=args.output_world_root,
            activation_id=args.activation_id,
            expected_activation_hash=args.expected_activation_hash,
            approve_provisional=args.approve_provisional,
            contracts_root=args.contracts_root,
        )
        print(f"Finalized source proposal activation: {item['activationId']}")
        print(f"Status: {item['status']}")
        print(f"Activation hash: {item['activationHash']}")
        print(f"Output world: {args.output_world_root.resolve()}")
        return 0

    item = verify_package(
        package_root=args.package,
        swipl=args.swipl,
        timeout_seconds=args.timeout_seconds,
        schemas=schemas,
    )
    print(f"Verified source proposal package: {item['proposalId']}")
    print(f"Package hash: {item['packageHash']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SourcePipelineError, CapsuleError, OSError, ValueError) as exc:
        print(f"Source proposal pipeline failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
