#!/usr/bin/env python3
"""Crash-safe activation of one reviewed LogicLens staged revision.

The transaction stores immutable package directories and atomically replaces only
``current.json``. A durable journal is written before the pointer swap. Any caught
post-swap error restores the previous pointer and verifies the rollback runtime.
An interrupted process is recovered fail-closed before another activation starts.
"""
from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
import shutil
import socket
import stat
import sys
import uuid
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from active_epoch.hashing import canonical_json_bytes, sha256
from builder_candidate.cli import tree_bytes, verify_active_baseline
from build_builder_activation_decision import (
    compute_decision_hash,
    validate_staged_package,
    verify_activation_decision,
)
from build_builder_staged_revision import run_request, validate_staged_runtime


UTF8 = "utf-8"
POINTER_DOMAIN = b"LogicLensActivePointer\0"
JOURNAL_DOMAIN = b"LogicLensActivationJournal\0"
ATTESTATION_DOMAIN = b"LogicLensActivationTransaction\0"
HASH_VERSION = bytes((1,))
TERMINAL_STATES = frozenset({"committed", "rolled-back"})


class ActivationTransactionError(RuntimeError):
    pass


class SimulatedCrash(BaseException):
    """Test-only interruption that deliberately bypasses rollback handling."""


class ActivationLock:
    def __init__(self, deployment_root: Path, transaction_id: str) -> None:
        self.path = deployment_root / ".activation.lock"
        self.transaction_id = transaction_id
        self.acquired = False

    def __enter__(self) -> "ActivationLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(2):
            try:
                descriptor = os.open(
                    self.path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600,
                )
            except FileExistsError:
                if attempt == 0 and remove_dead_local_lock(self.path):
                    continue
                owner = read_json_object_if_possible(self.path)
                raise ActivationTransactionError(
                    f"activation lock is held: {self.path}; owner={owner}"
                )
            payload = canonical_json_bytes(
                {
                    "schemaVersion": "0.1",
                    "transactionId": self.transaction_id,
                    "pid": os.getpid(),
                    "host": socket.gethostname(),
                }
            )
            try:
                os.write(descriptor, payload)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            self.acquired = True
            return self
        raise ActivationTransactionError("could not acquire activation lock")

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.acquired:
            try:
                self.path.unlink()
                fsync_directory(self.path.parent)
            except FileNotFoundError:
                pass
            self.acquired = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("initialize")
    initialize.add_argument("--deployment-root", required=True, type=Path)
    initialize.add_argument("--active-package", required=True, type=Path)
    initialize.add_argument("--pointer-schema", required=True, type=Path)
    initialize.add_argument("--initialization-id", required=True)

    activate = subparsers.add_parser("activate")
    activate.add_argument("--deployment-root", required=True, type=Path)
    activate.add_argument("--decision", required=True, type=Path)
    activate.add_argument("--staged", required=True, type=Path)
    activate.add_argument("--candidate-manifest", required=True, type=Path)
    activate.add_argument("--overlay-manifest", required=True, type=Path)
    activate.add_argument("--staged-schema", required=True, type=Path)
    activate.add_argument("--decision-schema", required=True, type=Path)
    activate.add_argument("--pointer-schema", required=True, type=Path)
    activate.add_argument("--journal-schema", required=True, type=Path)
    activate.add_argument("--attestation-schema", required=True, type=Path)
    activate.add_argument("--transaction-id", required=True)
    activate.add_argument("--attestation-output", type=Path)
    activate.add_argument("--swipl", default="swipl")
    activate.add_argument("--timeout-ms", type=int, default=30_000)
    activate.add_argument(
        "--test-failure-point",
        choices=(
            "after-install",
            "before-swap",
            "after-swap",
            "during-post-smoke",
            "crash-after-swap",
        ),
        help=argparse.SUPPRESS,
    )

    recover = subparsers.add_parser("recover")
    recover.add_argument("--deployment-root", required=True, type=Path)
    recover.add_argument("--pointer-schema", required=True, type=Path)
    recover.add_argument("--journal-schema", required=True, type=Path)
    recover.add_argument("--attestation-schema", required=True, type=Path)
    recover.add_argument("--swipl", default="swipl")
    recover.add_argument("--timeout-ms", type=int, default=30_000)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--deployment-root", required=True, type=Path)
    verify.add_argument("--pointer-schema", required=True, type=Path)
    verify.add_argument("--journal-schema", required=True, type=Path)
    verify.add_argument("--attestation-schema", required=True, type=Path)
    verify.add_argument("--attestation", type=Path)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if hasattr(args, "timeout_ms") and not 100 <= args.timeout_ms <= 60_000:
        raise ActivationTransactionError("timeout-ms must be between 100 and 60000")

    if args.command == "initialize":
        pointer = initialize_deployment(
            deployment_root=args.deployment_root,
            active_package=args.active_package,
            pointer_schema_path=args.pointer_schema,
            initialization_id=args.initialization_id,
        )
        print("Initialized transactional deployment.")
        print(f"Current: {pointer['epoch']}.{pointer['revision']}")
        print(f"Package: {pointer['packageHash']}")
        print(f"Pointer: {(args.deployment_root.resolve() / 'current.json')}")
        return 0

    if args.command == "activate":
        attestation = activate_revision(
            deployment_root=args.deployment_root,
            decision_path=args.decision,
            staged_root=args.staged,
            candidate_manifest_path=args.candidate_manifest,
            overlay_manifest_path=args.overlay_manifest,
            staged_schema_path=args.staged_schema,
            decision_schema_path=args.decision_schema,
            pointer_schema_path=args.pointer_schema,
            journal_schema_path=args.journal_schema,
            attestation_schema_path=args.attestation_schema,
            transaction_id=args.transaction_id,
            swipl=args.swipl,
            timeout_seconds=args.timeout_ms / 1000.0,
            attestation_output=args.attestation_output,
            failure_point=args.test_failure_point,
        )
        print("Activation transaction committed.")
        print(
            f"Current: {attestation['afterPointer']['epoch']}."
            f"{attestation['afterPointer']['revision']}"
        )
        print(f"Transaction hash: {attestation['transactionHash']}")
        print("Rollback package retained and verified.")
        return 0

    if args.command == "recover":
        deployment = args.deployment_root.resolve()
        with ActivationLock(deployment, "recovery"):
            recovered = recover_pending_transactions(
                deployment_root=deployment,
                pointer_schema=read_json_object(args.pointer_schema, "pointer schema"),
                journal_schema=read_json_object(args.journal_schema, "journal schema"),
                attestation_schema=read_json_object(
                    args.attestation_schema,
                    "attestation schema",
                ),
                swipl=args.swipl,
                timeout_seconds=args.timeout_ms / 1000.0,
            )
        print(f"Recovered transactions: {len(recovered)}")
        for item in recovered:
            print(f"  {item['transactionId']}: {item['outcome']}")
        return 0

    verify_deployment(
        deployment_root=args.deployment_root,
        pointer_schema_path=args.pointer_schema,
        journal_schema_path=args.journal_schema,
        attestation_schema_path=args.attestation_schema,
        attestation_path=args.attestation,
    )
    print("Transactional deployment verified.")
    return 0


