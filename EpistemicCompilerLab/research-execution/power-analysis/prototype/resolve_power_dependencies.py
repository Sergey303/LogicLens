#!/usr/bin/env python3
"""Resolve WP-006 upstream acceptance from local Git/reviewer artifacts.

A syntactically valid SHA or free-text reviewer reference is never enough. For an
ACCEPTED dependency this resolver verifies:
- candidate and review commits exist locally;
- the machine reviewer attestation exists at review_commit_sha with exact bytes/hash;
- attestation verdict/issue/dependency/candidate/review commit are exact;
- reviewer context differs from producer context;
- every accepted artifact is read from candidate_sha and hashes exactly.

PENDING dependencies remain explicitly unresolved and cannot yield a power-gate PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BINDINGS = ROOT / "POWER_DEPENDENCY_BINDINGS.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_bytes(*args: str) -> bytes:
    proc = subprocess.run(["git", *args], cwd=ROOT.parents[3], capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def git_commit_exists(sha: str) -> bool:
    proc = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=ROOT.parents[3], capture_output=True, check=False)
    return proc.returncode == 0


def git_file_at_commit(sha: str, path: str) -> bytes:
    return git_bytes("show", f"{sha}:{path}")


def resolve_dependency(dep: dict[str, Any]) -> dict[str, Any]:
    base = {
        "dependency_id": dep["dependency_id"],
        "linear_issue": dep["linear_issue"],
        "declared_status": dep["status"],
        "resolved_status": "PENDING",
        "checks": {},
    }
    if dep["status"] == "PENDING":
        for key in ("candidate_sha", "review_commit_sha", "attestation_path", "attestation_sha256"):
            require(dep.get(key) is None, f"{dep['dependency_id']}: PENDING must not carry fake {key}")
        base["reason"] = "upstream independent acceptance not yet bound"
        return base

    require(dep["status"] == "ACCEPTED", f"{dep['dependency_id']}: invalid status {dep['status']}")
    candidate = dep.get("candidate_sha")
    review_commit = dep.get("review_commit_sha")
    attestation_path = dep.get("attestation_path")
    attestation_sha = dep.get("attestation_sha256")
    require(isinstance(candidate, str) and HEX40.fullmatch(candidate), f"{dep['dependency_id']}: invalid candidate SHA")
    require(isinstance(review_commit, str) and HEX40.fullmatch(review_commit), f"{dep['dependency_id']}: invalid review commit SHA")
    require(candidate != review_commit, f"{dep['dependency_id']}: review commit cannot equal candidate commit")
    require(isinstance(attestation_path, str) and attestation_path.endswith(".json"), f"{dep['dependency_id']}: attestation must be a JSON path")
    require(isinstance(attestation_sha, str) and HEX64.fullmatch(attestation_sha), f"{dep['dependency_id']}: invalid attestation SHA-256")

    candidate_exists = git_commit_exists(candidate)
    review_exists = git_commit_exists(review_commit)
    require(candidate_exists, f"{dep['dependency_id']}: candidate commit is not resolvable locally")
    require(review_exists, f"{dep['dependency_id']}: review commit is not resolvable locally")
    review_bytes = git_file_at_commit(review_commit, attestation_path)
    require(sha256_bytes(review_bytes) == attestation_sha, f"{dep['dependency_id']}: attestation digest mismatch at review commit")
    current_path = ROOT.parents[3] / attestation_path
    require(current_path.is_file(), f"{dep['dependency_id']}: attestation missing from current checkout")
    require(current_path.read_bytes() == review_bytes, f"{dep['dependency_id']}: current attestation bytes differ from review commit")

    att = json.loads(review_bytes.decode("utf-8"))
    required_keys = {
        "schema_version", "dependency_id", "linear_issue", "verdict", "candidate_sha",
        "review_commit_sha", "reviewer_context_id", "producer_context_id", "review_scope",
        "accepted_artifacts", "holdout_replication_access",
    }
    require(set(att) == required_keys, f"{dep['dependency_id']}: attestation fields drift")
    require(att["schema_version"] == "1.0.0", f"{dep['dependency_id']}: attestation schema drift")
    require(att["dependency_id"] == dep["dependency_id"], f"{dep['dependency_id']}: attestation dependency mismatch")
    require(att["linear_issue"] == dep["linear_issue"], f"{dep['dependency_id']}: attestation issue mismatch")
    require(att["verdict"] == "PASS", f"{dep['dependency_id']}: reviewer verdict is not PASS")
    require(att["candidate_sha"] == candidate, f"{dep['dependency_id']}: attested candidate mismatch")
    require(att["review_commit_sha"] == review_commit, f"{dep['dependency_id']}: attested review commit mismatch")
    require(att["reviewer_context_id"] != att["producer_context_id"], f"{dep['dependency_id']}: reviewer context equals producer context")
    require(len(att["reviewer_context_id"]) >= 16 and len(att["producer_context_id"]) >= 16, f"{dep['dependency_id']}: context identity too weak")
    require(len(att["review_scope"]) >= 16, f"{dep['dependency_id']}: review scope missing")
    require(att["holdout_replication_access"] == "NONE", f"{dep['dependency_id']}: sealed-data access not allowed for W0 acceptance")
    require(isinstance(att["accepted_artifacts"], list) and att["accepted_artifacts"], f"{dep['dependency_id']}: no accepted artifacts")

    verified_artifacts = []
    for artifact in att["accepted_artifacts"]:
        require(set(artifact) == {"path", "sha256"}, f"{dep['dependency_id']}: accepted artifact fields drift")
        path = artifact["path"]
        digest = artifact["sha256"]
        require(isinstance(path, str) and path, f"{dep['dependency_id']}: invalid artifact path")
        require(isinstance(digest, str) and HEX64.fullmatch(digest), f"{dep['dependency_id']}: invalid artifact digest")
        candidate_bytes = git_file_at_commit(candidate, path)
        actual = sha256_bytes(candidate_bytes)
        require(actual == digest, f"{dep['dependency_id']}: candidate artifact digest mismatch: {path}")
        verified_artifacts.append({"path": path, "sha256": actual})

    base.update({
        "resolved_status": "ACCEPTED",
        "candidate_sha": candidate,
        "review_commit_sha": review_commit,
        "attestation_path": attestation_path,
        "attestation_sha256": attestation_sha,
        "reviewer_context_id": att["reviewer_context_id"],
        "producer_context_id": att["producer_context_id"],
        "review_scope": att["review_scope"],
        "accepted_artifacts": verified_artifacts,
        "checks": {
            "candidate_commit_resolvable": True,
            "review_commit_resolvable": True,
            "attestation_exact_at_review_commit": True,
            "reviewer_distinct_from_producer": True,
            "candidate_artifacts_hash_verified": True,
        },
    })
    return base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bindings", type=Path, default=DEFAULT_BINDINGS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bindings = json.loads(args.bindings.read_text(encoding="utf-8"))
    require(bindings["work_package_id"] == "WP-006", "bindings package drift")
    dependencies = [resolve_dependency(dep) for dep in bindings["dependencies"]]
    all_accepted = all(dep["resolved_status"] == "ACCEPTED" for dep in dependencies)
    head = git_bytes("rev-parse", "HEAD").decode().strip()
    result = {
        "schema_version": "1.0.0",
        "work_package_id": "WP-006",
        "evidence_class": "REAL_LOCAL_GIT_RESOLUTION",
        "bindings_sha256": sha256_file(args.bindings),
        "resolved_at_git_head": head,
        "dependencies": dependencies,
        "all_required_dependencies_accepted": all_accepted,
        "power_gate_dependency_status": "READY" if all_accepted else "PENDING",
        "fixture_or_free_text_can_satisfy_acceptance": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
