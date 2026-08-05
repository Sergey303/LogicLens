# Prohibited Claims — Compile, Don’t Teach

Status: **normative WP-002 claim boundary**  
Applies to: title, abstract, contribution list, main text, captions, artifact README, press or project summaries.

## 1. Absolute or universal superiority

Do not write:

- “verified compilation is always better”;
- “all LLMs benefit”;
- “the method generalizes to arbitrary domains/tasks/models”;
- “the compiled frame is universally optimal”;
- “perfect” or “solves formal reasoning”.

Allowed boundary:

> Report the preregistered paired effect for the evaluated fixed-weight model profiles, strict epistemic tasks, domains, and source families.

## 2. Solver-versus-no-solver substitution

Do not present `Compiled Frame versus Raw Prolog` alone as proof of the central mechanism.

Do not write:

- “Prolog execution proves the interface advantage”;
- “the model cannot execute programs, therefore compilation wins”;
- “trusted execution is sufficient”.

Required boundary:

> The primary contrast is M6 versus the strongest matched non-compiled baseline, with token, typed-structure, and authoritative-conclusion controls.

## 3. Ready-answer copying

Do not write that a gain reflects formal reasoning relocation when it can be explained by an unmatched `allowedConclusion`, action label, status label, or answer string.

Required boundary:

- report answer-field and typed-frame ablations;
- separate canonical transport from task reasoning;
- delete mechanism wording if the ready-answer control explains the effect.

## 4. Learning or weight modification

Do not write:

- “Codex trained Qwen”;
- “the student learned Prolog”;
- “knowledge was distilled into the model”;
- “the teacher updated the student”;
- “the model acquired formal semantics”.

Allowed boundary:

> The student weights remain unchanged; teacher actions modify only declared prompts or program artifacts.

## 5. Teacher impossibility

Do not write:

- “prompt engineering does not work”;
- “program teaching never works”;
- “strong teachers cannot improve small models”;
- “Codex cannot improve Qwen”.

Allowed boundary:

> Under the tested frozen visibility and budget, contextual teacher editing had the measured mean effect and regression frequency.

## 6. Formal correctness beyond the contract

Do not write:

- “LogicLens proves the answer is true”;
- “the runtime guarantees real-world correctness”;
- “successful Prolog proof validates source extraction”;
- “the system eliminates hallucinations”;
- “verified frame means verified world knowledge”.

Allowed boundary:

> The runtime deterministically executes the loaded, schema-valid formal assertions and rules; source extraction and source truth require separate evidence.

## 7. Privacy and confidentiality

Do not use as empirical claims in the flagship paper:

- “private”;
- “privacy-preserving”;
- “confidentiality guaranteed”;
- “zero data leakage”;
- “the teacher cannot infer private information”;
- “differential privacy”;
- “secure by design”.

Allowed architectural wording:

> Declared private records are outside the teacher-visible development path.

This is a data-flow boundary, not a formal privacy guarantee. `CLM-010` remains future work and is excluded from the abstract.

## 8. Novelty before WP-003

Until `WP-003` passes independent review, do not write:

- “first”;
- “novel”;
- “unprecedented”;
- “the first comparison”;
- “no prior work”.

After WP-003, every novelty statement must be a positive, scoped comparison to named nearest work rather than an absence claim based on search snippets.

## 9. Generalization and replication

Do not write:

- “generalizes” without naming the evaluated strata;
- “replicated” for a rerun on the same source family or after HOLDOUT-informed changes;
- “robust across models” when only one family supports the effect;
- “domain independent”.

Allowed boundary:

> Name the evaluated model families, domains, source families, and independent replication direction; narrow or delete pooled wording when heterogeneity is material.

## 10. Statistical overstatement

Do not write:

- “statistically proven”;
- “no difference” from a non-significant test;
- “equivalent” without a preregistered equivalence/non-inferiority margin;
- “large effect” without the frozen smallest meaningful gain comparison;
- best-seed or best-paraphrase results as the primary estimate.

Required reporting:

- paired absolute effect;
- hierarchical bootstrap 95% interval;
- McNemar result;
- scenario-level unit;
- all failures under frozen rules;
- domain/model heterogeneity;
- independent replication.

## 11. Pilot misuse

The following are planning evidence only:

- compiled-frame `18/18`;
- frozen pilot replication `24/24`;
- B0/B1/C0/D0/D1/D2 opinion or numeric pilots;
- account-default Codex pilot latency;
- any one-repetition pilot.

Do not insert these as confirmatory abstract results or pool them with HOLDOUT/REPLICATION.

## 12. Component minimality

Do not write:

- “every field is necessary”;
- “the full frame is minimal”;
- “proof trace is required”;
- “provenance always improves accuracy”

unless the exact component survives its frozen matched ablation and multiplicity correction.

## 13. Publication decision rule

Any sentence containing prohibited wording is rejected unless a specific claim row:

1. authorizes the wording;
2. identifies a frozen confirmatory source;
3. identifies a target table and metric;
4. passes its retain rule;
5. survives independent manuscript evidence review.

When uncertain, use the row’s failure wording or delete the claim.
