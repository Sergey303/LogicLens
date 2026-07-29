#!/usr/bin/env python3
"""Cross-platform fail-closed checks for transactional runtime selection."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
from copy import deepcopy
from pathlib import Path

import apply_builder_activation_transaction as transaction
from transactional_runtime.selection import resolve_selected_runtime


class VerificationError(AssertionError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise VerificationError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_error(action, fragment: str) -> None:
    try:
        action()
    except Exception as exc:
        if fragment not in str(exc):
            raise VerificationError(
                f"expected error containing {fragment!r}, got {exc!r}"
            ) from exc
        return
    raise VerificationError(f"expected error containing {fragment!r}")


def contracts(repository: Path) -> tuple[Path, Path, Path]:
    root = repository / "contracts"
    return (
        root / "active-pointer-v0.schema.json",
        root / "activation-transaction-journal-v0.schema.json",
        root / "activation-transaction-attestation-v0.schema.json",
    )


def selected(repository: Path, deployment: Path):
    pointer, journal, attestation = contracts(repository)
    return resolve_selected_runtime(
        deployment_root=deployment,
        pointer_schema_path=pointer,
        journal_schema_path=journal,
        attestation_schema_path=attestation,
    )


def create_committed_deployment(repository: Path, root: Path):
    support = load_module(
        "builder_activation_transaction_fixture_for_selection",
        repository / "tests" / "builder_activation_transaction_test.py",
    )
    active, staged, _, _ = support.patched_decision_fixture(
        repository,
        root / "fixture",
    )
    pointer_schema_path, journal_schema_path, attestation_schema_path = contracts(
        repository
    )
    deployment = root / "deployment"
    previous = transaction.initialize_deployment(
        deployment_root=deployment,
        active_package=active,
        pointer_schema_path=pointer_schema_path,
        initialization_id="selection-init",
    )
    staged_manifest = transaction.read_json_object(
        staged / "manifest.json",
        "staged manifest",
    )
    target_hash = transaction.required_hash(
        staged_manifest,
        "packageHash",
        "staged manifest",
    )
    target_relative, _ = transaction.install_package(
        deployment_root=deployment,
        source_root=staged,
        epoch=0,
        revision=1,
        package_hash=target_hash,
        verify=lambda package: transaction.verify_staged_package(
            package,
            staged_manifest,
            0,
            1,
            target_hash,
        ),
    )
    decision_hash = "sha256:" + hashlib.sha256(b"selection-decision").hexdigest()
    target = transaction.build_pointer(
        generation=1,
        epoch=0,
        revision=1,
        package_hash=target_hash,
        package_path=target_relative,
        decision_hash=decision_hash,
        transaction_id="selection-commit",
    )
    journal_schema = transaction.read_json_object(
        journal_schema_path,
        "journal schema",
    )
    journal = transaction.build_journal(
        transaction_id="selection-commit",
        decision_hash=decision_hash,
        previous_pointer=previous,
        target_pointer=target,
    )
    journal = transaction.update_journal(journal, "committed")
    journal_path = deployment / "transactions" / "selection-commit.journal.json"
    transaction.write_journal(journal_path, journal, journal_schema)

    checks = {
        "decisionReverified": True,
        "currentMatched": True,
        "targetInstalled": True,
        "preSwitchRuntimePassed": True,
        "pointerSwapped": True,
        "postSwitchRuntimePassed": True,
        "rollbackPerformed": False,
        "rollbackRuntimePassed": False,
        "journalFinalized": True,
    }
    attestation = transaction.build_attestation(
        transaction_id="selection-commit",
        outcome="committed",
        decision_hash=decision_hash,
        before_pointer=previous,
        after_pointer=target,
        target_package_hash=target_hash,
        rollback_package_hash=previous["packageHash"],
        checks=checks,
        failure=None,
        journal_hash=journal["journalHash"],
        recovery="not-required",
        pointer_swapped=True,
    )
    attestation_schema = transaction.read_json_object(
        attestation_schema_path,
        "attestation schema",
    )
    transaction.validate_schema(
        attestation,
        attestation_schema,
        "activation attestation",
    )
    transaction.atomic_write_json(
        deployment / "transactions" / "selection-commit.attestation.json",
        attestation,
    )
    transaction.atomic_write_json(deployment / "current.json", target)
    return deployment, previous, target


def clone(source: Path, root: Path, name: str) -> Path:
    destination = root / name
    shutil.copytree(source, destination)
    return destination


def rewrite_pointer(deployment: Path, mutate) -> dict:
    path = deployment / "current.json"
    pointer = json.loads(path.read_text(encoding="utf-8"))
    mutate(pointer)
    pointer.pop("pointerHash", None)
    pointer["pointerHash"] = transaction.compute_pointer_hash(pointer)
    transaction.atomic_write_json(path, pointer)
    return pointer


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="logiclens-selected-runtime-") as tmp:
        root = Path(tmp)
        deployment, previous, target = create_committed_deployment(repository, root)

        runtime = selected(repository, deployment)
        if (runtime.generation, runtime.epoch, runtime.revision) != (1, 0, 1):
            raise VerificationError("committed selected runtime is not generation 1 / 0.1")
        if runtime.package_hash != target["packageHash"]:
            raise VerificationError("selected package hash differs")
        if runtime.transaction_id != "selection-commit":
            raise VerificationError("selected transaction identity differs")

        bad_hash = clone(deployment, root, "bad-pointer-hash")
        pointer_path = bad_hash / "current.json"
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        pointer["pointerHash"] = "sha256:" + "0" * 64
        transaction.atomic_write_json(pointer_path, pointer)
        expect_error(
            lambda: selected(repository, bad_hash),
            "active pointer hash does not match",
        )

        unsafe = clone(deployment, root, "unsafe-path")
        rewrite_pointer(unsafe, lambda value: value.__setitem__("packagePath", "../escape"))
        expect_error(lambda: selected(repository, unsafe), "active pointer failed schema")

        missing = clone(deployment, root, "missing-package")
        rewrite_pointer(
            missing,
            lambda value: value.__setitem__("packagePath", "packages/missing-package"),
        )
        expect_error(lambda: selected(repository, missing), "pointed package does not exist")

        stale_generation = clone(deployment, root, "stale-generation")
        rewrite_pointer(
            stale_generation,
            lambda value: value.__setitem__("generation", 2),
        )
        expect_error(
            lambda: selected(repository, stale_generation),
            "current pointer differs from the attested final state",
        )

        wrong_package = clone(deployment, root, "wrong-package-hash")
        rewrite_pointer(
            wrong_package,
            lambda value: value.__setitem__(
                "packageHash",
                "sha256:" + hashlib.sha256(b"wrong-package").hexdigest(),
            ),
        )
        expect_error(lambda: selected(repository, wrong_package), "packageHash")

        tampered = clone(deployment, root, "tampered-package")
        selected_package = tampered.joinpath(*target["packagePath"].split("/"))
        with (selected_package / "entry.pl").open("ab") as stream:
            stream.write(b"\n% tampered\n")
        expect_error(lambda: selected(repository, tampered), "file hash differs")

        incomplete = clone(deployment, root, "incomplete-journal")
        pending = transaction.build_journal(
            transaction_id="pending",
            decision_hash=target["decisionHash"],
            previous_pointer=previous,
            target_pointer=target,
        )
        journal_schema = transaction.read_json_object(
            contracts(repository)[1],
            "journal schema",
        )
        transaction.write_journal(
            incomplete / "transactions" / "pending.journal.json",
            pending,
            journal_schema,
        )
        expect_error(lambda: selected(repository, incomplete), "incomplete transaction remains")

        rollback = clone(deployment, root, "rollback-pointer")
        transaction.atomic_write_json(rollback / "current.json", previous)
        rollback_runtime = selected(repository, rollback)
        if (rollback_runtime.generation, rollback_runtime.revision) != (0, 0):
            raise VerificationError("explicit rollback pointer did not select 0.0")

    print("Transactional runtime selection tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
