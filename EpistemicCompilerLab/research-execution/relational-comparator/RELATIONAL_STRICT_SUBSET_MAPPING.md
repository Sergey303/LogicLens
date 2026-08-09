# ENG-197 — Lossless relational strict-subset mapping

Status: **frozen remediation producer contract; TRAIN/DEV only**.

## Purpose

M16 is a conventional relational trusted-execution comparator. It is not allowed to obtain apparent parity by silently simplifying source semantics that M6 can represent.

The relational package is therefore eligible only for scenarios that can be mapped **losslessly** into the exact subset below. Eligibility is decided from source/schema structure before split assignment and without status/outcome information.

## Representable subset v1

A scenario is eligible only when all conditions are true:

1. every queried proposition has one canonical `proposition_id` and ordered source-normalized subject/predicate/object fields;
2. source evidence uses explicit `positive` or `negative` polarity; absence is never negative evidence;
3. scope and version are exact identifiers and every assertion/rule used for the scenario belongs to the same required scope/version;
4. negative evidence is a direct explicit negative assertion for the queried proposition;
5. positive inference uses only zero or more **single-positive-premise → single-positive-head** strict implication edges;
6. implication semantics are monotone; there are no priorities, exceptions or negation-as-failure;
7. dependency groups, probabilistic/opinion fusion and duplicate-source independence do not affect the expected result;
8. no rule has multiple premises, `all`/`any` premise groups, negative premises, negative heads, polarity transforms or arithmetic predicates;
9. the complete source assertion IDs and source provenance required by the scenario can be preserved without truncation;
10. the conventional result contract is permitted to expose root evidence/provenance without claiming the full M6 proof-trace obligation is matched.

If any condition is false or unknown, the scenario is **relational-ineligible**. It is not approximated, dropped after outcomes, or rewritten to fit SQL.

## Mapping

| Frozen semantic object | Relational representation | Lossless condition |
| --- | --- | --- |
| proposition identity | `relational_cmp.proposition.proposition_id` | exact one-to-one ID |
| positive source assertion | `source_assertion(polarity='positive')` | exact assertion/source/scope/version |
| negative source assertion | `source_assertion(polarity='negative')` | direct target negative only |
| unary positive implication | `strict_implication` | one antecedent, one positive consequent |
| positive closure | recursive SQL reachability | same scope/version; monotone finite closure |
| four-state status | existence of positive/negative derivations | exact `supported/refuted/conflicting/unknown` truth table |
| decision action | frozen status→action table | `supported→accept`, `refuted→reject`, otherwise `review` |
| evidence | sorted unique root assertion IDs | complete roots, not minimal-proof claim |
| provenance | sorted unique source IDs | complete roots' provenance |

## Deliberate conventional-result difference from M6

M16 does **not** expose the full M6 proof graph or rule path to Qwen. Recursive SQL internally traverses rule IDs to prevent cyclic re-use, but the frozen M16 result returns root assertion evidence and source provenance only.

Therefore:

- `M16 vs M6` is a **conventional relational trusted-result interface vs explicit epistemic decision-frame bundle**;
- it is not a proof-interface-equivalence contrast;
- visible proof/provenance obligations are not described as identical;
- if proof visibility explains an M6 advantage, that is part of the bundle and must be localized by other matched WP-004 controls.

This difference is intentional: forcing SQL to mimic every M6 frame field would stop testing a strong conventional relational alternative.

## Eligibility timing and paired analysis

`relational_subset_eligible` is computed before split assignment from schema/source structure only. The eligibility report may contain structural reason codes but no expected status/action or model outcome.

WP-006 must power any M16 contrast using the number of **paired eligible base scenarios**, not the total benchmark size. If the accepted benchmark cannot supply a powered and source-family-diverse relational subset, M16 remains DEV-only rather than weakening the eligibility contract.

## STOP

STOP M16 confirmatory eligibility if:

- an accepted source contract cannot be represented one-to-one under this subset;
- eligibility requires reading expected outcomes;
- lossless evidence/provenance requires post-outcome truncation;
- a rule feature outside this subset is silently encoded in generator-specific SQL;
- the study starts describing M16 as proof-equivalent to M6.
