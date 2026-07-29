#!/usr/bin/env python3
"""End-to-end and fault-injection checks for atomic Builder activation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path, PurePosixPath


class VerificationError(AssertionError):
    pass


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise VerificationError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict, canonical_json_bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def patched_decision_fixture(repository: Path, root: Path):
    base = load_module(
        "builder_activation_decision_fixture",
        repository / "tests" / "builder_activation_decision_test.py",
    )
    original = base.build_fixture

    def valid_hash(character: str) -> str:
        return "sha256:" + hashlib.sha256(character.encode("utf-8")).hexdigest()

    base.hash64 = valid_hash
    result = original(root)
    staged = result[1]
    runtime_path = staged / "rules" / "revision_runtime.pl"
    source = runtime_path.read_text(encoding="utf-8")
    old_call = "Response,\n            1\n        )"
    if source.count(old_call) != 2:
        raise VerificationError("fixture error paths changed")
    source = source.replace(
        old_call,
        "Response,\n            ExitCode\n        )",
    )
    tail = "        diagnostics: []\n    }.\n"
    position = source.rfind(tail)
    if position < 0:
        raise VerificationError("fixture error response tail is missing")
    source = (
        source[:position]
        + "        diagnostics: []\n    },\n    ExitCode = 1.\n"
        + source[position + len(tail):]
    )
    runtime_path.write_text(source, encoding="utf-8", newline="\n")

    manifest_path = staged / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload = base.tree_bytes(staged)
    payload.pop(PurePosixPath("manifest.json"), None)
    manifest["files"] = {
        str(path): base.sha256(content)
        for path, content in sorted(payload.items(), key=lambda item: str(item[0]))
    }
    manifest["packageHash"] = base.aggregate_hash(
        b"LogicLensStagedRevision\0",
        1,
        payload.items(),
    )
    write_json(manifest_path, manifest, base.canonical_json_bytes)
    return result


def make_inputs(repository: Path, root: Path, swipl: str):
    decision_module = load_module(
        "build_builder_activation_decision_for_transaction_test",
        repository / "tools" / "build_builder_activation_decision.py",
    )
    active, staged, candidate_manifest, overlay_manifest = patched_decision_fixture(
        repository,
        root / "fixture",
    )
    decision_path = root / "activation-decision.json"
    record = decision_module.create_activation_decision(
        decision_id="fixture-authorize",
        staged_root=staged,
        active_root=active,
        candidate_manifest_path=candidate_manifest,
        overlay_manifest_path=overlay_manifest,
        staged_schema_path=repository / "contracts" / "staged-revision-v0.schema.json",
        decision_schema_path=repository / "contracts" / "activation-decision-v0.schema.json",
        swipl=swipl,
        timeout_seconds=30.0,
    )
    write_json(decision_path, record, decision_module.canonical_json_bytes)
    return active, staged, candidate_manifest, overlay_manifest, decision_path


def initialize(transaction, repository: Path, deployment: Path, active: Path, identity: str):
    return transaction.initialize_deployment(
        deployment_root=deployment,
        active_package=active,
        pointer_schema_path=repository / "contracts" / "active-pointer-v0.schema.json",
        initialization_id=identity,
    )


def activate(
    transaction,
    repository: Path,
    deployment: Path,
    staged: Path,
    candidate: Path,
    overlay: Path,
    decision: Path,
    swipl: str,
    transaction_id: str,
    failure_point: str | None = None,
):
    return transaction.activate_revision(
        deployment_root=deployment,
        decision_path=decision,
        staged_root=staged,
        candidate_manifest_path=candidate,
        overlay_manifest_path=overlay,
        staged_schema_path=repository / "contracts" / "staged-revision-v0.schema.json",
        decision_schema_path=repository / "contracts" / "activation-decision-v0.schema.json",
        pointer_schema_path=repository / "contracts" / "active-pointer-v0.schema.json",
        journal_schema_path=repository / "contracts" / "activation-transaction-journal-v0.schema.json",
        attestation_schema_path=repository / "contracts" / "activation-transaction-attestation-v0.schema.json",
        transaction_id=transaction_id,
        swipl=swipl,
        timeout_seconds=30.0,
        attestation_output=None,
        failure_point=failure_point,
    )


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


def pointer(repository: Path, transaction, deployment: Path):
    schema = transaction.read_json_object(
        repository / "contracts" / "active-pointer-v0.schema.json",
        "pointer schema",
    )
    return transaction.read_and_verify_pointer(deployment, schema)


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    transaction = load_module(
        "apply_builder_activation_transaction_tested",
        repository / "tools" / "apply_builder_activation_transaction.py",
    )
    swipl = shutil.which("swipl")
    if swipl is None:
        raise VerificationError("SWI-Prolog is required")

    with tempfile.TemporaryDirectory(prefix="logiclens-activation-transaction-") as tmp:
        root = Path(tmp)
        active, staged, candidate, overlay, decision = make_inputs(
            repository,
            root,
            swipl,
        )

        # Successful compare-and-swap activation.
        deployment = root / "deployment-success"
        before = initialize(transaction, repository, deployment, active, "init-success")
        result = activate(
            transaction,
            repository,
            deployment,
            staged,
            candidate,
            overlay,
            decision,
            swipl,
            "tx-success",
        )
        after = pointer(repository, transaction, deployment)
        if result["outcome"] != "committed":
            raise VerificationError("successful activation was not committed")
        if (before["epoch"], before["revision"]) != (0, 0):
            raise VerificationError("initial pointer is not 0.0")
        if (after["epoch"], after["revision"]) != (0, 1):
            raise VerificationError("committed pointer is not 0.1")
        if after["generation"] != before["generation"] + 1:
            raise VerificationError("pointer generation was not incremented")
        if result["checks"]["postSwitchRuntimePassed"] is not True:
            raise VerificationError("post-switch runtime was not verified")
        if result["checks"]["rollbackPerformed"] is not False:
            raise VerificationError("successful activation unexpectedly rolled back")
        if transaction.compute_attestation_hash(result) != result["transactionHash"]:
            raise VerificationError("transactionHash is not reproducible")
        transaction.verify_deployment(
            deployment_root=deployment,
            pointer_schema_path=repository / "contracts" / "active-pointer-v0.schema.json",
            journal_schema_path=repository / "contracts" / "activation-transaction-journal-v0.schema.json",
            attestation_schema_path=repository / "contracts" / "activation-transaction-attestation-v0.schema.json",
            attestation_path=deployment / "transactions" / "tx-success.attestation.json",
        )

        # Failure before swap leaves 0.0 selected and records a verified rollback outcome.
        deployment_before = root / "deployment-before-swap"
        initialize(transaction, repository, deployment_before, active, "init-before")
        expect_error(
            lambda: activate(
                transaction,
                repository,
                deployment_before,
                staged,
                candidate,
                overlay,
                decision,
                swipl,
                "tx-before-swap",
                "before-swap",
            ),
            "previous pointer restored and verified",
        )
        if pointer(repository, transaction, deployment_before)["revision"] != 0:
            raise VerificationError("failure before swap changed current revision")

        # Failure after swap must atomically restore 0.0 and verify its runtime.
        deployment_after = root / "deployment-after-swap"
        initialize(transaction, repository, deployment_after, active, "init-after")
        expect_error(
            lambda: activate(
                transaction,
                repository,
                deployment_after,
                staged,
                candidate,
                overlay,
                decision,
                swipl,
                "tx-after-swap",
                "after-swap",
            ),
            "previous pointer restored and verified",
        )
        restored = pointer(repository, transaction, deployment_after)
        rollback_attestation = json.loads(
            (deployment_after / "transactions" / "tx-after-swap.attestation.json")
            .read_text(encoding="utf-8")
        )
        if restored["revision"] != 0:
            raise VerificationError("post-swap failure did not restore revision 0")
        if rollback_attestation["outcome"] != "rolled-back":
            raise VerificationError("rollback attestation has wrong outcome")
        if rollback_attestation["checks"]["rollbackRuntimePassed"] is not True:
            raise VerificationError("rollback runtime was not verified")

        # An interrupted process leaves a journal; recover restores 0.0 fail-closed.
        deployment_crash = root / "deployment-crash"
        initialize(transaction, repository, deployment_crash, active, "init-crash")
        try:
            activate(
                transaction,
                repository,
                deployment_crash,
                staged,
                candidate,
                overlay,
                decision,
                swipl,
                "tx-crash",
                "crash-after-swap",
            )
        except transaction.SimulatedCrash:
            pass
        else:
            raise VerificationError("simulated process crash was not raised")
        if pointer(repository, transaction, deployment_crash)["revision"] != 1:
            raise VerificationError("crash fixture did not interrupt after pointer swap")
        with transaction.ActivationLock(deployment_crash, "recovery-test"):
            recovered = transaction.recover_pending_transactions(
                deployment_root=deployment_crash,
                pointer_schema=transaction.read_json_object(
                    repository / "contracts" / "active-pointer-v0.schema.json",
                    "pointer schema",
                ),
                journal_schema=transaction.read_json_object(
                    repository / "contracts" / "activation-transaction-journal-v0.schema.json",
                    "journal schema",
                ),
                attestation_schema=transaction.read_json_object(
                    repository / "contracts" / "activation-transaction-attestation-v0.schema.json",
                    "attestation schema",
                ),
                swipl=swipl,
                timeout_seconds=30.0,
            )
        if len(recovered) != 1 or recovered[0]["outcome"] != "rolled-back":
            raise VerificationError("crash recovery did not emit rollback attestation")
        if recovered[0]["intent"]["recovery"] != "performed":
            raise VerificationError("crash recovery was not recorded")
        if pointer(repository, transaction, deployment_crash)["revision"] != 0:
            raise VerificationError("crash recovery did not restore revision 0")

        # Staged tamper is rejected before current.json changes.
        deployment_tamper = root / "deployment-tamper"
        initialize(transaction, repository, deployment_tamper, active, "init-tamper")
        tampered = root / "tampered-stage"
        shutil.copytree(staged, tampered)
        with (tampered / "entry.pl").open("ab") as stream:
            stream.write(b"\n% tamper\n")
        expect_error(
            lambda: activate(
                transaction,
                repository,
                deployment_tamper,
                tampered,
                candidate,
                overlay,
                decision,
                swipl,
                "tx-tamper",
            ),
            "staged per-file hashes",
        )
        if pointer(repository, transaction, deployment_tamper)["revision"] != 0:
            raise VerificationError("tampered stage changed current revision")

        # Decision reuse after successful activation is stale and fails closed.
        expect_error(
            lambda: activate(
                transaction,
                repository,
                deployment,
                staged,
                candidate,
                overlay,
                decision,
                swipl,
                "tx-stale",
            ),
            "baseline manifest",
        )
        if pointer(repository, transaction, deployment)["revision"] != 1:
            raise VerificationError("stale decision changed committed revision")

        # Exclusive lock rejects a concurrent transaction.
        deployment_lock = root / "deployment-lock"
        initialize(transaction, repository, deployment_lock, active, "init-lock")
        with transaction.ActivationLock(deployment_lock, "lock-owner"):
            expect_error(
                lambda: transaction.ActivationLock(
                    deployment_lock,
                    "lock-contender",
                ).__enter__(),
                "activation lock is held",
            )

    print("Builder activation transaction contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