def initialize_deployment(
    *,
    deployment_root: Path,
    active_package: Path,
    pointer_schema_path: Path,
    initialization_id: str,
) -> dict[str, Any]:
    validate_identifier(initialization_id)
    deployment = deployment_root.resolve()
    source = active_package.resolve()
    if deployment == source or deployment in source.parents or source in deployment.parents:
        raise ActivationTransactionError("deployment root and source package must be separate")
    if (deployment / "current.json").exists():
        raise ActivationTransactionError("deployment is already initialized")
    if deployment.exists() and any(deployment.iterdir()):
        raise ActivationTransactionError("new deployment root must be absent or empty")
    deployment.mkdir(parents=True, exist_ok=True)
    (deployment / "packages").mkdir()
    (deployment / "transactions").mkdir()

    files = tree_bytes(source)
    manifest = verify_active_baseline(files)
    package_hash = required_hash(manifest, "packageHash", "active manifest")
    epoch = required_nonnegative_int(manifest, "epoch", "active manifest")
    revision = required_nonnegative_int(manifest, "baseRevision", "active manifest")
    package_relative, installed = install_package(
        deployment_root=deployment,
        source_root=source,
        epoch=epoch,
        revision=revision,
        package_hash=package_hash,
        verify=lambda root: verify_active_package(root, epoch, revision, package_hash),
    )
    if not installed.is_dir():
        raise ActivationTransactionError("initial package installation failed")

    pointer_schema = read_json_object(pointer_schema_path, "pointer schema")
    pointer = build_pointer(
        generation=0,
        epoch=epoch,
        revision=revision,
        package_hash=package_hash,
        package_path=package_relative,
        decision_hash=None,
        transaction_id=initialization_id,
    )
    validate_schema(pointer, pointer_schema, "active pointer")
    atomic_write_json(deployment / "current.json", pointer)
    return pointer


