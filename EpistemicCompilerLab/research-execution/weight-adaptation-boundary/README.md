# ENG-202 — Codex-supervised Qwen weight-adaptation boundary

Status: **producer design candidate; TRAIN/DEV-only; no training evidence yet; independent review required**.

This package defines a separate weight-changing boundary study for WP-004. It must never be used as evidence that the fixed-weight primary treatment worked.

## Frozen treatment classes

- **W-A — Base Qwen:** exact upstream Qwen checkpoint; no adapter.
- **W-B — Gold-only QLoRA/SFT:** independently adjudicated TRAIN targets only.
- **W-C — Codex-distilled QLoRA/SFT:** gold-blind Codex independently generates a TRAIN target from the frozen TRAIN input/evidence view under the same target schema and matched supervised-token/optimizer budget as W-B.
- **W-D — executable-trace distillation:** disabled and DEV-only until separately justified, powered and frozen.

W-C does not receive adjudicated gold targets or free extra rationale tokens. Free-form rationale/program-trace supervision belongs to W-D so W-C-vs-W-B does not silently become a gold-copying or target-length treatment.

## Exact model anchors

Scientific 7B candidate:

`Qwen/Qwen2.5-Coder-7B-Instruct@c03e6d358207e414f1eca0bb1891e29f1db0e242`

Pipeline-smoke candidate only:

`Qwen/Qwen2.5-Coder-0.5B-Instruct@bbf27711794f58ebd1796058f4280b53c32e19fc`

The tokenizer is loaded from the same immutable revision as the selected model. Moving tags/branches such as `main` are forbidden.

## Artifacts

Scientific/data contract:

- `WEIGHT_ADAPTATION_PROTOCOL.md`
- `DISTILLATION_DATA_CONTRACT.md`
- `TRAINING_MANIFEST.yaml`
- `ADAPTER_SELECTION_RULE.yaml`
- `TEACHER_RUNTIME_CONTRACT.md`
- `TEACHER_GENERATION_LEDGER.schema.json`
- `LEAKAGE_MEMORIZATION_REPORT.schema.json`
- `TRAINING_RUN_REPORT.schema.json`
- `GENERAL_REGRESSION_CHECK_PLAN.md`

Environment/smoke contract:

- `TRAINING_ENVIRONMENT_LOCK.json`
- `requirements-smoke.txt`
- `SMOKE_TRAINING_CONTRACT.md`
- `prototype/smoke_train.py`
- `prototype/synthetic_train.jsonl`

Pre-frozen general regression diagnostic:

- `prototype/general_regression_dev.jsonl`
- `prototype/score_general_regression.py`

Contract validation:

- `prototype/validate_eng202_contract.py`
- `EpistemicCompilerLab/scripts/run-eng202-contract-check.ps1`
- launcher action: `eng202-contract-check`

Local static validation without GitHub Actions:

```powershell
& 'D:\projects\ChatPilotGroup\LogicLens\EpistemicCompilerLab\scripts\launch.ps1' eng202-contract-check
```

This stdlib-only validator does not download a model or train weights. A static PASS is therefore only contract evidence. **A real successful CUDA QLoRA smoke from the exact frozen contract remains mandatory before producer handoff to independent review.** Merely having a script or passing static contract validation cannot substitute for smoke evidence.

No HOLDOUT or REPLICATION content is permitted in this package. Hidden-split overlap checks, when eventually required, are performed by a sealed custodian/scanner that returns only frozen report status and aggregate evidence; producer and teacher do not receive hidden examples.
