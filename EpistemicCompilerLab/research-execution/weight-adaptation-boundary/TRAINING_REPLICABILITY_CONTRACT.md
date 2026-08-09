# ENG-202 — Training replicability contract

Status: producer design candidate; no scientific training evidence.

## Claim boundary

ENG-202 requires a reproducible **training procedure**, not an unsupported claim of bitwise-identical QLoRA weights across GPUs, CUDA kernels or bitsandbytes implementations. The scientific evidence is based on all predeclared training seeds and retained run artifacts.

No result may be described as bitwise deterministic unless a later independent replay demonstrates that property under the exact frozen environment.

## Paired seed contract

Scientific seeds are exactly `17`, `29`, and `43`.

For a given seed, W-B and W-C must use:

- the same base checkpoint and tokenizer;
- the same ordered TRAIN record IDs;
- the same batch boundaries and gradient-accumulation boundaries;
- the same optimizer/scheduler/step count;
- the same adapter recipe and initialization seed;
- the same maximum sequence length;
- the same inference contract.

The target text is the scientific treatment and therefore differs between W-B and W-C. Data ordering must not depend on target bytes.

The frozen ordering rule is:

```text
order_key = SHA256(utf8(decimal_seed) || 0x00 || utf8(record_id))
sort ascending by (order_key, record_id)
```

`record_id` is evaluator-side only and is never student-visible.

## RNG and backend recording

Every scientific training runner must set and record, before model/adapter initialization:

- Python random seed;
- NumPy seed, if NumPy is in the execution path;
- PyTorch CPU seed;
- all CUDA seeds;
- Transformers/Trainer seed where applicable;
- `PYTHONHASHSEED`;
- `CUBLAS_WORKSPACE_CONFIG=:4096:8` when supported;
- `torch.use_deterministic_algorithms(True)` or a fail-closed documented exception reviewed before execution;
- TF32 disabled for CUDA matmul/cuDNN unless the scientific contract is versioned;
- dataloader worker count and worker seed policy;
- exact ordered-record manifest hash.

A required deterministic setting that cannot be applied must be recorded before training. It may not be silently ignored.

## Reproducibility evidence

For every run retain:

- complete environment/package lock and `pip freeze`;
- GPU/driver/CUDA/PyTorch/bitsandbytes identities;
- ordered-record manifest hash;
- complete recipe hash;
- seed;
- start/end timestamps and wall time;
- loss trace at predeclared logging intervals;
- failure state if any;
- final adapter file hashes;
- inference configuration hash.

Three seeds are not three independent benchmark cases. They quantify training-run variability. `WEIGHT_BOUNDARY_ESTIMANDS.json` defines the no-pseudoreplication aggregation boundary.

## Failed runs

No bad seed may be replaced by a fourth seed and no best seed may be selected.

A scientific recipe failure such as OOM, NaN or divergence remains part of the arm's evidence. A future WP-006 rule must specify how a non-producing scientific seed enters the system-level confirmatory estimand before HOLDOUT access.

A demonstrably external infrastructure outage may be rerun only under a separately frozen symmetric paired-block rule that does not depend on scientific outcomes and retains the failed artifacts.

## STOP

Stop the affected candidate before confirmatory use if W-B/W-C same-seed ordering differs, the base/tokenizer/recipe hashes differ, seed-dependent records are dropped asymmetrically, required environment evidence is missing, or an implementation silently falls back from the deterministic settings above.
