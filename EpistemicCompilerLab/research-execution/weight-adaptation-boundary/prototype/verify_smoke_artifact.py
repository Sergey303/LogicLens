from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTO = ROOT / "prototype"
EXPECTED = {
    "model_repository": "Qwen/Qwen2.5-Coder-0.5B-Instruct",
    "model_revision": "bbf27711794f58ebd1796058f4280b53c32e19fc",
    "tokenizer_repository": "Qwen/Qwen2.5-Coder-0.5B-Instruct",
    "tokenizer_revision": "bbf27711794f58ebd1796058f4280b53c32e19fc",
    "seed": 17,
    "optimizer_steps": 1,
    "max_sequence_length": 256,
    "evidence_class": "INFRASTRUCTURE_SMOKE_ONLY_NOT_SCIENTIFIC",
}
EXPECTED_PACKAGES = {
    "torch": "2.5.1",
    "transformers": "4.46.3",
    "peft": "0.14.0",
    "accelerate": "1.2.1",
    "datasets": "3.2.0",
    "bitsandbytes": "0.46.0",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def aggregate_tree_hash(root: Path) -> tuple[str, dict[str, str]]:
    files = {}
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest = sha256_file(path)
        files[rel] = digest
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(digest.encode("ascii"))
        h.update(b"\n")
    require(files, f"no files under {root}")
    return h.hexdigest(), files


def git_evidence() -> dict:
    repo = ROOT.parents[2]
    commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True
    ).stdout.strip()
    require(len(commit) == 40, "could not resolve exact git commit")
    dirty = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"],
        check=True, capture_output=True, text=True
    ).stdout.strip()
    require(not dirty, "tracked repository files changed after/before smoke; verify from a clean frozen checkout")
    return {"commit": commit, "tracked_tree_clean": True}


def parse_pip_freeze(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "==" in line and not line.startswith("#"):
            name, version = line.split("==", 1)
            result[name.lower()] = version
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True, help="Directory produced by smoke_train.py")
    parser.add_argument("--attestation", default=None)
    args = parser.parse_args()

    artifact = Path(args.artifact).resolve()
    report_path = artifact / "smoke-report.json"
    freeze_path = artifact / "pip-freeze.txt"
    adapter_dir = artifact / "adapter"
    tokenizer_dir = artifact / "tokenizer"
    for required in [report_path, freeze_path, adapter_dir, tokenizer_dir]:
        require(required.exists(), f"missing smoke artifact path: {required}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    require(report.get("schema_version") == "1.0.0", "smoke report schema drift")
    require(report.get("issue") == "ENG-202", "wrong issue in smoke report")
    for key, value in EXPECTED.items():
        require(report.get(key) == value, f"smoke report {key} drift: {report.get(key)!r}")

    require(report.get("packages") == EXPECTED_PACKAGES, "smoke package versions drift")
    require(str(report.get("python", "")).startswith("3.11."), "smoke Python must be 3.11.x")
    require(report.get("python_implementation") == "CPython", "smoke Python implementation drift")
    require(report.get("torch") == "2.5.1", "smoke torch runtime drift")
    require(report.get("cuda_runtime") == "12.4", "smoke CUDA runtime must be 12.4")
    require(report.get("gpu") not in {None, "", "unavailable"}, "GPU identity missing")
    require(report.get("driver") not in {None, "", "unavailable"}, "NVIDIA driver identity missing")
    require(isinstance(report.get("loss"), (int, float)) and math.isfinite(report["loss"]), "smoke loss not finite")
    require(report.get("wall_seconds", 0) > 0, "smoke wall time invalid")
    require(report.get("peak_allocated_vram_bytes", 0) > 0, "smoke did not allocate CUDA VRAM")
    require(report.get("trainable_parameters", 0) > 0, "smoke has no trainable adapter parameters")
    require(report.get("adapter_pre_sha256") != report.get("adapter_post_sha256"), "adapter trainable state did not change")

    corpus_path = PROTO / "synthetic_train.jsonl"
    require(report.get("corpus_sha256") == sha256_file(corpus_path), "smoke corpus hash differs from frozen checkout")

    adapter_hash, adapter_files = aggregate_tree_hash(adapter_dir)
    tokenizer_hash, tokenizer_files = aggregate_tree_hash(tokenizer_dir)
    reported_files = report.get("adapter_files", {})
    for rel, digest in reported_files.items():
        full_rel = rel.removeprefix("adapter/")
        require(adapter_files.get(full_rel) == digest, f"adapter file hash mismatch: {rel}")
    require("adapter_config.json" in adapter_files, "adapter_config.json missing")
    require(any(name.endswith(".safetensors") for name in adapter_files), "saved adapter safetensors missing")

    freeze = parse_pip_freeze(freeze_path)
    for package, version in EXPECTED_PACKAGES.items():
        require(freeze.get(package.lower()) == version, f"pip freeze mismatch for {package}")

    git = git_evidence()
    source_hashes = {
        "SMOKE_TRAINING_CONTRACT.md": sha256_file(ROOT / "SMOKE_TRAINING_CONTRACT.md"),
        "TRAINING_ENVIRONMENT_LOCK.json": sha256_file(ROOT / "TRAINING_ENVIRONMENT_LOCK.json"),
        "TRAINING_MANIFEST.yaml": sha256_file(ROOT / "TRAINING_MANIFEST.yaml"),
        "requirements-smoke.txt": sha256_file(ROOT / "requirements-smoke.txt"),
        "prototype/smoke_train.py": sha256_file(PROTO / "smoke_train.py"),
        "prototype/synthetic_train.jsonl": sha256_file(corpus_path),
        "SMOKE_REPORT.schema.json": sha256_file(ROOT / "SMOKE_REPORT.schema.json"),
        "prototype/verify_smoke_artifact.py": sha256_file(Path(__file__)),
    }

    attestation = {
        "schema_version": "1.0.0",
        "issue": "ENG-202",
        "status": "CUDA_SMOKE_ARTIFACT_PASS",
        "evidence_class": "INFRASTRUCTURE_SMOKE_ONLY_NOT_SCIENTIFIC",
        "git": git,
        "report_sha256": sha256_file(report_path),
        "pip_freeze_sha256": sha256_file(freeze_path),
        "adapter_tree_sha256": adapter_hash,
        "tokenizer_tree_sha256": tokenizer_hash,
        "adapter_files": adapter_files,
        "tokenizer_files": tokenizer_files,
        "source_hashes": source_hashes,
        "model_revision": EXPECTED["model_revision"],
        "cuda_runtime": report["cuda_runtime"],
        "gpu": report["gpu"],
        "driver": report["driver"],
        "loss": report["loss"],
        "peak_allocated_vram_bytes": report["peak_allocated_vram_bytes"],
        "scientific_training_evidence": False,
        "holdout_or_replication_evidence": False
    }

    out = Path(args.attestation).resolve() if args.attestation else artifact / "smoke-attestation.json"
    out.write_text(json.dumps(attestation, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(attestation, sort_keys=True))


if __name__ == "__main__":
    main()
