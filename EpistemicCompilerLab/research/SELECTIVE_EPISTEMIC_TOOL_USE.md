# Selective Epistemic Tool Use

Status: research protocol baseline  
Primary system: LogicLens Epistemic DSL + verified capsule query runtime  
Primary question: when should an LLM answer directly, query a verified epistemic capsule, or combine both paths?

## 1. Core research claim

The strongest publication target is not merely that symbolic tools improve average accuracy. The target claim is:

> A language model can route queries between direct parametric answering and a verified epistemic capsule so that it preserves most of the capsule's reliability gains while avoiding unnecessary latency, token cost and tool-use failures on queries that the model already answers well.

This study treats tool use as a selective decision under an explicit quality-cost trade-off.

## 2. Why this is stronger than a full-DSL implementation paper

A nearly complete DSL is an engineering contribution, but completeness alone does not establish scientific value. The study should instead use a publication-complete executable subset and evaluate:

1. necessity: whether the capsule contains information or semantics that the model cannot safely recover from parametric memory;
2. utility: whether the returned verified frame changes the final answer in a beneficial way;
3. affordability: whether the accuracy or calibration gain justifies latency, tokens and tool invocations;
4. faithfulness: whether the model uses the returned status, evidence, scope and warnings rather than fabricating or ignoring them;
5. abstention: whether `unknown` and `conflicting` are preserved instead of collapsed into unsupported certainty.

## 3. Experimental conditions

Every case is evaluated under the same answer schema and scoring code.

### D0 — Direct

Codex receives only the question and public task instructions. No capsule data or tools.

### D1 — Full context

Codex receives a serialized relevant capsule or evidence subset directly in the prompt, but cannot call `capsule_query.py`. This separates the value of information from the value of verified execution.

### D2 — Always query

Codex must call `capsule_query.py` before answering every case.

### D3 — Self-routed

Codex decides whether to answer directly or query the capsule.

### D4 — Learned or rule-based router

A lightweight router decides among direct and capsule paths using only pre-answer features. Candidate features include predicate availability, entity/version specificity, explicit source requirement, contradiction cues, model uncertainty, prior per-family performance and estimated tool latency.

### D5 — Oracle router

For each case, choose the path with the highest observed utility. This is an upper bound for routing rather than a deployable system.

### D6 — Hybrid material-formal

Codex performs material interpretation and planning; the capsule supplies only verified epistemic frames for atomic claims. The final answer must bind every tool-supported statement to a returned query hash and evidence set.

## 4. Benchmark families

The benchmark must intentionally contain cases where each path is preferable. Labels are determined by frozen ground truth, not by which system happens to win.

### 4.1. Direct-favoured cases

These test unnecessary-tool cost and noise.

- stable, common, non-versioned facts likely to be present in model memory;
- simple transformations where all inputs are in the question;
- writing or explanation tasks where no capsule claim is needed;
- questions outside the capsule's declared predicate space;
- cases where the capsule correctly returns `unknown`, but the task is answerable from supplied local context without making a world claim;
- deliberately irrelevant capsule attachments.

Expected result: Direct should match or beat Always-query on latency and often on answer quality because no formal lookup is needed.

### 4.2. Capsule-favoured cases

These test information and semantics unavailable or unsafe in parametric memory.

- private or newly generated facts absent from training data;
- exact document versions, dates, local policies and source-bound scopes;
- explicit negative evidence where absence must not be treated as false;
- `unknown` cases requiring abstention;
- conflicting evidence from independent dependency groups;
- cases where a familiar role or term has a local definition that differs from common usage;
- multi-hop strict rules over capsule assertions;
- quantitative cases requiring typed units, bounds or a deterministic policy;
- adversarially plausible statements contradicted by the capsule;
- stale-memory cases where the public fact changed after a frozen model knowledge date.

Expected result: Capsule-backed paths should improve strict status, scope preservation, provenance and abstention.

### 4.3. Hybrid-favoured cases

These require both language understanding and formal verification.

