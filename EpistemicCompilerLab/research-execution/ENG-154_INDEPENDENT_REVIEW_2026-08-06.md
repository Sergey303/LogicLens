# ENG-154 / WP-002 — Independent Manuscript-Evidence Review

Date: 2026-08-06  
Decision: **REVISE**  
Reviewer role: Manuscript Evidence Reviewer  
Gate impact: `GATE-001` remains blocked.

## 1. Scope reviewed

- Linear issue `ENG-154` and producer handoff;
- `CLAIM_EVIDENCE_MATRIX.yaml`;
- `ABSTRACT_CONTRACT.md`;
- `PROHIBITED_CLAIMS.md`;
- `schemas/claim-evidence-row.schema.json`;
- `handoffs/WP-002.json`;
- current `CAUSAL_CONTRASTS.yaml` and `BASELINE_SELECTION_RULE.yaml`;
- current `statistics/ANALYSIS_REGISTRY.yaml`;
- committed `scripts/validate_claim_evidence.py`.

## 2. Confirmed strengths

- Exactly one intended primary empirical claim (`CLM-003`).
- Seven abstract slots are mapped to explicit claim rows.
- Pilot `18/18` and `24/24` results are treated only as planning evidence.
- Privacy is excluded from the flagship abstract and frozen as future work.
- Each current abstract row includes a control, alternative explanation, target table and retain/narrow/delete logic.
- Universal superiority, learning, privacy, solver/no-solver and answer-copying overclaims are explicitly prohibited.
- The producer disclosed conflict and did not self-accept.

## 3. Blocking findings

### B1 — No reproducible semantic validator

`validate_claim_evidence.py` is only a generic artifact wrapper. It does not perform the producer-claimed semantic checks across the matrix, abstract contract, prohibited-claims contract, causal design and statistics registry.

The handoff cites a local deterministic cross-file audit, but its source and exact command are not committed. Therefore an independent reviewer cannot reproduce the central acceptance result.

Required correction:

- replace or extend `validate_claim_evidence.py` with a committed semantic validator;
- make it fail closed on every condition listed below;
- commit a machine-readable validation report or make the exact command deterministically regenerate it;
- update the handoff to list only commands that actually exist and pass on a clean checkout.

### B2 — Primary contrast drift against WP-004

WP-002 defines a symbolic primary contrast and generic strongest matched baseline. Current WP-004 freezes:

- contrast `C-PRIMARY`;
- treatment `M6`;
- comparator `M14`;
- baseline rule `DEV-GLOBAL-STRONGEST-MATCHED-V2`;
- interpretation as a **multi-component deployed-interface bundle**;
- an explicit prohibition on attributing the primary effect uniquely to execution, type structure, conclusion, compression or rendering.

The claim matrix and abstract must bind to these exact identifiers or explicitly declare unresolved cross-package placeholders that block GATE-001. The current central claim can be read as assigning the gain to compilation/runtime specifically, which is broader than the current primary estimand.

Required correction:

- bind `CLM-003` to `C-PRIMARY`, `M6`, `M14`, `E-PRIMARY-COMPILED-BUNDLE` and the accepted baseline-rule version;
- describe the primary result as a verified-interface **bundle** effect;
- reserve component-level mechanism wording for the separately retained falsification contrasts;
- synchronize ABS-02 and ABS-07 with that boundary.

### B3 — Teacher claim evidence is internally inconsistent

`CLM-006` requires independent reproducibility in its delete/activation rules, but its `confirmatory_evidence` contains only `frozen_holdout`.

Required correction: either add an independently sourced replication result under the frozen teacher protocol, or remove independent-reproducibility wording and keep the claim explicitly HOLDOUT-bounded. The preferred design is HOLDOUT plus independent REPLICATION because current mode coverage already plans teacher diagnostics in both confirmatory sets.

### B4 — Cross-package version drift is not detected

Current WP-004 baseline rule is `DEV-GLOBAL-STRONGEST-MATCHED-V2`, while current WP-006 registry still references `DEV-GLOBAL-STRONGEST-MATCHED-V1`. WP-002 currently masks this mismatch by using an unversioned generic description.

This is not solely a WP-002 authorship error, but WP-002 acceptance requires a claim contract that cannot silently bind to inconsistent causal/statistical specifications.

Required correction:

- semantic validator must compare exact contrast, comparator, endpoint, unit, baseline-rule ID and retain criteria across WP-002, WP-004 and WP-006;
- any mismatch must block WP-002 acceptance and GATE-001;
- after WP-004/WP-006 converge, regenerate the WP-002 handoff hashes.

### B5 — Schema permits unauthorized claim drift

The JSON Schema does not enforce several invariants asserted by the handoff:

- `claim_id` uniqueness;
- exactly ten frozen rows or an explicit reviewed extension mechanism;
- exactly seven `abstract_inclusion: true` rows;
- included rows must use exactly `ABS-01…ABS-07` and may not use `null` or an undeclared `ABS-*`;
- exact cross-field equality between `primary_design` and `CLM-003`;
- `CLM-003` must include both HOLDOUT and independent REPLICATION;
- privacy future-work row must have no flagship confirmatory evidence;
- placeholders in matrix and abstract must match exactly;
- every target table/figure identifier must resolve to a frozen registry entry before freeze.

These may be enforced by JSON Schema where possible and by the semantic validator for cross-record/cross-file invariants.

## 4. Required acceptance command

The corrected package must expose one reviewer command such as:

```text
python EpistemicCompilerLab/research-execution/scripts/validate_claim_evidence.py \
  --matrix EpistemicCompilerLab/research-execution/CLAIM_EVIDENCE_MATRIX.yaml \
  --abstract EpistemicCompilerLab/research-execution/ABSTRACT_CONTRACT.md \
  --prohibited EpistemicCompilerLab/research-execution/PROHIBITED_CLAIMS.md \
  --causal EpistemicCompilerLab/research-execution/CAUSAL_CONTRASTS.yaml \
  --baseline EpistemicCompilerLab/research-execution/BASELINE_SELECTION_RULE.yaml \
  --analysis EpistemicCompilerLab/research-execution/statistics/ANALYSIS_REGISTRY.yaml
```

It must return non-zero on every B1–B5 violation and leave the checkout unchanged.

## 5. Decision

**REVISE.**

The conceptual claim discipline is strong and should be preserved. The revision is limited to reproducible semantic validation, exact cross-package binding, teacher-evidence consistency and stronger invariants. No new claim may be added during remediation. No HOLDOUT or REPLICATION content may be accessed.