def activate_revision(
    *,
    deployment_root: Path,
    decision_path: Path,
    staged_root: Path,
    candidate_manifest_path: Path,
    overlay_manifest_path: Path,
    staged_schema_path: Path,
    decision_schema_path: Path,
    pointer_schema_path: Path,
    journal_schema_path: Path,
    attestation_schema_path: Path,
    transaction_id: str,
    swipl: str,
    timeout_seconds: float,
    attestation_output: Path | None,
    failure_point: str | None,
) -> dict[str, Any]:
    validate_identifier(transaction_id)
    deployment = deployment_root.resolve()
    pointer_schema = read_json_object(pointer_schema_path, "pointer schema")
    journal_schema = read_json_object(journal_schema_path, "journal schema")
    attestation_schema = read_json_object(attestation_schema_path, "attestation schema")
    deployment_required(deployment)

    with ActivationLock(deployment, transaction_id):
        recovered = recover_pending_transactions(
            deployment_root=deployment,
            pointer_schema=pointer_schema,
            journal_schema=journal_schema,
            attestation_schema=attestation_schema,
            swipl=swipl,
            timeout_seconds=timeout_seconds,
        )
        if recovered:
            raise ActivationTransactionError(
                "an interrupted activation was recovered; rerun the requested activation"
            )

        previous = read_and_verify_pointer(deployment, pointer_schema)
        previous_package = resolve_pointer_package(deployment, previous)
        verify_pointer_package(previous_package, previous)

        decision = verify_activation_decision(
            decision_path=decision_path,
            staged_root=staged_root,
            active_root=previous_package,
            candidate_manifest_path=candidate_manifest_path,
            overlay_manifest_path=overlay_manifest_path,
            staged_schema_path=staged_schema_path,
            decision_schema_path=decision_schema_path,
            swipl=swipl,
            timeout_seconds=timeout_seconds,
        )
        if compute_decision_hash(decision) != decision.get("decisionHash"):
            raise ActivationTransactionError("decisionHash changed after verification")
        require_pointer_matches_decision(previous, decision)

        target = required_object(decision, "target", "activation decision")
        target_epoch = required_nonnegative_int(target, "epoch", "decision target")
        target_revision = required_nonnegative_int(target, "revision", "decision target")
        target_hash = required_hash(target, "packageHash", "decision target")

        staged_manifest = read_json_object(staged_root / "manifest.json", "staged manifest")
        target_relative, target_package = install_package(
            deployment_root=deployment,
            source_root=staged_root.resolve(),
            epoch=target_epoch,
            revision=target_revision,
            package_hash=target_hash,
            verify=lambda root: verify_staged_package(
                root,
                staged_manifest,
                target_epoch,
                target_revision,
                target_hash,
            ),
        )
        if failure_point == "after-install":
            raise ActivationTransactionError("injected failure after target installation")

        candidate_manifest = read_json_object(candidate_manifest_path, "candidate manifest")
        overlay_manifest = read_json_object(overlay_manifest_path, "overlay manifest")
        validate_staged_runtime(
            staged_root=target_package,
            active_root=previous_package,
            candidate_manifest=candidate_manifest,
            overlay_manifest=overlay_manifest,
            swipl=swipl,
            timeout_seconds=timeout_seconds,
        )

        target_pointer = build_pointer(
            generation=required_nonnegative_int(previous, "generation", "active pointer") + 1,
            epoch=target_epoch,
            revision=target_revision,
            package_hash=target_hash,
            package_path=target_relative,
            decision_hash=required_hash(decision, "decisionHash", "activation decision"),
            transaction_id=transaction_id,
        )
        validate_schema(target_pointer, pointer_schema, "target active pointer")

        journal = build_journal(
            transaction_id=transaction_id,
            decision_hash=required_hash(decision, "decisionHash", "activation decision"),
            previous_pointer=previous,
            target_pointer=target_pointer,
        )
        journal_path = deployment / "transactions" / f"{transaction_id}.journal.json"
        attestation_path = deployment / "transactions" / f"{transaction_id}.attestation.json"
        if journal_path.exists() or attestation_path.exists():
            raise ActivationTransactionError(
                f"transaction id already exists in deployment: {transaction_id}"
            )
        write_journal(journal_path, journal, journal_schema)

        checks = {
            "decisionReverified": True,
            "currentMatched": True,
            "targetInstalled": True,
            "preSwitchRuntimePassed": True,
            "pointerSwapped": False,
            "postSwitchRuntimePassed": False,
            "rollbackPerformed": False,
            "rollbackRuntimePassed": False,
            "journalFinalized": False,
        }
        pointer_swapped = False
        try:
            if failure_point == "before-swap":
                raise ActivationTransactionError("injected failure before pointer swap")
            current_again = read_and_verify_pointer(deployment, pointer_schema)
            if current_again != previous:
                raise ActivationTransactionError(
                    "compare-and-swap failed: active pointer changed before mutation"
                )

            atomic_write_json(deployment / "current.json", target_pointer)
            pointer_swapped = True
            checks["pointerSwapped"] = True
            journal = update_journal(journal, "switched")
            write_journal(journal_path, journal, journal_schema)

            if failure_point == "crash-after-swap":
                raise SimulatedCrash("injected process crash after pointer swap")
            if failure_point == "after-swap":
                raise ActivationTransactionError("injected failure after pointer swap")

            journal = update_journal(journal, "verifying")
            write_journal(journal_path, journal, journal_schema)
            selected = read_and_verify_pointer(deployment, pointer_schema)
            if selected != target_pointer:
                raise ActivationTransactionError("post-switch pointer differs from target")
            selected_package = resolve_pointer_package(deployment, selected)
            verify_pointer_package(selected_package, selected)
            if failure_point == "during-post-smoke":
                raise ActivationTransactionError("injected failure during post-switch smoke")
            validate_staged_runtime(
                staged_root=selected_package,
                active_root=previous_package,
                candidate_manifest=candidate_manifest,
                overlay_manifest=overlay_manifest,
                swipl=swipl,
                timeout_seconds=timeout_seconds,
            )
            checks["postSwitchRuntimePassed"] = True

            journal = update_journal(journal, "committed")
            write_journal(journal_path, journal, journal_schema)
            checks["journalFinalized"] = True
            attestation = build_attestation(
                transaction_id=transaction_id,
                outcome="committed",
                decision_hash=decision["decisionHash"],
                before_pointer=previous,
                after_pointer=target_pointer,
                target_package_hash=target_hash,
                rollback_package_hash=previous["packageHash"],
                checks=checks,
                failure=None,
                journal_hash=journal["journalHash"],
                recovery="not-required",
                pointer_swapped=True,
            )
            validate_schema(attestation, attestation_schema, "activation attestation")
            atomic_write_json(attestation_path, attestation)
            copy_attestation(attestation_output, attestation)
            return attestation
        except SimulatedCrash:
            raise
        except Exception as exc:
            rollback_error: Exception | None = None
            checks["rollbackPerformed"] = pointer_swapped
            try:
                journal = update_journal(
                    journal,
                    "rolling-back",
                    error=str(exc),
                )
                write_journal(journal_path, journal, journal_schema)
                current = read_and_verify_pointer(deployment, pointer_schema)
                if current == target_pointer:
                    atomic_write_json(deployment / "current.json", previous)
                elif current != previous:
                    raise ActivationTransactionError(
                        "cannot rollback: current pointer is neither target nor previous"
                    )
                verify_pointer_package(previous_package, previous)
                verify_runtime_health(
                    swipl=swipl,
                    package=previous_package,
                    pointer=previous,
                    timeout_seconds=timeout_seconds,
                )
                checks["rollbackRuntimePassed"] = True
                journal = update_journal(
                    journal,
                    "rolled-back",
                    error=str(exc),
                    rollback_verified=True,
                )
                write_journal(journal_path, journal, journal_schema)
                checks["journalFinalized"] = True
                attestation = build_attestation(
                    transaction_id=transaction_id,
                    outcome="rolled-back",
                    decision_hash=decision["decisionHash"],
                    before_pointer=previous,
                    after_pointer=previous,
                    target_package_hash=target_hash,
                    rollback_package_hash=previous["packageHash"],
                    checks=checks,
                    failure=str(exc),
                    journal_hash=journal["journalHash"],
                    recovery="not-required",
                    pointer_swapped=pointer_swapped,
                )
                validate_schema(attestation, attestation_schema, "rollback attestation")
                atomic_write_json(attestation_path, attestation)
                copy_attestation(attestation_output, attestation)
            except Exception as rollback_exc:
                rollback_error = rollback_exc
                journal = update_journal(
                    journal,
                    "rollback-failed",
                    error=f"activation={exc}; rollback={rollback_exc}",
                    rollback_verified=False,
                )
                write_journal(journal_path, journal, journal_schema)
            if rollback_error is not None:
                raise ActivationTransactionError(
                    f"activation failed and rollback failed: {rollback_error}"
                ) from exc
            raise ActivationTransactionError(
                f"activation failed; previous pointer restored and verified: {exc}"
            ) from exc


