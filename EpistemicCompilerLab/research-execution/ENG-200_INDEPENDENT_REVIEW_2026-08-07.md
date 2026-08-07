# ENG-200 — Independent Tool-Routing and Causal Review

Date: 2026-08-07  
Decision: **REVISE**  
Reviewer role: **Independent Tool-Routing and Causal Reviewer**  
Reviewer session: `ChatGPT ENG-200 independent review / 2026-08-07`  
Producer session recorded in handoff: `ChatGPT ENG-200 producer / 2026-08-07`  
Reviewed implementation merge: `b32de2be597e67280a3f5021e0b46a9f3a323da5`  
Reviewed handoff commit/current main: `1330837a76bff0548a07047216f0040572fe7aa6`  
Reviewed PR: `#74`  
Reviewed CI run/job: `31142949125 / 92756456753`

No HOLDOUT or REPLICATION content was accessed during this review.

## 1. Scope reviewed

- Linear ENG-200 description, relations, state history and producer comments;
- immutable producer handoff `handoffs/ENG-200.json`;
- PR #74 implementation diff;
- routing mode contracts;
- capability registry;
- teacher-generation contract;
- decision-graph and Prolog contracts;
- canonical routing IR and synthetic TRAIN/DEV cases;
- decision-graph executor and deterministic Prolog lowering;
- Qwen-visible neutral/adapted catalogues and frozen policy explanation;
- verifier and explicit leakage-mutation verifier;
- CI steps and downloadable machine-readable verification artifact.

A separate local `git clone` was attempted but this review environment cannot resolve `github.com`; this is an environment DNS limitation, not a project finding. The exact GitHub-hosted CI artifact and source files were independently re-fetched through the connected GitHub source.

## 2. Confirmed strengths

### S1 — One canonical policy source prevents fake tree-vs-Prolog effects

`policy.ir.json` is normative and `generate_policy.py` deterministically lowers it to SWI-Prolog. The Prolog representation is not independently authored. This is the correct design for a representation/runtime comparison: it prevents two different policies from being mislabeled as a representation effect.

### S2 — Real SWI-Prolog execution evidence exists

The successful GitHub Actions job installed SWI-Prolog 9.0.4 and executed the verifier with `--require-swipl`. The downloaded machine-readable report records:

- 9 synthetic TRAIN/DEV cases;
- 80 complete feature-space vectors;
- 80/80 decision-graph ↔ SWI-Prolog agreement;
- 9 mutation checks;
- deterministic generation PASS;
- explicit injected visible case-leak detection PASS.

This is materially stronger than static inspection.

### S3 — Qwen-visible names are separated from internal capability identity

The capability registry keeps canonical IDs internal and exposes opaque handles plus visible labels/descriptions. Neutral and schema-adapted surfaces are represented separately, which is the correct control for the known tool-schema/name adaptation confound.

### S4 — Router scope is appropriately narrow

The package explicitly prohibits the router from computing epistemic status, action, conclusion, SQL result, Prolog proof, Python result or final answer. This is essential if routing is to be studied separately from domain reasoning.

### S5 — No teacher-effect overclaim is made

The handoff correctly states that the committed policy is a producer-authored synthetic contract exemplar, not an empirical Codex-generated policy. No Qwen behavioral effect is claimed and all M19/M20 arms remain DEV-first proposals.

### S6 — Current repository state matches the reviewed handoff chain

`b32de2... -> 1330837...` is exactly one commit adding only `handoffs/ENG-200.json`, and current `main` equals `1330837...`. There is no post-handoff implementation drift at review time.

## 3. Blocking findings

### B1 — M19 vs M20 is not yet causally identifiable because input visibility is underspecified

The package says M19 executes the policy from a frozen typed feature vector, while M20 is described as Qwen receiving the policy explanation plus capability catalogue and choosing a handle. It never freezes whether M20 receives the **same typed feature vector** or must infer those features from the natural-language question.

If M19 receives typed features while M20 must extract them from text, `M19 vs M20` bundles at least two effects:

1. feature extraction;
2. policy following / route selection.

That contradicts the stated interpretation that this contrast isolates Qwen's ability to follow the teacher policy.

Required correction:

- create a separate frozen `ROUTING_FEATURE_CONTRACT` with exact operational definitions;
- for the primary M19-vs-M20 policy-following contrast, feed the same frozen typed features to both arms;
- give the direct-Qwen-selection baseline the same typed features and same neutral catalogue;
- if raw-question routing is scientifically useful, make it a separate DEV-only feature-extraction arm rather than silently bundling it into M20;
- record prompt-visible inputs field-by-field for every routing mode.

### B2 — The required independent feature extractor is not actually frozen

Linear requires the exact feature extractor to be frozen independently of the teacher policy. The prototype instead starts from manually supplied typed features, while the feature contract is embedded inside `policy.ir.json` and its schema.

This leaves a critical causal boundary unresolved. In particular, `requires_strict_policy` is almost a direct selector for the Prolog capability, and `goal_class` is close to a capability-class label for several branches. Unless these features are independently operationalized, the hard routing decision can be encoded upstream and credited to the teacher policy.

Required correction:

- freeze a standalone feature schema/annotation or deterministic extraction contract before teacher policy generation;
- define each feature using request-observable semantics, not target-tool identity;
- specifically justify and adversarially test `requires_strict_policy` against label-proxy leakage;
- hash the feature contract independently and have every policy candidate reference that version/hash;
- record feature-extraction error separately from route-selection error.

