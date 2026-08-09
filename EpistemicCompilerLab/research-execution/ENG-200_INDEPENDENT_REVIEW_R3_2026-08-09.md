# ENG-200 Independent Review R3 — 2026-08-09

## Decision

**PASS**

Reviewer role: **Independent Tool-Routing and Causal Reviewer**.

Reviewer context: `ChatGPT ENG-200 independent re-review R3 / 2026-08-09`.

This review is a distinct recorded reviewer context from the R3 remediation producer. It is not represented as an independent human or organizational review.

## Scope

This R3 review adjudicates the single blocker introduced by the prior independent R2 review and checks non-regression of the already accepted R1/R2 remediation.

Reviewed evidence:

- Linear issue `ENG-200` in `In Review`;
- PR #76, accepted head `3483af4e656b8054616c76d8c85ee89fbaf8b62e`, squash merge `61cb160e18bb0acd50b2c9d2302fbf05a85b2d48`;
- R3 producer handoff `EpistemicCompilerLab/research-execution/handoffs/ENG-200.json`, handoff-only commit `70135dc858f1140aa6019966ee0f8dacb1afb9e0`;
- normative `ROUTING_FEATURE_CONTRACT.json`;
- current `prototype/verify.py` on `main`;
- dedicated GitHub Actions run `31304022326`, job `93221339252`;
- downloaded workflow artifact `9035371923`.

No HOLDOUT or REPLICATION content was accessed.

## R2 blocker adjudication

### Canonical feature serialization

**CLOSED.**

The normative contract requires compact UTF-8 JSON with sorted keys, separators `(',', ':')`, no whitespace, and lowercase JSON booleans.

The current implementation now serializes with:

```python
json.dumps(features, sort_keys=True, separators=(",", ":")).encode("utf-8")
```

and does not append a line terminator. It additionally fails if the resulting byte sequence ends with `LF`.

Therefore an independent implementation following the normative contract produces the same canonical byte representation expected by the verifier.

The machine-readable report explicitly records:

```text
feature_contract.canonical_serialization_no_trailing_lf = true
feature_contract.primary_input_same_bytes = true
```

## PR-scope / non-regression check

PR #76 changed exactly two files:

1. `router-comparator/prototype/verify.py`;
2. `router-comparator/ENG-200_FREEZE_MANIFEST.json`.

The scientific routing contract, feature definitions, capability registry, policy IR, generated Prolog, Qwen-visible catalogues, mode contracts and argument-binding boundary were not changed by this remediation.

The six blockers previously independently confirmed closed in R2 therefore remain closed unless subsequent repository drift changed the package.

A comparison from R3 handoff commit `70135dc858f1140aa6019966ee0f8dacb1afb9e0` to current `main` showed `main` ahead by 65 commits, but none of the reported changed paths are under `research-execution/router-comparator/` or the ENG-200 handoff. Thus no post-handoff ENG-200 package drift was found.

## Independent CI artifact inspection

Downloaded artifact `9035371923` was inspected independently.

Observed ZIP SHA-256:

`f982c4690dbab95676b36a34959b74595913e7bbed7d6a929136478c0d1e0373`

This matches the GitHub Actions artifact digest and producer handoff.

`verification-report.json` records:

- `status = PASS`;
- Python `3.12.13`;
- SWI-Prolog `9.0.4`;
- synthetic cases `12`;
- complete feature-space vectors `80`;
- tree ↔ SWI-Prolog vectors checked `80`;
- `canonical_serialization_no_trailing_lf = true`;
- `primary_input_same_bytes = true`;
- raw-question parsing excluded from the primary contrast;
- 9 typed capability contracts with valid input/result schemas, budgets and fail-closed semantics;
- 10 named mutation checks;
- freeze manifest `30` files;
- freeze-manifest SHA-256 `709af06a6676ec4b15025285cbcb3bd6b2a6d810dec27f10a33e8618d23220cc`.

The dedicated workflow steps for deterministic regeneration, immutable freeze manifest, leakage mutations, exhaustive causal-contract verification and tree↔Prolog verification all completed successfully.

## Scientific interpretation retained

This PASS is **design/artifact acceptance only**.

It does not establish that:

- a Codex-generated routing policy improves Qwen;
- M19 outperforms M20 or direct-Qwen selection;
- Prolog routing is superior to a decision graph;
- the router should enter the confirmatory subset.

Those conclusions require the later DEV/model experiments and WP-004/WP-006/WP-007 adjudication before HOLDOUT.

The previously recorded integration guard remains: if routing arms later feed final-answer rendering, rendering must start from a fresh held-equal context (or an explicitly matched post-routing context), otherwise M20 may carry policy/catalogue context that M19 does not.

## Governance observation

Linear state history again shows a short producer-side transition through `Done` before `In Review`. No confirmatory work was authorized from that state and the scientific artifact was not affected, so this is **non-blocking for ENG-200 PASS**. However the producer/handoff status automation should be corrected before GATE-001 and later critical packages.

## Final verdict

**PASS — ENG-200 may move from `In Review` to `Done`.**

ENG-200 provides an accepted TRAIN/DEV-only design contract and executable routing-comparator prototype suitable as an input to WP-004 causal adjudication. It does not independently authorize benchmark scaling or HOLDOUT access.
