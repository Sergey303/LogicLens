# ENG-155 / WP-003 — Independent Related-Work and Novelty Review

Date: 2026-08-06  
Decision: **REVISE**  
Reviewer role: Research Program Architect  
Gate impact: `GATE-001` remains blocked.

## 1. Scope reviewed

- Linear `ENG-155` producer handoff and amendments;
- `RELATED_WORK_MATRIX.csv`;
- `RELATED_WORK_SEARCH_LOG.yaml`;
- `NEAREST_PRIOR_WORK.md`;
- `NOVELTY_BOUNDARY.md`;
- `handoffs/WP-003.json`;
- current primary pages for the most recent and nearest 2026 work;
- follow-on progressive-core comments only to ensure they do not contaminate the novelty decision.

## 2. Confirmed strengths

- Broad claims for solver-aided reasoning, Prolog use, tool use, constrained output, prompt optimization, compiler-runtime interfaces and ontology compilation are explicitly deleted.
- The surviving contribution is stated as a positive matched causal study, not as `first` or `unique`.
- The matrix exceeds the minimum source count and uses primary proceedings/preprint pages.
- The producer invalidated an earlier saturation claim after finding newer 2026 compiler-runtime work.
- Recent Prolog training, formal verification and faithfulness evaluation are represented.
- The current decision is `NARROW`, not an unsupported novelty victory.

## 3. Blocking findings

### B1 — A materially nearest July 2026 paper is missing

The search misses:

**SIGIL: Compiling Agent Skills into Typed Harnesses**, arXiv:2607.27309, submitted 2026-07-29.

SIGIL compiles prose skills into executable harnesses through a typed agentic IR that separates model-owned cognition from code-owned mechanism. It reports model-independent procedural compliance improvements and token reductions.

This paper directly occupies additional territory currently presented as part of the flagship distinction:

- typed compiler/runtime boundary;
- executable harness instead of repeated contextual interpretation;
- explicit division between model cognition and code mechanism;
- model-independent enforcement by the compiled runtime;
- causal comparison of prose/context execution against compiled mechanism.

It does not appear to occupy the complete strict-epistemic result-interface design, but it must become a top-three nearest neighbour. Until compared dimension by dimension, provisional saturation is invalid.

### B2 — Additional close offline-compilation work is missing

At minimum, screen and disposition:

1. **FACTS: Table Summarization via Offline Template Generation with Agentic Workflows**, Findings ACL 2026. It creates reusable offline SQL/Jinja templates, executes deterministic queries and renders results without sending full data to the LLM.
2. **Skill Discovery for Software Scripting Automation via Offline Simulations with LLMs**, Findings EACL 2026. It uses offline LLM simulation to generate and execution-verify reusable scripts, avoiding unverified runtime code generation.
3. Other July 2026 compiler/workflow papers discovered from SIGIL, SkillSmith and ACL 2026 citation/terminology chains.

These papers may remain adjacent rather than exact, but they occupy offline generation of verified executable artifacts and deterministic post-compilation execution. They must be explicitly included or excluded with recorded reasons.

### B3 — The declared saturation test is not reproducible

The log declares a seven-dimension threshold and two empty rounds, but no machine-readable source-by-dimension score matrix exists. A reviewer cannot reproduce:

- how many dimensions each paper satisfies;
- why a paper is nearest versus adjacent;
- whether Q9/Q10 actually found zero papers at the stated threshold;
- whether screening decisions were consistent.

Required correction:

- create a row for every screened candidate with the seven defining dimensions;
- record `yes / partial / no / unclear` plus evidence location;
- freeze a deterministic nearest-neighbour ranking rule;
- rerun saturation after adding the omitted sources.

### B4 — Search and screening audit trail is incomplete

The search log records databases, queries and added IDs, but not:

- result counts;
- screened titles;
- duplicate resolution;
- excluded candidates and exact exclusion reasons;
- primary-source sections/pages actually read;
- author, version and retrieval identifiers;
- forward-citation source and date.

This is insufficient to support the claim that the exact-profile search is saturated. A registered systematic review is not required, but a reproducible screening ledger is.

### B5 — Required nearest-paper fields are incomplete

ENG-155 explicitly requires exact task, model scale, weight updates, runtime, baselines, data, evaluation and distinction for each close paper.

The current nearest comparison is mostly prose and does not consistently record model scale, datasets, baselines, evaluation endpoints or exact weight-update regime for all seven nearest papers.

Required correction: add a common structured nearest-work table containing every required field and evidence citation for each nearest neighbour.

### B6 — The validator remains artifact-level

The producer handoff acknowledges that the shared validator does not verify source count, URL uniqueness, dimension scoring, nearest IDs, saturation, cross-file consistency or prohibited priority wording.

Required correction: commit a semantic validator that fails on:

- duplicate IDs/URLs;
- missing required fields;
- nearest IDs absent from the matrix;
- nearest comparisons missing required dimensions;
- saturation without two reproducible post-refresh rounds;
- `first`, `unique`, `unprecedented` or general compiler-runtime novelty claims;
- search-log counts inconsistent with the matrix;
- unreviewed recent-source cutoff.

## 4. Novelty boundary after the new attack

The present evidence does **not** yet force a full PIVOT or STOP, but it narrows the contribution further.

The flagship cannot claim novelty for:

- compiler-runtime interfaces;
- typed executable harnesses;
- model/code responsibility separation;
- strong-model compilation reused by weaker runtime models;
- offline generation of verified executable artifacts;
- deterministic execution plus template rendering;
- broad compile-instead-of-teach/train rhetoric.

The remaining candidate contribution is limited to:

> A preregistered matched causal evaluation of authoritative semantic-result placement for fixed-weight small language models under a four-state strict epistemic contract, including no-conclusion and answer-copying controls plus an independently implemented layer-specific oracle/scorer.

That boundary must be tested directly against SIGIL, SkillSmith, ontology-to-tools, FACTS, LINC, Logic-LM, Faithful CoT and SatLM.

## 5. Decision

**REVISE.** Do not expand the matrix by arbitrary source count. Add the missing closest work, create a reproducible screening/dimension ledger, complete the nearest-paper fields, rerun saturation and update the novelty boundary and handoff. No new flagship claim is authorized during remediation.
