# Nearest Prior Work — WP-003

Status: **producer comparison artifact; pending independent review**  
As of: **2026-08-06**

## Common comparison dimensions

The nearest papers are compared on the same dimensions:

1. whether model weights change;
2. whether an LM produces or receives a compiled representation;
3. whether a trusted runtime executes formal or tool semantics;
4. what object is returned after execution;
5. whether a smaller/fixed-weight LM remains responsible for final interpretation/rendering;
6. whether `supported`, `refuted`, `unknown`, and `conflicting` are typed and preserved;
7. whether matched raw, teacher-edited, structured-only, executed, and answer-copying controls exist;
8. whether oracle/scorer independence and layer error localization are central.

## SkillSmith — RW-038

**Shared:** an offline stronger-model/compiler stage turns reusable agent skills into compact executable runtime interfaces that can be consumed by smaller models without changing their weights at deployment time.

**Occupied claim:** a stronger model can compile artifacts once and expose smaller runtime models to reduced, boundary-guided executable interfaces with lower context and reasoning overhead.

**Remaining distinction:** the flagship cannot claim the compiler-runtime pattern or strong-to-small artifact reuse. Its narrower question is whether *placement of authoritative formal semantics* changes strict epistemic contract preservation under one matched causal design. It requires raw/teacher/structured/executed/conclusion controls, four explicit epistemic statuses, source/provenance obligations, an independent oracle, and layer-specific scoring.

**Adversarial consequence:** the title phrase `Compile, Don't Teach` is positioning, not a method-priority claim. The paper must cite SkillSmith prominently and demonstrate that its contribution is causal decomposition rather than another skill compiler.

## Ontology-to-tools Compilation — RW-039

**Shared:** formal knowledge is compiled into typed executable tools so an LLM agent consumes enforced semantic constraints at runtime rather than relying only on textual instructions.

**Occupied claim:** ontology or formal semantics can be compiled into executable tool interfaces for LLM agents.

**Remaining distinction:** ontology-to-tools focuses on executable semantic extraction/actions and stateful agent tooling. The flagship studies a fixed-weight small-model interpreter/renderer after trusted execution and asks whether a typed strict-epistemic *result interface* outperforms matched non-executed representations. It also separates source assertion, request interpretation, derived status, decision policy, proof/evidence, and rendering.

**Adversarial consequence:** the flagship may not claim that compiling formal semantics into executable interfaces is new. It must show value beyond tool enforcement itself.

## LINC — RW-003

**Shared:** LM semantic parsing, FOL execution by an external theorem prover, and evidence that a comparatively small open model benefits from symbolic execution.

**Occupied claim:** an LM can translate natural language into FOL and benefit from an external theorem prover.

**Remaining distinction:** the flagship studies interface placement under one frozen fixed-weight small-model design. Raw context/program, teacher-edited representations, structured controls, executed results, and a typed decision frame are compared; the formal result is consumed by a separate renderer and strict epistemic contract preservation is scored.

## Logic-LM — RW-002

**Shared:** semantic parsing before deterministic inference, solver-driven error feedback, and separation of symbolic inference from free-form LM reasoning.

**Occupied claim:** deterministic symbolic solvers can improve logical reasoning and help refine faulty formalizations.

**Remaining distinction:** the flagship directly contrasts contextual teaching with trusted execution while weights remain fixed. It separates assertion, interpretation, status, policy, frame, and rendering and requires an independent oracle/scorer.

## Faithful Chain-of-Thought — RW-004

**Shared:** translation, symbolic reasoning, and answer construction are separated; deterministic solvers target faithful reasoning.

**Occupied claim:** a translation-plus-solver pipeline can be more faithful than free-form chain of thought.

**Remaining distinction:** the flagship freezes exact epistemic states, policy, provenance, warnings and proof/evidence obligations and uses M6 versus the strongest matched non-compiled baseline—not free-form CoT versus solver alone.

## SatLM — RW-005

**Shared:** LM-generated declarative specification, automated theorem proving, and correctness explicitly conditional on the parsed specification.

**Occupied claim:** declarative specifications plus theorem proving can outperform imperative program-aided reasoning and avoid solver-side planning errors.

**Remaining distinction:** the flagship asks whether a verified **result interface** preserves epistemic behavior better than matched raw or teacher-edited representations, with controls for solver access, structure, tokens, and authoritative answer fields.

## Program-Aided Language Models — RW-001

**Shared:** LM-generated executable representation and deterministic external computation.

**Occupied claim:** executing LM-generated programs can improve reasoning.

**Remaining distinction:** PAL primarily uses execution for program-suitable answers. The flagship focuses on open-world epistemic decisions, keeps a fixed LM as interpreter/renderer after execution, and studies a typed verified decision frame rather than generic program execution.

## Comparison verdict

No defensible priority claim remains for any of the following:

- external symbolic execution for LMs;
- program-aided or solver-aided reasoning;
- compiling formal semantics into executable tools;
- an offline strong model compiling reusable runtime interfaces for a smaller model;
- compile-not-fine-tune rhetoric;
- typed or grammar-constrained outputs;
- automatic prompt/program optimization.

The defensible positive comparison is narrower:

> The study performs a preregistered causal decomposition of where authoritative formal semantics are placed in a fixed-weight small-model pipeline, comparing matched contextual, teacher-edited, structured-only, trusted-executed, and conclusion-bearing interfaces under a typed strict-epistemic contract and independent layer evaluation.

This is a behavioral causal-study boundary. It is not an invention claim for neuro-symbolic reasoning, Prolog tool use, agent skill compilation, ontology compilation, formal grammars, or knowledge compilation.

## Mandatory adversarial checks

- Show M6 is not merely a ready-answer condition.
- Include the strongest structured/no-authoritative-conclusion baseline.
- Match available information, tokens, output schema, and decoding.
- Keep non-trivial obligations for the final renderer.
- Separate parser/source errors from solver correctness.
- Compare directly against compiler-runtime and executable-semantics prior work in the manuscript.
- Refresh all seven nearest works before claim freeze and submission.
