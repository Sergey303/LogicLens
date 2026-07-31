# Strict epistemic benchmark and factor ablation

## Research question

Can a strong teacher compile an external, verifiable cognitive structure that improves a fixed weak local LLM without changing its weights?

The optimized object is the complete system: question interpretation, source assertions, executable theory, decision policy, intermediate frame and natural-language renderer.

## Scope of this stage

This stage tests strict epistemic distinctions before probability or fuzzy logic:

- `supported`: loaded positive evidence and no loaded negative evidence;
- `refuted`: loaded negative evidence and no loaded positive evidence;
- `unknown`: neither polarity is supported by loaded evidence;
- `conflicting`: both polarities have addressable loaded evidence.

Negation as failure is used only to inspect the finite loaded assertion set. It never means that an absent real-world fact is false.

## Typed layers

1. Source assertion: proposition, source and explicit polarity.
2. Interpretation: values literally present in the user request.
3. Epistemic conclusion: one of the four statuses with evidence IDs.
4. Decision policy: answer, clarify, abstain or report conflict.
5. Renderer: Russian natural language over a verified decision frame.

Assertions, conclusions and decisions must remain different predicates and different JSON fields.

## Minimal oracle contract

The first fixture uses `uses_material(Revision, Material)` and contains one example of each status. The oracle exposes:

- `assertion/4`;
- `source_ref/2`;
- `claim_status/2`;
- `claim_evidence/3`;
- `decision/2`;
- `decision_reason/2`;
- `decision_frame/2`.

The existing material-selection oracle and frozen compiled-frame replication remain unchanged.

## Primary factor experiment

Use one frozen benchmark and compare four modes:

1. `raw-solver`: Qwen receives the question and full source-grounded representation.
2. `interpretation-frame`: deterministic extraction is supplied; Qwen derives status and action.
3. `status-frame`: interpretation and verified epistemic status are supplied; Qwen applies policy.
4. `decision-frame`: the full verified decision is supplied; Qwen only renders.

Each mode has separate frozen hashes for parser, knowledge, policy, prompt, response schema and cases.

## Benchmark design

Minimum publication pilot: 48 cases, balanced across the four statuses. Each base claim receives controlled variants:

- natural paraphrase;
- source-order permutation;
- internal-ID renaming;
- irrelevant source assertion;
- temporal or provenance wording variation;
- one missing-required-field variant where applicable.

Use TRAIN/DEV/HOLDOUT for development and a separately generated replication split frozen before student evaluation.

## Trusted expected values

Expected interpretation fields are derived from hidden annotations. Expected epistemic status, evidence IDs and decision action are computed by SWI-Prolog. Expected values never enter Qwen prompts.

## Primary metrics

- exact epistemic-status accuracy;
- exact decision/action accuracy;
- evidence-set exact match;
- conflict precision and recall;
- clarification precision and recall;
- false-certain-answer rate;
- `unknown` to `refuted` confusion rate;
- hidden-conflict rate;
- semantic rendering accuracy;
- Russian-language compliance.

## Robustness and efficiency

Report accuracy deltas under paraphrase, fact order, ID renaming and irrelevant assertions. Also report prompt/output tokens, latency, representation bytes and teacher calls per correct case.

## Main experiment

Freeze a 48-case strict-epistemic benchmark and run the four modes with the same Qwen profile, response schema, seed set and output budget. The key contrast is the earliest mode at which accuracy becomes stable.

## Reserve experiment

If all four modes are near ceiling, add contradictory temporal scopes and source-authority tiers while preserving the same typed statuses. If all modes fail, first validate the deterministic interpretation and SWI-Prolog oracle rather than adding richer logic.

## Stop and rejection criteria

Stop increasing representational complexity when two consecutive frozen experiments show no improvement in status or decision accuracy. Reject the direction if the full verified decision frame still produces frequent semantic-copy errors across seeds. Do not add probability or fuzzy membership until a separate task provides meaningful numerical provenance and calibration.

## Publication boundary

A claim requires at least three Qwen seeds, three independently generated paraphrase families, a static deterministic baseline, direct-Codex upper bound, confidence intervals and a never-touched replication set. The current four-claim oracle is only an architectural gate.
