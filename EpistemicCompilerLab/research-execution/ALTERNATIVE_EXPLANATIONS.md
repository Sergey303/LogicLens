# Alternative Explanations and Falsification Controls — WP-004

Status: **producer causal-design artifact; pending distinct independent review**

## Primary interpretation boundary

The primary contrast is `M6 − M14(global B*)`. It estimates the total effect of a trusted compiled verified-interface bundle versus the globally strongest full-information non-compiled source interface under matched student, question, answer schema and a lossless common token envelope that has separately passed the frozen padding-invariance audit.

It is intentionally a bundle estimand. It does not by itself identify whether execution, typed structure, explicit conclusion, provenance, policy fields or another component causes the effect. Component claims require separately valid contrasts.

## 1. Solver versus no solver

**Threat:** M6 wins only because one condition receives a solved task while the other must reason.

**Controls:** M14 is the strongest full-information non-compiled source interface; M9, M10 and M12 progressively test verified-result serialization, a minimal executed status/action contract and direct conclusion availability; M7 diagnoses production compiler loss.

**Falsification:** The primary result may support only a bundle effect. If minimal M10 already matches M6 and materially beats M14, rich-frame necessity is not supported. If M12 does not materially outperform M14 while M6 does, the effect is concentrated in `allowedConclusion` and the paper pivots accordingly.

## 2. Ready-answer / decision copying

**Threat:** `allowedConclusion`, or even a verified minimal decision label, gives the student most of the answer.

**Controls:** M12 removes only `allowedConclusion`; normative M10 contains **verified status + action**, not status alone; M14 contains no computed result. The decomposition is therefore:

- `M6 − M12`: incremental effect of `allowedConclusion`;
- `M12 − M10`: bundled effect of scope/provenance/evidence/warnings/proof fields beyond the minimal status/action decision contract;
- `M10 − M14`: value of a minimal executed decision contract versus strongest non-compiled source context.

A status-only arm is not silently encoded as M10. If later scientifically necessary it requires a new versioned identifier before HOLDOUT.

**Falsification:** If M10 explains essentially all of M6's gain, report a minimal executable decision-contract result rather than rich verified-frame necessity. If only M6−M12 is substantial, direct conclusion availability is the dominant measured component.

## 3. Result-interface serialization rather than “typing alone”

**Threat:** JSON field names, ordering, lexical cues, redundancy or reduced parsing burden explain M6 relative to an unstructured verified result.

**Control:** M9 contains exactly the same verified semantic values as M6 through a canonical deterministic lossless serialization. A pre-model round-trip verifier must prove semantic field/value equivalence.

**Interpretation boundary:** `M6 − M9` is a **typed-frame versus canonical unstructured result-interface serialization bundle**. It is not evidence that field typing alone caused any difference.

**Falsification:** If M9 matches M6, the tested typed/structured serialization bundle has no measured marginal value. A future pure-typing claim would require an additional matched control that changes only the relevant container/field-typing factor.

## 4. Token length and behaviorally active padding

**Threat:** M6 is easier because its input is shorter, more salient, or because the chosen “neutral” padding changes attention or decoding behavior.

**Controls:** No compared mode may lose assertions, rules, policy clauses, provenance or verified-frame fields for token matching. For each scenario/model-profile block, the common envelope equals the maximum unpadded token count among compared LLM modes. Only shorter modes receive scenario-independent padding whose exact bytes, placement and tokenizer-specific token IDs are frozen by `MODE_CONTRACTS/PADDING_INVARIANCE_CONTRACT.yaml`.

Before benchmark construction, representative DEV cases for every student profile must compare padded versus unpadded behavior. A failing mode/profile blocks the matching design; exact token equality is not treated as evidence that padding is inert.

**Falsification:** Informative padding, truncation, outcome-dependent selection, post-HOLDOUT repair, source deletion, or a failed padding-invariance gate invalidates the length-control claim and requires redesign before split freeze.

## 5. Additional or missing information rather than execution

**Threat:** M6 receives facts unavailable to controls, or M14 is weakened by truncation.

**Controls:** M14 retains the complete selected B* representation from the same scenario/source package available to the compiler. Hidden gold and other-mode outputs are prohibited. Source-manifest and information-retention audits run before model calls.

**Falsification:** A source-manifest mismatch or missing assertion/rule invalidates the scenario block rather than being adjusted after scoring.

## 6. Convenient global baseline

**Threat:** one global B* is not the strongest non-compiled comparator for every student model profile.

**Controls:** the headline keeps one globally DEV-selected B* to avoid outcome-driven switching, while a mandatory secondary sensitivity applies the same frozen ranking independently within each model profile.

**Falsification:** If M6 survives global B* but is non-inferior or worse against a profile-specific strongest baseline, the pooled/model-general claim is narrowed and that profile receives no compilation-advantage claim.

## 7. Strong-teacher contextual improvement

