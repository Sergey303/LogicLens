from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import apply_builder_activation_transaction as transaction


class SelectedRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True)
class SelectedRuntime:
    deployment_root: Path
    package_root: Path
    entry_path: Path
    generation: int
    epoch: int
    revision: int
    package_hash: str
    pointer_hash: str
    transaction_id: str
    decision_hash: str | None

    def as_json(self) -> dict[str, Any]:
        return {
            "schemaVersion": "0.1",
            "stage": "selected-runtime",
            "deploymentRoot": str(self.deployment_root),
            "packageRoot": str(self.package_root),
            "entryPath": str(self.entry_path),
            "generation": self.generation,
            "epoch": self.epoch,
            "revision": self.revision,
            "packageHash": self.package_hash,
            "pointerHash": self.pointer_hash,
            "transactionId": self.transaction_id,
            "decisionHash": self.decision_hash,
        }


def default_contract_paths(repository_root: Path) -> tuple[Path, Path, Path]:
    contracts = repository_root.resolve() / "contracts"
    return (
        contracts / "active-pointer-v0.schema.json",
        contracts / "activation-transaction-journal-v0.schema.json",
        contracts / "activation-transaction-attestation-v0.schema.json",
    )


def resolve_selected_runtime(
    *,
    deployment_root: Path,
    pointer_schema_path: Path,
    journal_schema_path: Path,
    attestation_schema_path: Path,
) -> SelectedRuntime:
    deployment = deployment_root.resolve()
    transaction.verify_deployment(
        deployment_root=deployment,
        pointer_schema_path=pointer_schema_path.resolve(),
        journal_schema_path=journal_schema_path.resolve(),
        attestation_schema_path=attestation_schema_path.resolve(),
        attestation_path=None,
    )

    pointer_schema = transaction.read_json_object(
        pointer_schema_path.resolve(),
        "active pointer schema",
    )
    pointer = transaction.read_and_verify_pointer(deployment, pointer_schema)
    package = transaction.resolve_pointer_package(deployment, pointer)
    transaction.verify_pointer_package(package, pointer)

    entry = package / "entry.pl"
    if entry.is_symlink() or not entry.is_file():
        raise SelectedRuntimeError(
            f"selected runtime entry point is unavailable or unsafe: {entry}"
        )

    generation = transaction.required_nonnegative_int(
        pointer,
        "generation",
        "active pointer",
    )
    epoch = transaction.required_nonnegative_int(pointer, "epoch", "active pointer")
    revision = transaction.required_nonnegative_int(
        pointer,
        "revision",
        "active pointer",
    )
    package_hash = transaction.required_hash(
        pointer,
        "packageHash",
        "active pointer",
    )
    pointer_hash = transaction.required_hash(
        pointer,
        "pointerHash",
        "active pointer",
    )
    transaction_id = transaction.required_string(
        pointer,
        "transactionId",
        "active pointer",
    )
    decision_hash = pointer.get("decisionHash")
    if decision_hash is not None:
        decision_hash = transaction.required_hash(
            pointer,
            "decisionHash",
            "active pointer",
        )

    return SelectedRuntime(
        deployment_root=deployment,
        package_root=package,
        entry_path=entry,
        generation=generation,
        epoch=epoch,
        revision=revision,
        package_hash=package_hash,
        pointer_hash=pointer_hash,
        transaction_id=transaction_id,
        decision_hash=decision_hash,
    )
