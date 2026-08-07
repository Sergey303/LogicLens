# Nearest Prior Work — WP-003

Status: **producer remediation complete; pending independent re-review**  
As of: **2026-08-07**

The independent review of 2026-08-06 returned **REVISE** because materially close 2026 work was missing and the nearest comparison was not reproducible. This revision incorporates the omitted work and delegates the machine-readable comparison to:

- `context-packets/WP-003/DIMENSION_LEDGER_ALL_2026-08-07.csv`;
- `context-packets/WP-003/NEAREST_WORK_STRUCTURED_2026-08-07.csv`;
- `context-packets/WP-003/NEAREST_RANKING_RULE_2026-08-07.md`.

The producer does **not** accept WP-003 or GATE-001.

## Frozen comparison dimensions

Every included source is scored on the same seven defining dimensions:

1. fixed-weight small/open student;
2. matched contextual/raw/teacher-edited/executed interface contrast;
3. trusted deterministic runtime executing domain semantics;
4. typed `supported` / `refuted` / `unknown` / `conflicting` status;
5. verified result consumed by an LM that remains renderer/interpreter;
6. matched structure/no-conclusion and answer-copying controls;
7. independent oracle/scorer with layer error localization.

The structured nearest table separately records the fields required by ENG-155: exact task, model scale, weight updates, runtime, baselines, data, evaluation, distinction, and primary-source evidence location.

## Architecture anchor 1 — SIGIL (RW-042)

**SIGIL: Compiling Agent Skills into Typed Harnesses** is now the first mandatory comparison.

SIGIL compiles a prose skill into AG-IR, a typed intermediate representation whose nodes explicitly distinguish model-owned cognition from code-owned mechanism and retain source provenance. Accepted AG-IR is lowered deterministically into an executable harness. Its experiment directly compares prose consumption against the compiled harness while keeping authoring behavior on the same model interface.

The paper evaluates 30 skills with `gpt-4o` and `gpt-5`, nine runs per skill per arm per model. The compiled harness raises mandated-step execution from 56% to 86% on the weaker-model sweep, raises complete-procedure execution from 28% to 65%, and reduces median token use. These results occupy several claims that the flagship may not use: typed compiler/runtime separation, code-vs-model ownership, source-grounded compilation, deterministic lowering, and a causal prose-versus-compiled procedure comparison.

**Remaining distinction:** SIGIL compiles procedures, not authoritative domain truth states. It does not test a frozen small renderer consuming a four-state strict-epistemic result contract, nor the flagship's structured-no-conclusion and answer-copying controls.

## Architecture anchor 2 — SkillSmith (RW-038)

SkillSmith compiles heterogeneous skill packages offline into minimal executable boundary contracts exposing typed operators, policies, validation evidence, and fallback paths. It compares Raw-Skills, compiled skill execution and SkVM-style alternatives on SkillsBench and explicitly tests artifact reuse across runtime models and harnesses.

Its current primary paper reports a main GPT-5.5 runtime plus cross-model evaluation with Claude Opus 4.7, DeepSeek V4 Flash, and Qwen3.6 35B A3B, using a SkillsBench checkout with 87 runnable tasks and 227 task-local packages and a seven-task verified suite. The work therefore occupies the broad claim that a stronger compile-time model can produce reusable executable artifacts that reduce repeated interpretation and can help a weaker or more efficient runtime model.

**Remaining distinction:** it does not define or causally test the four-state strict-epistemic semantic-result transport boundary, and does not isolate no-conclusion or ready-answer copying as the alternative explanation.

A screenshot request for the primary arXiv PDF was attempted during this refresh as required by the review workflow, but the screenshot endpoint returned `Cache miss`; experimental facts above are therefore tied to the primary PDF text and page/section locators in the structured table, not a secondary summary.

## Architecture anchor 3 — Ontology-to-tools (RW-039)

Ontology-to-tools compilation transforms formal ontological specifications into executable LLM-callable tools inside The World Avatar. Agents must use those tools to create and modify knowledge-graph instances, so semantic constraints are enforced during generation rather than merely described in prompts or checked after the fact.

This occupies the broad claim that formal domain semantics can be compiled into executable tool interfaces for LLM agents.

**Remaining distinction:** the case is ontology-constrained scientific knowledge extraction and graph construction, not a matched fixed-small-model experiment in which an authoritative four-state query result is passed to a separate renderer.

## High-score compiler/runtime neighbours

The 2026 refresh also found additional work that prevents the paper from treating SkillSmith or SIGIL as isolated exceptions:

- **SkCC (RW-048)** uses a strongly typed skill IR and compile-time analysis for portable cross-framework execution;
- **SkillRT (RW-045)** studies capability-oriented skill compilation and runtime/JIT solidification across models and harnesses;
- **Auto (RW-047)** compiles witnessed-deterministic agent behavior into reusable verified programs or distilled specialists with guard/deoptimization mechanisms;
- **Harnessing LLM Agents with Skill Programs (RW-046)** uses executable Program Functions as runtime interventions;
- **Anything2Skill (RW-049)** compiles heterogeneous external knowledge into reusable procedural skill contracts with evidence/confidence metadata.

These papers mean the flagship cannot retreat to a broad claim about executable skills, typed skill IRs, portable compiled artifacts, or moving repeated agent reasoning into code.

