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

## Command

From the repository root in the frozen ML environment:

```bash
python EpistemicCompilerLab/research-execution/weight-adaptation-boundary/prototype/smoke_train.py \
  --output artifacts/eng-202/smoke-001
```

Do not add `--model`, `--revision`, step-count or hyperparameter overrides. Changing the smoke recipe requires versioning this contract first.

## Acceptance boundary

Existence of this command is not evidence that it ran. ENG-202 remains producer **In Progress** until a real successful smoke artifact from this exact contract is recorded. A dry contract validator cannot substitute for the training smoke.
