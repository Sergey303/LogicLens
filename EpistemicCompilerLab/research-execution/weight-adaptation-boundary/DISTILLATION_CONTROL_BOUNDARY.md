# ENG-202 — Current distillation control boundary

Status: producer literature/control note; ENG-155 remains the authoritative novelty-review package.

ENG-202 is **not** a novelty claim for teacher-generated supervision, small-model fine-tuning, QLoRA, trajectory distillation, data selection, student-capacity alignment or reinforcement distillation. Those mechanisms are established prior work and are controls/alternative explanations for this boundary experiment.

## Mandatory prior controls

### SmartAD — Capacity-Aligned Agent Distillation for Small Language Models

Findings ACL 2026, `2026.findings-acl.1349`.

Relevant occupied mechanisms: teacher reason-act-observe trajectories, student-friendly trajectory selection based on student likelihood, and segment-weighted supervision emphasizing actions/final decisions in 1.5B/3B students.

ENG-202 consequence: Codex may not silently select examples from observed student weaknesses or apply teacher-specific token/segment weights in W-C. Either treatment would be a separate causal factor.

### Skill-Aware Data Selection and Fine-Tuning for Data-Efficient Reasoning Distillation

ACL 2026, `2026.acl-short.49`.

Relevant occupied mechanisms: teacher-generated corpus, skill-based student-weakness selection, and skill-aware SFT evaluated on Qwen3-4B/8B.

ENG-202 consequence: W-C and W-B must use the same frozen grouped TRAIN record IDs. Student-weakness-guided teacher-data selection is forbidden in core W-C.

### Harnessing Negative Signals / REDI

ACL 2026, `2026.acl-long.74`.

Relevant occupied mechanisms: positive and negative teacher traces, SFT plus reinforcement distillation, including a Qwen 1.5B student.

ENG-202 consequence: negative-trace weighting, preference optimization, REINFORCE-style objectives, RL and GRPO are outside core W-C. Adding them requires a separately versioned treatment.

### AgenticQwen

ACL 2026 Industry, `2026.acl-industry.37`.

Relevant occupied mechanisms: synthetic-data flywheels and multi-round reasoning/agentic RL for small agentic Qwen models.

ENG-202 consequence: outcome-driven curriculum/flywheel regeneration is not allowed in core W-C.

### Distillation Traps and Guards

ACL 2026, `2026.acl-long.908`.

Relevant risk evidence: teacher-student gap, tail noise and off-policy instability can make distillation fail or distort student behavior.

ENG-202 consequence: W-C failure is scientifically interpretable and must not trigger favorable teacher regeneration, extra epochs, seed replacement or post-hoc target repair. Failed/weak runs remain evidence.

## Core causal boundary

The primary ENG-202 teacher question remains:

```text
same base student
+ same frozen TRAIN records
+ same target schema
+ same adaptation recipe / steps / seeds

W-B: independently adjudicated gold TRAIN target
W-C: one gold-blind Codex-generated TRAIN target
```

The contrast is **content/source of supervision**, not teacher-aware data selection, rationale length, trajectory weighting, RL, curriculum adaptation or best-seed selection.

Any introduction of those mechanisms creates a new treatment and requires a versioned causal contract before HOLDOUT.
