# ENG-201 — M21 outcome-blind mapper contract

The M21 mapper is a deterministic adapter from the public request object to one public capability handle and its arguments. It is frozen independently of program outcomes and model outputs.

## Inputs

Only fields in `public_request` may be read. The mapper may use the request's declared semantic `kind` and the argument fields required by that kind. It may not read case ID, split, expected result, model output, evaluator notes or any hidden source field.

## Output

Exactly one `(capability_handle, arguments)` pair conforming to the frozen API. The mapper does not execute the capability, infer an epistemic answer, add provenance or render natural language.

## Current synthetic mapping

- `evidence_status` -> `py_cap_01` with `positive_evidence`, `negative_evidence`;
- `threshold_relation` -> `py_cap_02` with `value`, `threshold`;
- `interval_threshold` -> `py_cap_03` with `lower`, `upper`, `threshold`.

This mapping is intentionally simple and is not evidence that teacher-generated routing is useful. If a future benchmark requires nontrivial routing, ENG-200 owns routing-policy treatments; ENG-201 must not silently absorb them.

## Causal boundary

M21 measures executed-result placement with deterministic tool/argument selection. M22 adds student selection/formation. Any change to mapper logic after looking at DEV outcomes creates a new version and invalidates direct comparison with the frozen candidate.
