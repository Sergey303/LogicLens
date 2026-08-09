# ENG-202 — Weight-adaptation protocol

Status: producer design candidate. Separate boundary study; not fixed-weight primary evidence.

## Question

At matched teacher/adaptation budgets, does transferring TRAIN-only supervision into Qwen weights improve over gold-only adaptation, and does either adapted arm outperform the strongest fixed-weight external-interface condition after accounting for compute, auditability, rollback and update cost?

## Model-binding boundary

The scientific Qwen checkpoint in `TRAINING_MANIFEST.yaml` is a **provisional boundary candidate** until WP-004 freezes the fixed-weight student profile used for the external-interface comparison.

`MODEL_BINDING_CONTRACT.json` is normative: a causal statement about **where knowledge is placed** (external interface versus weights) requires the adapted W-A/W-B/W-C base checkpoint and tokenizer to be byte-identical in repository/revision identity to the compared fixed-weight student profile, with the same inference prompt/decoding/output contracts.

If that exact binding is not satisfied, the result is a descriptive cross-model comparison only. The model may not be switched after DEV/HOLDOUT to recover a favorable result.

## Arms

### W-A — Base Qwen

No weight update. Exact base checkpoint/tokenizer from `TRAINING_MANIFEST.yaml`.

### W-B — Gold-only QLoRA/SFT

Uses independently adjudicated TRAIN targets. It receives no Codex explanation, rationale, trace, rewrite or label repair.

### W-C — Codex-distilled QLoRA/SFT

Codex sees only the frozen TRAIN input/evidence view, target schema and teacher instructions. **Core W-C does not expose independently adjudicated gold targets to Codex.** Codex emits one independently generated supervision target in exactly the same output schema as W-B.

W-C does not append unconstrained rationales. This prevents W-C-vs-W-B from conflating teacher identity with gold copying or extra rationale supervision.

### W-D — Executable-trace distillation

Disabled by default. Any trace/rationale/program supervision belongs here. W-D remains DEV-only until separately specified, powered and approved before HOLDOUT.

RL/GRPO/reward optimization, student-weakness-directed example selection, teacher-trajectory selection, outcome-driven curricula and segment-specific teacher loss weighting are out of core W-C. They require separately versioned treatments. `DISTILLATION_CONTROL_BOUNDARY.md` records the current prior-work/control boundary.

## Causal contrasts

1. **W-C vs W-B** — independently generated Codex TRAIN targets versus independently adjudicated gold TRAIN targets under the same records and frozen adaptation recipe.
2. **W-B vs W-A** — value of gold-only parameter adaptation.
3. **W-C vs W-A** — descriptive total adapted effect; not sufficient by itself to establish why teacher-generated targets help.
4. **strongest fixed-weight arm vs W-B/W-C** — external verified interface versus parameter update, but this is causal only when `MODEL_BINDING_CONTRACT.json` passes; report jointly with compute/update/audit costs.

No adapted result may be re-described as evidence for the fixed-weight primary hypothesis.

`WEIGHT_BOUNDARY_ESTIMANDS.json` freezes the seed-aware estimand boundary. Training seeds are nested training-run replications, never extra independent benchmark cases.

## Held equal W-B / W-C

Freeze and match:

- same immutable base-model and tokenizer revision;
- same grouped TRAIN record IDs and student-visible input template;
- same **record order within each seed**, computed only from seed + evaluator-side record ID and never from target bytes;
- same target schema and same maximum complete-target length contract;
- QLoRA method and quantization;
- adapter rank/alpha/dropout/target modules/bias;
- optimizer and learning-rate schedule;
- effective batch size and gradient accumulation;
- maximum sequence length;
- exact optimizer-step count;
- three training seeds `[17, 29, 43]`;
- final-step-only checkpoint selection;
- inference prompt, decoding and output schema;
- evaluation cases and scorer.

### Target-length rule

**Do not truncate, subsample, pad with supervised no-op content, or otherwise alter a semantically valid target merely to force exact equality of W-B/W-C target-token totals.** Such editing changes the supervision treatment itself.

Instead:

- both arms use the same complete grouped record set;
- both use the same target schema and predeclared maximum complete-target length;
- a target exceeding that limit makes the candidate corpus invalid rather than being semantically truncated;
- actual supervised target-token totals and per-record distributions are retained and reported;
- the same optimizer steps/batch boundaries/sequence limit/adapter capacity are used;
- training loss is normalized under one frozen implementation for both arms.