- a free-form memo containing several atomic claims, only some of which map to the capsule;
- a scenario requiring business judgement plus strict role-boundary checks;
- ambiguous language that requires clarification before formal query construction;
- multiple candidate formalizations where only one type-checks;
- decision tasks where the capsule verifies premises but does not choose the business trade-off.

Expected result: Hybrid should beat both Direct and raw Always-query because the LLM handles material inference while the DSL handles formal epistemic status.

### 4.4. Tool-adversarial controls

These diagnose tool-use failures separately from final accuracy.

- tool available but unnecessary;
- tool required and result non-guessable;
- tool returns `unknown`;
- tool returns conflict;
- tool returns evidence that contradicts the model's draft;
- tool result is malformed or times out;
- package hash or semantic ID is invalid;
- capsule is valid but stale for the question's requested version.

## 5. Publication-complete Epistemic DSL subset

Implement features only when they support a benchmark family and can be deterministically verified.

### Layer A — strict claims

Already substantially implemented:

- typed predicates and semantic IDs;
- support and oppose assertions;
- provenance and source manifests;
- dependency groups;
- scope and generalisability;
- open-world `supported`, `refuted`, `unknown`, `conflicting`;
- deterministic capsule packages and query hashes;
- Python/SWI-Prolog cross-verification.

### Layer B — strict logical derivation

Add:

- `logical_rule` declarations;
- safe allowlisted operators: `all`, `any`, `not_explicit`, `exists`;
- proof DAG in the query result;
- cycle and unsafe-variable rejection;
- derived-claim regression tests.

### Layer C — typed observations

Add:

- `point`, `bounded` and `normal` values;
- explicit units and conversion allowlists;
- observation provenance and dependency groups;
- deterministic numerical kernels;
- query operations for value, bounds and source trace.

### Layer D — fuzzy membership

Add only deterministic v0 functions:

- triangle;
- trapezoid;
- piecewise linear;
- expected membership for point and bounded inputs;
- conservative membership bounds;
- no free-form LLM-authored arithmetic.

### Layer E — decision policies

Add:

- threshold policies over verified strict, numeric and fuzzy inputs;
- explicit policy ID and version;
- decision output separated from world facts;
- full input and assumption trace;
- fail-closed handling of missing inputs.

### Layer F — assessments and calibrated uncertainty

Defer until Layers A–E are stable. A minimal later extension may support:

- classifier scores with named calibration adapters;
- beta opinions;
- credible intervals distinct from credal bounds;
- dependency-aware fusion;
- conflict preserved separately from uncertainty.

Do not claim a nearly complete DSL until this layer has independent numerical oracle tests.

## 6. Dataset construction

### 6.1. Sources

Use at least three domains with different epistemic structures:

1. management and software governance: role boundaries, versioned frameworks, local policies;
2. engineering specifications: typed measurements, ranges, revisions and exceptions;
3. scientific or technical classification: uncertainty, conflicting evidence and fuzzy categories.

At least one domain must use private or procedurally generated source material that cannot be answered from model memory.

### 6.2. Case generation

Create case templates from formal query plans, then generate multiple natural-language paraphrases without exposing labels to the evaluated model.

Each case record should include:

- immutable case ID and family;
- question text;
- required semantic interpretation;
- expected tool necessity: direct, capsule, hybrid or either;
- expected formal queries;
- expected status, evidence IDs, scope and action;
- answer rubric;
- expected abstention behaviour;
- cost weight profile;
- source and generation hashes.

### 6.3. Splits

- TRAIN: router development and extractor diagnostics;
- DEV: threshold and policy selection;
- HOLDOUT: frozen evaluation used once per selected system;
- REPLICATION: different sources, entities and paraphrase generator.

Split by source families and rule templates, not only by question text, to prevent near-duplicate leakage.

## 7. Primary metrics

### 7.1. Answer quality

- exact task accuracy;
- atomic claim precision, recall and F1;
- strict status accuracy;
- scope-preservation accuracy;
- provenance precision and recall;
- decision-policy accuracy;
- contradiction rate.

