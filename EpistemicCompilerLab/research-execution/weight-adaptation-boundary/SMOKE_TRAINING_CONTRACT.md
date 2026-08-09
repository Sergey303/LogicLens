# ENG-202 — Smoke-training contract

The smoke run verifies that the frozen adapter pipeline can perform an actual forward/backward/update/save cycle before any 7B scientific run. It is **infrastructure evidence only** and is never scored as scientific evidence.

## Model

Use only the exact smoke checkpoint:

`Qwen/Qwen2.5-Coder-0.5B-Instruct@bbf27711794f58ebd1796058f4280b53c32e19fc`

The tokenizer must use the same revision.

## Data

Use `prototype/synthetic_train.jsonl`. It is synthetic TRAIN-only data and contains no course, DEV, HOLDOUT or REPLICATION content.

## Frozen smoke action

Run exactly one optimizer step with seed `17`, sequence length `256`, QLoRA 4-bit NF4 + double quantization, rank `16`, alpha `32`, dropout `0.05`, `target_modules=all-linear`, and save the adapter.

The smoke script fails if:

- CUDA is unavailable;
- the loaded repository/revision differs from the exact smoke anchor;
- the dataset contains a non-TRAIN split or forbidden split text;
- no trainable LoRA parameters exist;
- loss is non-finite;
- no adapter files are saved;
- manifest/environment values disagree with the script contract.

## Reference environment

Use Python 3.11 and `TRAINING_ENVIRONMENT_LOCK.json`. Create an isolated environment and install the exact frozen package set:

```bash
python3.11 -m venv .venv-eng202
source .venv-eng202/bin/activate
python -m pip install --upgrade pip
python -m pip install -r EpistemicCompilerLab/research-execution/weight-adaptation-boundary/requirements-smoke.txt
```

The first successful run must preserve:

- `pip freeze`;
- Python/PyTorch/CUDA versions;
- GPU name and driver;
- input corpus SHA-256;
- base/tokenizer repository and exact revision;
- adapter configuration;
- pre/post trainable adapter hashes;
- scalar loss for the one update;
- wall time and peak allocated VRAM.

## Commands

Run from a **clean checkout of the exact candidate commit** in the frozen Linux/CUDA environment:

```bash
python EpistemicCompilerLab/research-execution/weight-adaptation-boundary/prototype/smoke_train.py \
  --output artifacts/eng-202/smoke-001

python EpistemicCompilerLab/research-execution/weight-adaptation-boundary/prototype/verify_smoke_artifact.py \
  --artifact artifacts/eng-202/smoke-001
```

Do not add `--model`, `--revision`, step-count or hyperparameter overrides. Changing the smoke recipe requires versioning this contract first.

## Machine acceptance

`SMOKE_REPORT.schema.json` freezes the report surface. `prototype/verify_smoke_artifact.py` is the fail-closed acceptance verifier.

A smoke is eligible for producer handoff only when the verifier emits:

```text
status = CUDA_SMOKE_ARTIFACT_PASS
```

The verifier independently checks at least:

- exact model/tokenizer repository + immutable revision;
- Python 3.11, PyTorch 2.5.1 and CUDA runtime 12.4;
- non-empty GPU and NVIDIA driver identities;
- finite loss, positive CUDA VRAM allocation and non-zero trainable adapter parameters;
- pre-training and post-training adapter states differ;
- frozen synthetic-corpus hash;
- reported adapter-file hashes against the saved files;
- `adapter_config.json` and a saved safetensors adapter;
- frozen package versions against `pip-freeze.txt`;
- tracked Git checkout is clean;
- exact Git commit and hashes of the smoke script, contract, environment lock, manifest, requirements, synthetic data, report schema and verifier.

The resulting `smoke-attestation.json` is immutable evidence and must be included in the ENG-202 producer handoff together with the smoke report, `pip-freeze.txt`, adapter hashes and exact Git commit.

## Acceptance boundary

**Existence of this command is not evidence that it ran.** In particular, existence of the smoke command, verifier command, a static CI PASS, or a hand-written claim that training succeeded is **not evidence that the CUDA smoke ran**. ENG-202 remains producer **In Progress** until a real successful smoke artifact from this exact contract is recorded and passes `verify_smoke_artifact.py`.

The smoke proves only pipeline executability. It does not prove W-B/W-C scientific training quality, a Codex teaching effect, model generalization, or any HOLDOUT/REPLICATION result.
