# ENG-200 — Independent Tool-Routing and Causal Re-Review R2

Date: 2026-08-09  
Decision: **REVISE**  
Reviewer role: **Independent Tool-Routing and Causal Reviewer**  
Reviewer context: `ChatGPT ENG-200 independent re-review R2 / 2026-08-09`  
Independence statement: this is a distinct reviewer role/context from the recorded remediation-producer role; it is not represented as an independent human/organizational review.  
Reviewed remediation merge: `3e3ed8f952fff02885d4e05d36da3cd6312d1799`  
Reviewed handoff/current main before this audit: `af792c00c00d157cbf228b09baf5032f7536496f`  
Reviewed dedicated CI: run `31149715285`, job `92776668839`  
Reviewed artifact: `8982831177`, ZIP SHA-256 `d795f3324943267e3a3dc3cfca122f5e329ee767db4caf21ec02a5d2c209359e`

No HOLDOUT or REPLICATION content was accessed.

## 1. Re-review scope

This re-review checked the six blockers from `ENG-200_INDEPENDENT_REVIEW_2026-08-07.md` against the merged remediation rather than accepting the producer handoff assertions at face value. It also re-fetched current `main`, the frozen contracts, generated Qwen catalogue, policy IR, verifier, freeze manifest, CI evidence, and downloaded the machine-readable Actions artifact.

Before this audit commit, `main` was byte-identical to the handoff commit `af792c00...`; there was no post-handoff implementation drift.

## 2. Previous blockers — closure status

### B1 — Same routing input for M19/M20/direct baseline: **CLOSED**

`ROUTING_FEATURE_CONTRACT.json` and `ROUTING_MODE_CONTRACTS.yaml` now require the same precomputed typed feature vector for M19, M20 and direct-Qwen selection. Raw-question parsing is explicitly excluded from the primary contrast and moved to a DEV-only ablation.

The verifier constructs the same canonical feature bytes for all three routing arms and fails on inequality.

### B2 — Independent feature boundary / target-tool proxy risk: **CLOSED for design acceptance**

A standalone feature contract now owns and defines all five routing features independently of the teacher policy. The policy IR binds the exact feature-contract ID and SHA-256.

`requires_strict_policy` is defined as an observable output obligation for claim-resolution requests, not as an implementation/tool identity. The verifier forbids capability IDs, handles and implementation technology names in feature definitions, proves strict-policy toggling does not affect non-claim routing, and records eight reachable capabilities under both strict=true and strict=false.

This does not establish that the feature will be behaviorally useful; direct-Qwen and static-router controls remain necessary downstream. That is a falsification property, not a design blocker.

### B3 — Typed capability contract: **CLOSED**

All nine capabilities now have machine-validated input and result JSON schemas, provenance requirements, side-effect declarations, one-call execution budgets, timeout/output bounds, fail-closed semantics, no implicit retries and canonical failure codes.

The generated neutral Qwen catalogue includes the typed schemas/budgets/failure semantics while exposing opaque handles rather than internal canonical capability IDs.

### B4 — Capability selection vs argument generation: **CLOSED**

Linear and the artifact now define ENG-200 as **capability-selection-only**. `ARGUMENT_BINDING_CONTRACT.md` freezes argument binding as an independent downstream, held-equal layer. It cannot change capability choice or retry by rerouting, and its errors are accounted separately.

### B5 — Immutable hash closure: **CLOSED**

`ENG-200_FREEZE_MANIFEST.json` hashes 30 scientific/runtime/visibility/generation/execution/verification files. Dedicated CI regenerates and byte-checks the manifest before running later checks.

The downloaded verification artifact records freeze-manifest SHA-256 `1ecf52bab2e1989fce31862ac3c2fa890bdc4afd40f5d72cb1ec2ebec1678837`, matching the handoff.

### B6 — Canonical capability-ID leak mutation: **CLOSED**

The verifier now injects both a case ID and an internal canonical capability ID into Qwen-visible text and requires the shared scanner to reject both. The machine report lists ten mutation names, including `canonical_capability_id_leak_detected`.

## 3. Independently confirmed executable evidence

The downloaded Actions artifact contains `verification-report.json` with:

- status `PASS`;
- Python `3.12.13`;
- SWI-Prolog `9.0.4`;
- 12 synthetic TRAIN/DEV cases;
- 80 complete feature-space vectors;
- 80/80 decision-graph ↔ SWI-Prolog agreement;
- nine typed capability contracts valid with budgets and fail-closed semantics;
- 10 named mutation checks;
- exact feature-contract SHA-256 `49ef3a01e7977a44abe4dcc3878d102416e2650218e526d98389e044c6bab92e`;
- exact 30-file freeze-manifest SHA-256 `1ecf52bab2e1989fce31862ac3c2fa890bdc4afd40f5d72cb1ec2ebec1678837`.

The unrelated ENG-153 workflow failure on the same commit is outside ENG-200's evidence scope and does not invalidate the dedicated ENG-200 run.

## 4. New blocking finding

### R2-B1 — Canonical feature serialization contract contradicts the verifier

The normative `ROUTING_FEATURE_CONTRACT.json` states:

`UTF-8 JSON; sort_keys=true; separators=(',', ':'); no whitespace; booleans lowercase`

However `prototype/verify.py::canonical_feature_bytes()` serializes exactly that compact JSON **and then appends a trailing LF (`\n`)** before UTF-8 encoding.

The same function is used to assert byte equality for M19, M20 and direct-Qwen routing. Therefore all three are equal to each other, but the bytes called "canonical" by the executable verifier do not conform to the normative contract's "no whitespace" requirement.

For an ordinary experiment this would be cosmetic. For ENG-200 it is blocking because the causal contract explicitly relies on **exact byte-identical frozen routing inputs**, and an independent implementation following the normative contract would produce different bytes from the verifier.

Required bounded correction — choose exactly one and freeze it:

1. **preferred:** remove the trailing LF from `canonical_feature_bytes()` so the implementation matches the existing normative `no whitespace` contract; or
2. change the normative contract to state that exactly one trailing LF is part of canonical serialization, and update every relevant consumer/test accordingly.

Then regenerate the freeze manifest, rerun the dedicated real SWI-Prolog CI, publish a new handoff-only child, and return to re-review.

No Qwen/Codex behavioral run is required for this correction.

## 5. Non-blocking downstream integration guards

### N1 — Reset/hold equal the post-routing renderer context

ENG-200 is correctly scoped to capability selection, so this is not a blocker here. But when M19/M20 are integrated into an end-to-end answer experiment, M20 has seen typed features + policy explanation + catalogue during routing while the M19 renderer need not have seen them. If the same conversation context is reused for final rendering, final-answer differences can include residual prompt-context effects.

WP-004/runtime integration should therefore either:

- use route-selection accuracy as the routing endpoint and render later in a fresh, held-equal context; or
- explicitly freeze equivalent post-routing renderer-visible context across arms.

### N2 — `requires_strict_policy` may make some routing cases intentionally easy

Within valid claim-resolution requests the feature deliberately selects between the ordinary relational resolver and the strict epistemic resolver. This is now semantically justified rather than an implementation leak, but direct-Qwen/static-router baselines may therefore match the teacher router. That is exactly a STOP/PIVOT outcome already anticipated by ENG-200 and should not be "fixed" by making routing artificially difficult.

## 6. Governance finding

Linear state history again shows a transient `In Progress -> Done -> In Review` transition during remediation, despite the prior review explicitly recording that `Done` is reserved for reviewer PASS. This is the second occurrence.

It did not authorize downstream confirmatory work and is not a scientific blocker, but the workflow/automation that performs producer handoff should be corrected before later critical packages to prevent accidental gate bypass.

## 7. Decision

**REVISE.** The six original scientific/reproducibility blockers are closed, and the core ENG-200 design is otherwise acceptable. One narrow reproducibility contradiction remains in the exact canonical feature-byte contract.

No PIVOT is required.

Minimum evidence for the next re-review:

1. normative feature serialization and executable `canonical_feature_bytes()` agree exactly;
2. freeze manifest regenerated from the corrected candidate;
3. dedicated ENG-200 CI including real SWI-Prolog returns PASS;
4. updated immutable producer handoff from that exact candidate/attestation chain.

Once those four points are satisfied without introducing new drift, ENG-200 should be eligible for **PASS** and `Done`.