### B3 — `ROUTING_CAPABILITY_REGISTRY.yaml` does not satisfy its own typed-capability acceptance contract

The Linear issue requires each capability to declare typed inputs, result schema, provenance obligations, allowed side effects, tool budget and failure semantics.

The current registry has:

- input **field names**, but no field types or input-schema references;
- a `result_contract` string, but no linked/frozen result schema;
- provenance and side-effect flags;
- **no tool budget**;
- **no failure-semantics contract**.

Thus the current catalogue is typed only nominally, not machine-verifiably.

Required correction:

- add frozen input schema references/types per capability;
- add frozen result-schema references;
- add per-capability execution budget fields relevant to the tool class (e.g. calls, timeout, rows/output bytes/tokens as applicable);
- add canonical failure codes/semantics and fail-closed behavior;
- validate these fields mechanically and include them in Qwen-visible catalogues only where visibility is part of the frozen treatment.

### B4 — M19 scope drift: Linear says capability + arguments, implementation selects capability only

The Linear mode definition says M19 selects `capability + arguments` before Qwen acts. The implemented IR and executor return only a capability ID. No argument-binding contract exists in ENG-200.

The narrower design may be scientifically preferable, but it must not remain ambiguous because a hidden adapter could otherwise perform a substantial part of query/tool formation.

Required correction — choose one and freeze it:

1. **preferred:** redefine ENG-200 explicitly as capability-selection-only and add a separate frozen argument binder/formation layer held equal across M19, M20 and direct-Qwen routing; or
2. extend the routing IR to include typed argument-binding decisions and score argument errors separately.

Do not let an unversioned adapter silently supply correct arguments.

### B5 — The immutable handoff hash closure is incomplete

The CI/handoff hashes the registry, IR schema, policy IR, generated Prolog, cases, explanation and two catalogues. Several artifacts that can change scientific interpretation or runtime behavior are not in the frozen closure, including at least:

- `ROUTING_MODE_CONTRACTS.yaml`;
- `TEACHER_POLICY_GENERATION_CONTRACT.md`;
- `DECISION_GRAPH_CONTRACT.md`;
- `PROLOG_ROUTER_CONTRACT.md`;
- `ROUTING_EQUIVALENCE_TESTS.md`;
- `decision_graph.py`;
- `generate_policy.py`;
- `generate_visible_catalogue.py`;
- `verify.py`;
- `verify_leakage_mutation.py`;
- the validation workflow / dependency-version contract where it affects reproducibility.

Required correction:

- create one top-level machine-readable ENG-200 freeze manifest hashing every scientific, visibility, generation, execution and verification artifact;
- make CI validate that manifest from a clean checkout;
- regenerate the producer handoff from the exact accepted candidate/report chain.

### B6 — Adversarial acceptance is not fully demonstrated

The issue explicitly requires mutation coverage for a leaf-ID leak. The current explicit leakage mutation injects a synthetic **case ID**. The normal verifier checks that canonical capability IDs are absent from current Qwen-visible text, but there is no mutation proving that an injected canonical leaf/capability ID is caught by the scanner.

The overlapping-branch requirement is reasonably discharged by the deterministic binary DAG representation: overlap is structurally unavailable and full feature-space enumeration checks lowering agreement. That part is accepted.

Required correction:

- add an explicit canonical-capability-ID leak mutation and require the shared scanner to reject it;
- keep the existing case/question leak mutation;
- report mutation names, not only a mutation count, in the machine-readable report.

## 4. Non-blocking governance finding

Linear state history shows ENG-200 briefly entered `Done` before being returned to `In Review`. This violates the project's rule that a critical task reaches Done only after independent reviewer PASS. Because it was corrected before this review and no evidence was found that this transient state authorized confirmatory work, it is recorded as a process deviation rather than a scientific blocker.

Future producer automation should transition `In Progress -> In Review`, never `In Progress -> Done -> In Review`.

## 5. Items accepted for the next round

The next producer does **not** need to redesign the central approach. The following should be preserved:

- M19/M20 remain DEV-first proposal identifiers until WP-004 adjudication;
- one canonical routing IR;
- deterministic Prolog lowering from that IR;
- no Prolog-specific Qwen-effect claim when downstream inputs are identical;
- canonical internal capability IDs separated from Qwen-visible handles/labels;
- neutral-vs-schema-adapted surface as a separate factor;
- router performs capability routing only unless argument formation is explicitly added as a treatment;
- no HOLDOUT/REPLICATION access;
- no teacher-effect claim from the synthetic exemplar.

No PIVOT is required.

## 6. Decision

**REVISE.** ENG-200 has a sound core design and strong executable tree↔Prolog evidence, but it does not yet satisfy the causal and reproducibility contract required for independent PASS.

Minimum evidence for re-review:

1. frozen standalone feature contract/extractor boundary and identical M19/M20/direct-baseline input contract;
2. operational anti-label-proxy definition/test for `requires_strict_policy`;
3. genuinely typed capability schemas plus budgets and failure semantics;
4. explicit capability-only vs capability+arguments decision and a frozen argument-formation boundary;
5. complete freeze/hash manifest validated in CI;
6. explicit canonical-ID leak mutation and named mutation report;
7. new immutable producer handoff from a clean candidate/attestation chain.

After those bounded corrections, ENG-200 should return to independent review. Behavioral Qwen/Codex runs, costs and confirmatory inclusion remain downstream and are not required to close this design review unless the issue scope is expanded.