Any later length-matched sensitivity analysis is a separate DEV-only analysis; it cannot replace the core result after outcomes are known.

## Seeds and checkpoint selection

Seeds are `[17, 29, 43]`. Every seed is retained and reported. There is no best-seed selection and no replacement fourth seed.

W-B/W-C use the same deterministic record ordering for a given seed under `TRAINING_REPLICABILITY_CONTRACT.md`. Data ordering cannot depend on target bytes.

Early stopping is disabled. The only eligible checkpoint for a seed is the final checkpoint at the predeclared optimizer-step count. Intermediate checkpoints may be retained for diagnostics but cannot replace the final checkpoint after DEV inspection.

For the primary teacher increment, each `base_scenario_id` contributes one W-B and one W-C value after averaging the three predeclared seed-specific binary outcomes. The three seed runs must not be treated as three independent copies of the benchmark sample. Exact confirmatory inference remains subject to WP-006 approval.

DEV may be used only as an aggregate boundary/feasibility diagnostic under the frozen analysis plan. Teacher generation never receives DEV questions or DEV labels.

## Training replicability

`TRAINING_REPLICABILITY_CONTRACT.md` is normative. ENG-202 claims a frozen reproducible procedure plus multi-seed evidence, not bitwise-identical adapters across arbitrary GPU/CUDA/bitsandbytes stacks.

Within each seed pair W-B/W-C, base/tokenizer, ordered record IDs, batch boundaries, recipe and inference contracts must match. RNG/backend settings and exact environment evidence are retained. A silent backend fallback or asymmetric record drop invalidates the pair.

## Data visibility

Teacher generation: TRAIN input/evidence view only; no adjudicated gold target, student output or outcome metric.

Training: TRAIN only.

Development diagnostics: aggregate DEV after adapters are produced.

HOLDOUT and REPLICATION remain inaccessible to producer/teacher until the adapter recipe, corpus hashes, leakage report, adapter-selection rule, model-binding rule and analysis contract are frozen and independently accepted.

A sealed split custodian may later run predefined overlap scanners against hidden split material and return only the frozen report fields/aggregate evidence needed for eligibility. This does not authorize producer or teacher access to held-out text.

## Leakage and memorization

Before any adapter training, each training corpus must pass the frozen leakage report contract. At minimum it records:

- exact normalized-content overlap;
- case/source identifiers accidentally embedded in text;
- prohibited split words/paths/references;
- lexical near-duplicate signal;
- semantic near-duplicate signal when the frozen scanner is available;
- group/source-family overlap policy;
- generated-target provenance and hashes.

Checks requiring hidden split material are executed only by the sealed custodian/scanner; the producer receives pass/fail/unknown plus aggregate evidence, not hidden examples. A leakage failure invalidates the affected arm until a new versioned corpus is independently reviewed. Silent repair is forbidden.

## Failure retention

OOM, divergence, malformed training rows, overfit runs, NaNs and weak seeds remain in the run ledger. Epochs/steps, rank, LR or data are not extended or changed because a result is disappointing. A recipe change creates a new candidate version and restarts all compared seeds.

A failed scientific seed is never silently discarded or replaced. `WEIGHT_BOUNDARY_ESTIMANDS.json` requires WP-006 to freeze how a non-producing adapter enters the system-level confirmatory estimand before HOLDOUT. Pure infrastructure block reruns, if allowed at all, require a pre-outcome symmetric paired-block rule and retained failure evidence.

## Auditability / cost reporting

For every arm retain teacher calls/tokens, corpus bytes/tokens, GPU model, wall time, peak VRAM, training energy proxy when available, adapter bytes/hash, update procedure and rollback procedure. Accuracy without these costs is not a complete comparison.

## STOP / PIVOT

- W-B approximately matches W-C: no useful incremental Codex-supervision effect.
- Fixed-weight external interface approximately matches adapted Qwen under an exact same-base binding: weight modification is unnecessary for the evaluated class; report that directly.
- Adaptation wins only with materially larger compute/update burden: report the trade-off, not a universal win.
- The fixed-weight comparison uses a different base checkpoint/tokenizer: remove the causal weight-placement interpretation and report cross-model results descriptively only.
- Leakage/memorization cannot be excluded: adapted arm is invalid for publication evidence.
- Required training-seed/run evidence is missing or unfavorable seeds are discarded: adapted-arm evidence is invalid.
- Any request to fold weight-changing results into the fixed-weight primary claim after HOLDOUT: stop and require a pre-HOLDOUT versioned scientific-contract decision.