## Offline verified-artifact neighbours

### FACTS (RW-043)

FACTS generates reusable SQL/Jinja2 templates offline, then deterministically executes queries and renders table summaries repeatedly without asking the LLM to reinterpret the entire table each time.

It occupies offline compilation into reusable deterministic artifacts. Its task and evaluation are table summarization rather than strict epistemic decision rendering.

### Skill Discovery (RW-044)

Skill Discovery uses offline LLM simulation and execution feedback to generate and curate reusable scripts for software automation, avoiding unverified code generation at runtime and reporting improvements in success, latency, and token cost.

It occupies offline generation of execution-verified reusable artifacts, but not the four-state result-interface question.

## Solver and faithful-execution anchors

### LINC (RW-003)

LINC combines LM semantic parsing with a first-order theorem prover and demonstrates that an open model such as StarCoder+ can benefit from symbolic execution.

**Occupied:** external formal proof after LM parsing.

**Remaining distinction:** no matched raw/teacher/structured/executed result placement and no four-state result frame consumed by a fixed renderer.

### Logic-LM (RW-002)

Logic-LM translates natural-language reasoning problems into symbolic formulations, runs deterministic solvers, and uses solver feedback to refine formalization errors.

**Occupied:** symbolic formulation plus deterministic inference and solver-feedback correction.

**Remaining distinction:** no fixed-weight semantic-result placement experiment or strict four-state transport contract.

### Faithful Chain-of-Thought (RW-004)

Faithful CoT separates translation, deterministic symbolic solving and answer construction.

**Occupied:** translation-solve-render decomposition for faithful reasoning.

**Remaining distinction:** no explicit four-state open-world epistemic frame and no matched no-conclusion/answer-copying control family.

### SatLM (RW-005)

SatLM asks an LM to generate a declarative specification and delegates satisfiability/theorem proving to an automated solver.

**Occupied:** declarative solver-aided reasoning and correctness relative to the generated specification.

**Remaining distinction:** no matched study of how an authoritative verified result should be exposed to a renderer.

### PAL (RW-001)

PAL establishes the execution-first program-aided baseline: an LM emits executable code and an interpreter computes the result.

**Occupied:** deterministic program execution can improve reasoning.

**Remaining distinction:** no open-world four-state epistemic state preservation or typed verified result-frame transport.

## Mandatory causal-control predecessor — Readout Shortcut (RW-050)

`The Readout Shortcut` is not a compiler/runtime nearest neighbour, but it is a mandatory causal-design comparison. It reports controlled experiments on fixed 1–3B instruction-tuned models in which answer-like trailing values can dominate the model's final readout.

This means the flagship cannot present the answer-copying control as an arbitrary internal precaution. Prior work provides a concrete alternative explanation: a small renderer can appear to benefit from a conclusion-bearing representation simply by copying an answer-like field rather than using the intermediate semantics causally.

The flagship result survives only if the no-conclusion and copying controls rule out that shortcut.

## Layer-diagnosis adjacency — PROTEA (RW-051)

PROTEA evaluates intermediate workflow artifacts and localizes likely faulty nodes before targeted refinement. It narrows any broad claim that layer-wise error localization in LLM workflows is novel.

The remaining distinction is narrower: the flagship requires an independently implemented oracle/scorer tied specifically to source, query, status, policy, frame transport and rendering, rather than general workflow-node diagnostics.

## Comparison verdict after remediation

No defensible priority claim remains for:

- external symbolic or program execution for LMs;
- compile-time versus runtime division of model/code responsibility;
- typed agent-skill intermediate representations;
- executable skill harnesses and portable compiled skills;
- stronger-model artifacts reused by weaker or more efficient runtime models;
- formal semantics compiled into executable LLM tools;
- offline generation of deterministic or execution-verified reusable artifacts;
- translation-solve-render decomposition;
- structured or grammar-constrained output;
- layer-wise workflow diagnostics in the broad sense;
- the observation that small models can copy answer-like fields instead of using reasoning causally.

The remaining candidate comparison is:

> A preregistered matched causal evaluation of **authoritative semantic-result placement** for fixed-weight small language models under a four-state strict epistemic contract, comparing contextual/raw, teacher-edited, structured-no-conclusion, trusted-executed, conclusion-bearing, and answer-copying conditions with an independently implemented layer-specific oracle/scorer.

This is a behavioral causal-study boundary. It is not an invention claim for neuro-symbolic reasoning, Prolog use, agent skill compilation, formal semantics compilation, verified scripts, formal grammars, or compiler-runtime architecture.

## Mandatory adversarial checks

- M6 must beat the DEV-frozen strongest matched non-compiled baseline, not only Raw Prolog.
- Structured/no-authoritative-conclusion and explicit copying controls must survive.
- Available information, token budget, output schema and decoding must be matched.
- The renderer must retain non-trivial obligations; a ready answer alone is insufficient.
- Parser/source errors must be separated from solver/runtime correctness.
- The manuscript must compare directly against SIGIL, SkillSmith, ontology-to-tools, FACTS, Skill Discovery, LINC, Logic-LM, Faithful CoT, SatLM and Readout Shortcut.
- All nearest/control work must be refreshed again before final claim freeze and submission.