### 7.2. Epistemic behaviour

- unknown-preservation rate;
- conflict-preservation rate;
- unsupported-certainty rate;
- selective accuracy at fixed coverage;
- risk-coverage curve and area;
- calibration error for declared confidence where applicable.

### 7.3. Tool behaviour

- necessary-tool recall;
- unnecessary-tool avoidance;
- tool-skip rate;
- result-ignore rate;
- output-fabrication rate;
- malformed-query rate;
- successful correction after a rejected query.

### 7.4. Efficiency

- end-to-end latency p50, p95 and mean;
- model input and output tokens;
- number of tool calls;
- SWI-Prolog execution time;
- package loading and validation time;
- bytes of context supplied;
- quality-cost utility under multiple predeclared cost weights.

Report Pareto frontiers rather than one arbitrary combined score.

## 8. Main hypotheses

H1. Always-query improves epistemic correctness on capsule-favoured cases but is slower and no better on direct-favoured controls.

H2. Direct answering has lower latency and equal or higher quality on direct-favoured cases, demonstrating that indiscriminate symbolic augmentation is suboptimal.

H3. A selective router approaches the oracle quality-cost frontier and dominates both Direct and Always-query over the mixed benchmark.

H4. Hybrid material-formal answering has the highest accuracy on cases requiring both natural-language interpretation and strict verification.

H5. Verified frames improve `unknown`, conflict, scope and provenance behaviour more than they improve ordinary binary accuracy.

H6. Most residual hybrid errors originate in semantic parsing and query construction rather than the deterministic DSL runtime.

## 9. Ablations

- remove scope and generalisability warnings;
- remove dependency groups;
- replace SWI-Prolog execution with JSONL-only status calculation;
- provide raw evidence without a verified frame;
- provide the full capsule in context instead of querying;
- remove Python/SWI-Prolog cross-verification;
- corrupt one source or package hash;
- remove explicit `unknown` action;
- compare one query with batched queries;
- compare cold and warm package loading;
- compare exact-rule router, k-nearest-neighbour router and LLM self-routing.

## 10. Statistical protocol

- predeclare the primary endpoint before HOLDOUT evaluation;
- use paired evaluation because every system sees the same cases;
- report bootstrap confidence intervals for accuracy and utility deltas;
- use McNemar tests for paired binary correctness comparisons;
- report latency distributions and paired non-parametric comparisons;
- correct for multiple comparisons across secondary ablations;
- publish every failed tool call and excluded case with a reason;
- repeat stochastic LLM conditions across multiple runs;
- freeze model identifiers, prompts, schemas, source hashes and runtime versions.

## 11. Proposed paper framing

Working title:

> Selective Epistemic Tool Use: When Verified Knowledge Capsules Help Language Models

Primary contributions:

1. a benchmark explicitly containing direct-favoured, capsule-favoured and hybrid-favoured cases;
2. a verified open-world capsule runtime preserving support, opposition, unknown, conflict, scope, dependency and provenance;
3. a diagnostic tool-use taxonomy separating skip, unnecessary call, ignored result and fabricated output;
4. a cost-aware routing evaluation with oracle and deployable router baselines;
5. evidence that the largest gains occur in epistemic behaviour, not necessarily in ordinary factual questions.

## 12. First implementation milestone

Do not begin with the full uncertainty stack. The next milestone is:

1. add safe `logical_rule` compilation and proof DAGs;
2. add a batch query operation to reduce process startup cost;
3. add a benchmark schema with direct/capsule/hybrid necessity labels;
4. generate an initial balanced 90-case engineering benchmark: 30 cases per family;
5. run Direct, Full-context, Always-query and Oracle-routing baselines;
6. use the observed error distribution to decide whether typed observations or fuzzy membership is the next justified DSL layer.

The first 90-case run is an engineering study. Publication claims require a larger frozen holdout, independent source families, repeated model runs and external replication.