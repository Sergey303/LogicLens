from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTO = ROOT / "prototype"
MODEL = "Qwen/Qwen2.5-Coder-0.5B-Instruct"
REV = "bbf27711794f58ebd1796058f4280b53c32e19fc"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def main() -> None:
    schema = json.loads((ROOT / "SMOKE_REPORT.schema.json").read_text(encoding="utf-8"))
    props = schema["properties"]
    require(props["issue"]["const"] == "ENG-202", "smoke report issue drift")
    require(props["evidence_class"]["const"] == "INFRASTRUCTURE_SMOKE_ONLY_NOT_SCIENTIFIC", "smoke evidence class drift")
    require(props["model_repository"]["const"] == MODEL, "smoke model repository drift")
    require(props["model_revision"]["const"] == REV, "smoke model revision drift")
    require(props["tokenizer_repository"]["const"] == MODEL, "smoke tokenizer repository drift")
    require(props["tokenizer_revision"]["const"] == REV, "smoke tokenizer revision drift")
    require(props["seed"]["const"] == 17, "smoke seed drift")
    require(props["optimizer_steps"]["const"] == 1, "smoke optimizer-step drift")
    require(props["max_sequence_length"]["const"] == 256, "smoke sequence length drift")
    require(props["peak_allocated_vram_bytes"]["exclusiveMinimum"] == 0, "VRAM evidence must be positive")

    verifier = (PROTO / "verify_smoke_artifact.py").read_text(encoding="utf-8")
    ast.parse(verifier)
    for fragment in [
        '"status": "CUDA_SMOKE_ARTIFACT_PASS"',
        'report.get("cuda_runtime") == "12.4"',
        'adapter_pre_sha256") != report.get("adapter_post_sha256")',
        'git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"',
        '"scientific_training_evidence": False',
        '"holdout_or_replication_evidence": False',
        'SMOKE_REPORT.schema.json',
        'smoke_train.py',
    ]:
        require(fragment in verifier, f"smoke verifier missing: {fragment}")

    contract = (ROOT / "SMOKE_TRAINING_CONTRACT.md").read_text(encoding="utf-8")
    for fragment in [
        "verify_smoke_artifact.py",
        "status = CUDA_SMOKE_ARTIFACT_PASS",
        "clean checkout of the exact candidate commit",
        "not evidence that the CUDA smoke ran",
        "pipeline executability",
    ]:
        require(fragment in contract, f"smoke contract missing: {fragment}")

    smoke = (PROTO / "smoke_train.py").read_text(encoding="utf-8")
    ast.parse(smoke)
    require(f'MODEL_REPO = "{MODEL}"' in smoke, "smoke runner model drift")
    require(f'MODEL_REVISION = "{REV}"' in smoke, "smoke runner revision drift")
    require("torch.cuda.is_available()" in smoke, "smoke runner does not require CUDA")
    require("optimizer.step()" in smoke, "smoke runner does not perform update")

    print(json.dumps({
        "issue": "ENG-202",
        "status": "SMOKE_EVIDENCE_CONTRACT_STATIC_PASS",
        "cuda_smoke_executed": False,
        "scientific_training_executed": False
    }, sort_keys=True))


if __name__ == "__main__":
    main()