def recover_pending_transactions(
    *,
    deployment_root: Path,
    pointer_schema: dict[str, Any],
    journal_schema: dict[str, Any],
    attestation_schema: dict[str, Any],
    swipl: str,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    transactions = deployment_root / "transactions"
    transactions.mkdir(parents=True, exist_ok=True)
    recovered: list[dict[str, Any]] = []
    for journal_path in sorted(transactions.glob("*.journal.json")):
        journal = read_json_object(journal_path, "transaction journal")
        validate_schema(journal, journal_schema, "transaction journal")
        if compute_journal_hash(journal) != journal.get("journalHash"):
            raise ActivationTransactionError(
                f"journal hash does not match its payload: {journal_path}"
            )
        if journal.get("state") in TERMINAL_STATES:
            continue
        previous = required_object(journal, "previousPointer", "transaction journal")
        target = required_object(journal, "targetPointer", "transaction journal")
        validate_pointer(previous, pointer_schema)
        validate_pointer(target, pointer_schema)
        current = read_and_verify_pointer(deployment_root, pointer_schema)
        if current == target:
            atomic_write_json(deployment_root / "current.json", previous)
        elif current != previous:
            raise ActivationTransactionError(
                f"cannot recover {journal_path.name}: current pointer is unexpected"
            )
        previous_package = resolve_pointer_package(deployment_root, previous)
        verify_pointer_package(previous_package, previous)
        verify_runtime_health(
            swipl=swipl,
            package=previous_package,
            pointer=previous,
            timeout_seconds=timeout_seconds,
        )
        journal = update_journal(
            journal,
            "rolled-back",
            error="recovered incomplete activation transaction",
            rollback_verified=True,
        )
        write_journal(journal_path, journal, journal_schema)
        checks = {
            "decisionReverified": False,
            "currentMatched": True,
            "targetInstalled": True,
            "preSwitchRuntimePassed": False,
            "pointerSwapped": current == target,
            "postSwitchRuntimePassed": False,
            "rollbackPerformed": current == target,
            "rollbackRuntimePassed": True,
            "journalFinalized": True,
        }
        attestation = build_attestation(
            transaction_id=required_string(journal, "transactionId", "transaction journal"),
            outcome="rolled-back",
            decision_hash=required_hash(journal, "decisionHash", "transaction journal"),
            before_pointer=previous,
            after_pointer=previous,
            target_package_hash=required_hash(target, "packageHash", "target pointer"),
            rollback_package_hash=required_hash(previous, "packageHash", "previous pointer"),
            checks=checks,
            failure="recovered incomplete activation transaction",
            journal_hash=journal["journalHash"],
            recovery="performed",
            pointer_swapped=current == target,
        )
        validate_schema(attestation, attestation_schema, "recovery attestation")
        attestation_path = transactions / (
            f"{journal['transactionId']}.attestation.json"
        )
        atomic_write_json(attestation_path, attestation)
        recovered.append(attestation)
    return recovered


def verify_deployment(
    *,
    deployment_root: Path,
    pointer_schema_path: Path,
    journal_schema_path: Path,
    attestation_schema_path: Path,
    attestation_path: Path | None,
) -> None:
    deployment = deployment_root.resolve()
    deployment_required(deployment)
    pointer_schema = read_json_object(pointer_schema_path, "pointer schema")
    journal_schema = read_json_object(journal_schema_path, "journal schema")
    attestation_schema = read_json_object(attestation_schema_path, "attestation schema")
    pointer = read_and_verify_pointer(deployment, pointer_schema)
    verify_pointer_package(resolve_pointer_package(deployment, pointer), pointer)
    for path in sorted((deployment / "transactions").glob("*.journal.json")):
        journal = read_json_object(path, "transaction journal")
        validate_schema(journal, journal_schema, "transaction journal")
        if compute_journal_hash(journal) != journal.get("journalHash"):
            raise ActivationTransactionError(f"journalHash differs: {path}")
        if journal.get("state") not in TERMINAL_STATES:
            raise ActivationTransactionError(f"incomplete transaction remains: {path}")
    if attestation_path is not None:
        attestation = read_json_object(attestation_path, "activation attestation")
        validate_schema(attestation, attestation_schema, "activation attestation")
        if compute_attestation_hash(attestation) != attestation.get("transactionHash"):
            raise ActivationTransactionError("transactionHash differs")
        expected_pointer = (
            attestation.get("afterPointer")
            if attestation.get("outcome") == "committed"
            else attestation.get("beforePointer")
        )
        if pointer != expected_pointer:
            raise ActivationTransactionError(
                "current pointer differs from the attested final state"
            )


def install_package(
    *,
    deployment_root: Path,
    source_root: Path,
    epoch: int,
    revision: int,
    package_hash: str,
    verify,
) -> tuple[str, Path]:
    if not source_root.is_dir():
        raise ActivationTransactionError(f"source package does not exist: {source_root}")
    name = package_directory_name(epoch, revision, package_hash)
    relative = f"packages/{name}"
    final = deployment_root / "packages" / name
    if final.exists():
        verify(final)
        return relative, final
    temporary = deployment_root / "packages" / f".incoming-{name}-{uuid.uuid4().hex}"
    if temporary.exists():
        raise ActivationTransactionError(f"incoming package already exists: {temporary}")
    try:
        shutil.copytree(source_root, temporary, copy_function=copy_file_durable)
        verify(temporary)
        fsync_tree(temporary)
        durable_move(temporary, final, replace_existing=False)
        verify(final)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
    return relative, final


def verify_active_package(root: Path, epoch: int, revision: int, package_hash: str) -> None:
    manifest = verify_active_baseline(tree_bytes(root))
    if (
        manifest.get("epoch") != epoch
        or manifest.get("baseRevision") != revision
        or manifest.get("packageHash") != package_hash
    ):
        raise ActivationTransactionError("active package identity differs")


def verify_staged_package(
    root: Path,
    expected_manifest: dict[str, Any],
    epoch: int,
    revision: int,
    package_hash: str,
) -> None:
    manifest = read_json_object(root / "manifest.json", "staged manifest")
    if manifest != expected_manifest:
        raise ActivationTransactionError("installed staged manifest differs from source")
    validate_staged_package(root, manifest)
    target = required_object(manifest, "target", "staged manifest")
    if (
        target.get("epoch") != epoch
        or target.get("revision") != revision
        or manifest.get("packageHash") != package_hash
    ):
        raise ActivationTransactionError("staged package identity differs")


def verify_pointer_package(package: Path, pointer: dict[str, Any]) -> None:
    manifest = read_json_object(package / "manifest.json", "pointed package manifest")
    stage = manifest.get("stage")
    if stage == "active":
        verify_active_package(
            package,
            required_nonnegative_int(pointer, "epoch", "active pointer"),
            required_nonnegative_int(pointer, "revision", "active pointer"),
            required_hash(pointer, "packageHash", "active pointer"),
        )
        return
    if stage == "staged-revision":
        validate_staged_package(package, manifest)
        target = required_object(manifest, "target", "staged manifest")
        if (
            target.get("epoch") != pointer.get("epoch")
            or target.get("revision") != pointer.get("revision")
            or manifest.get("packageHash") != pointer.get("packageHash")
        ):
            raise ActivationTransactionError("pointer differs from staged package identity")
        return
    raise ActivationTransactionError(f"unsupported pointed package stage: {stage}")


def verify_runtime_health(
    *,
    swipl: str,
    package: Path,
    pointer: dict[str, Any],
    timeout_seconds: float,
) -> None:
    request = {
        "protocolVersion": "0.1",
        "requestId": "activation-rollback-health",
        "command": "health",
        "epoch": pointer["epoch"],
        "revision": pointer["revision"],
        "options": {},
    }
    code, response, _ = run_request(swipl, package, request, timeout_seconds)
    if (
        code != 0
        or response.get("status") != "ok"
        or response.get("epoch") != pointer["epoch"]
        or response.get("revision") != pointer["revision"]
    ):
        raise ActivationTransactionError(
            f"rollback runtime health failed: code={code}; response={response}"
        )


def build_pointer(
    *,
    generation: int,
    epoch: int,
    revision: int,
    package_hash: str,
    package_path: str,
    decision_hash: str | None,
    transaction_id: str,
) -> dict[str, Any]:
    pointer: dict[str, Any] = {
        "schemaVersion": "0.1",
        "stage": "active-pointer",
        "generation": generation,
        "epoch": epoch,
        "revision": revision,
        "packageHash": package_hash,
        "packagePath": package_path,
        "decisionHash": decision_hash,
        "transactionId": transaction_id,
    }
    pointer["pointerHash"] = compute_record_hash(POINTER_DOMAIN, pointer, "pointerHash")
    return pointer


def build_journal(
    *,
    transaction_id: str,
    decision_hash: str,
    previous_pointer: dict[str, Any],
    target_pointer: dict[str, Any],
) -> dict[str, Any]:
    journal: dict[str, Any] = {
        "schemaVersion": "0.1",
        "stage": "activation-transaction-journal",
        "transactionId": transaction_id,
        "sequence": 0,
        "state": "prepared",
        "decisionHash": decision_hash,
        "previousPointer": deepcopy(previous_pointer),
        "targetPointer": deepcopy(target_pointer),
        "error": None,
        "rollbackVerified": False,
    }
    journal["journalHash"] = compute_record_hash(JOURNAL_DOMAIN, journal, "journalHash")
    return journal


def update_journal(
    journal: dict[str, Any],
    state: str,
    *,
    error: str | None = None,
    rollback_verified: bool | None = None,
) -> dict[str, Any]:
    result = deepcopy(journal)
    result["sequence"] = required_nonnegative_int(result, "sequence", "journal") + 1
    result["state"] = state
    if error is not None:
        result["error"] = error[:4000]
    if rollback_verified is not None:
        result["rollbackVerified"] = rollback_verified
    result.pop("journalHash", None)
    result["journalHash"] = compute_record_hash(JOURNAL_DOMAIN, result, "journalHash")
    return result


def build_attestation(
    *,
    transaction_id: str,
    outcome: str,
    decision_hash: str,
    before_pointer: dict[str, Any],
    after_pointer: dict[str, Any],
    target_package_hash: str,
    rollback_package_hash: str,
    checks: dict[str, bool],
    failure: str | None,
    journal_hash: str,
    recovery: str,
    pointer_swapped: bool,
) -> dict[str, Any]:
    attestation: dict[str, Any] = {
        "schemaVersion": "0.1",
        "stage": "activation-transaction-attestation",
        "transactionId": transaction_id,
        "outcome": outcome,
        "decisionHash": decision_hash,
        "beforePointer": deepcopy(before_pointer),
        "afterPointer": deepcopy(after_pointer),
        "targetPackageHash": target_package_hash,
        "rollbackPackageHash": rollback_package_hash,
        "checks": deepcopy(checks),
        "failure": failure,
        "journalHash": journal_hash,
        "intent": {
            "apply": (
                "performed"
                if outcome == "committed"
                else ("rolled-back" if pointer_swapped else "not-performed")
            ),
            "activePointerUpdate": (
                "performed"
                if outcome == "committed"
                else ("restored" if pointer_swapped else "not-performed")
            ),
            "recovery": recovery,
        },
    }
    attestation["transactionHash"] = compute_record_hash(
        ATTESTATION_DOMAIN,
        attestation,
        "transactionHash",
    )
    return attestation


def compute_record_hash(domain: bytes, record: dict[str, Any], field: str) -> str:
    payload = deepcopy(record)
    payload.pop(field, None)
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(HASH_VERSION)
    digest.update(canonical_json_bytes(payload))
    return "sha256:" + digest.hexdigest()


def compute_pointer_hash(pointer: dict[str, Any]) -> str:
    return compute_record_hash(POINTER_DOMAIN, pointer, "pointerHash")


def compute_journal_hash(journal: dict[str, Any]) -> str:
    return compute_record_hash(JOURNAL_DOMAIN, journal, "journalHash")


def compute_attestation_hash(attestation: dict[str, Any]) -> str:
    return compute_record_hash(ATTESTATION_DOMAIN, attestation, "transactionHash")


def read_and_verify_pointer(
    deployment_root: Path,
    pointer_schema: dict[str, Any],
) -> dict[str, Any]:
    pointer = read_json_object(deployment_root / "current.json", "active pointer")
    validate_pointer(pointer, pointer_schema)
    return pointer


def validate_pointer(pointer: dict[str, Any], schema: dict[str, Any]) -> None:
    validate_schema(pointer, schema, "active pointer")
    if compute_pointer_hash(pointer) != pointer.get("pointerHash"):
        raise ActivationTransactionError("active pointer hash does not match its payload")


def resolve_pointer_package(deployment_root: Path, pointer: dict[str, Any]) -> Path:
    raw = required_string(pointer, "packagePath", "active pointer")
    relative = PurePosixPath(raw)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ActivationTransactionError("active pointer packagePath is unsafe")
    if relative.parts[0] != "packages" or len(relative.parts) != 2:
        raise ActivationTransactionError("active pointer must reference one immutable package")
    path = deployment_root.joinpath(*relative.parts)
    if path.is_symlink() or not path.is_dir():
        raise ActivationTransactionError(f"pointed package does not exist: {path}")
    resolved = path.resolve()
    packages = (deployment_root / "packages").resolve()
    if resolved.parent != packages:
        raise ActivationTransactionError("pointed package escapes deployment packages")
    tree_bytes(resolved)
    return resolved


def require_pointer_matches_decision(
    pointer: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    expected = required_object(decision, "expectedCurrent", "activation decision")
    if (
        pointer.get("epoch") != expected.get("epoch")
        or pointer.get("revision") != expected.get("revision")
        or pointer.get("packageHash") != expected.get("packageHash")
    ):
        raise ActivationTransactionError(
            "stale activation decision: current pointer differs from expectedCurrent"
        )
    rollback = required_object(decision, "rollback", "activation decision")
    if rollback != expected:
        raise ActivationTransactionError("decision rollback differs from expectedCurrent")


def write_journal(path: Path, journal: dict[str, Any], schema: dict[str, Any]) -> None:
    if compute_journal_hash(journal) != journal.get("journalHash"):
        raise ActivationTransactionError("journalHash differs before write")
    validate_schema(journal, schema, "transaction journal")
    atomic_write_json(path, journal)


def copy_attestation(output: Path | None, attestation: dict[str, Any]) -> None:
    if output is None:
        return
    destination = output.resolve()
    if destination.exists():
        raise ActivationTransactionError(f"attestation output already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(destination, attestation)


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        view = memoryview(canonical_json_bytes(value))
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        durable_move(temporary, path, replace_existing=True)
    finally:
        if temporary.exists():
            temporary.unlink()


def durable_move(source: Path, destination: Path, *, replace_existing: bool) -> None:
    if os.name == "nt":
        flags = 0x00000008
        if replace_existing:
            flags |= 0x00000001
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        move = kernel32.MoveFileExW
        move.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        move.restype = ctypes.c_int
        if not move(str(source), str(destination), flags):
            error = ctypes.get_last_error()
            raise OSError(error, os.strerror(error), str(destination))
        return
    if replace_existing:
        os.replace(source, destination)
    else:
        os.rename(source, destination)
    fsync_directory(destination.parent)


def copy_file_durable(source: str, destination: str) -> str:
    result = shutil.copy2(source, destination)
    with open(result, "rb") as stream:
        os.fsync(stream.fileno())
    return result


def fsync_tree(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ActivationTransactionError(f"symlink is forbidden: {path}")
        if path.is_file():
            with path.open("rb") as stream:
                os.fsync(stream.fileno())
    directories = [path for path in root.rglob("*") if path.is_dir()]
    for path in sorted(directories, reverse=True):
        fsync_directory(path)
    fsync_directory(root)


def fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def remove_dead_local_lock(path: Path) -> bool:
    owner = read_json_object_if_possible(path)
    if not isinstance(owner, dict):
        return False
    if owner.get("host") != socket.gethostname():
        return False
    pid = owner.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return False
    if process_is_alive(pid):
        return False
    try:
        path.unlink()
        fsync_directory(path.parent)
    except FileNotFoundError:
        pass
    return True


def process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        if exc.errno == errno.EPERM:
            return True
        return False
    return True


def package_directory_name(epoch: int, revision: int, package_hash: str) -> str:
    digest = package_hash.removeprefix("sha256:")
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ActivationTransactionError("package hash is not lowercase sha256")
    return f"e{epoch:06d}-r{revision:06d}-{digest}"


def deployment_required(root: Path) -> None:
    if not root.is_dir():
        raise ActivationTransactionError(f"deployment root does not exist: {root}")
    for required in (root / "packages", root / "transactions", root / "current.json"):
        if not required.exists():
            raise ActivationTransactionError(f"deployment is incomplete: {required}")


def validate_identifier(value: str) -> None:
    import re

    if not re.fullmatch(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$", value):
        raise ActivationTransactionError(f"invalid identifier: {value}")


def validate_schema(value: dict[str, Any], schema: dict[str, Any], context: str) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: list(item.path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in errors[:5]
        )
        raise ActivationTransactionError(f"{context} schema validation failed: {details}")


def read_json_object(path: Path, context: str) -> dict[str, Any]:
    try:
        value = json.loads(path.resolve().read_text(encoding=UTF8))
    except (OSError, json.JSONDecodeError) as exc:
        raise ActivationTransactionError(f"cannot read {context} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ActivationTransactionError(f"{context} must be a JSON object: {path}")
    return value


def read_json_object_if_possible(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding=UTF8))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def required_object(value: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    result = value.get(key)
    if not isinstance(result, dict):
        raise ActivationTransactionError(f"{context}.{key} must be an object")
    return result


def required_string(value: dict[str, Any], key: str, context: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise ActivationTransactionError(f"{context}.{key} must be a non-empty string")
    return result


def required_hash(value: dict[str, Any], key: str, context: str) -> str:
    import re

    result = required_string(value, key, context)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", result):
        raise ActivationTransactionError(f"{context}.{key} must be a lowercase sha256 hash")
    return result


def required_nonnegative_int(value: dict[str, Any], key: str, context: str) -> int:
    result = value.get(key)
    if not isinstance(result, int) or isinstance(result, bool) or result < 0:
        raise ActivationTransactionError(f"{context}.{key} must be a non-negative integer")
    return result


def run_entry() -> int:
    try:
        return main()
    except SimulatedCrash as exc:
        print(f"Activation transaction interrupted: {exc}", file=sys.stderr)
        return 86
    except (ActivationTransactionError, OSError) as exc:
        print(f"Activation transaction failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run_entry())
