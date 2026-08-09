# ENG-201 — Frozen executable Python program contract

Status: producer candidate, TRAIN/DEV-only; independent review required.
Parent: WP-004 / ENG-156.

## Scientific purpose

ENG-201 is a falsification/control comparator for the fixed-weight interface-placement study. It does not claim novelty for Python execution, program synthesis, program-aided reasoning, tool use, teacher-generated code, or model training.

The treatment asks whether TRAIN-only task knowledge can be compiled into a frozen reusable executable artifact and exposed to a fixed-weight student only through a typed interface/result.

## Frozen modes

### M21 — executed Python result interface

An outcome-blind deterministic mapper consumes only the public typed request fields and selects one capability plus arguments. The frozen Python module executes. Qwen receives the original user question plus the typed execution result, provenance references and final response schema. Qwen never receives Python source, bytecode, comments, stack traces or implementation identifiers.

### M22 — Python tool agent (DEV-only by default)

Qwen receives the same user question and the same frozen public capability catalogue, chooses one capability handle and arguments, the same frozen Python module executes, and Qwen receives the same result schema as M21. M22 therefore adds tool-selection/query-formation cost without adding code-reading cost.

M22 remains DEV-only unless WP-004, WP-006 and WP-007 explicitly approve confirmatory inclusion before HOLDOUT.

## Held-equal factors

M21 and M22 must hold equal:

- student model and weights;
- decoding parameters and context budget;
- frozen Python module bytes and SHA-256;
- public capability API and result schemas;
- execution limits and failure codes;
- final response schema;
- provenance representation;
- post-execution rendering instructions.

The only intended M22-vs-M21 difference is capability/argument selection by Qwen versus the frozen outcome-blind mapper.

## Teacher visibility

Program generation may use only TRAIN examples plus the written task/interface contract. It may not use DEV questions, HOLDOUT, REPLICATION, model outputs, hidden expected fields or post-hoc outcome summaries.

The committed prototype is a producer-authored synthetic contract exemplar, not evidence that Codex generated a better program and not evidence of a teacher effect.

## Allowed program class

The frozen module may contain reusable pure deterministic functions, bounded decision logic, validation logic and arithmetic. It must not contain:

- case IDs or question hashes;
- hidden answer tables;
- branches keyed to evaluation labels;
- network/filesystem/subprocess/shell access;
- dynamic imports, package installation, reflection, eval/exec/compile;
- random or time-dependent behavior;
- writes or external side effects.

## Error decomposition

Score separately:

1. mapper error (M21 only);
2. Qwen capability-selection error (M22 only);
3. argument-formation error;
4. Python execution/failure error;
5. result-interpretation error;
6. final rendering/schema error.

A precomputed correct result is reported as executable-interface benefit, not reasoning transferred into model weights.

## Required matched controls

- deterministic/human-written Python baseline where feasible;
- M6/M16/M17 comparison only after matching Qwen-visible information and semantic obligations;
- direct Codex upper bound is descriptive only;
- if simpler hand-written Python matches the teacher-generated artifact, do not attribute benefit to program synthesis;
- if M21 matches simpler executed controls, remove any claim that Prolog-specific execution is necessary.

## STOP / PIVOT

- M22 < M21: tool selection/query formation is a bottleneck.
- M22 ~= M21: fixed-weight Qwen can select the typed capability reliably under this contract.
- hand-written Python ~= teacher-generated Python: delete teacher-synthesis attribution.
- simpler executed interface ~= M21: narrow mechanism claims to executed semantic-result placement.
- any evidence of case-specific encoding, hidden-data access or Qwen code visibility invalidates the affected candidate.
