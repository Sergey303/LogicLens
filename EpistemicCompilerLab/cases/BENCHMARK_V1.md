# Benchmark v1: teacher-compiled query frames

Benchmark v1 preserves the nine user-facing tasks from v0 but removes one overloaded assumption: not every question is a `current-material` call.

## Why v1 exists

In v0, explanation and exception-inspection questions were represented as material-selection queries. The exception question expected revision `b` and date `20260701` even though neither value appeared in the user question. That conflicted with the planner rule that forbids inventing arguments.

V0 remains immutable as the first historical comparison. V1 is a new contract rather than a rewrite of old results.

## Task types

- `material_selection` chooses a material for an explicit revision and date;
- `clarification` asks for one missing mandatory field;
- `explanation` verifies the base rule and opens its `evidence` expansion;
- `exception_inspection` directly opens the `exceptions` expansion owned by the rule entity.

## Teacher frame

`teacherFrame` is an input representation, not an answer. It may contain:

- normalized intent;
- revision and date explicitly extracted from the question;
- rule entity and requested tail kind explicitly named by the question;
- `missingFields` when required input is absent.

It must not contain expected status, expected material, Prolog output or expansion payload.

## Expected plan

The hidden `expected.plan` is used only for validation and scoring:

- `current-material` arguments must equal the frame revision and date;
- `expand` arguments must equal the frame entity and tail kind;
- no operation may introduce a domain value absent from the teacher frame;
- clarification cases have an empty plan.

## Scoring

The `scoring` object states which dimensions apply to the task.

Material is required only for `material_selection`. Explanation and exception tasks are evaluated by the correct operation and tail, not by an unrelated material field. `unknown` and clarification are separate dimensions.

## Next experiment

The raw-question planner and teacher-frame planner will use the same local model, CPU profile, seed and temperature. The comparison asks whether teacher compilation improves action choice and tool planning without changing the knowledge base or model weights.
