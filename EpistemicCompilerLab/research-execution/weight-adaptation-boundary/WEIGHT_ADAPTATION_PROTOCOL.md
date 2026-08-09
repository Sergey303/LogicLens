# ENG-202 — Weight-adaptation protocol

Status: producer design candidate. Separate boundary study; not fixed-weight primary evidence.

## Question

At matched teacher/adaptation budgets, does transferring TRAIN-only supervision into Qwen weights improve over gold-only adaptation, and does either adapted arm outperform the strongest fixed-weight external-interface condition after accounting for compute, auditability, rollback and update cost?

## Arms

### W-A — Base Qwen

No weight update. Exact base checkpoint/tokenizer from `TRAINING_MANIFEST.yaml`.

### W-B — Gold-only QLoRA/SFT

Uses independently adjudicated TRAIN targets. It receives no Codex explanation, rationale, trace, rewrite or label repair.

### W-C — Codex-distilled QLoRA/SFT

Codex sees only TRAIN inputs, independently adjudicated TRAIN targets where the teacher contract explicitly permits them, the frozen output schema and teacher instructions. It emits one replacement supervision target in exactly the same output schema as W-B. The deterministic corpus builder enforces the same supervised-target token budget and optimizer-step budget as W-B.

W-C does not append unconstrained rationales. This prevents W-C-vs-W-B from conflating teacher identity with extra target information/length.

### W-D — Executable-trace distillation

Disabled by default. Any trace/rationale/program supervision belongs here. W-D remains DEV-only until separately specified, powered and approved before HOLDOUT.

RL/GRPO/reward optimization is out of scope and requires a new protocol.

## Causal contrasts

1. **W-C vs W-B** — incremental value of Codex-produced TRAIN supervision under matched training budget.
2. **W-B vs W-A** — value of gold-only parameter adaptation.
3. **W-C vs W-A** — descriptive total adapted effect; not sufficient to identify teacher contribution.
4. **strongest fixed-weight arm vs W-B/W-C** — external verified interface versus parameter update, reported jointly with compute/update/audit costs.

No adapted result may be re-described as evidence for the fixed-weight primary hypothesis.

## Held equal W-B / W-C

Freeze and match:

- same immutable base-model and tokenizer revision;
- QLoRA method and quantization;
- adapter rank/alpha/dropout/target modules/bias;
- optimizer and learning-rate schedule;
- effective batch size and gradient accumulation;
- maximum sequence length;
- exact optimizer-step count;
- effective supervised target-token budget;
- three training seeds;
- final-step-only checkpoint selection;
- inference prompt, decoding and output schema;
- evaluation cases and scorer.

If token matching requires truncation/subsampling, the deterministic rule is applied before training and recorded; no arm-specific manual edits are allowed.

## Seeds and checkpoint selection

Seeds are `[17, 29, 43]`. Every seed is retained and reported. There is no best-seed selection.

Early stopping is disabled. The only eligible checkpoint for a seed is the final checkpoint at the predeclared optimizer-step count. Intermediate checkpoints may be retained for diagnostics but cannot replace the final checkpoint after DEV inspection.

DEV may be used only as an aggregate boundary/feasibility diagnostic under the frozen analysis plan. Teacher generation never receives DEV questions or DEV labels.

## Data visibility

Teacher generation: TRAIN only.

Training: TRAIN only.

Development diagnostics: aggregate DEV after adapters are produced.

HOLDOUT and REPLICATION remain inaccessible until the adapter recipe, corpus hashes, leakage report, adapter-selection rule and analysis contract are frozen and independently accepted.

## Leakage and memorization

Before any adapter training, each training corpus must pass the frozen leakage report contract. At minimum it records:

- exact normalized-content overlap;
- case/source identifiers accidentally embedded in text;
- prohibited split words/paths/references;
- lexical near-duplicate signal;
- semantic near-duplicate signal when the frozen scanner is available;
- group/source-family overlap policy;
- generated-target provenance and hashes.

A leakage failure invalidates the affected arm until a new versioned corpus is independently reviewed. Silent repair is forbidden.

## Failure retention

OOM, divergence, malformed training rows, overfit runs, NaNs and weak seeds remain in the run ledger. Epochs/steps, rank, LR or data are not extended or changed because a result is disappointing. A recipe change creates a new candidate version and restarts all compared seeds.

## Auditability / cost reporting

For every arm retain teacher calls/tokens, corpus bytes/tokens, GPU model, wall time, peak VRAM, training energy proxy when available, adapter bytes/hash, update procedure and rollback procedure. Accuracy without these costs is not a complete comparison.

## STOP / PIVOT

- W-B approximately matches W-C: no Codex-teaching attribution.
- Fixed-weight external interface approximately matches adapted Qwen: weight modification is unnecessary for the evaluated class; report that directly.
- Adaptation wins only with materially larger compute/update burden: report the trade-off, not a universal win.
- Leakage/memorization cannot be excluded: adapted arm is invalid for publication evidence.
- Any request to fold weight-changing results into the fixed-weight primary claim after HOLDOUT: stop and require a pre-HOLDOUT versioned scientific-contract decision.
