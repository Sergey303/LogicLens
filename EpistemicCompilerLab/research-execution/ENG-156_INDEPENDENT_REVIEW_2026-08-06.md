# ENG-156 / WP-004 — Independent Adversarial Causal-Design Review

Date: 2026-08-06  
Decision: **REVISE**  
Reviewer role: Senior Adversarial Gatekeeper  
Gate impact: `GATE-001` remains blocked.

## 1. Scope reviewed

- Linear `ENG-156` and producer amendments;
- `CAUSAL_CONTRASTS.yaml`;
- `MODE_CONTRACTS/modes.yaml` and README;
- `BASELINE_SELECTION_RULE.yaml`;
- `ESTIMANDS.yaml`;
- `ALTERNATIVE_EXPLANATIONS.md`;
- `handoffs/WP-004.json`;
- current WP-002 claim contract and WP-006 analysis registry;
- normative target-paper roadmap and critical protocols;
- `scripts/validate_causal_design.py`.

## 2. Confirmed strengths

- The earlier deterministic truncation of M14 was correctly removed.
- Matching is now lossless: the common envelope is the block maximum and only shorter modes receive neutral padding.
- One global B* is selected on DEV for the headline, with a mandatory profile-specific sensitivity.
- M6–M14 is now honestly described as a multi-component deployed-interface bundle effect.
- M6 versus Raw Prolog alone is prohibited as the headline causal result.
- M9–M14 cover structure, conclusion, deterministic rendering, corruption, compiler-boundary and strongest-source controls.
- PIVOT/STOP rules explicitly allow null, minimal-contract, no-LLM-renderer and compiler-boundary outcomes.
- The producer disclosed the material initial design defect rather than hiding it.

## 3. Blocking findings

### B1 — Task acceptance contradicts the corrected estimand

The Linear acceptance still requires:

> the primary contrast changes exactly one scientifically interpretable factor.

The current and scientifically honest design states that M6–M14 is a **multi-component bundle** changing trusted execution, result availability, representation and interface obligations together. The handoff marks this as PASS despite the explicit task criterion not being satisfied.

This is a governance defect, not a reason to return to a falsely isolated interpretation.

Required correction:

- amend the Linear/context-packet acceptance to state that the headline primary contrast estimates one deployed-interface bundle;
- require one-factor or clearly bounded secondary falsification estimands for any mechanism attribution;
- update the objective from “separately measures” to “estimates the bundle and tests competing mechanism explanations”;
- synchronize WP-002 wording with the bundle boundary.

### B2 — M10 drifts from the normative contract

The frozen roadmap defines M10 as the minimal verified `status/action` decision contract. Current `modes.yaml` exposes only `status`.

This changes the answer-copying decomposition materially:

- status-only tests class-label copying;
- status+action tests a minimal executable decision contract;
- conclusion-only tests direct answer copying;
- the current design does not clearly distinguish all three.

Required correction: choose and name explicit minimal controls. At minimum:

- retain a `status+action` minimal decision mode as the normative M10; and
- state whether a conclusion-only control is required or why M6–M12 plus M10 identifies the intended copying threat.

Do not silently reuse the same mode ID for a different semantic contract.

### B3 — M9 does not identify “typed structure” alone

M6–M9 changes typed fields into frozen prose. Even with identical semantic values and token envelope, it changes serialization, ordering, lexical cues, redundancy and parsing burden.

Therefore `E-STRUCTURE` is too narrow. The contrast estimates a typed-versus-unstructured **result-interface serialization bundle**, not pure type structure.

Required correction:

- rename/reword the estimand and claims;
- freeze a canonical lossless serialization with a machine-verifiable semantic-equivalence transform;
- prohibit claims that field typing alone caused the effect unless an additional control isolates field names/container structure.

### B4 — Corruption sensitivity lacks a validity contract

M13 mutates one field, but not every one-field mutation is detectable from the remaining visible information. If an authoritative, internally consistent status or conclusion is changed without redundant evidence, following it may be the contractually correct behavior rather than “blind corruption following.”

Required correction:

For every mutation family preregister:

- corrupted field;
- whether contradiction is externally detectable from remaining frame/question content;
- expected safe behavior;
- valid answer set;
- scoring rule;
- whether the test measures consistency checking, authority following or fabrication.

Analyze detectable and non-detectable corruptions separately. Never aggregate “follow corruption” as universally unsafe.

### B5 — Neutral padding can itself create a treatment effect

Exact token equality prevents length confounding but does not prove padding is behaviorally neutral. Long neutral tails, placement and repeated tokens can alter attention or salience differently across modes.

Required correction:

- freeze exact padding bytes, placement and tokenizer-specific construction;
- include a DEV-only padding invariance audit comparing padded and unpadded versions of representative modes;
- set a predeclared tolerance for padding-induced degradation;
- if invariance fails, redesign matching before benchmark construction rather than keeping a harmful “matched” envelope;
- report both unpadded and padded token counts and padding fraction.

### B6 — M11 comparability is underspecified

The common contract exempts M11 from the same output schema. Yet the claim “LLM renderer unnecessary” requires comparison on the same semantic answer obligations and scoring record.

Required correction:

- M11 may use a deterministic internal adapter, but must emit or be deterministically mapped to the same canonical answer schema;
- freeze identical required fields, language/content obligations and failure treatment;
- separate task correctness from stylistic preference;
- define non-inferiority/equivalence criterion rather than relying only on informal “matches or exceeds.”

### B7 — Cross-package V1/V2 drift remains unresolved

WP-004 freezes `DEV-GLOBAL-STRONGEST-MATCHED-V2`; current WP-006 registry references `V1`. WP-002 also does not yet bind exact current IDs.

Required correction:

- make the causal validator compare exact contrast, estimand, comparator, baseline-rule version, endpoint and unit against WP-002 and WP-006;
- fail closed on drift;
- regenerate all affected handoffs after convergence.

### B8 — No committed semantic validator

`validate_causal_design.py` remains a generic artifact wrapper. It does not check:

- unique M0–M14 IDs and complete mode fields;
- exact visible/hidden/authoritative contracts;
- no semantic truncation path;
- M10 normative semantics;
- all estimands resolve to declared modes;
- each alternative explanation maps to a contrast and decision;
- primary bundle wording;
- baseline-rule consistency;
- M13 mutation contract;
- M11 scoring comparability;
- cross-package WP-002/WP-006 alignment.

Required correction: commit a non-mutating semantic validator and exact reviewer command that fails on B1–B8.

## 4. Required scientific interpretation

After remediation, the headline claim may be only:

> the total effect of a trusted compiled verified-result interface bundle versus the strongest losslessly matched non-compiled source interface.

Execution, typed structure, conclusion fields, renderer value and corruption behavior remain secondary falsification questions. They may be claimed only to the extent supported by their separately valid contrasts.

## 5. Decision

**REVISE.** Preserve the lossless matching, global/profile baseline rules and honest bundle estimand. Correct the task contract, mode semantics, corruption and padding validity, deterministic-renderer comparability, cross-package drift and validator before independent re-review.