**Threat:** a sufficiently strong teacher can produce an equally effective prompt or program without execution.

**Controls:** M4/M5 use fixed TRAIN-only and aggregate-DEV-only budgets; no DEV questions, HOLDOUT, replication or computed result is visible; teacher artifacts can enter B* selection only if their complete representation fits the lossless envelope.

**Falsification:** If M4 or M5 becomes B* and is non-inferior to M6, reject the compilation-advantage headline.

## 8. LLM renderer is unnecessary

**Threat:** once the frame exists, deterministic templating is as good as or better than an LLM.

**Control:** M11 consumes the exact M6 semantic frame and deterministically emits the same canonical answer/scoring schema, semantic fields, language/content obligations and failure taxonomy. `MODE_CONTRACTS/M11_RENDERER_COMPARABILITY.yaml` freezes the secondary non-inferiority rule; style/preference metrics remain descriptive.

**Falsification:** If M11 is non-inferior to M6 under the frozen criterion, state that an LLM renderer was unnecessary for the evaluated task class under the tested obligations. Efficiency or style cannot rescue an LLM-necessity claim.

## 9. Corruption following versus legitimate authority following

**Threat:** M13 could falsely label a model unsafe for following an authoritative corrupted field that cannot be contradicted from the remaining visible information.

**Control:** `MODE_CONTRACTS/M13_MUTATION_CONTRACT.yaml` preregisters, per mutation instance, the corrupted field, detectability from remaining visible bytes, witness/reason, expected safe behavior, valid answer set, scoring rule and semantic role.

Detectable inconsistency tests and non-detectable authority-following tests are separate estimands. Hidden M6 truth alone cannot turn a visible mutation into a detectable one.

**Falsification:** Practically important silent following of **detectable** contradictions narrows auditability/safety claims. Following a **non-detectable** visible authoritative value is not automatically scored unsafe and is never pooled into a universal “blind corruption” rate.

## 10. Production compiler/query errors

**Threat:** errors attributed to the renderer originate in extraction, query building or compilation.

**Control:** M7 supplies an independent gold frame to the same renderer.

**Falsification:** A large M7−M6 gap relocates the main bottleneck to the production boundary and blocks renderer-centric interpretation.

## 11. Shared oracle/scorer error

**Threat:** production compiler and evaluator encode the same bug.

**Controls required downstream:** independent path B, no imports/calls to production path A, mutation suite, differential checks, source-bound gold and preserved disagreements.

**Falsification:** Failure of dependency or mutation audit blocks all correctness and mechanism claims.

## 12. One favorable model, domain or status

**Threat:** pooled effect is driven by one stratum.

**Controls:** one global headline B*, profile-wise strongest sensitivity, scenario-level clustered analysis, preregistered model/domain/status tables and independent replication.

**Falsification:** practically important reversal, profile-control failure or single-stratum dominance forces explicit narrowing.

## 13. Strong-model ceiling

**Threat:** the local pipeline is less useful than simply using a strong remote model.

**Control:** M8 records accuracy, latency, tokens, hardware and amortized teacher cost.

**Interpretation:** M8 is an economic/quality ceiling, not the primary causal baseline. A strong M8 result must still be reported.

## 14. Conventional executable alternatives and routing responsibility

**Threat:** a simpler relational, SQL→Prolog, router, or hidden-Python interface explains the same benefit at lower complexity; alternatively the main bottleneck is Qwen query/tool selection rather than semantic representation.

**Control:** candidate M15–M22 are governed by `MODE_CONTRACTS/TRANSFER_LADDER_ADJUDICATION.yaml`. No candidate becomes confirmatory merely because its subtask produced an artifact. Exact upstream independent acceptance, factor vectors, semantic ownership, WP-006 power and WP-007 feasibility are required before activation.

**Falsification/PIVOT:** if a simpler accepted conventional executable result interface matches M6, prefer and report the simpler engineering boundary and narrow custom-interface necessity. If deterministic result selection is strong but Qwen tool/query selection is weak, localize the bottleneck to routing/selection.

## 15. Weight-changing adaptation is a separate boundary study

**Threat:** apparent teacher-interface advantage disappears once Qwen weights are adapted, or Codex-generated training data adds nothing beyond ordinary matched gold-only adaptation.

**Control:** ENG-202 remains outside fixed-weight M-modes. W-C must be compared with matched W-B; no best-seed selection; fixed-weight versus adapted-weight reporting is a separate boundary result with its own leakage, seed, power, rollback and feasibility contract.

**Current status:** not activatable until the mandatory real Linux/CUDA smoke and distinct independent ENG-202 review are complete.

## 16. World truth and privacy overclaim

Runtime correctness is only relative to validated loaded assertions and rules. Fixed-weight and local execution do not prove source truth, confidentiality, differential privacy or absence from RAM/VRAM. These are prohibited alternative interpretations, not measured outcomes of WP-004.
